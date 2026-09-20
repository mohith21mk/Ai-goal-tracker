# Mastery Key Coach — Netlify Migration Inventory

> **Document Status:** MIGRATION COMPLETE — ALL 121 ENDPOINTS IMPLEMENTED & TESTED
> **Target Architecture:** Netlify Functions (Express.js + TypeScript) + Supabase Free PostgreSQL
> **Target Domain:** Same-origin deployment at `https://mastery-key-coach.netlify.app`

## Executive Summary
- **Total Distinct Endpoints Analyzed:** 121
- **Total Controller Modules:** 15
- **Public Endpoints:** 15
- **Authenticated User Endpoints:** 95
- **Admin-Only Endpoints:** 11

---

## ADMIN Controller (`netlify/functions/src/controllers/admin.ts`)

**Endpoints in this module:** 12

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/admin/feedback` | **Admin** | feedback, users | src\services\api.js:1323<br>src\services\api.js:1305<br>src\services\api.js:1314<br>*(+1 more)* | `get_admin_feedback` | **Done & Tested** |
| `GET` | `/api/admin/feedback/stats` | **Admin** | feedback, users | src\services\api.js:1314 | `get_admin_feedback_stats` | **Done & Tested** |
| `DELETE` | `/api/admin/feedback/{feedback_id}` | **Admin** | feedback, users | src\services\api.js:1323<br>src\services\api.js:1314<br>src\services\api.js:1335 | `delete_admin_feedback_feedback_id` | **Done & Tested** |
| `GET` | `/api/admin/feedback/{feedback_id}` | **Admin** | feedback, users | src\services\api.js:1323<br>src\services\api.js:1314<br>src\services\api.js:1335 | `get_admin_feedback_feedback_id` | **Done & Tested** |
| `PATCH` | `/api/admin/feedback/{feedback_id}` | **Admin** | feedback, users | src\services\api.js:1323<br>src\services\api.js:1314<br>src\services\api.js:1335 | `patch_admin_feedback_feedback_id` | **Done & Tested** |
| `GET` | `/api/admin/overview` | **Admin** | users, feedback, user_settings, missions, habits, goals | src\services\api.js:1346 | `get_admin_overview` | **Done & Tested** |
| `GET` | `/api/admin/users` | **Admin** | users, app_sessions, user_settings | src\services\api.js:1393<br>src\services\api.js:1363<br>src\services\api.js:1372<br>*(+2 more)* | `get_admin_users` | **Done & Tested** |
| `GET` | `/api/admin/users/{user_id}` | **Admin** | users, app_sessions, user_settings | src\services\api.js:1381<br>src\services\api.js:1393<br>src\services\api.js:1405<br>*(+1 more)* | `get_admin_users_user_id` | **Done & Tested** |
| `PATCH` | `/api/admin/users/{user_id}/email` | **Admin** | users, app_sessions, user_settings | src\services\api.js:1405 | `patch_admin_users_user_id_email` | **Done & Tested** |
| `PATCH` | `/api/admin/users/{user_id}/role` | **Admin** | users, app_sessions, user_settings | src\services\api.js:1381 | `patch_admin_users_user_id_role` | **Done & Tested** |
| `PATCH` | `/api/admin/users/{user_id}/status` | **Admin** | users, app_sessions, user_settings | src\services\api.js:1393 | `patch_admin_users_user_id_status` | **Done & Tested** |
| `POST` | `/api/feedback` | **User** | feedback, users | src\services\api.js:1285 | `post_feedback` | **Done & Tested** |

---

## AUTH Controller (`netlify/functions/src/controllers/auth.ts`)

**Endpoints in this module:** 14

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/change-password` | **User** | users, app_sessions, user_settings | src\services\api.js:354 | `post_auth_change_password` | **Done & Tested** |
| `GET` | `/api/auth/check-username` | **Public** | users, app_sessions, user_settings | src\services\api.js:260 | `get_auth_check_username` | **Done & Tested** |
| `POST` | `/api/auth/deactivate` | **User** | users, app_sessions, user_settings | src\services\api.js:396 | `post_auth_deactivate` | **Done & Tested** |
| `POST` | `/api/auth/forgot-password` | **Public** | users, app_sessions, user_settings | src\services\api.js:307 | `post_auth_forgot_password` | **Done & Tested** |
| `POST` | `/api/auth/login` | **Public** | users, app_sessions, user_settings | src\services\api.js:235<br>src\services\api.js:78<br>src\services\api.js:280 | `post_auth_login` | **Done & Tested** |
| `POST` | `/api/auth/logout` | **Public** | users, app_sessions, user_settings | src\services\api.js:235<br>src\services\api.js:292 | `post_auth_logout` | **Done & Tested** |
| `GET` | `/api/auth/me` | **User** | users, app_sessions, user_settings | src\services\api.js:299<br>src\services\api.js:77 | `get_auth_me` | **Done & Tested** |
| `POST` | `/api/auth/register` | **Public** | users, app_sessions, user_settings | src\services\api.js:268<br>src\services\api.js:78 | `post_auth_register` | **Done & Tested** |
| `POST` | `/api/auth/resend-verification` | **User** | users, app_sessions, user_settings | src\services\api.js:343 | `post_auth_resend_verification` | **Done & Tested** |
| `POST` | `/api/auth/reset-password` | **Public** | users, app_sessions, user_settings | src\services\api.js:319 | `post_auth_reset_password` | **Done & Tested** |
| `GET` | `/api/auth/sessions` | **User** | users, app_sessions, user_settings | src\services\api.js:366<br>src\services\api.js:374<br>src\services\api.js:385 | `get_auth_sessions` | **Done & Tested** |
| `POST` | `/api/auth/sessions/revoke-others` | **User** | users, app_sessions, user_settings | src\services\api.js:385 | `post_auth_sessions_revoke_others` | **Done & Tested** |
| `DELETE` | `/api/auth/sessions/{session_id}` | **User** | users, app_sessions, user_settings | src\services\api.js:374<br>src\services\api.js:385 | `delete_auth_sessions_session_id` | **Done & Tested** |
| `POST` | `/api/auth/verify-email` | **Public** | users, app_sessions, user_settings | src\services\api.js:331 | `post_auth_verify_email` | **Done & Tested** |

