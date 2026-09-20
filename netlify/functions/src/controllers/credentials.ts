import { toInt } from '../utils/helpers';
import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

// ----------------------------------------------------------------------------
// GET /api/credentials
// ----------------------------------------------------------------------------
router.get('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await query(
      `SELECT id, credential_type, slug, title, description, tier, xp_value, evidence_type, evidence_id, issued_at 
       FROM user_credentials 
       WHERE user_id = $1 
       ORDER BY issued_at DESC`,
      [req.user!.id]
    );

    return res.json({ credentials: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch credentials' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/credentials/check
// ----------------------------------------------------------------------------
router.post('/check', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    const newlyAwarded: any[] = [];

    // Check completed missions count
    const mCountRes = await query('SELECT COUNT(*) FROM mission_logs WHERE user_id = $1', [userId]);
    const missionCount = parseInt(mCountRes.rows[0].count, 10);

    // Badge 1: First Protocol (1 mission)
    if (missionCount >= 1) {
      const ins = await query(
        `INSERT INTO user_credentials (user_id, credential_type, slug, title, description, tier, xp_value, evidence_type)
         VALUES ($1, 'milestone', 'first_protocol', 'First Protocol Master', 'Completed your first daily execution protocol.', 'bronze', 50, 'missions')
         ON CONFLICT (user_id, slug) DO NOTHING
         RETURNING *`,
        [userId]
      );
      if (ins.rows.length > 0) newlyAwarded.push(ins.rows[0]);
    }

    // Badge 2: Decathlete (10 missions)
    if (missionCount >= 10) {
      const ins = await query(
        `INSERT INTO user_credentials (user_id, credential_type, slug, title, description, tier, xp_value, evidence_type)
         VALUES ($1, 'milestone', 'decathlete', 'Protocol Decathlete', 'Completed 10 daily execution protocols.', 'silver', 100, 'missions')
         ON CONFLICT (user_id, slug) DO NOTHING
         RETURNING *`,
        [userId]
      );
      if (ins.rows.length > 0) newlyAwarded.push(ins.rows[0]);
    }

    return res.json({
      newly_awarded: newlyAwarded,
      message: newlyAwarded.length > 0 ? `Awarded ${newlyAwarded.length} new credentials!` : 'No new credentials to award.',
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to check credentials' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/credentials/user/:userId
// ----------------------------------------------------------------------------
router.get('/user/:userId', async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = toInt(req.params.userId);
    const result = await query(
      `SELECT id, credential_type, slug, title, description, tier, xp_value, issued_at 
       FROM user_credentials 
       WHERE user_id = $1 
       ORDER BY issued_at DESC`,
      [userId]
    );

    return res.json({ credentials: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch user credentials' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/credentials/verify/:credentialId
// ----------------------------------------------------------------------------
router.get('/verify/:credentialId', async (req: AuthenticatedRequest, res: Response) => {
  try {
    const credId = toInt(req.params.credentialId);
    const result = await query(
      `SELECT c.*, u.full_name, u.username, u.mkc_id 
       FROM user_credentials c
       JOIN users u ON c.user_id = u.id
       WHERE c.id = $1`,
      [credId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ detail: 'Credential not found or invalid' });
    }

    return res.json({ credential: result.rows[0], verified: true });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Verification error' });
  }
});

export default router;
