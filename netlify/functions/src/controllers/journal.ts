import { toInt } from '../utils/helpers';
import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

function getTodayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

// ----------------------------------------------------------------------------
// GET /api/journal/today
// ----------------------------------------------------------------------------
router.get('/today', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const today = getTodayStr();
    const result = await query(
      `SELECT * FROM journal_entries WHERE user_id = $1 AND entry_date = $2`,
      [req.user!.id, today]
    );

    return res.json({ entry: result.rows[0] || null });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch today entry' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/journal
// ----------------------------------------------------------------------------
router.post('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const {
      entry_date,
      mood,
      energy_level,
      wins_text,
      challenges_text,
      learnings_text,
      growth_next_text,
    } = req.body || {};

    const date = entry_date || getTodayStr();
    const cleanMood = mood || 'focused';
    const energy = Math.max(1, Math.min(10, parseInt(energy_level, 10) || 7));

    const result = await query(
      `INSERT INTO journal_entries (
        user_id, entry_date, mood, energy_level, wins_text, 
        challenges_text, learnings_text, growth_next_text, updated_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)
      ON CONFLICT (user_id, entry_date) DO UPDATE SET
        mood = EXCLUDED.mood,
        energy_level = EXCLUDED.energy_level,
        wins_text = EXCLUDED.wins_text,
        challenges_text = EXCLUDED.challenges_text,
        learnings_text = EXCLUDED.learnings_text,
        growth_next_text = EXCLUDED.growth_next_text,
        updated_at = CURRENT_TIMESTAMP
      RETURNING *`,
      [
        req.user!.id,
        date,
        cleanMood,
        energy,
        wins_text || '',
        challenges_text || '',
        learnings_text || '',
        growth_next_text || '',
      ]
    );

    return res.json({
      message: 'Journal entry saved successfully',
      entry: result.rows[0],
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to save journal entry' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/journal/history
// ----------------------------------------------------------------------------
router.get('/history', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const limit = Math.min(100, toInt(req.query.limit) || 30);
    const result = await query(
      `SELECT * FROM journal_entries 
       WHERE user_id = $1 
       ORDER BY entry_date DESC 
       LIMIT $2`,
      [req.user!.id, limit]
    );

    return res.json({ entries: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch history' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/journal/stats
// ----------------------------------------------------------------------------
router.get('/stats', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const entriesRes = await query(
      `SELECT mood, energy_level, entry_date FROM journal_entries WHERE user_id = $1 ORDER BY entry_date DESC`,
      [req.user!.id]
    );
    const entries = entriesRes.rows;

    const total = entries.length;
    const avgEnergy = total > 0 ? entries.reduce((acc, e) => acc + (e.energy_level || 7), 0) / total : 7;

    const moodCounts: Record<string, number> = {};
    entries.forEach((e) => {
      const m = e.mood || 'focused';
      moodCounts[m] = (moodCounts[m] || 0) + 1;
    });

    return res.json({
      total_entries: total,
      average_energy: Math.round(avgEnergy * 10) / 10,
      mood_distribution: moodCounts,
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch journal stats' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/journal/:entryId/analyze
// ----------------------------------------------------------------------------
router.post('/:entryId/analyze', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const entryId = toInt(req.params.entryId);
    const entryRes = await query('SELECT * FROM journal_entries WHERE id = $1 AND user_id = $2', [
      entryId,
      req.user!.id,
    ]);

    if (entryRes.rows.length === 0) {
      return res.status(404).json({ detail: 'Journal entry not found' });
    }

    const entry = entryRes.rows[0];
    const apiKey = process.env.GEMINI_API_KEY;

    let analysisText = `Strong focus detected with solid self-awareness. Keep compounding daily wins.`;

    if (apiKey && !apiKey.startsWith('your_')) {
      try {
        const prompt = `You are a high-performance cognitive coach. Analyze this daily journal reflection:\nMood: ${entry.mood}\nEnergy: ${entry.energy_level}/10\nWins: ${entry.wins_text}\nChallenges: ${entry.challenges_text}\nLearnings: ${entry.learnings_text}\n\nProvide 2-3 sentences of sharp, practical insight and encouragement.`;
        const resp = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              contents: [{ parts: [{ text: prompt }] }],
            }),
          }
        );
        const data: any = await resp.json();
        const geminiText = data?.candidates?.[0]?.content?.parts?.[0]?.text;
        if (geminiText) {
          analysisText = geminiText.trim();
        }
      } catch (geminiErr) {
        console.warn('[Journal Analyze] Gemini error, using fallback:', geminiErr);
      }
    }

    await query('UPDATE journal_entries SET ai_analysis = $1 WHERE id = $2', [analysisText, entryId]);

    return res.json({
      entry_id: entryId,
      analysis: analysisText,
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Analysis failed' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/journal/:entryId
// ----------------------------------------------------------------------------
router.delete('/:entryId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const entryId = toInt(req.params.entryId);
    await query('DELETE FROM journal_entries WHERE id = $1 AND user_id = $2', [entryId, req.user!.id]);
    return res.json({ message: 'Journal entry deleted' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to delete entry' });
  }
});

export default router;
