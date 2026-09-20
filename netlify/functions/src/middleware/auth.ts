import { Request, Response, NextFunction } from 'express';
import { query } from '../db';

export interface AuthenticatedUser {
  id: number;
  email: string;
  full_name: string;
  username: string;
  role: string;
  is_active: number;
  mkc_id: string;
  avatar_initials: string;
  bio?: string;
  email_verified: number;
  onboarding_completed: number;
  created_at: string;
}

export interface AuthenticatedRequest extends Request {
  user?: AuthenticatedUser;
  sessionToken?: string;
}

export const SESSION_COOKIE_NAME = 'mkc_session';
export const SESSION_DURATION_DAYS = 30;

export function setSessionCookie(res: Response, token: string): void {
  const isProduction = process.env.NODE_ENV === 'production' || process.env.MKC_SECURE_COOKIES === 'true';
  res.cookie(SESSION_COOKIE_NAME, token, {
    httpOnly: true,
    secure: isProduction,
    sameSite: 'lax',
    path: '/',
    maxAge: SESSION_DURATION_DAYS * 24 * 60 * 60 * 1000,
  });
}

export function clearSessionCookie(res: Response): void {
  res.clearCookie(SESSION_COOKIE_NAME, {
    httpOnly: true,
    sameSite: 'lax',
    path: '/',
  });
}

export async function authenticateSession(req: AuthenticatedRequest, _res: Response, next: NextFunction): Promise<void> {
  try {
    let token: string | undefined = req.cookies?.[SESSION_COOKIE_NAME];

    if (!token && req.headers.authorization) {
      const parts = req.headers.authorization.split(' ');
      if (parts.length === 2 && parts[0].toLowerCase() === 'bearer') {
        token = parts[1];
      }
    }

    if (!token) {
      return next();
    }

    // Check session in database
    const sessionRes = await query(
      `SELECT user_id, expires_at, revoked_at 
       FROM app_sessions 
       WHERE token = $1`,
      [token]
    );

    if (sessionRes.rows.length === 0) {
      return next();
    }

    const session = sessionRes.rows[0];
    if (session.revoked_at || new Date(session.expires_at) < new Date()) {
      return next();
    }

    // Update last seen asynchronously
    query('UPDATE app_sessions SET last_seen_at = CURRENT_TIMESTAMP WHERE token = $1', [token]).catch(() => {});

    // Fetch active user
    const userRes = await query(
      `SELECT id, email, full_name, username, role, is_active, mkc_id, 
              avatar_initials, bio, email_verified, onboarding_completed, created_at 
       FROM users 
       WHERE id = $1 AND is_active = 1`,
      [session.user_id]
    );

    if (userRes.rows.length > 0) {
      req.user = userRes.rows[0] as AuthenticatedUser;
      req.sessionToken = token;
    }

    next();
  } catch (err) {
    console.error('[Auth Middleware] Session error:', err);
    next();
  }
}

export function requireAuth(req: AuthenticatedRequest, res: Response, next: NextFunction) {
  if (!req.user) {
    return res.status(401).json({ detail: 'Not authenticated' });
  }
  next();
}

export function requireAdmin(req: AuthenticatedRequest, res: Response, next: NextFunction) {
  if (!req.user) {
    return res.status(401).json({ detail: 'Not authenticated' });
  }
  if (req.user.role !== 'admin') {
    return res.status(403).json({ detail: 'Admin privileges required' });
  }
  next();
}
