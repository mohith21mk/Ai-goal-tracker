/**
 * Mastery Key Coach (MKC) — Centralized Route Constants
 * 
 * Strict single source of truth for application routing paths.
 */

export const ROUTES = {
  // Public & Authentication Routes
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  VERIFY_EMAIL: '/verify-email',
  LANDING: '/landing',

  // Protected Core Application Routes
  ROOT: '/',
  DASHBOARD: '/dashboard',
  ANALYTICS: '/analytics',
  MISSIONS: '/missions',
  GOALS: '/goals',
  COACH: '/coach',
  AI_COACH_ALIAS: '/ai-coach',
  HABITS: '/habits',
  STREAKS_ALIAS: '/streaks',
  JOURNAL: '/journal',
  BLUEPRINT: '/blueprint',
  LIFE_BLUEPRINT_ALIAS: '/life-blueprint',
  SETTINGS: '/settings',
  COMMUNITY: '/community',
  MESSAGES: '/messages',
  CHAT_ALIAS: '/chat',
  PROFILE: '/profile',
  MY_IDENTITY_ALIAS: '/my-identity',
};

export default ROUTES;
