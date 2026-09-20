import { toInt } from '../utils/helpers';
import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth, requireAdmin } from '../middleware/auth';

const router = Router();

// ----------------------------------------------------------------------------
// POST /api/feedback (Public or User feedback submission)
// ----------------------------------------------------------------------------
router.post('/feedback', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { category, message, severity, page_url, user_agent } = req.body || {};
    if (!message || !message.trim()) {
      return res.status(400).json({ detail: 'Feedback message cannot be empty.' });
    }

    const ins = await query(
      `INSERT INTO feedback (user_id, category, message, severity, status, page_url, user_agent)
       VALUES ($1, $2, $3, $4, 'new', $5, $6)
       RETURNING *`,
      [
        req.user!.id,
        category || 'general',
        message.trim(),
        severity || 'Normal',
        page_url || null,
        user_agent || req.headers['user-agent'] || null,
      ]
    );

    return res.status(201).json({ message: 'Feedback submitted successfully', feedback: ins.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to submit feedback' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/admin/overview
// ----------------------------------------------------------------------------
router.get('/overview', requireAdmin, async (_req: AuthenticatedRequest, res: Response) => {
  try {
    const totalUsersRes = await query('SELECT COUNT(*) FROM users');
    const activeUsersRes = await query('SELECT COUNT(*) FROM users WHERE is_active = 1');
    const totalMissionsRes = await query('SELECT COUNT(*) FROM mission_logs');
    const totalHabitsRes = await query('SELECT COUNT(*) FROM habit_logs');
    const totalFeedbackRes = await query("SELECT COUNT(*) FROM feedback WHERE status = 'new'");

    return res.json({
      total_users: parseInt(totalUsersRes.rows[0].count, 10),
      active_users: parseInt(activeUsersRes.rows[0].count, 10),
      total_missions_completed: parseInt(totalMissionsRes.rows[0].count, 10),
      total_habits_logged: parseInt(totalHabitsRes.rows[0].count, 10),
      pending_feedback: parseInt(totalFeedbackRes.rows[0].count, 10),
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch admin overview' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/admin/users
// ----------------------------------------------------------------------------
router.get('/users', requireAdmin, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const limit = Math.min(100, toInt(req.query.limit) || 50);
    const search = (req.query.search as string || '').trim().toLowerCase();

    let sql = `
      SELECT id, email, username, full_name, role, is_active, 
             mkc_id, avatar_initials, email_verified, onboarding_completed, created_at
      FROM users
    `;
    const params: any[] = [];

    if (search) {
      sql += ` WHERE LOWER(email) LIKE $1 OR LOWER(username) LIKE $1 OR LOWER(full_name) LIKE $1`;
      params.push(`%${search}%`);
    }

    sql += ` ORDER BY id DESC LIMIT $${params.length + 1}`;
    params.push(limit);

    const result = await query(sql, params);
    return res.json({ users: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch users' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/admin/users/:userId
// ----------------------------------------------------------------------------
router.get('/users/:userId', requireAdmin, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = toInt(req.params.userId);
    const result = await query(
      `SELECT id, email, username, full_name, role, is_active, mkc_id, 
              avatar_initials, bio, email_verified, onboarding_completed, created_at 
       FROM users 
       WHERE id = $1`,
      [userId]
    );

    if (result.rows.length === 0) return res.status(404).json({ detail: 'User not found' });
    return res.json({ user: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch user' });
  }
});

// ----------------------------------------------------------------------------
// PATCH /api/admin/users/:userId/role
// ----------------------------------------------------------------------------
router.patch('/users/:userId/role', requireAdmin, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = toInt(req.params.userId);
    const { role } = req.body || {};
    if (!role || !['user', 'admin'].includes(role)) {
      return res.status(400).json({ detail: 'Invalid role' });
    }

    await query('UPDATE users SET role = $1 WHERE id = $2', [role, userId]);
    return res.json({ message: 'Role updated successfully' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to update role' });
  }
});

// ----------------------------------------------------------------------------
// PATCH /api/admin/users/:userId/status
// ----------------------------------------------------------------------------
router.patch('/users/:userId/status', requireAdmin, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = toInt(req.params.userId);
    const { is_active } = req.body || {};
    const activeVal = is_active ? 1 : 0;

    await query('UPDATE users SET is_active = $1 WHERE id = $2', [activeVal, userId]);
    if (!activeVal) {
      await query('UPDATE app_sessions SET revoked_at = CURRENT_TIMESTAMP WHERE user_id = $1', [userId]);
    }

    return res.json({ message: 'Status updated successfully' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to update status' });
  }
});

// ----------------------------------------------------------------------------
// PATCH /api/admin/users/:userId/email
// ----------------------------------------------------------------------------
router.patch('/users/:userId/email', requireAdmin, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = toInt(req.params.userId);
    const { email } = req.body || {};
    if (!email || !email.includes('@')) {
      return res.status(400).json({ detail: 'Invalid email' });
    }

    await query('UPDATE users SET email = $1 WHERE id = $2', [email.trim().toLowerCase(), userId]);
    return res.json({ message: 'Email updated successfully' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to update email' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/admin/feedback
// ----------------------------------------------------------------------------
router.get('/feedback', requireAdmin, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await query(
      `SELECT f.*, u.username, u.email 
       FROM feedback f
       JOIN users u ON f.user_id = u.id
       ORDER BY f.created_at DESC`
    );
    return res.json({ feedback: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch feedback' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/admin/feedback/stats
// ----------------------------------------------------------------------------
router.get('/feedback/stats', requireAdmin, async (_req: AuthenticatedRequest, res: Response) => {
  try {
    const total = await query('SELECT COUNT(*) FROM feedback');
    const newCount = await query("SELECT COUNT(*) FROM feedback WHERE status = 'new'");
    const resolved = await query("SELECT COUNT(*) FROM feedback WHERE status = 'resolved'");

    return res.json({
      total: parseInt(total.rows[0].count, 10),
      new: parseInt(newCount.rows[0].count, 10),
      resolved: parseInt(resolved.rows[0].count, 10),
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch feedback stats' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/admin/feedback/:id
// ----------------------------------------------------------------------------
router.get('/feedback/:id', requireAdmin, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const id = toInt(req.params.id);
    const result = await query(
      `SELECT f.*, u.username, u.email 
       FROM feedback f
       JOIN users u ON f.user_id = u.id
       WHERE f.id = $1`,
      [id]
    );
    if (result.rows.length === 0) return res.status(404).json({ detail: 'Feedback not found' });
    return res.json({ feedback: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch feedback item' });
  }
});

// ----------------------------------------------------------------------------
// PATCH /api/admin/feedback/:id
// ----------------------------------------------------------------------------
router.patch('/feedback/:id', requireAdmin, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const id = toInt(req.params.id);
    const { status, admin_notes } = req.body || {};
    const updates: string[] = [];
    const params: any[] = [];
    let pIdx = 1;

    if (status !== undefined) {
      updates.push(`status = $${pIdx++}`);
      params.push(status);
      if (status === 'resolved') {
        updates.push('resolved_at = CURRENT_TIMESTAMP');
      }
    }
    if (admin_notes !== undefined) {
      updates.push(`admin_notes = $${pIdx++}`);
      params.push(admin_notes);
    }

    if (updates.length === 0) return res.json({ message: 'No updates' });

    updates.push('updated_at = CURRENT_TIMESTAMP');
    params.push(id);

    const sql = `UPDATE feedback SET ${updates.join(', ')} WHERE id = $${pIdx} RETURNING *`;
    const result = await query(sql, params);

    return res.json({ feedback: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to update feedback' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/admin/feedback/:id
// ----------------------------------------------------------------------------
router.delete('/feedback/:id', requireAdmin, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const id = toInt(req.params.id);
    await query('DELETE FROM feedback WHERE id = $1', [id]);
    return res.json({ message: 'Feedback deleted successfully' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to delete feedback' });
  }
});

export default router;
