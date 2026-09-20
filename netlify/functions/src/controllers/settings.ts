import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

router.get('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await query(
      `SELECT theme, notifications_enabled, coach_style, daily_reminder_time, profile_visibility 
       FROM user_settings 
       WHERE user_id = $1`,
      [req.user!.id]
    );

    if (result.rows.length === 0) {
      // Create defaults
      const ins = await query(
        `INSERT INTO user_settings (user_id, theme, notifications_enabled, coach_style, daily_reminder_time, profile_visibility)
         VALUES ($1, 'dark', 1, 'strategic', '08:00', 'public')
         RETURNING theme, notifications_enabled, coach_style, daily_reminder_time, profile_visibility`,
        [req.user!.id]
      );
      return res.json({ settings: ins.rows[0] });
    }

    return res.json({ settings: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch settings' });
  }
});

router.patch('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { theme, notifications_enabled, coach_style, daily_reminder_time, profile_visibility } = req.body || {};
    const updates: string[] = [];
    const params: any[] = [];
    let pIdx = 1;

    if (theme !== undefined) {
      updates.push(`theme = $${pIdx++}`);
      params.push(theme);
    }
    if (notifications_enabled !== undefined) {
      updates.push(`notifications_enabled = $${pIdx++}`);
      params.push(notifications_enabled ? 1 : 0);
    }
    if (coach_style !== undefined) {
      updates.push(`coach_style = $${pIdx++}`);
      params.push(coach_style);
    }
    if (daily_reminder_time !== undefined) {
      updates.push(`daily_reminder_time = $${pIdx++}`);
      params.push(daily_reminder_time);
    }
    if (profile_visibility !== undefined) {
      updates.push(`profile_visibility = $${pIdx++}`);
      params.push(profile_visibility);
    }

    if (updates.length === 0) {
      return res.json({ message: 'No settings modified' });
    }

    updates.push(`updated_at = CURRENT_TIMESTAMP`);
    params.push(req.user!.id);

    const sql = `UPDATE user_settings SET ${updates.join(', ')} WHERE user_id = $${pIdx} RETURNING theme, notifications_enabled, coach_style, daily_reminder_time, profile_visibility`;
    const result = await query(sql, params);

    return res.json({
      message: 'Settings updated successfully',
      settings: result.rows[0],
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to update settings' });
  }
});

export default router;
