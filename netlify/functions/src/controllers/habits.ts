import { toInt } from '../utils/helpers';
import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

function getTodayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

// ----------------------------------------------------------------------------
// GET /api/habits
// ----------------------------------------------------------------------------
router.get('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const today = getTodayStr();
    const userId = req.user!.id;

    const habitsRes = await query(
      `SELECT id, title, description, category, frequency, target_days_per_week, status, created_at 
       FROM habits 
       WHERE user_id = $1 
       ORDER BY id ASC`,
      [userId]
    );

    const logsRes = await query(
      `SELECT habit_id, completed_date 
       FROM habit_logs 
       WHERE user_id = $1 
       ORDER BY completed_date DESC`,
      [userId]
    );

    // Group logs by habit_id
    const logsByHabit: Record<number, string[]> = {};
    for (const log of logsRes.rows) {
      if (!logsByHabit[log.habit_id]) logsByHabit[log.habit_id] = [];
      logsByHabit[log.habit_id].push(log.completed_date);
    }

    const habits = habitsRes.rows.map((h) => {
      const dates = logsByHabit[h.id] || [];
      const completedToday = dates.includes(today);

      // Calculate streak
      let streak = 0;
      let checkDate = new Date();
      if (!completedToday) {
        // check if yesterday was completed
        checkDate.setDate(checkDate.getDate() - 1);
      }

      while (true) {
        const dStr = checkDate.toISOString().slice(0, 10);
        if (dates.includes(dStr)) {
          streak++;
          checkDate.setDate(checkDate.getDate() - 1);
        } else {
          break;
        }
      }

      return {
        ...h,
        completed_today: completedToday ? 1 : 0,
        streak,
        total_completions: dates.length,
      };
    });

    return res.json({ habits });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch habits' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/habits
// ----------------------------------------------------------------------------
router.post('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { title, description, category, frequency, target_days_per_week } = req.body || {};
    if (!title || !title.trim()) {
      return res.status(400).json({ detail: 'Habit title is required.' });
    }

    const ins = await query(
      `INSERT INTO habits (user_id, title, description, category, frequency, target_days_per_week, status)
       VALUES ($1, $2, $3, $4, $5, $6, 'active')
       RETURNING id, title, description, category, frequency, target_days_per_week, status, created_at`,
      [
        req.user!.id,
        title.trim(),
        description || '',
        category || 'general',
        frequency || 'daily',
        target_days_per_week || 7,
      ]
    );

    return res.status(201).json({ habit: ins.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to create habit' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/habits/stats
// ----------------------------------------------------------------------------
router.get('/stats', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    const totalHabitsRes = await query('SELECT COUNT(*) FROM habits WHERE user_id = $1 AND status = $2', [
      userId,
      'active',
    ]);
    const totalCompletionsRes = await query('SELECT COUNT(*) FROM habit_logs WHERE user_id = $1', [userId]);

    return res.json({
      active_habits: parseInt(totalHabitsRes.rows[0].count, 10),
      total_completions: parseInt(totalCompletionsRes.rows[0].count, 10),
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch habit stats' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/habits/:habitId/toggle
// ----------------------------------------------------------------------------
router.post('/:habitId/toggle', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const habitId = toInt(req.params.habitId);
    const userId = req.user!.id;
    const today = getTodayStr();

    // Verify habit belongs to user
    const hRes = await query('SELECT id FROM habits WHERE id = $1 AND user_id = $2', [habitId, userId]);
    if (hRes.rows.length === 0) {
      return res.status(404).json({ detail: 'Habit not found' });
    }

    const check = await query('SELECT id FROM habit_logs WHERE habit_id = $1 AND completed_date = $2', [
      habitId,
      today,
    ]);

    let completed = false;
    if (check.rows.length > 0) {
      await query('DELETE FROM habit_logs WHERE id = $1', [check.rows[0].id]);
      completed = false;
    } else {
      await query(
        `INSERT INTO habit_logs (habit_id, user_id, completed_date)
         VALUES ($1, $2, $3)
         ON CONFLICT (habit_id, completed_date) DO NOTHING`,
        [habitId, userId, today]
      );
      completed = true;
    }

    return res.json({
      message: completed ? 'Habit completed for today' : 'Habit uncompleted for today',
      completed,
      habit_id: habitId,
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to toggle habit' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/habits/:habitId
// ----------------------------------------------------------------------------
router.get('/:habitId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const habitId = toInt(req.params.habitId);
    const result = await query('SELECT * FROM habits WHERE id = $1 AND user_id = $2', [habitId, req.user!.id]);
    if (result.rows.length === 0) return res.status(404).json({ detail: 'Habit not found' });
    return res.json({ habit: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch habit' });
  }
});

// ----------------------------------------------------------------------------
// PATCH /api/habits/:habitId
// ----------------------------------------------------------------------------
router.patch('/:habitId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const habitId = toInt(req.params.habitId);
    const { title, description, category, frequency, target_days_per_week, status } = req.body || {};
    const updates: string[] = [];
    const params: any[] = [];
    let pIdx = 1;

    if (title !== undefined) { updates.push(`title = $${pIdx++}`); params.push(title.trim()); }
    if (description !== undefined) { updates.push(`description = $${pIdx++}`); params.push(description.trim()); }
    if (category !== undefined) { updates.push(`category = $${pIdx++}`); params.push(category); }
    if (frequency !== undefined) { updates.push(`frequency = $${pIdx++}`); params.push(frequency); }
    if (target_days_per_week !== undefined) { updates.push(`target_days_per_week = $${pIdx++}`); params.push(target_days_per_week); }
    if (status !== undefined) { updates.push(`status = $${pIdx++}`); params.push(status); }

    if (updates.length === 0) return res.json({ message: 'No updates' });

    params.push(habitId, req.user!.id);
    const sql = `UPDATE habits SET ${updates.join(', ')} WHERE id = $${pIdx++} AND user_id = $${pIdx} RETURNING *`;
    const result = await query(sql, params);

    return res.json({ habit: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to update habit' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/habits/:habitId
// ----------------------------------------------------------------------------
router.delete('/:habitId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const habitId = toInt(req.params.habitId);
    await query('DELETE FROM habits WHERE id = $1 AND user_id = $2', [habitId, req.user!.id]);
    return res.json({ message: 'Habit deleted successfully' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to delete habit' });
  }
});

export default router;
