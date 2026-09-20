import { toInt } from '../utils/helpers';
import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth, clearSessionCookie } from '../middleware/auth';
import { validateUsername, normalizeUsername } from '../utils/security';

const router = Router();

// ----------------------------------------------------------------------------
// GET /api/users/me & GET /api/users
// ----------------------------------------------------------------------------
router.get(['/me', '/'], requireAuth, (req: AuthenticatedRequest, res: Response) => {
  return res.json({ user: req.user });
});

// ----------------------------------------------------------------------------
// PATCH /api/users & PATCH /api/users/me
// ----------------------------------------------------------------------------
router.patch(['/me', '/'], requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { full_name, bio, username, avatar_initials } = req.body || {};
    const updates: string[] = [];
    const params: any[] = [];
    let pIdx = 1;

    if (full_name !== undefined) {
      updates.push(`full_name = $${pIdx++}`);
      params.push(full_name.trim());
    }

    if (bio !== undefined) {
      updates.push(`bio = $${pIdx++}`);
      params.push(bio ? bio.trim() : '');
    }

    if (avatar_initials !== undefined) {
      updates.push(`avatar_initials = $${pIdx++}`);
      params.push(avatar_initials.trim().toUpperCase());
    }

    if (username !== undefined) {
      const clean = normalizeUsername(username);
      if (clean !== req.user!.username) {
        const v = validateUsername(clean);
        if (!v.valid) {
          return res.status(400).json({ detail: v.message });
        }
        const check = await query('SELECT id FROM users WHERE LOWER(username) = $1 AND id != $2', [
          clean,
          req.user!.id,
        ]);
        if (check.rows.length > 0) {
          return res.status(409).json({ detail: 'Username is already taken.' });
        }
        updates.push(`username = $${pIdx++}`);
        params.push(clean);
      }
    }

    if (updates.length === 0) {
      return res.json({ user: req.user });
    }

    params.push(req.user!.id);
    const sql = `UPDATE users SET ${updates.join(', ')} WHERE id = $${pIdx} RETURNING id, email, full_name, username, role, is_active, mkc_id, avatar_initials, bio, email_verified, onboarding_completed, created_at`;
    const updated = await query(sql, params);

    return res.json({
      message: 'Profile updated successfully',
      user: updated.rows[0],
    });
  } catch (err: any) {
    console.error('[Users] Update profile error:', err);
    return res.status(500).json({ detail: err?.message || 'Failed to update profile' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/users/onboarding
// ----------------------------------------------------------------------------
router.post('/onboarding', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const onboardingData = req.body ? JSON.stringify(req.body) : null;
    await query(
      `UPDATE users 
       SET onboarding_completed = 1, onboarding_data = $1 
       WHERE id = $2`,
      [onboardingData, req.user!.id]
    );

    return res.json({ message: 'Onboarding completed successfully.' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to save onboarding data' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/users/search
// ----------------------------------------------------------------------------
router.get('/search', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const q = (req.query.q as string || '').trim().toLowerCase();
    if (!q) {
      return res.json({ users: [] });
    }

    const result = await query(
      `SELECT id, username, full_name, avatar_initials, bio, mkc_id 
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

// ----------------------------------------------------------------------------
// GET /api/users/:userId
// ----------------------------------------------------------------------------
router.get('/:userId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = toInt(req.params.userId);
    if (isNaN(userId)) {
      return res.status(400).json({ detail: 'Invalid user ID.' });
    }

    const userRes = await query(
      `SELECT id, username, full_name, avatar_initials, bio, mkc_id, created_at 
       FROM users 
       WHERE id = $1 AND is_active = 1`,
      [userId]
    );

    if (userRes.rows.length === 0) {
      return res.status(404).json({ detail: 'User not found.' });
    }

    return res.json({ user: userRes.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch user' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/users/account
// ----------------------------------------------------------------------------
router.delete('/account', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    await query('DELETE FROM users WHERE id = $1', [req.user!.id]);
    clearSessionCookie(res);
    return res.json({ message: 'Account deleted successfully.' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to delete account' });
  }
});

export default router;
