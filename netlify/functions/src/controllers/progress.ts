import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

function parseDate(val: any): string | null {
  if (!val) return null;
  const s = String(val).slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(s) ? s : null;
}

function confidenceFactor(n: number, k = 15.0): number {
  if (n <= 0) return 0.0;
  return Math.max(0.0, Math.min(1.0, 1.0 - Math.exp(-n / k)));
}

function calculateStreak(activeDates: Set<string>, referenceDateStr: string): { currentStreak: number; longestStreak: number } {
  const dates = Array.from(activeDates)
    .filter((d) => d <= referenceDateStr)
    .sort();

  if (dates.length === 0) return { currentStreak: 0, longestStreak: 0 };

  let longest = 1;
  let running = 1;

  for (let i = 1; i < dates.length; i++) {
    const prev = new Date(dates[i - 1]).getTime();
    const curr = new Date(dates[i]).getTime();
    const diffDays = Math.round((curr - prev) / (1000 * 60 * 60 * 24));

    if (diffDays === 1) {
      running++;
      if (running > longest) longest = running;
    } else if (diffDays > 1) {
      running = 1;
    }
  }
  if (running > longest) longest = running;

  // Current streak
  const refTime = new Date(referenceDateStr).getTime();
  const latestTime = new Date(dates[dates.length - 1]).getTime();
  const daysSince = Math.round((refTime - latestTime) / (1000 * 60 * 60 * 24));

  let current = 0;
  if (daysSince <= 1) {
    current = 1;
    let currRefTime = latestTime;
    for (let i = dates.length - 2; i >= 0; i--) {
      const prevTime = new Date(dates[i]).getTime();
      const diff = Math.round((currRefTime - prevTime) / (1000 * 60 * 60 * 24));
      if (diff === 1) {
        current++;
        currRefTime = prevTime;
      } else if (diff === 0) {
        continue;
      } else {
        break;
      }
    }
  }

  return { currentStreak: current, longestStreak: longest };
}