---

## CHAT Controller (`netlify/functions/src/controllers/chat.ts`)

**Endpoints in this module:** 6

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/chat/conversations` | **User** | conversations, conversation_members, chat_messages, users | src\services\api.js:1080<br>src\services\api.js:1088<br>src\services\api.js:1068<br>*(+1 more)* | `get_chat_conversations` | **Done & Tested** |
| `POST` | `/api/chat/conversations` | **User** | conversations, conversation_members, chat_messages, users | src\services\api.js:1080<br>src\services\api.js:1088<br>src\services\api.js:1068<br>*(+1 more)* | `post_chat_conversations` | **Done & Tested** |
| `GET` | `/api/chat/conversations/{conversation_id}/messages` | **User** | conversations, conversation_members, chat_messages, users | src\services\api.js:1088 | `get_chat_conversations_conversation_id_messages` | **Done & Tested** |
| `POST` | `/api/chat/conversations/{conversation_id}/read` | **User** | conversations, conversation_members, chat_messages, users | src\services\api.js:1097 | `post_chat_conversations_conversation_id_read` | **Done & Tested** |
| `DELETE` | `/api/chat/messages/{message_id}` | **User** | conversations, conversation_members, chat_messages, users | src\services\api.js:1107 | `delete_chat_messages_message_id` | **Done & Tested** |
| `POST` | `/api/chat/upload` | **User** | conversations, conversation_members, chat_messages, users | src\services\api.js:1122 | `post_chat_upload` | **Done & Tested** |

---

## COACH Controller (`netlify/functions/src/controllers/coach.ts`)

**Endpoints in this module:** 3

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/coach/chat` | **User** | conversations, conversation_members, chat_messages, users | src\services\api.js:560 | `post_coach_chat` | **Done & Tested** |
| `DELETE` | `/api/coach/history` | **User** | messages, goals, missions, habits, users | src\services\api.js:582<br>src\services\api.js:573 | `delete_coach_history` | **Done & Tested** |
| `GET` | `/api/coach/history` | **User** | messages, goals, missions, habits, users | src\services\api.js:582<br>src\services\api.js:573 | `get_coach_history` | **Done & Tested** |

