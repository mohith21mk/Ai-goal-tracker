import { toInt } from '../utils/helpers';
import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

// ----------------------------------------------------------------------------
// GET /api/notifications
// ----------------------------------------------------------------------------
router.get('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await query(
      `SELECT id, user_id, type, title, message, reference_type, reference_id, data, is_read, created_at 
       FROM notifications 
       WHERE user_id = $1 
       ORDER BY created_at DESC 
       LIMIT 50`,
      [req.user!.id]
    );

    return res.json({ notifications: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch notifications' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/notifications/unread-count
// ----------------------------------------------------------------------------
router.get('/unread-count', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await query('SELECT COUNT(*) FROM notifications WHERE user_id = $1 AND is_read = 0', [
      req.user!.id,
    ]);
    return res.json({ unread_count: parseInt(result.rows[0].count, 10) });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch count' });
  }
});

// ----------------------------------------------------------------------------
// PATCH /api/notifications/read-all & /read_all
// ----------------------------------------------------------------------------
const readAllHandler = async (req: AuthenticatedRequest, res: Response) => {
  try {
    await query('UPDATE notifications SET is_read = 1 WHERE user_id = $1', [req.user!.id]);
    return res.json({ message: 'All notifications marked as read' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to mark notifications read' });
  }
};

router.patch('/read-all', requireAuth, readAllHandler);
router.patch('/read_all', requireAuth, readAllHandler);

// ----------------------------------------------------------------------------
// PATCH /api/notifications/:id/read
// ----------------------------------------------------------------------------
router.patch('/:id/read', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const id = toInt(req.params.id);
    await query('UPDATE notifications SET is_read = 1 WHERE id = $1 AND user_id = $2', [id, req.user!.id]);
    return res.json({ message: 'Notification marked as read' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to update notification' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/notifications/:id
// ----------------------------------------------------------------------------
router.delete('/:id', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const id = toInt(req.params.id);
    await query('DELETE FROM notifications WHERE id = $1 AND user_id = $2', [id, req.user!.id]);
    return res.json({ message: 'Notification deleted' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to delete notification' });
  }
});

export default router;
