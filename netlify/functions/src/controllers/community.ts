import { toInt } from '../utils/helpers';
import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

// ----------------------------------------------------------------------------
// GET /api/community/posts
// ----------------------------------------------------------------------------
router.get('/posts', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    const category = req.query.category as string;
    const limit = Math.min(50, toInt(req.query.limit) || 20);

    let sql = `
      SELECT p.id, p.user_id, p.author_name, p.content, p.category, 
             p.credential_id, p.likes_count, p.created_at,
             u.username, u.avatar_initials,
             CASE WHEN l.id IS NOT NULL THEN 1 ELSE 0 END AS user_liked,
             (SELECT COUNT(*) FROM community_comments c WHERE c.post_id = p.id) AS comments_count
      FROM community_posts p
      JOIN users u ON p.user_id = u.id
      LEFT JOIN community_likes l ON p.id = l.post_id AND l.user_id = $1
    `;
    const params: any[] = [userId];

    if (category && category !== 'all') {
      sql += ` WHERE p.category = $2`;
      params.push(category);
    }

    sql += ` ORDER BY p.created_at DESC LIMIT $${params.length + 1}`;
    params.push(limit);

    const result = await query(sql, params);
    return res.json({ posts: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch posts' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/community/posts
// ----------------------------------------------------------------------------
router.post('/posts', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { content, category, credential_id } = req.body || {};
    if (!content || !content.trim()) {
      return res.status(400).json({ detail: 'Post content cannot be empty.' });
    }

    const ins = await query(
      `INSERT INTO community_posts (user_id, author_name, content, category, credential_id, likes_count)
       VALUES ($1, $2, $3, $4, $5, 0)
       RETURNING *`,
      [
        req.user!.id,
        req.user!.full_name,
        content.trim(),
        category || 'general',
        credential_id || null,
      ]
    );

    return res.status(201).json({ post: ins.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to create post' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/community/posts/:postId
// ----------------------------------------------------------------------------
router.get('/posts/:postId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const postId = toInt(req.params.postId);
    const result = await query(
      `SELECT p.*, u.username, u.avatar_initials,
              CASE WHEN l.id IS NOT NULL THEN 1 ELSE 0 END AS user_liked
       FROM community_posts p
       JOIN users u ON p.user_id = u.id
       LEFT JOIN community_likes l ON p.id = l.post_id AND l.user_id = $1
       WHERE p.id = $2`,
      [req.user!.id, postId]
    );

    if (result.rows.length === 0) return res.status(404).json({ detail: 'Post not found' });
    return res.json({ post: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch post' });
  }
});

// ----------------------------------------------------------------------------
// PATCH /api/community/posts/:postId
// ----------------------------------------------------------------------------
router.patch('/posts/:postId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const postId = toInt(req.params.postId);
    const { content, category } = req.body || {};
    const updates: string[] = [];
    const params: any[] = [];
    let pIdx = 1;

    if (content !== undefined) { updates.push(`content = $${pIdx++}`); params.push(content.trim()); }
    if (category !== undefined) { updates.push(`category = $${pIdx++}`); params.push(category); }

    if (updates.length === 0) return res.json({ message: 'No updates' });

    params.push(postId, req.user!.id);
    const sql = `UPDATE community_posts SET ${updates.join(', ')} WHERE id = $${pIdx++} AND user_id = $${pIdx} RETURNING *`;
    const result = await query(sql, params);

    if (result.rows.length === 0) return res.status(404).json({ detail: 'Post not found or unauthorized' });
    return res.json({ post: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to update post' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/community/posts/:postId
// ----------------------------------------------------------------------------
router.delete('/posts/:postId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const postId = toInt(req.params.postId);
    const isAdm = req.user!.role === 'admin';
    const where = isAdm ? 'WHERE id = $1' : 'WHERE id = $1 AND user_id = $2';
    const params = isAdm ? [postId] : [postId, req.user!.id];

    await query(`DELETE FROM community_posts ${where}`, params);
    return res.json({ message: 'Post deleted successfully' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to delete post' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/community/posts/:postId/like
// ----------------------------------------------------------------------------
router.post('/posts/:postId/like', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const postId = toInt(req.params.postId);
    const userId = req.user!.id;

    const exists = await query('SELECT id FROM community_likes WHERE post_id = $1 AND user_id = $2', [postId, userId]);

    let liked = false;
    if (exists.rows.length > 0) {
      await query('DELETE FROM community_likes WHERE id = $1', [exists.rows[0].id]);
      await query('UPDATE community_posts SET likes_count = GREATEST(0, likes_count - 1) WHERE id = $1', [postId]);
      liked = false;
    } else {
      await query('INSERT INTO community_likes (post_id, user_id) VALUES ($1, $2) ON CONFLICT DO NOTHING', [postId, userId]);
      await query('UPDATE community_posts SET likes_count = likes_count + 1 WHERE id = $1', [postId]);
      liked = true;
    }

    const postRes = await query('SELECT likes_count FROM community_posts WHERE id = $1', [postId]);
    return res.json({
      liked,
      likes_count: postRes.rows[0]?.likes_count || 0,
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to toggle like' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/community/posts/:postId/like
// ----------------------------------------------------------------------------
router.delete('/posts/:postId/like', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const postId = toInt(req.params.postId);
    await query('DELETE FROM community_likes WHERE post_id = $1 AND user_id = $2', [postId, req.user!.id]);
    await query('UPDATE community_posts SET likes_count = GREATEST(0, likes_count - 1) WHERE id = $1', [postId]);
    const postRes = await query('SELECT likes_count FROM community_posts WHERE id = $1', [postId]);
    return res.json({ liked: false, likes_count: postRes.rows[0]?.likes_count || 0 });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to unlike' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/community/posts/:postId/comments
// ----------------------------------------------------------------------------
router.get('/posts/:postId/comments', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const postId = toInt(req.params.postId);
    const result = await query(
      `SELECT c.*, u.username, u.avatar_initials 
       FROM community_comments c
       JOIN users u ON c.user_id = u.id
       WHERE c.post_id = $1 
       ORDER BY c.created_at ASC`,
      [postId]
    );

    return res.json({ comments: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch comments' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/community/posts/:postId/comments
// ----------------------------------------------------------------------------
router.post('/posts/:postId/comments', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const postId = toInt(req.params.postId);
    const { content } = req.body || {};
    if (!content || !content.trim()) {
      return res.status(400).json({ detail: 'Comment content cannot be empty.' });
    }

    const ins = await query(
      `INSERT INTO community_comments (post_id, user_id, author_name, content)
       VALUES ($1, $2, $3, $4)
       RETURNING *`,
      [postId, req.user!.id, req.user!.full_name, content.trim()]
    );

    return res.status(201).json({ comment: ins.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to add comment' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/community/comments/:commentId
// ----------------------------------------------------------------------------
router.delete('/comments/:commentId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const commentId = toInt(req.params.commentId);
    const isAdm = req.user!.role === 'admin';
    const where = isAdm ? 'WHERE id = $1' : 'WHERE id = $1 AND user_id = $2';
    const params = isAdm ? [commentId] : [commentId, req.user!.id];

    await query(`DELETE FROM community_comments ${where}`, params);
    return res.json({ message: 'Comment deleted' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to delete comment' });
  }
});

// ----------------------------------------------------------------------------
// PATCH /api/community/comments/:commentId
// ----------------------------------------------------------------------------
router.patch('/comments/:commentId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const commentId = toInt(req.params.commentId);
    const { content } = req.body || {};
    if (!content || !content.trim()) return res.status(400).json({ detail: 'Content required' });

    const result = await query(
      'UPDATE community_comments SET content = $1 WHERE id = $2 AND user_id = $3 RETURNING *',
      [content.trim(), commentId, req.user!.id]
    );

    if (result.rows.length === 0) return res.status(404).json({ detail: 'Comment not found' });
    return res.json({ comment: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to update comment' });
  }
});

export default router;