---

## COMMUNITY Controller (`netlify/functions/src/controllers/community.ts`)

**Endpoints in this module:** 21

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `DELETE` | `/api/community/comments/{comment_id}` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:967<br>src\services\api.js:979 | `delete_community_comments_comment_id` | **Done & Tested** |
| `PATCH` | `/api/community/comments/{comment_id}` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:967<br>src\services\api.js:979 | `patch_community_comments_comment_id` | **Done & Tested** |
| `GET` | `/api/community/posts` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:927<br>src\services\api.js:937<br>src\services\api.js:955<br>*(+5 more)* | `get_community_posts` | **Done & Tested** |
| `POST` | `/api/community/posts` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:927<br>src\services\api.js:937<br>src\services\api.js:955<br>*(+5 more)* | `post_community_posts` | **Done & Tested** |
| `DELETE` | `/api/community/posts/{post_id}` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:927<br>src\services\api.js:937<br>src\services\api.js:955<br>*(+3 more)* | `delete_community_posts_post_id` | **Done & Tested** |
| `GET` | `/api/community/posts/{post_id}` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:927<br>src\services\api.js:937<br>src\services\api.js:955<br>*(+3 more)* | `get_community_posts_post_id` | **Done & Tested** |
| `PATCH` | `/api/community/posts/{post_id}` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:927<br>src\services\api.js:937<br>src\services\api.js:955<br>*(+3 more)* | `patch_community_posts_post_id` | **Done & Tested** |
| `GET` | `/api/community/posts/{post_id}/comments` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:947<br>src\services\api.js:955 | `get_community_posts_post_id_comments` | **Done & Tested** |
| `POST` | `/api/community/posts/{post_id}/comments` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:947<br>src\services\api.js:955 | `post_community_posts_post_id_comments` | **Done & Tested** |
| `DELETE` | `/api/community/posts/{post_id}/like` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:927<br>src\services\api.js:937 | `delete_community_posts_post_id_like` | **Done & Tested** |
| `POST` | `/api/community/posts/{post_id}/like` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:927<br>src\services\api.js:937 | `post_community_posts_post_id_like` | **Done & Tested** |
| `GET` | `/api/social/connections` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:1010<br>src\services\api.js:1033<br>src\services\api.js:1018<br>*(+1 more)* | `get_social_connections` | **Done & Tested** |
| `POST` | `/api/social/connections/accept` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:1033 | `post_social_connections_accept` | **Done & Tested** |
| `POST` | `/api/social/connections/reject` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:1048 | `post_social_connections_reject` | **Done & Tested** |
| `POST` | `/api/social/connections/request` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:1018 | `post_social_connections_request` | **Done & Tested** |
| `GET` | `/api/social/follow-stats/{user_id}` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:1160 | `get_social_follow_stats_user_id` | **Done & Tested** |
| `POST` | `/api/social/follow/{user_id}` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:1138 | `post_social_follow_user_id` | **Done & Tested** |
| `GET` | `/api/social/followers/{user_id}` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:1169 | `get_social_followers_user_id` | **Done & Tested** |
| `GET` | `/api/social/following/{user_id}` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:1178 | `get_social_following_user_id` | **Done & Tested** |
| `GET` | `/api/social/search` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:1002 | `get_social_search` | **Done & Tested** |
| `POST` | `/api/social/unfollow/{user_id}` | **User** | community_posts, community_likes, community_comments, user_connections, user_follows | src\services\api.js:1149 | `post_social_unfollow_user_id` | **Done & Tested** |

