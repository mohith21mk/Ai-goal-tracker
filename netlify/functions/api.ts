import express, { Request, Response, NextFunction } from 'express';
import serverless from 'serverless-http';
import cookieParser from 'cookie-parser';
import cors from 'cors';
import dotenv from 'dotenv';

import { authenticateSession } from './src/middleware/auth';
import healthRouter from './src/controllers/health';
import authRouter from './src/controllers/auth';
import usersRouter from './src/controllers/users';
import settingsRouter from './src/controllers/settings';
import goalsRouter from './src/controllers/goals';
import blueprintsRouter from './src/controllers/blueprints';
import missionsRouter from './src/controllers/missions';
import habitsRouter from './src/controllers/habits';
import progressRouter from './src/controllers/progress';
import journalRouter from './src/controllers/journal';
import reflectionRouter from './src/controllers/reflection';
import communityRouter from './src/controllers/community';
import socialRouter from './src/controllers/social';
import chatRouter from './src/controllers/chat';
import notificationsRouter from './src/controllers/notifications';
import credentialsRouter from './src/controllers/credentials';
import adminRouter from './src/controllers/admin';
import coachRouter from './src/controllers/coach';

dotenv.config();

const app = express();

// ----------------------------------------------------------------------------
// Core Middleware
// ----------------------------------------------------------------------------
app.use(cors({
  origin: true,
  credentials: true,
}));
app.use(cookieParser());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// URL Normalizer for Netlify redirects and path routing
app.use((req: Request, _res: Response, next: NextFunction) => {
  // Strip Netlify Functions prefix if invoked directly
  if (req.url.startsWith('/.netlify/functions/api')) {
    req.url = req.url.replace('/.netlify/functions/api', '') || '/';
  }
  // Ensure router path starts with /api if incoming path omits it
  if (!req.url.startsWith('/api') && req.url !== '/' && !req.url.startsWith('/health') && !req.url.startsWith('/ready')) {
    req.url = '/api' + req.url;
  }
  next();
});

// Authenticate session on all requests
app.use(authenticateSession);

// ----------------------------------------------------------------------------
// Mount Routers
// ----------------------------------------------------------------------------
app.use('/', healthRouter);
app.use('/api/health', healthRouter);
app.use('/api/auth', authRouter);
app.use('/api/users', usersRouter);
app.use('/api/settings', settingsRouter);
app.use('/api/goals', goalsRouter);
app.use('/api/blueprints', blueprintsRouter);
app.use('/api/missions', missionsRouter);
app.use('/api/habits', habitsRouter);
app.use('/api/progress', progressRouter);
app.use('/api/progression', progressRouter);
app.use('/api/telemetry', progressRouter);
app.use('/api/journal', journalRouter);
app.use('/api/reflection', reflectionRouter);
app.use('/api/community', communityRouter);
app.use('/api/social', socialRouter);
app.use('/api/chat', chatRouter);
app.use('/api/notifications', notificationsRouter);
app.use('/api/credentials', credentialsRouter);
app.use('/api/admin', adminRouter);
app.use('/api/feedback', adminRouter);
app.use('/api/coach', coachRouter);

// ----------------------------------------------------------------------------
// Fallback 404 Handler
// ----------------------------------------------------------------------------
app.use((req: Request, res: Response) => {
  res.status(404).json({ detail: `Route not found: ${req.method} ${req.originalUrl || req.url}` });
});

// ----------------------------------------------------------------------------
// Global Error Handler
// ----------------------------------------------------------------------------
app.use((err: any, _req: Request, res: Response, _next: NextFunction) => {
  console.error('[Netlify API Error]:', err);
  res.status(500).json({ detail: err?.message || 'Internal Server Error' });
});

export { app };
export const handler = serverless(app);
