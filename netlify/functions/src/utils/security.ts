import crypto from 'crypto';

export const RESERVED_USERNAMES = new Set([
  'admin',
  'administrator',
  'support',
  'masterykeycoach',
  'mkc',
  'api',
  'system',
  'root',
  'null',
  'undefined',
  'anonymous',
  'help',
  'login',
  'register',
  'auth',
  'user',
  'users',
  'dashboard',
  'settings',
  'profile',
  'community',
]);

/**
 * Generates secure PBKDF2-HMAC-SHA256 hash with 100,000 iterations and random salt.
 * Exact 1:1 match with Python backend's hash_password.
 */
export function hashPassword(password: string): string {
  const salt = crypto.randomBytes(16).toString('hex');
  const key = crypto.pbkdf2Sync(password, Buffer.from(salt, 'utf-8'), 100000, 32, 'sha256');
  return `pbkdf2_sha256$100000$${salt}$${key.toString('hex')}`;
}

/**
 * Constant-time password verification against pbkdf2_sha256 format.
 * Matches Python backend verify_password.
 */
export function verifyPassword(password: string, passwordHash: string): boolean {
  if (!password || !passwordHash) return false;
  try {
    const parts = passwordHash.split('$');
    if (parts.length !== 4 || parts[0] !== 'pbkdf2_sha256') {
      return false;
    }
    const iterations = parseInt(parts[1], 10);
    const salt = parts[2];
    const expectedKey = parts[3];

    const computed = crypto.pbkdf2Sync(password, Buffer.from(salt, 'utf-8'), iterations, 32, 'sha256');
    const computedHex = computed.toString('hex');

    if (computedHex.length !== expectedKey.length) return false;
    return crypto.timingSafeEqual(Buffer.from(computedHex), Buffer.from(expectedKey));
  } catch {
    return false;
  }
}

export function normalizeUsername(rawUsername: string): string {
  if (!rawUsername) return '';
  let cleaned = rawUsername.trim();
  if (cleaned.startsWith('@')) {
    cleaned = cleaned.slice(1);
  }
  return cleaned.toLowerCase();
}

export function validateUsername(rawUsername: string): { valid: boolean; message: string } {
  const username = normalizeUsername(rawUsername);
  if (!username) {
    return { valid: false, message: 'Username cannot be empty.' };
  }

  if (username.length < 3 || username.length > 30) {
    return { valid: false, message: 'Username must be between 3 and 30 characters.' };
  }

  if (!/^[a-z_][a-z0-9_]*$/.test(username)) {
    if (/^[0-9]/.test(username)) {
      return { valid: false, message: 'Username cannot start with a number.' };
    }
    return { valid: false, message: 'Username can only contain letters, numbers, and underscores.' };
  }

  if (RESERVED_USERNAMES.has(username)) {
    return { valid: false, message: `Username '${username}' is reserved by the system.` };
  }

  return { valid: true, message: 'Username is valid.' };
}

export function generateSessionToken(): string {
  return crypto.randomBytes(32).toString('base64url');
}

export function generateTokenHash(): string {
  return crypto.randomBytes(24).toString('hex');
}