---

## CREDENTIALS Controller (`netlify/functions/src/controllers/credentials.ts`)

**Endpoints in this module:** 4

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/credentials` | **User** | user_credentials, users | src\services\api.js:1276<br>src\services\api.js:1265<br>src\services\api.js:1257<br>*(+1 more)* | `get_credentials` | **Done & Tested** |
| `POST` | `/api/credentials/check` | **User** | user_credentials, users | src\services\api.js:1265 | `post_credentials_check` | **Done & Tested** |
| `GET` | `/api/credentials/user/{user_id}` | **Public** | user_credentials, users | src\services\api.js:1257 | `get_credentials_user_user_id` | **Done & Tested** |
| `GET` | `/api/credentials/verify/{credential_id}` | **Public** | user_credentials, users | src\services\api.js:1276 | `get_credentials_verify_credential_id` | **Done & Tested** |

---

## GOALS Controller (`netlify/functions/src/controllers/goals.ts`)

**Endpoints in this module:** 18

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/blueprints` | **User** | life_blueprints, blueprint_areas, blueprint_phases, blueprint_milestones | src\services\api.js:723<br>src\services\api.js:225<br>src\services\api.js:783<br>*(+11 more)* | `get_blueprints` | **Done & Tested** |
| `POST` | `/api/blueprints` | **User** | life_blueprints, blueprint_areas, blueprint_phases, blueprint_milestones | src\services\api.js:723<br>src\services\api.js:225<br>src\services\api.js:783<br>*(+11 more)* | `post_blueprints` | **Done & Tested** |
| `GET` | `/api/blueprints/active` | **User** | life_blueprints, blueprint_areas, blueprint_phases, blueprint_milestones | src\services\api.js:715 | `get_blueprints_active` | **Done & Tested** |
| `DELETE` | `/api/blueprints/milestones/{milestone_id}` | **User** | life_blueprints, blueprint_areas, blueprint_phases, blueprint_milestones | src\services\api.js:843<br>src\services\api.js:832 | `delete_blueprints_milestones_milestone_id` | **Done & Tested** |
| `POST` | `/api/blueprints/milestones/{milestone_id}/toggle` | **User** | life_blueprints, blueprint_areas, blueprint_phases, blueprint_milestones | src\services\api.js:832 | `post_blueprints_milestones_milestone_id_toggle` | **Done & Tested** |
| `DELETE` | `/api/blueprints/phases/{phase_id}` | **User** | life_blueprints, blueprint_areas, blueprint_phases, blueprint_milestones | src\services\api.js:808<br>src\services\api.js:796<br>src\services\api.js:819 | `delete_blueprints_phases_phase_id` | **Done & Tested** |
| `PATCH` | `/api/blueprints/phases/{phase_id}` | **User** | life_blueprints, blueprint_areas, blueprint_phases, blueprint_milestones | src\services\api.js:808<br>src\services\api.js:796<br>src\services\api.js:819 | `patch_blueprints_phases_phase_id` | **Done & Tested** |
| `POST` | `/api/blueprints/phases/{phase_id}/milestones` | **User** | life_blueprints, blueprint_areas, blueprint_phases, blueprint_milestones | src\services\api.js:819 | `post_blueprints_phases_phase_id_milestones` | **Done & Tested** |
| `DELETE` | `/api/blueprints/{blueprint_id}` | **User** | life_blueprints, blueprint_areas, blueprint_phases, blueprint_milestones | src\services\api.js:783<br>src\services\api.js:819<br>src\services\api.js:763<br>*(+8 more)* | `delete_blueprints_blueprint_id` | **Done & Tested** |
| `GET` | `/api/blueprints/{blueprint_id}` | **User** | life_blueprints, blueprint_areas, blueprint_phases, blueprint_milestones | src\services\api.js:783<br>src\services\api.js:819<br>src\services\api.js:763<br>*(+8 more)* | `get_blueprints_blueprint_id` | **Done & Tested** |
| `PATCH` | `/api/blueprints/{blueprint_id}` | **User** | life_blueprints, blueprint_areas, blueprint_phases, blueprint_milestones | src\services\api.js:783<br>src\services\api.js:819<br>src\services\api.js:763<br>*(+8 more)* | `patch_blueprints_blueprint_id` | **Done & Tested** |
| `POST` | `/api/blueprints/{blueprint_id}/activate` | **User** | life_blueprints, blueprint_areas, blueprint_phases, blueprint_milestones | src\services\api.js:763 | `post_blueprints_blueprint_id_activate` | **Done & Tested** |
| `POST` | `/api/blueprints/{blueprint_id}/phases` | **User** | life_blueprints, blueprint_areas, blueprint_phases, blueprint_milestones | src\services\api.js:796<br>src\services\api.js:783<br>src\services\api.js:808<br>*(+1 more)* | `post_blueprints_blueprint_id_phases` | **Done & Tested** |
| `GET` | `/api/goals` | **User** | goals, life_blueprints, blueprint_milestones | src\services\api.js:539<br>src\services\api.js:520<br>src\services\api.js:550<br>*(+2 more)* | `get_goals` | **Done & Tested** |
| `POST` | `/api/goals` | **User** | goals, life_blueprints, blueprint_milestones | src\services\api.js:539<br>src\services\api.js:520<br>src\services\api.js:550<br>*(+2 more)* | `post_goals` | **Done & Tested** |
| `DELETE` | `/api/goals/{goal_id}` | **User** | goals, life_blueprints, blueprint_milestones | src\services\api.js:550<br>src\services\api.js:539 | `delete_goals_goal_id` | **Done & Tested** |
| `GET` | `/api/goals/{goal_id}` | **User** | goals, life_blueprints, blueprint_milestones | src\services\api.js:550<br>src\services\api.js:539 | `get_goals_goal_id` | **Done & Tested** |
| `PATCH` | `/api/goals/{goal_id}` | **User** | goals, life_blueprints, blueprint_milestones | src\services\api.js:550<br>src\services\api.js:539 | `patch_goals_goal_id` | **Done & Tested** |

