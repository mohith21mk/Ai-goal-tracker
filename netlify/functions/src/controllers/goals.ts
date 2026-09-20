import { toInt } from '../utils/helpers';
import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

// ============================================================================
// GOALS ENDPOINTS (/api/goals)
// ============================================================================

router.get('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await query(
      `SELECT id, title, description, category, status, target_date, blueprint_id, milestone_id, created_at 
       FROM goals 
       WHERE user_id = $1 
       ORDER BY id ASC`,
      [req.user!.id]
    );
    return res.json({ goals: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch goals' });
  }
});

router.post('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { title, description, category, status, target_date, blueprint_id, milestone_id } = req.body || {};
    if (!title || !title.trim()) {
      return res.status(400).json({ detail: 'Goal title is required.' });
    }

    const result = await query(
      `INSERT INTO goals (user_id, title, description, category, status, target_date, blueprint_id, milestone_id)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
       RETURNING id, title, description, category, status, target_date, blueprint_id, milestone_id, created_at`,
      [
        req.user!.id,
        title.trim(),
        description ? description.trim() : '',
        category || 'general',
        status || 'active',
        target_date || null,
        blueprint_id || null,
        milestone_id || null,
      ]
    );

    return res.status(201).json({ goal: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to create goal' });
  }
});

router.get('/:goalId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const goalId = toInt(req.params.goalId);
    const result = await query(
      `SELECT id, title, description, category, status, target_date, blueprint_id, milestone_id, created_at 
       FROM goals 
       WHERE id = $1 AND user_id = $2`,
      [goalId, req.user!.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ detail: 'Goal not found' });
    }

    return res.json({ goal: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch goal' });
  }
});

router.patch('/:goalId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const goalId = toInt(req.params.goalId);
    const { title, description, category, status, target_date } = req.body || {};
    const updates: string[] = [];
    const params: any[] = [];
    let pIdx = 1;

    if (title !== undefined) {
      updates.push(`title = $${pIdx++}`);
      params.push(title.trim());
    }
    if (description !== undefined) {
      updates.push(`description = $${pIdx++}`);
      params.push(description.trim());
    }
    if (category !== undefined) {
      updates.push(`category = $${pIdx++}`);
      params.push(category);
    }
    if (status !== undefined) {
      updates.push(`status = $${pIdx++}`);
      params.push(status);
    }
    if (target_date !== undefined) {
      updates.push(`target_date = $${pIdx++}`);
      params.push(target_date);
    }

    if (updates.length === 0) {
      return res.json({ message: 'No updates provided' });
    }

    params.push(goalId, req.user!.id);
    const sql = `UPDATE goals SET ${updates.join(', ')} WHERE id = $${pIdx++} AND user_id = $${pIdx} RETURNING id, title, description, category, status, target_date, blueprint_id, milestone_id, created_at`;
    const result = await query(sql, params);

    if (result.rows.length === 0) {
      return res.status(404).json({ detail: 'Goal not found' });
    }

    return res.json({ goal: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to update goal' });
  }
});

router.delete('/:goalId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const goalId = toInt(req.params.goalId);
    await query('DELETE FROM goals WHERE id = $1 AND user_id = $2', [goalId, req.user!.id]);
    return res.json({ message: 'Goal deleted successfully' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to delete goal' });
  }
});

export default router;
