# Mastery Key Coach — Netlify Environment Variables Reference

This document details all environment variables required by **Mastery Key Coach (MKC)** when running as a unified frontend and backend on Netlify.

## Where to Set Environment Variables

In your Netlify Dashboard:
1. Navigate to **Site configuration** -> **Environment variables**
2. Click **Add a variable** -> **Add a single variable** (or **Import from .env**)
3. Set the scope to **All scopes** (Builds, Functions, Post-processing, etc.)
4. Save the variable. Subsequent deploys or function invocations will automatically have access to these variables via `process.env`.

---

## Variable Reference Table

| Variable Name | Required? | Category | Description | Example Value |
| :--- | :--- | :--- | :--- | :--- |
| `DATABASE_URL` | **YES** | Database | Connection string for Supabase PostgreSQL. Supports both direct (5432) and transaction pooler (6543). | `postgresql://postgres.example:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require` |
| `GEMINI_API_KEY` | **YES** | AI Coach | Google Gemini API key for the AI Coach chat (`/api/coach/chat`) and Journal sentiment reflection (`/api/journal/{id}/analyze`). | `AIzaSyD_ExampleApiKey1234567890abcdef` |
| `SESSION_SECRET` | **YES** | Security | Secret string used for signing and verifying session cookies and tokens. | `mkc_prod_sec_9874528174a7b8c9d0e1f2a3b4c5d6e7f8` |
| `NODE_ENV` | Optional | Runtime | Environment flag. Defaults to `production` in Netlify builds. | `production` |
| `MKC_SECURE_COOKIES` | Optional | Security | Set to `true` (default in production) to enforce `Secure; HttpOnly; SameSite=Lax` on all auth session cookies. | `true` |
| `VITE_API_URL` | Optional | Frontend | In the unified architecture, the API is hosted on the same domain (`/api/*`), so this should either be left blank or set to `/api`. | `""` (empty string) |

---

## Supabase PostgreSQL Connection String Guidance

When retrieving the connection string from Supabase:
1. Open your Supabase project dashboard at `app.supabase.com`.
2. Go to **Project Settings** -> **Database**.
3. Under **Connection string**, select the **URI** tab.
4. If connecting from serverless functions (like Netlify Functions), choose **Transaction Pooler (Port 6543)** for optimal connection management under serverless auto-scaling:
   ```text
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
   ```
5. Replace `[YOUR-PASSWORD]` with your actual Supabase database password.
6. Make sure `?sslmode=require` is appended to the URI so encrypted TLS is enforced.
