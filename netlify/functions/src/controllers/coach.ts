import { toInt } from '../utils/helpers';
import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

// ----------------------------------------------------------------------------
// GET /api/coach/history
// ----------------------------------------------------------------------------
router.get('/history', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const limit = Math.min(100, Math.max(1, toInt(req.query.limit) || 50));
    const result = await query(
      `SELECT id, sender, content, created_at 
       FROM messages 
       WHERE user_id = $1 
       ORDER BY created_at ASC, id ASC 
       LIMIT $2`,
      [req.user!.id, limit]
    );

    return res.json({ messages: result.rows, count: result.rows.length });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch history' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/coach/history
// ----------------------------------------------------------------------------
router.delete('/history', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await query('DELETE FROM messages WHERE user_id = $1', [req.user!.id]);
    return res.json({
      message: 'Chat history cleared successfully',
      deleted_count: result.rowCount || 0,
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to clear history' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/coach/chat
// ----------------------------------------------------------------------------
router.post('/chat', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { message } = req.body || {};
    if (!message || !message.trim()) {
      return res.status(400).json({ detail: 'Message prompt cannot be empty' });
    }

    const userId = req.user!.id;
    const userPrompt = message.trim();

    // 1. Save user prompt
    await query('INSERT INTO messages (user_id, sender, content) VALUES ($1, $2, $3)', [
      userId,
      'user',
      userPrompt,
    ]);

    // 2. Fetch context (goals, missions, habits, settings)
    const goalsRes = await query('SELECT title, category FROM goals WHERE user_id = $1 AND status = $2 LIMIT 5', [
      userId,
      'active',
    ]);
    const missionsRes = await query('SELECT title, completed FROM missions WHERE user_id = $1 LIMIT 10', [userId]);
    const habitsRes = await query('SELECT title, frequency FROM habits WHERE user_id = $1 AND status = $2 LIMIT 10', [
      userId,
      'active',
    ]);
    const settingsRes = await query('SELECT coach_style FROM user_settings WHERE user_id = $1', [userId]);

    const goalsSummary = goalsRes.rows.map((g) => g.title).join(', ') || 'Personal Growth & AI Mastery';
    const coachStyle = settingsRes.rows[0]?.coach_style || 'strategic';

    // 3. Check Gemini API key
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey || apiKey.startsWith('your_') || apiKey === 'placeholder') {
      const fallbackReply = `I'm here to support your focus on "${goalsSummary}". Let's execute today's protocols with clarity.`;
      await query('INSERT INTO messages (user_id, sender, content) VALUES ($1, $2, $3)', [
        userId,
        'coach',
        fallbackReply,
      ]);

      return res.json({
        reply: fallbackReply,
        context_used: true,
        live_llm: false,
        note: 'Configure GEMINI_API_KEY in Netlify dashboard for live AI generation.',
      });
    }

    // 4. Fetch recent history
    const historyRes = await query(
      `SELECT sender, content FROM messages WHERE user_id = $1 ORDER BY created_at DESC, id DESC LIMIT 6`,
      [userId]
    );
    const history = historyRes.rows.reverse();

    // 5. System prompt
    const systemPrompt = `You are AI Coach for Mastery Key Coach (MKC). You are a calm, sharp, highly intelligent, and practical mentor (like ChatGPT).
User Name: ${req.user!.full_name} (@${req.user!.username})
Primary Goals: ${goalsSummary}
Coach Style: ${coachStyle}
Respond conversationally, warmly, and concisely. If the user asks a technical question, answer directly. If they need planning, refer to their goals.`;

    const contents: any[] = [
      { role: 'user', parts: [{ text: systemPrompt }] },
      { role: 'model', parts: [{ text: 'Understood. I am ready to converse warmly, practically, and accurately.' }] },
    ];

    for (const h of history) {
      contents.push({
        role: h.sender === 'user' ? 'user' : 'model',
        parts: [{ text: h.content }],
      });
    }

    // Call Gemini REST API (gemini-2.0-flash with fallback to gemini-1.5-flash)
    let replyText = '';
    const models = ['gemini-2.0-flash', 'gemini-1.5-flash'];

    for (const model of models) {
      try {
        const resp = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              contents,
              generationConfig: {
                temperature: 0.7,
                maxOutputTokens: 1024,
              },
            }),
          }
        );

        if (resp.ok) {
          const data: any = await resp.json();
          const candidateText = data?.candidates?.[0]?.content?.parts?.[0]?.text;
          if (candidateText) {
            replyText = candidateText.trim();
            break;
          }
        }
      } catch (e) {
        console.warn(`[AI Coach] Error with ${model}:`, e);
      }
    }

    if (!replyText) {
      replyText = `Understood. Stay focused on your core vision: ${goalsSummary}. What is your immediate next step?`;
    }

    // Save coach response
    await query('INSERT INTO messages (user_id, sender, content) VALUES ($1, $2, $3)', [
      userId,
      'coach',
      replyText,
    ]);

    return res.json({
      reply: replyText,
      context_used: true,
      live_llm: true,
    });
  } catch (err: any) {
    console.error('[AI Coach] Chat error:', err);
    return res.status(500).json({ detail: err?.message || 'Chat processing failed' });
  }
});

export default router;