---

## HABITS Controller (`netlify/functions/src/controllers/habits.ts`)

**Endpoints in this module:** 7

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/habits` | **User** | habits, habit_logs, users | src\services\api.js:621<br>src\services\api.js:601<br>src\services\api.js:593<br>*(+4 more)* | `get_habits` | **Done & Tested** |
| `POST` | `/api/habits` | **User** | habits, habit_logs, users | src\services\api.js:621<br>src\services\api.js:601<br>src\services\api.js:593<br>*(+4 more)* | `post_habits` | **Done & Tested** |
| `GET` | `/api/habits/stats` | **User** | habits, habit_logs, users | src\services\api.js:601 | `get_habits_stats` | **Done & Tested** |
| `DELETE` | `/api/habits/{habit_id}` | **User** | habits, habit_logs, users | src\services\api.js:621<br>src\services\api.js:633<br>src\services\api.js:601<br>*(+1 more)* | `delete_habits_habit_id` | **Done & Tested** |
| `GET` | `/api/habits/{habit_id}` | **User** | habits, habit_logs, users | src\services\api.js:621<br>src\services\api.js:633<br>src\services\api.js:601<br>*(+1 more)* | `get_habits_habit_id` | **Done & Tested** |
| `PATCH` | `/api/habits/{habit_id}` | **User** | habits, habit_logs, users | src\services\api.js:621<br>src\services\api.js:633<br>src\services\api.js:601<br>*(+1 more)* | `patch_habits_habit_id` | **Done & Tested** |
| `POST` | `/api/habits/{habit_id}/toggle` | **User** | habits, habit_logs, users | src\services\api.js:643 | `post_habits_habit_id_toggle` | **Done & Tested** |

---

## HEALTH Controller (`netlify/functions/src/controllers/health.ts`)

**Endpoints in this module:** 5

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | **Public** | N/A | *api.js / direct* | `get__` | **Done & Tested** |
| `GET` | `/api/health` | **Public** | N/A | *api.js / direct* | `get_health` | **Done & Tested** |
| `GET` | `/api/health/ready` | **Public** | N/A | *api.js / direct* | `get_health_ready` | **Done & Tested** |
| `GET` | `/health` | **Public** | N/A | *api.js / direct* | `get__health` | **Done & Tested** |
| `GET` | `/ready` | **Public** | N/A | *api.js / direct* | `get__ready` | **Done & Tested** |

---

## JOURNAL Controller (`netlify/functions/src/controllers/journal.ts`)

**Endpoints in this module:** 7

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/journal` | **User** | journal_entries, users | src\services\api.js:663<br>src\services\api.js:655<br>src\services\api.js:229<br>*(+4 more)* | `post_journal` | **Done & Tested** |
| `GET` | `/api/journal/history` | **User** | journal_entries, users | src\services\api.js:663 | `get_journal_history` | **Done & Tested** |
| `GET` | `/api/journal/stats` | **User** | journal_entries, users | src\services\api.js:671 | `get_journal_stats` | **Done & Tested** |
| `GET` | `/api/journal/today` | **User** | journal_entries, users | src\services\api.js:655 | `get_journal_today` | **Done & Tested** |
| `DELETE` | `/api/journal/{entry_id}` | **User** | journal_entries, users | src\services\api.js:663<br>src\services\api.js:655<br>src\services\api.js:704<br>*(+2 more)* | `delete_journal_entry_id` | **Done & Tested** |
| `POST` | `/api/journal/{entry_id}/analyze` | **User** | journal_entries, users | src\services\api.js:692 | `post_journal_entry_id_analyze` | **Done & Tested** |
| `GET` | `/api/reflection/daily` | **User** | journal_entries, users | src\services\api.js:990 | `get_reflection_daily` | **Done & Tested** |

