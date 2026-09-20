import { toInt } from '../utils/helpers';
import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

// ----------------------------------------------------------------------------
// GET /api/social/connections
// ----------------------------------------------------------------------------
router.get('/connections', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    const result = await query(
      `SELECT c.id, c.requester_id, c.recipient_id, c.status, c.created_at,
              u1.username AS requester_username, u1.full_name AS requester_name, u1.avatar_initials AS requester_avatar,
              u2.username AS recipient_username, u2.full_name AS recipient_name, u2.avatar_initials AS recipient_avatar
       FROM user_connections c
       JOIN users u1 ON c.requester_id = u1.id
       JOIN users u2 ON c.recipient_id = u2.id
       WHERE (c.requester_id = $1 OR c.recipient_id = $1)
       ORDER BY c.created_at DESC`,
      [userId]
    );

    return res.json({ connections: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch connections' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/social/connections/request
// ----------------------------------------------------------------------------
router.post('/connections/request', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { recipient_id } = req.body || {};
    const requesterId = req.user!.id;

    if (!recipient_id || recipient_id === requesterId) {
      return res.status(400).json({ detail: 'Invalid recipient ID.' });
    }

    const ins = await query(
      `INSERT INTO user_connections (requester_id, recipient_id, status)
       VALUES ($1, $2, 'pending')
       ON CONFLICT (requester_id, recipient_id) DO UPDATE SET status = 'pending', updated_at = CURRENT_TIMESTAMP
       RETURNING *`,
      [requesterId, recipient_id]
    );

    return res.status(201).json({ connection: ins.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to request connection' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/social/connections/accept
// ----------------------------------------------------------------------------
router.post('/connections/accept', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { connection_id } = req.body || {};
    const userId = req.user!.id;

    const result = await query(
      `UPDATE user_connections 
       SET status = 'accepted', updated_at = CURRENT_TIMESTAMP 
       WHERE id = $1 AND recipient_id = $2
       RETURNING *`,
      [connection_id, userId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ detail: 'Connection request not found' });
    }

    return res.json({ message: 'Connection accepted', connection: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to accept connection' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/social/connections/reject
// ----------------------------------------------------------------------------
router.post('/connections/reject', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { connection_id } = req.body || {};
    await query('DELETE FROM user_connections WHERE id = $1 AND recipient_id = $2', [connection_id, req.user!.id]);
    return res.json({ message: 'Connection rejected' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to reject connection' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/social/follow/:userId
// ----------------------------------------------------------------------------
router.post('/follow/:userId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const targetUserId = toInt(req.params.userId);
    const followerId = req.user!.id;

    if (targetUserId === followerId) {
      return res.status(400).json({ detail: 'Cannot follow yourself.' });
    }

    await query(
      `INSERT INTO user_follows (follower_id, following_id)
       VALUES ($1, $2)
       ON CONFLICT DO NOTHING`,
      [followerId, targetUserId]
    );

    return res.json({ message: 'Followed successfully', following: true });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to follow' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/social/unfollow/:userId
// ----------------------------------------------------------------------------
router.post('/unfollow/:userId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const targetUserId = toInt(req.params.userId);
    await query('DELETE FROM user_follows WHERE follower_id = $1 AND following_id = $2', [
      req.user!.id,
      targetUserId,
    ]);
    return res.json({ message: 'Unfollowed successfully', following: false });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to unfollow' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/social/followers/:userId
// ----------------------------------------------------------------------------
router.get('/followers/:userId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = toInt(req.params.userId);
    const result = await query(
      `SELECT u.id, u.username, u.full_name, u.avatar_initials, u.bio 
       FROM user_follows f
       JOIN users u ON f.follower_id = u.id
       WHERE f.following_id = $1`,
      [userId]
    );
    return res.json({ followers: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch followers' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/social/following/:userId
// ----------------------------------------------------------------------------
router.get('/following/:userId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = toInt(req.params.userId);
    const result = await query(
      `SELECT u.id, u.username, u.full_name, u.avatar_initials, u.bio 
       FROM user_follows f
       JOIN users u ON f.following_id = u.id
       WHERE f.follower_id = $1`,
      [userId]
    );
    return res.json({ following: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch following' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/social/follow-stats/:userId
// ----------------------------------------------------------------------------
router.get('/follow-stats/:userId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = toInt(req.params.userId);
    const followersRes = await query('SELECT COUNT(*) FROM user_follows WHERE following_id = $1', [userId]);
    const followingRes = await query('SELECT COUNT(*) FROM user_follows WHERE follower_id = $1', [userId]);
    const isFollowingRes = await query(
      'SELECT id FROM user_follows WHERE follower_id = $1 AND following_id = $2',
      [req.user!.id, userId]
    );

    return res.json({
      followers_count: parseInt(followersRes.rows[0].count, 10),
      following_count: parseInt(followingRes.rows[0].count, 10),
      is_following: isFollowingRes.rows.length > 0,
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch stats' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/social/search
// ----------------------------------------------------------------------------
router.get('/search', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const q = (req.query.q as string || '').trim().toLowerCase();
    const result = await query(
      `SELECT id, username, full_name, avatar_initials, bio 
       FROM users 
       WHERE is_active = 1 AND id != $1 AND (LOWER(username) LIKE $2 OR LOWER(full_name) LIKE $2) 
       LIMIT 20`,
      [req.user!.id, `%${q}%`]
    );
    return res.json({ users: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Search failed' });
  }
});

export default router;
