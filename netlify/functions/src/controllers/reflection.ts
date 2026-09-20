import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

router.get('/daily', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const today = new Date().toISOString().slice(0, 10);
    const journalRes = await query('SELECT * FROM journal_entries WHERE user_id = $1 AND entry_date = $2', [
      req.user!.id,
      today,
    ]);

    const entry = journalRes.rows[0] || null;

    const questions = [
      'What was your primary high-leverage win today?',
      'Where did you experience friction or resistance, and why?',
      'What mental model or insight will you carry forward tomorrow?',
    ];

    return res.json({
      date: today,
      completed: !!entry,
      entry,
      questions,
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch reflection' });
  }
});

export default router;