---

## MISC Controller (`netlify/functions/src/controllers/misc.ts`)

**Endpoints in this module:** 2

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/search` | **User** | N/A | src\services\api.js:854 | `get_search` | **Done & Tested** |
| `GET` | `/health/ready` | **Public** | N/A | *api.js / direct* | `get__health_ready` | **Done & Tested** |

---

## MISSIONS Controller (`netlify/functions/src/controllers/missions.ts`)

**Endpoints in this module:** 3

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/missions` | **User** | missions, mission_logs, users | src\services\api.js:475<br>src\services\api.js:219<br>src\services\api.js:486<br>*(+1 more)* | `get_missions` | **Done & Tested** |
| `POST` | `/api/missions` | **User** | missions, mission_logs, users | src\services\api.js:475<br>src\services\api.js:219<br>src\services\api.js:486<br>*(+1 more)* | `post_missions` | **Done & Tested** |
| `PATCH` | `/api/missions/{mission_id}/toggle` | **User** | missions, mission_logs, users | src\services\api.js:486 | `patch_missions_mission_id_toggle` | **Done & Tested** |

---

## NOTIFICATIONS Controller (`netlify/functions/src/controllers/notifications.ts`)

**Endpoints in this module:** 6

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/notifications` | **User** | notifications | src\services\api.js:1217<br>src\hooks\useNotificationsSocket.js:37<br>src\hooks\useNotificationsSocket.js:39<br>*(+5 more)* | `get_notifications` | **Done & Tested** |
| `PATCH` | `/api/notifications/read-all` | **User** | notifications | *api.js / direct* | `patch_notifications_read_all` | **Done & Tested** |
| `PATCH` | `/api/notifications/read_all` | **User** | notifications | src\services\api.js:1217 | `patch_notifications_read_all` | **Done & Tested** |
| `GET` | `/api/notifications/unread-count` | **User** | notifications | src\services\api.js:1199 | `get_notifications_unread_count` | **Done & Tested** |
| `DELETE` | `/api/notifications/{notification_id}` | **User** | notifications | src\services\api.js:1217<br>src\hooks\useNotificationsSocket.js:37<br>src\hooks\useNotificationsSocket.js:39<br>*(+4 more)* | `delete_notifications_notification_id` | **Done & Tested** |
| `PATCH` | `/api/notifications/{notification_id}/read` | **User** | notifications | src\services\api.js:1207<br>src\services\api.js:1217 | `patch_notifications_notification_id_read` | **Done & Tested** |

---

## PROGRESS Controller (`netlify/functions/src/controllers/progress.ts`)

**Endpoints in this module:** 5

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/progress` | **User** | missions, mission_logs, habits, habit_logs, journal_entries, users | src\services\api.js:1241<br>src\services\api.js:504<br>src\services\api.js:496<br>*(+1 more)* | `get_progress` | **Done & Tested** |
| `GET` | `/api/progress/daily` | **User** | missions, mission_logs, habits, habit_logs, journal_entries, users | src\services\api.js:504 | `get_progress_daily` | **Done & Tested** |
| `GET` | `/api/progress/telemetry` | **User** | missions, mission_logs, habits, habit_logs, journal_entries, users | src\services\api.js:512 | `get_progress_telemetry` | **Done & Tested** |
| `GET` | `/api/progression` | **User** | missions, mission_logs, habits, habit_logs, journal_entries, users | src\services\api.js:1241 | `get_progression` | **Done & Tested** |
| `GET` | `/api/telemetry` | **User** | missions, mission_logs, habits, habit_logs, journal_entries, users | *api.js / direct* | `get_telemetry` | **Done & Tested** |

