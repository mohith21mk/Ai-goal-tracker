# MKC Deployment Backlog & Deferred Release Plan

## Netlify Deployment Status

**Status:** `DEPLOYMENT PAUSED — ACCOUNT OPERATIONAL CREDITS EXCEEDED`  
**Current Production Site:** [https://mastery-key-coach.netlify.app](https://mastery-key-coach.netlify.app)  
**Backend Production API:** [https://mkc-backend-iguj.onrender.com](https://mkc-backend-iguj.onrender.com)  
**Repository:** [https://github.com/mohith21mk/Ai-goal-tracker](https://github.com/mohith21mk/Ai-goal-tracker)  
**Branch:** `main`  
**Currently Published Production Commit:** `2af855e` (*fix(theme): improve light mode with classic warm sand palette and responsive sidebar theme switching*)

---

## 1. Operating Rules During Credit Freeze

1. **NO Netlify Production Deployments**: Do NOT trigger, force, retry, or repeatedly rebuild Netlify production deployments while credits are paused.
2. **NO Code Reverts**: Do NOT delete, refactor, or revert valid working code simply because Netlify skipped a build.
3. **GitHub `main` is Canonical**: All ongoing development, verified features, and backend updates remain committed and pushed to `origin/main`.
4. **Local & Backend Continuity**:
   - Continue development locally (`http://localhost:5173`).
   - Continue running full backend and frontend test suites (`pytest`, `npm run lint`, `npm run build`).
   - Keep the Render backend synchronized with current database schemas.
5. **Evaluation Rule**: Do not judge new frontend features against the currently published Netlify UI until the next deployment. GitHub `main` holds the true source code.

---

## 2. Skipped Commits Registry

The following table records every commit pushed to `main` that was skipped by Netlify due to credit limits. All work is preserved in Git and verified locally.

| Commit | Message | Features / Scope | Local Code Status | Netlify Status | Needs Production Deploy |
|---|---|---|---|---|---|
| `9d000f2` | `Remove theme switching and restore permanent premium dark theme` | Removed light/dark toggle; restored unified permanent dark MKC styling across TopBar, Settings, App. | Verified & Passing | **Skipped** (*Credit usage exceeded*) | **YES** (Included in latest batch) |
| `41fefaa` | `Enhance real-time chat with typing indicators, sidebar unread badges, and fast filter search` | Added WebSocket typing indicators, sidebar unread chat badges, conversation search filtering. | Verified & Passing | **Skipped** (*Credit usage exceeded*) | **YES** (Included in latest batch) |
| `b9cfc74` | `feat(v2): release MKC Messages, Social Follows & Account Management Full Upgrade` | Added Followers/Following social system, Rich Chat (Emojis popover, MKC vector stickers, image upload + lightbox, voice memos with waveform player), Danger Zone account deletion with last-admin guard, and storage adapter. | Verified & Passing (15/15 tests) | **Skipped** (*Credit usage exceeded*) | **YES** (Included in latest batch) |
| `3a53101` | `fix(deploy): add root package.json and harmonize Netlify monorepo build configs` | Added root `package.json` monorepo configuration, Node 20 build environment in `netlify.toml` and `frontend/netlify.toml`. | Verified & Passing | **Skipped** (*Credit usage exceeded*) | **YES** (Included in latest batch) |
| `1c11608` | `feat(telemetry): separate overall performance metrics from daily progress with normalized formulas` | Architectural refactor separating Overall Performance Metrics (lifetime, Bayesian normalized, stable) from Daily Progress (current day only, auto-reset). Added `GET /api/progress/daily` and `progress_engine.py`. | Verified & Passing (20/20 tests) | **Skipped** (*Credit usage exceeded*) | **YES** (Included in latest batch) |
| `dd75209` | `fix(telemetry): implement multi-horizon historical models and volume confidence scaling` | Implemented multi-horizon time modeling (Lifetime 50%, 90d 25%, 30d 15%, 7d 10%), account baseline normalization, and asymptotic volume-confidence scaling $C_v(N) = 1 - e^{-N/k}$. Today's activity is intentionally a small component of the overall score, while historical data carries the majority of the weighting. | Verified & Passing (20/20 tests) | **Skipped** (*Credit usage exceeded*) | **YES** (Included in latest batch) |
| `[PENDING]` | `feat(missions): automatic daily checklist reset with mission_logs historical persistence` | Added `mission_logs` architecture for recurring daily protocol completions. The checklist automatically resets to unchecked on a new calendar day (whether missions were completed or uncompleted yesterday), while permanently retaining historical completions, cumulative XP, active days, and streak telemetry. | Verified & Passing (200+ tests) | **Skipped** (*Credit usage exceeded*) | **YES** (Included in latest batch) |

---

## 3. Deferred Production Deployment

**Target Review Date:** `2026-09-30`

At or after this review date, check whether Netlify production deployment credits have been restored for the billing cycle.

### Deployment Workflow (When Credits Return):
1. **Verify Canonical Head**: Review all commits on `main` up to the newest verified commit.
2. **Single Atomic Deployment**: Trigger a single production deployment of the latest verified `main` commit. All accumulated changes (`9d000f2` through `dd75209`+) will be bundled together in one build. Do **not** deploy intermediate commits one by one.
3. **Backend Compatibility**: Confirm Render backend (`https://mkc-backend-iguj.onrender.com`) is running and compatible with the latest frontend contracts.
4. **Execute Production Smoke Test**: Run the complete checklist below.

---

## 4. Final Acceptance Test Scenario (When Credits Return)

When the new frontend is deployed, verify this exact progression scenario:

- [ ] **Day 1**:
  - Complete 1 mission.
  - **Daily Progress**: Displays $100\%$ ($1/1$ actions done, XP earned today).
  - **Overall Discipline**: Remains low/modest ($\le 15.0$, confidence-damped).
- [ ] **Day 2**:
  - Complete zero actions.
  - **Daily Progress**: Resets to $0\%$ ($0$ completed actions today).
  - **Overall Discipline**: Does NOT reset to $0$; historical score persists.
- [ ] **Day 3**:
  - Complete several missions and habits.
  - **Daily Progress**: Reflects today's activity accurately.
  - **Overall Performance**: Rises gradually (e.g. $+0.5$ to $+1.5$), never jumping wildly to $100$.
- [ ] **Long-Term Evolution**:
  - Historical behavior dominates all calculations.
  - Overall score becomes increasingly stable and reflective of true cumulative mastery.

---

## 5. Production Smoke-Test Checklist

Once the production deployment is completed on Netlify, execute the following end-to-end audit:

### A. Core Architecture & Authentication
- [ ] Landing page loads correctly.
- [ ] User registration flow succeeds.
- [ ] User login and session persistence via secure cookies.
- [ ] Protected route guards enforce authentication.
- [ ] Single Page Application (SPA) browser refresh works without 404s (verified `_redirects`).
- [ ] User sign out clears active session and redirects cleanly.

### B. Progression & Performance Telemetry
- [ ] **Dashboard — Today's Progress (Section A)**:
  - [ ] Progress circle displays today's completion percentage.
  - [ ] Today's actions completed / scheduled count accurately reflects current day.
  - [ ] Toggling a mission updates daily actions and today's XP.
- [ ] **Dashboard — Overall Performance (Section B)**:
  - [ ] Discipline Score reflects normalized lifetime execution (stable, no wild 0 $\rightarrow$ 100 jumps).
  - [ ] Mindset Strength, Consistency, and Growth Index display stable values.
  - [ ] Current Streak, Longest Streak, and Active Days display accurate integers.
  - [ ] Identity Level, Rank, and Total XP match server-authoritative progression.
- [ ] **New Day Transition**:
  - [ ] Daily Progress resets to 0 actions on a new calendar day.
  - [ ] Overall Performance Metrics, Total XP, and active streaks do NOT reset.

### C. Rich Messaging & Social System
- [ ] **Social Follows**:
  - [ ] Public profile displays Follow / Unfollow button with real-time stat counts.
  - [ ] Profile page shows interactive Followers / Following list modal with toggle action.
- [ ] **Rich Chat Messages**:
  - [ ] Text messages send and render in real-time via WebSockets.
  - [ ] Emoji picker inserts emojis into the message composer.
  - [ ] MKC Stickers send and render custom graphic cards.
  - [ ] Image attachment upload displays thumbnail and opens full-screen Lightbox modal.
  - [ ] Voice memo records audio, displays live timer, and plays back via interactive waveform scrubber.
  - [ ] Deleting a message removes it from the conversation.

### D. Community & Identity
- [ ] Community feed loads public posts with category filters.
- [ ] Post creation, comment submission, and like/unlike toggle.
- [ ] Credential badge attachment and modal verification.
- [ ] Direct messaging author from community post.

### E. Admin Dashboard (`/admin`)
- [ ] Admin route enforces role authorization (accessible to admin, blocked for standard users).
- [ ] User directory loads real database users with pagination and search.
- [ ] User detail modal opens individual telemetry, streak, and XP data.
- [ ] Feedback queue loads user submissions with status updates.

### F. Theme & Visual Consistency
- [ ] Permanent premium dark theme renders consistently across all pages.
- [ ] No light mode toggle or theme switcher visible.
- [ ] Contrast, typography, glassmorphism cards, and inputs display properly.

---

## 6. Deployment Safety & Pre-Deploy Validation

Before triggering the deferred deployment on Netlify, run:

```bash
# 1. Run full backend regression suite
cd backend
python -m pytest tests/ -q

# 2. Run frontend lint and production build
cd ../frontend
npm run lint
npm run build
```

**Verify:**
1. `frontend/dist/` exists and contains `index.html` and bundled assets.
2. `frontend/dist/_redirects` exists with `/* /index.html 200`.
3. No hardcoded `localhost` URLs in production code.
4. `VITE_API_URL` defaults to `https://mkc-backend-iguj.onrender.com`.
5. `git status` confirms a clean working tree on `main`.
