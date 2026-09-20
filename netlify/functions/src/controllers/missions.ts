import { toInt } from '../utils/helpers';
import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

function getTodayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

// ----------------------------------------------------------------------------
// GET /api/missions
// ----------------------------------------------------------------------------
router.get('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const today = getTodayStr();
    const userId = req.user!.id;

    // Fetch user missions
    const missionsRes = await query(
      `SELECT id, title, description, category, time, difficulty, xp_reward, goal_id, created_at 
       FROM missions 
       WHERE user_id = $1 
       ORDER BY id ASC`,
      [userId]
    );

    // Fetch today's completions from mission_logs
    const logsRes = await query(
      `SELECT mission_id 
       FROM mission_logs 
       WHERE user_id = $1 AND completed_date = $2`,
      [userId, today]
    );

    const completedToday = new Set(logsRes.rows.map((r) => r.mission_id));

    const missions = missionsRes.rows.map((m) => ({
      ...m,
      completed: completedToday.has(m.id) ? 1 : 0,
    }));

    return res.json({ missions });
  } catch (err: any) {
    console.error('[Missions] Error fetching missions:', err);
    return res.status(500).json({ detail: err?.message || 'Failed to fetch missions' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/missions
// ----------------------------------------------------------------------------
router.post('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { title, description, category, time, difficulty, xp_reward, goal_id } = req.body || {};
    if (!title || !title.trim()) {
      return res.status(400).json({ detail: 'Mission title is required.' });
    }

    const ins = await query(
      `INSERT INTO missions (title, description, category, time, difficulty, xp_reward, completed, user_id, goal_id)
       VALUES ($1, $2, $3, $4, $5, $6, 0, $7, $8)
       RETURNING id, title, description, category, time, difficulty, xp_reward, completed, user_id, goal_id, created_at`,
      [
        title.trim(),
        description ? description.trim() : '',
        category || 'general',
        time || '15 min',
        difficulty || 'easy',
        xp_reward || 10,
        req.user!.id,
        goal_id || null,
      ]
    );

    return res.status(201).json({ mission: ins.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to create mission' });
  }
});

// ----------------------------------------------------------------------------
// PATCH /api/missions/:missionId/toggle (and POST)
// ----------------------------------------------------------------------------
const toggleHandler = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const missionId = toInt(req.params.missionId);
    const userId = req.user!.id;
    const today = getTodayStr();

    // Verify mission exists and belongs to user
    const mRes = await query('SELECT id, xp_reward FROM missions WHERE id = $1 AND user_id = $2', [
      missionId,
      userId,
    ]);

    if (mRes.rows.length === 0) {
      return res.status(404).json({ detail: 'Mission not found' });
    }

    const mission = mRes.rows[0];
    const xpReward = mission.xp_reward || 10;

    // Check if completed today in mission_logs
    const logCheck = await query(
      'SELECT id FROM mission_logs WHERE user_id = $1 AND mission_id = $2 AND completed_date = $3',
      [userId, missionId, today]
    );

    let completed = 0;
    let xpEarned = 0;

    if (logCheck.rows.length > 0) {
      // Uncomplete for today
      await query('DELETE FROM mission_logs WHERE id = $1', [logCheck.rows[0].id]);
      await query('UPDATE missions SET completed = 0 WHERE id = $1', [missionId]);
      completed = 0;
    } else {
      // Complete for today
      await query(
        `INSERT INTO mission_logs (user_id, mission_id, completed_date, xp_reward)
         VALUES ($1, $2, $3, $4)
         ON CONFLICT (user_id, mission_id, completed_date) DO NOTHING`,
        [userId, missionId, today, xpReward]
      );
      await query('UPDATE missions SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = $1', [missionId]);
      completed = 1;
      xpEarned = xpReward;
    }

    return res.json({
      message: completed ? 'Mission completed' : 'Mission marked incomplete',
      mission_id: missionId,
      completed,
      xp_earned: xpEarned,
    });
  } catch (err: any) {
    console.error('[Missions] Toggle error:', err);
    return res.status(500).json({ detail: err?.message || 'Failed to toggle mission' });
  }
};

router.patch('/:missionId/toggle', requireAuth, toggleHandler);
router.post('/:missionId/toggle', requireAuth, toggleHandler);

export default router;
