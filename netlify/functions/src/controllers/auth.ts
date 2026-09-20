import { Router, Response } from 'express';
import crypto from 'crypto';
import { query } from '../db';
import {
  hashPassword,
  verifyPassword,
  validateUsername,
  normalizeUsername,
  generateSessionToken,
  generateTokenHash,
} from '../utils/security';
import {
  AuthenticatedRequest,
  requireAuth,
  setSessionCookie,
  clearSessionCookie,
  SESSION_DURATION_DAYS,
} from '../middleware/auth';

const router = Router();

function deriveInitials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  if (parts.length === 1 && parts[0].length >= 2) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  return 'MK';
}

function generateMkcId(year: number = new Date().getFullYear()): string {
  const rnd = crypto.randomBytes(3).toString('hex').toUpperCase();
  return `MKC-${year}-${rnd}`;
}

// ----------------------------------------------------------------------------
// POST /api/auth/register
// ----------------------------------------------------------------------------
router.post('/register', async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { email, password, full_name, username } = req.body || {};

    if (!email || !password || !full_name) {
      return res.status(400).json({ detail: 'Email, password, and full name are required.' });
    }

    const cleanEmail = email.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanEmail)) {
      return res.status(400).json({ detail: 'Invalid email address.' });
    }

    if (password.length < 8) {
      return res.status(400).json({ detail: 'Password must be at least 8 characters long.' });
    }

    let cleanUsername = username ? normalizeUsername(username) : '';
    if (cleanUsername) {
      const v = validateUsername(cleanUsername);
      if (!v.valid) {
        return res.status(400).json({ detail: v.message });
      }
    } else {
      // Auto-generate username from email prefix
      const prefix = cleanEmail.split('@')[0].replace(/[^a-z0-9_]/g, '');
      cleanUsername = `${prefix || 'user'}_${crypto.randomBytes(2).toString('hex')}`;
    }

    // Check duplicate email or username
    const existing = await query(
      'SELECT id, email, username FROM users WHERE LOWER(email) = $1 OR LOWER(username) = $2',
      [cleanEmail, cleanUsername]
    );

    if (existing.rows.length > 0) {
      const match = existing.rows[0];
      if (match.email.toLowerCase() === cleanEmail) {
        return res.status(409).json({ detail: 'An account with this email already exists.' });
      }
      return res.status(409).json({ detail: 'Username is already taken.' });
    }

    const pwdHash = hashPassword(password);
    const avatarInitials = deriveInitials(full_name);
    const mkcId = generateMkcId();

    const insertUser = await query(
      `INSERT INTO users (
        email, full_name, username, password_hash, mkc_id, 
        avatar_initials, bio, role, email_verified, onboarding_completed
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
      RETURNING id, email, full_name, username, role, mkc_id, avatar_initials, bio, email_verified, onboarding_completed, created_at`,
      [cleanEmail, full_name.trim(), cleanUsername, pwdHash, mkcId, avatarInitials, '', 'user', 0, 0]
    );

    const user = insertUser.rows[0];

    // Create default settings
    await query(
      `INSERT INTO user_settings (user_id, theme, notifications_enabled, coach_style, daily_reminder_time, profile_visibility)
       VALUES ($1, 'dark', 1, 'strategic', '08:00', 'public')
       ON CONFLICT (user_id) DO NOTHING`,
      [user.id]
    );

    // Create session
    const token = generateSessionToken();
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + SESSION_DURATION_DAYS);

    await query(
      `INSERT INTO app_sessions (token, user_id, expires_at, user_agent, ip_address)
       VALUES ($1, $2, $3, $4, $5)`,
      [token, user.id, expiresAt.toISOString(), req.headers['user-agent'] || null, req.ip || null]
    );

    setSessionCookie(res, token);

    return res.status(201).json({
      message: 'Registration successful',
      user: {
        id: user.id,
        email: user.email,
        full_name: user.full_name,
        username: user.username,
        role: user.role,
        mkc_id: user.mkc_id,
        avatar_initials: user.avatar_initials,
        bio: user.bio,
        email_verified: user.email_verified,
        onboarding_completed: user.onboarding_completed,
      },
    });
  } catch (err: any) {
    console.error('[Auth] Register error:', err);
    return res.status(500).json({ detail: err?.message || 'Registration failed' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/auth/login
// ----------------------------------------------------------------------------
router.post('/login', async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { email, username, email_or_username, password } = req.body || {};
    const identifier = (email_or_username || email || username || '').trim().toLowerCase();

    if (!identifier || !password) {
      return res.status(400).json({ detail: 'Email/Username and password are required.' });
    }

    const userRes = await query(
      `SELECT id, email, full_name, username, password_hash, role, is_active, 
              mkc_id, avatar_initials, bio, email_verified, onboarding_completed, created_at 
       FROM users 
       WHERE LOWER(email) = $1 OR LOWER(username) = $1`,
      [identifier]
    );

    if (userRes.rows.length === 0) {
      return res.status(401).json({ detail: 'Invalid credentials.' });
    }

    const user = userRes.rows[0];

    if (!user.is_active) {
      return res.status(403).json({ detail: 'Account has been deactivated.' });
    }

    const isValid = verifyPassword(password, user.password_hash);
    if (!isValid) {
      return res.status(401).json({ detail: 'Invalid credentials.' });
    }

    // Create session
    const token = generateSessionToken();
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + SESSION_DURATION_DAYS);

    await query(
      `INSERT INTO app_sessions (token, user_id, expires_at, user_agent, ip_address)
       VALUES ($1, $2, $3, $4, $5)`,
      [token, user.id, expiresAt.toISOString(), req.headers['user-agent'] || null, req.ip || null]
    );

    setSessionCookie(res, token);

    return res.json({
      message: 'Login successful',
      user: {
        id: user.id,
        email: user.email,
        full_name: user.full_name,
        username: user.username,
        role: user.role,
        mkc_id: user.mkc_id,
        avatar_initials: user.avatar_initials,
        bio: user.bio,
        email_verified: user.email_verified,
        onboarding_completed: user.onboarding_completed,
      },
    });
  } catch (err: any) {
    console.error('[Auth] Login error:', err);
    return res.status(500).json({ detail: err?.message || 'Login failed' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/auth/logout
// ----------------------------------------------------------------------------
router.post('/logout', async (req: AuthenticatedRequest, res: Response) => {
  try {
    if (req.sessionToken) {
      await query('UPDATE app_sessions SET revoked_at = CURRENT_TIMESTAMP WHERE token = $1', [req.sessionToken]);
    }
    clearSessionCookie(res);
    return res.json({ message: 'Logged out successfully' });
  } catch (err: any) {
    console.error('[Auth] Logout error:', err);
    clearSessionCookie(res);
    return res.json({ message: 'Logged out' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/auth/me
// ----------------------------------------------------------------------------
router.get('/me', requireAuth, (req: AuthenticatedRequest, res: Response) => {
  return res.json({
    user: req.user,
  });
});

// ----------------------------------------------------------------------------
// GET /api/auth/check-username
// ----------------------------------------------------------------------------
router.get('/check-username', async (req: AuthenticatedRequest, res: Response) => {
  const rawUsername = (req.query.username as string) || '';
  const validation = validateUsername(rawUsername);

  if (!validation.valid) {
    return res.json({
      valid: false,
      available: false,
      message: validation.message,
    });
  }

  const clean = normalizeUsername(rawUsername);
  const exists = await query('SELECT id FROM users WHERE LOWER(username) = $1', [clean]);

  if (exists.rows.length > 0) {
    return res.json({
      valid: true,
      available: false,
      message: 'Username is already taken.',
    });
  }

  return res.json({
    valid: true,
    available: true,
    message: 'Username is available.',
  });
});

// ----------------------------------------------------------------------------
// POST /api/auth/change-password
// ----------------------------------------------------------------------------
router.post('/change-password', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { current_password, new_password } = req.body || {};
    if (!current_password || !new_password) {
      return res.status(400).json({ detail: 'Current and new password are required.' });
    }

    if (new_password.length < 8) {
      return res.status(400).json({ detail: 'New password must be at least 8 characters long.' });
    }

    const userRes = await query('SELECT password_hash FROM users WHERE id = $1', [req.user!.id]);
    if (userRes.rows.length === 0) {
      return res.status(404).json({ detail: 'User not found.' });
    }

    const valid = verifyPassword(current_password, userRes.rows[0].password_hash);
    if (!valid) {
      return res.status(400).json({ detail: 'Incorrect current password.' });
    }

    const newHash = hashPassword(new_password);
    await query('UPDATE users SET password_hash = $1 WHERE id = $2', [newHash, req.user!.id]);

    return res.json({ message: 'Password changed successfully.' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to change password.' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/auth/forgot-password
// ----------------------------------------------------------------------------
router.post('/forgot-password', async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { email } = req.body || {};
    if (!email) {
      return res.status(400).json({ detail: 'Email is required.' });
    }

    const userRes = await query('SELECT id FROM users WHERE LOWER(email) = $1', [email.trim().toLowerCase()]);
    if (userRes.rows.length > 0) {
      const token = generateTokenHash();
      const expiresAt = new Date(Date.now() + 60 * 60 * 1000); // 1 hour
      await query(
        'INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES ($1, $2, $3)',
        [userRes.rows[0].id, token, expiresAt.toISOString()]
      );
    }

    return res.json({ message: 'If an account exists with this email, a password reset link has been sent.' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Error processing request.' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/auth/reset-password
// ----------------------------------------------------------------------------
router.post('/reset-password', async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { token, new_password } = req.body || {};
    if (!token || !new_password) {
      return res.status(400).json({ detail: 'Token and new password are required.' });
    }

    if (new_password.length < 8) {
      return res.status(400).json({ detail: 'Password must be at least 8 characters long.' });
    }

    const resetRes = await query(
      `SELECT id, user_id FROM password_resets 
       WHERE token_hash = $1 AND used_at IS NULL AND expires_at > CURRENT_TIMESTAMP`,
      [token]
    );

    if (resetRes.rows.length === 0) {
      return res.status(400).json({ detail: 'Invalid or expired password reset token.' });
    }

    const reset = resetRes.rows[0];
    const newHash = hashPassword(new_password);

    await query('UPDATE users SET password_hash = $1 WHERE id = $2', [newHash, reset.user_id]);
    await query('UPDATE password_resets SET used_at = CURRENT_TIMESTAMP WHERE id = $1', [reset.id]);

    return res.json({ message: 'Password has been reset successfully.' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Error resetting password.' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/auth/verify-email
// ----------------------------------------------------------------------------
router.post('/verify-email', async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { token } = req.body || {};
    if (!token) {
      return res.status(400).json({ detail: 'Token is required.' });
    }

    const vRes = await query(
      `SELECT id, user_id FROM email_verifications 
       WHERE token_hash = $1 AND used_at IS NULL AND expires_at > CURRENT_TIMESTAMP`,
      [token]
    );

    if (vRes.rows.length === 0) {
      return res.status(400).json({ detail: 'Invalid or expired verification token.' });
    }

    const row = vRes.rows[0];
    await query('UPDATE users SET email_verified = 1, verified_at = CURRENT_TIMESTAMP WHERE id = $1', [row.user_id]);
    await query('UPDATE email_verifications SET used_at = CURRENT_TIMESTAMP WHERE id = $1', [row.id]);

    return res.json({ message: 'Email verified successfully.' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Verification failed.' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/auth/resend-verification
// ----------------------------------------------------------------------------
router.post('/resend-verification', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  return res.json({ message: 'Verification link resent.' });
});

// ----------------------------------------------------------------------------
// GET /api/auth/sessions
// ----------------------------------------------------------------------------
router.get('/sessions', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const sessionsRes = await query(
      `SELECT token, created_at, last_seen_at, expires_at, user_agent, ip_address 
       FROM app_sessions 
       WHERE user_id = $1 AND revoked_at IS NULL AND expires_at > CURRENT_TIMESTAMP 
       ORDER BY last_seen_at DESC`,
      [req.user!.id]
    );

    const sessions = sessionsRes.rows.map((s) => ({
      id: s.token,
      created_at: s.created_at,
      last_seen_at: s.last_seen_at,
      user_agent: s.user_agent,
      ip_address: s.ip_address,
      is_current: s.token === req.sessionToken,
    }));

    return res.json({ sessions });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch sessions.' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/auth/sessions/:sessionId
// ----------------------------------------------------------------------------
router.delete('/sessions/:sessionId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { sessionId } = req.params;
    await query('UPDATE app_sessions SET revoked_at = CURRENT_TIMESTAMP WHERE token = $1 AND user_id = $2', [
      sessionId,
      req.user!.id,
    ]);

    if (sessionId === req.sessionToken) {
      clearSessionCookie(res);
    }

    return res.json({ message: 'Session revoked successfully.' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to revoke session.' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/auth/sessions/revoke-others
// ----------------------------------------------------------------------------
router.post('/sessions/revoke-others', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    await query(
      `UPDATE app_sessions 
       SET revoked_at = CURRENT_TIMESTAMP 
       WHERE user_id = $1 AND token != $2 AND revoked_at IS NULL`,
      [req.user!.id, req.sessionToken || '']
    );

    return res.json({ message: 'Other sessions revoked successfully.' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to revoke other sessions.' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/auth/deactivate
// ----------------------------------------------------------------------------
router.post('/deactivate', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { password } = req.body || {};
    if (!password) {
      return res.status(400).json({ detail: 'Password confirmation required.' });
    }

    const uRes = await query('SELECT password_hash FROM users WHERE id = $1', [req.user!.id]);
    if (!verifyPassword(password, uRes.rows[0].password_hash)) {
      return res.status(400).json({ detail: 'Incorrect password.' });
    }

    await query('UPDATE users SET is_active = 0, deactivated_at = CURRENT_TIMESTAMP WHERE id = $1', [req.user!.id]);
    await query('UPDATE app_sessions SET revoked_at = CURRENT_TIMESTAMP WHERE user_id = $1', [req.user!.id]);
    clearSessionCookie(res);

    return res.json({ message: 'Account deactivated successfully.' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to deactivate account.' });
  }
});

export default router;