// ----------------------------------------------------------------------------
// Core Progress & Telemetry Calculation Engine
// ----------------------------------------------------------------------------
async function calculateTelemetryForUser(userId: number) {
  const todayStr = new Date().toISOString().slice(0, 10);

  // 1. Fetch user missions
  const missionsRes = await query('SELECT id, xp_reward FROM missions WHERE user_id = $1', [userId]);
  const userMissions = missionsRes.rows;
  const totalMissions = userMissions.length;

  // 2. Fetch mission logs (all time)
  const mLogsRes = await query(
    'SELECT mission_id, completed_date, xp_reward FROM mission_logs WHERE user_id = $1',
    [userId]
  );
  const missionLogs = mLogsRes.rows;

  // 3. Fetch habits & habit logs
  const habitsRes = await query('SELECT id FROM habits WHERE user_id = $1 AND status = $2', [userId, 'active']);
  const totalActiveHabits = habitsRes.rows.length;

  const hLogsRes = await query('SELECT habit_id, completed_date FROM habit_logs WHERE user_id = $1', [userId]);
  const habitLogs = hLogsRes.rows;

  // 4. Daily Progress (Today Only)
  const todayMissionLogs = missionLogs.filter((l) => l.completed_date === todayStr);
  const completedMissionsToday = todayMissionLogs.length;

  const todayHabitLogs = habitLogs.filter((l) => l.completed_date === todayStr);
  const completedHabitsToday = todayHabitLogs.length;

  const missionDailyPct = totalMissions > 0 ? (completedMissionsToday / totalMissions) * 100 : 0;
  const habitDailyPct = totalActiveHabits > 0 ? (completedHabitsToday / totalActiveHabits) * 100 : 0;

  const dailyProgressScore = Math.round(
    totalMissions > 0 && totalActiveHabits > 0
      ? missionDailyPct * 0.5 + habitDailyPct * 0.5
      : totalMissions > 0
      ? missionDailyPct
      : habitDailyPct
  );

  // 5. Streaks & Active Dates
  const activeDates = new Set<string>();
  missionLogs.forEach((l) => activeDates.add(l.completed_date));
  habitLogs.forEach((l) => activeDates.add(l.completed_date));

  const { currentStreak, longestStreak } = calculateStreak(activeDates, todayStr);

  // 6. Multi-Horizon Historical Engine (Lifetime, 90d, 30d, 7d)
  const now = new Date();
  const getDaysAgo = (days: number) => {
    const d = new Date(now);
    d.setDate(d.getDate() - days);
    return d.toISOString().slice(0, 10);
  };

  const d7 = getDaysAgo(7);
  const d30 = getDaysAgo(30);
  const d90 = getDaysAgo(90);

  const filterWindow = (fromDate: string) => {
    const mCount = missionLogs.filter((l) => l.completed_date >= fromDate).length;
    const hCount = habitLogs.filter((l) => l.completed_date >= fromDate).length;
    return mCount + hCount;
  };

  const actions7d = filterWindow(d7);
  const actions30d = filterWindow(d30);
  const actions90d = filterWindow(d90);
  const actionsLifetime = missionLogs.length + habitLogs.length;

  // Calculate scores per horizon with confidence factor damping
  const rate7d = Math.min(100, (actions7d / Math.max(1, 7 * (totalMissions + totalActiveHabits))) * 100);
  const rate30d = Math.min(100, (actions30d / Math.max(1, 30 * (totalMissions + totalActiveHabits))) * 100);
  const rate90d = Math.min(100, (actions90d / Math.max(1, 90 * (totalMissions + totalActiveHabits))) * 100);
  const rateLifetime = Math.min(100, (actionsLifetime / Math.max(1, 100)) * 100);

  const rawWeighted = rate7d * 0.35 + rate30d * 0.35 + rate90d * 0.2 + rateLifetime * 0.1;
  const cv = confidenceFactor(actionsLifetime, 15.0);
  const overallPerformanceScore = Math.min(100, Math.round(rawWeighted * cv));

  // 7. Cumulative XP & Level
  let totalXp = 0;
  missionLogs.forEach((l) => {
    totalXp += l.xp_reward || 10;
  });
  habitLogs.forEach(() => {
    totalXp += 5; // 5 XP per habit check-in
  });

  // Add credentials XP
  const credsRes = await query('SELECT xp_value FROM user_credentials WHERE user_id = $1', [userId]);
  credsRes.rows.forEach((c) => {
    totalXp += c.xp_value || 50;
  });

  const level = Math.max(1, Math.floor(Math.sqrt(totalXp / 100)) + 1);
  const xpForCurrentLevel = (level - 1) * (level - 1) * 100;
  const xpForNextLevel = level * level * 100;
  const levelProgressPct = Math.min(
    100,
    Math.round(((totalXp - xpForCurrentLevel) / Math.max(1, xpForNextLevel - xpForCurrentLevel)) * 100)
  );

  return {
    daily_progress: {
      score: dailyProgressScore,
      completed_missions: completedMissionsToday,
      total_missions: totalMissions,
      completed_habits: completedHabitsToday,
      total_habits: totalActiveHabits,
      target_date: todayStr,
    },
    overall_performance: {
      score: overallPerformanceScore,
      confidence_factor: Math.round(cv * 100) / 100,
      total_actions: actionsLifetime,
      windows: {
        last_7_days: actions7d,
        last_30_days: actions30d,
        last_90_days: actions90d,
        lifetime: actionsLifetime,
      },
    },
    streaks: {
      current_streak: currentStreak,
      longest_streak: longestStreak,
      active_days_count: activeDates.size,
    },
    progression: {
      level,
      total_xp: totalXp,
      xp_for_current_level: xpForCurrentLevel,
      xp_for_next_level: xpForNextLevel,
      level_progress_percentage: levelProgressPct,
    },
  };
}

// ----------------------------------------------------------------------------
// GET /api/progress
// ----------------------------------------------------------------------------
router.get('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const data = await calculateTelemetryForUser(req.user!.id);
    return res.json(data);
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch progress' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/progress/daily
// ----------------------------------------------------------------------------
router.get('/daily', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const data = await calculateTelemetryForUser(req.user!.id);
    return res.json({ daily_progress: data.daily_progress });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch daily progress' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/progress/telemetry & GET /api/telemetry
// ----------------------------------------------------------------------------
router.get(['/telemetry', '/api/telemetry'], requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const data = await calculateTelemetryForUser(req.user!.id);
    return res.json(data);
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch telemetry' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/progression
// ----------------------------------------------------------------------------
router.get('/progression', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const data = await calculateTelemetryForUser(req.user!.id);
    return res.json(data.progression);
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch progression' });
  }
});

export default router;