---

## USERS Controller (`netlify/functions/src/controllers/users.ts`)

**Endpoints in this module:** 8

| Method | Endpoint | Auth | DB Tables | Frontend Callers | Replacement Handler | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/settings` | **User** | N/A | src\services\api.js:862<br>src\services\api.js:870<br>src\services\api.js:231 | `get_settings` | **Done & Tested** |
| `PATCH` | `/api/settings` | **User** | N/A | src\services\api.js:862<br>src\services\api.js:870<br>src\services\api.js:231 | `patch_settings` | **Done & Tested** |
| `GET` | `/api/users` | **User** | users, app_sessions, user_settings | src\services\api.js:407<br>src\services\api.js:446<br>src\services\api.js:438<br>*(+4 more)* | `get_users` | **Done & Tested** |
| `PATCH` | `/api/users` | **User** | users, app_sessions, user_settings | src\services\api.js:407<br>src\services\api.js:446<br>src\services\api.js:438<br>*(+4 more)* | `patch_users` | **Done & Tested** |
| `DELETE` | `/api/users/account` | **User** | users, app_sessions, user_settings | src\services\api.js:407 | `delete_users_account` | **Done & Tested** |
| `POST` | `/api/users/onboarding` | **User** | users, app_sessions, user_settings | src\services\api.js:422 | `post_users_onboarding` | **Done & Tested** |
| `GET` | `/api/users/search` | **User** | users, app_sessions, user_settings | src\services\api.js:1060 | `get_users_search` | **Done & Tested** |
| `GET` | `/api/users/{user_id}` | **User** | users, app_sessions, user_settings | src\services\api.js:407<br>src\services\api.js:446<br>src\services\api.js:422<br>*(+1 more)* | `get_users_user_id` | **Done & Tested** |

---
