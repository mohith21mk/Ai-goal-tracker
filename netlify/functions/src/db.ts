import { Pool, QueryResult } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

let pool: Pool | null = null;

// Custom in-memory query handler for local offline testing if needed
let mockQueryHandler: ((text: string, params?: any[]) => Promise<QueryResult<any>>) | null = null;

export function setMockQueryHandler(handler: ((text: string, params?: any[]) => Promise<QueryResult<any>>) | null) {
  mockQueryHandler = handler;
}

export function getPool(): Pool {
  if (pool) return pool;

  const connectionString = process.env.DATABASE_URL || '';
  const isPostgres = connectionString.startsWith('postgres://') || connectionString.startsWith('postgresql://');

  if (!isPostgres) {
    console.warn('[DB] Warning: No valid DATABASE_URL configured. Database queries may fail unless mocked.');
  }

  // Supabase connections require SSL
  const isRemote = isPostgres && (
    connectionString.includes('supabase.co') || 
    connectionString.includes('pooler.supabase.com') ||
    connectionString.includes('render.com') ||
    connectionString.includes('aws') ||
    connectionString.includes('sslmode=require')
  );

  pool = new Pool({
    connectionString,
    ssl: isRemote ? { rejectUnauthorized: false } : false,
    max: 5,
    idleTimeoutMillis: 10000,
    connectionTimeoutMillis: 8000,
  });

  pool.on('error', (err) => {
    console.error('[DB] Unexpected error on idle client:', err);
  });

  return pool;
}

export async function query<T = any>(text: string, params?: any[]): Promise<QueryResult<T>> {
  if (mockQueryHandler) {
    return mockQueryHandler(text, params);
  }

  const p = getPool();
  return p.query<T>(text, params);
}

export async function closePool(): Promise<void> {
  if (pool) {
    await pool.end();
    pool = null;
  }
}
