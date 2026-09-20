import { toInt } from '../utils/helpers';
import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

// ----------------------------------------------------------------------------
// GET /api/chat/conversations
// ----------------------------------------------------------------------------
router.get('/conversations', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    const result = await query(
      `SELECT c.id, c.updated_at, c.created_at,
              cm2.user_id AS other_user_id,
              u.username AS other_username, u.full_name AS other_name, u.avatar_initials AS other_avatar,
              (SELECT message FROM chat_messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) AS last_message,
              (SELECT created_at FROM chat_messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) AS last_message_at,
              (SELECT COUNT(*) FROM chat_messages m WHERE m.conversation_id = c.id AND m.sender_id != $1 AND m.read_at IS NULL) AS unread_count
       FROM conversations c
       JOIN conversation_members cm1 ON c.id = cm1.conversation_id AND cm1.user_id = $1
       JOIN conversation_members cm2 ON c.id = cm2.conversation_id AND cm2.user_id != $1
       JOIN users u ON cm2.user_id = u.id
       ORDER BY c.updated_at DESC`,
      [userId]
    );

    return res.json({ conversations: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch conversations' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/chat/conversations
// ----------------------------------------------------------------------------
router.post('/conversations', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { recipient_id } = req.body || {};
    const userId = req.user!.id;

    if (!recipient_id || recipient_id === userId) {
      return res.status(400).json({ detail: 'Invalid recipient' });
    }

    // Check existing conversation
    const existing = await query(
      `SELECT cm1.conversation_id 
       FROM conversation_members cm1
       JOIN conversation_members cm2 ON cm1.conversation_id = cm2.conversation_id
       WHERE cm1.user_id = $1 AND cm2.user_id = $2
       LIMIT 1`,
      [userId, recipient_id]
    );

    if (existing.rows.length > 0) {
      return res.json({ conversation_id: existing.rows[0].conversation_id });
    }

    // Create new conversation
    const cRes = await query('INSERT INTO conversations DEFAULT VALUES RETURNING id');
    const convId = cRes.rows[0].id;

    await query('INSERT INTO conversation_members (conversation_id, user_id) VALUES ($1, $2), ($1, $3)', [
      convId,
      userId,
      recipient_id,
    ]);

    return res.status(201).json({ conversation_id: convId });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to create conversation' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/chat/conversations/:conversationId/messages
// ----------------------------------------------------------------------------
router.get('/conversations/:conversationId/messages', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const convId = toInt(req.params.conversationId);
    const userId = req.user!.id;

    // Check member
    const mem = await query('SELECT 1 FROM conversation_members WHERE conversation_id = $1 AND user_id = $2', [
      convId,
      userId,
    ]);
    if (mem.rows.length === 0) return res.status(403).json({ detail: 'Not a member of this conversation' });

    const messagesRes = await query(
      `SELECT m.id, m.conversation_id, m.sender_id, m.message, m.message_type, 
              m.attachment_url, m.attachment_metadata, m.attachment_duration, 
              m.created_at, m.read_at, u.username, u.avatar_initials
       FROM chat_messages m
       JOIN users u ON m.sender_id = u.id
       WHERE m.conversation_id = $1 
       ORDER BY m.created_at ASC`,
      [convId]
    );

    return res.json({ messages: messagesRes.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch messages' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/chat/conversations/:conversationId/messages
// ----------------------------------------------------------------------------
router.post('/conversations/:conversationId/messages', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const convId = toInt(req.params.conversationId);
    const userId = req.user!.id;
    const { message, message_type, attachment_url, attachment_metadata, attachment_duration } = req.body || {};

    if (!message || !message.trim()) {
      return res.status(400).json({ detail: 'Message content cannot be empty.' });
    }

    const ins = await query(
      `INSERT INTO chat_messages (
        conversation_id, sender_id, message, message_type, 
        attachment_url, attachment_metadata, attachment_duration
      ) VALUES ($1, $2, $3, $4, $5, $6, $7)
      RETURNING *`,
      [
        convId,
        userId,
        message.trim(),
        message_type || 'text',
        attachment_url || null,
        attachment_metadata ? JSON.stringify(attachment_metadata) : null,
        attachment_duration || null,
      ]
    );

    await query('UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = $1', [convId]);

    return res.status(201).json({ message: ins.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to send message' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/chat/conversations/:conversationId/read
// ----------------------------------------------------------------------------
router.post('/conversations/:conversationId/read', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const convId = toInt(req.params.conversationId);
    await query(
      `UPDATE chat_messages 
       SET read_at = CURRENT_TIMESTAMP 
       WHERE conversation_id = $1 AND sender_id != $2 AND read_at IS NULL`,
      [convId, req.user!.id]
    );
    return res.json({ message: 'Marked as read' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to mark as read' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/chat/messages/:messageId
// ----------------------------------------------------------------------------
router.delete('/messages/:messageId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const msgId = toInt(req.params.messageId);
    await query('DELETE FROM chat_messages WHERE id = $1 AND sender_id = $2', [msgId, req.user!.id]);
    return res.json({ message: 'Message deleted' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to delete message' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/chat/upload
// ----------------------------------------------------------------------------
router.post('/upload', requireAuth, async (_req: AuthenticatedRequest, res: Response) => {
  return res.json({
    url: 'https://mastery-key-coach.netlify.app/assets/attachment-placeholder.png',
    message: 'Upload simulated',
  });
});

export default router;
