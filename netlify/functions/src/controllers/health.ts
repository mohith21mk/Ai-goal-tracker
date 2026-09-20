import { Router, Request, Response } from 'express';
import { query } from '../db';

const router = Router();

router.get(['/', '/health', '/api/health'], (_req: Request, res: Response) => {
  res.json({
    status: 'ok',
    service: 'Mastery Key Coach API (Netlify Functions)',
    version: '2.1.0',
    timestamp: new Date().toISOString(),
  });
});

router.get(['/ready', '/api/health/ready', '/health/ready'], async (_req: Request, res: Response) => {
  try {
    const dbTest = await query('SELECT 1 as healthy');
    if (dbTest.rows.length > 0) {
      return res.json({
        status: 'ready',
        database: 'connected',
        timestamp: new Date().toISOString(),
      });
    }
    res.status(503).json({ status: 'unhealthy', database: 'no_rows' });
  } catch (err: any) {
    res.status(503).json({
      status: 'unhealthy',
      database: 'error',
      error: err?.message || 'Database ping failed',
    });
  }
});

export default router;
