# QuMail Cloud Troubleshooting Guide

Use this checklist whenever the Render deployment (KMEs + backend) or MongoDB Atlas/Redis Cloud integrations misbehave.

## 1. Render Deployment Issues

| Symptom | Checks | Fix |
| --- | --- | --- |
| Service stuck in build loop | Review **Logs → Build** in Render dashboard | Ensure `pip install -r requirements.txt` succeeds; pin Python version via `render.yaml` if needed |
| Service crashes immediately | Inspect **Logs → Runtime** | Confirm `PORT` env var matches Render-provided port, not hard-coded 8010/8020 for backend |
| `ModuleNotFoundError` | Build log shows missing dependency | Re-run `pip freeze` locally and commit updated `requirements.txt` |
| Blueprint ignored rootDir | Render service built wrong folder | Double-check `rootDir` in `render.yaml` matches `next-door-key-simulator` or `qumail-backend` |

## 2. MongoDB Atlas Connection Problems

- **Timeout / auth failed:**
  - Verify `DATABASE_URL` string includes database name (e.g., `/qumail`).
  - Make sure the user has **Read/Write to Any Database** or specific DB.
  - Check Atlas IP Access List includes Render egress IPs or `0.0.0.0/0` (temporary).
- **TLS errors:** Ensure SRV URI uses `mongodb+srv://`. Render supports TLS by default—do not downgrade.
- **Schema mismatch:** Use Atlas Data Explorer to confirm `users`, `drafts`, and `encryption_metadata` exist and contain the expected fields (`flow_id`, `security_level`, `key_ids`, etc.).

## 3. Redis Cloud Configuration Issues

- **`Redis connection failed`:**
  - Confirm hostname/port/password exactly match the Redis Cloud dashboard.
  - The username is usually `default`; include it in the URI.
  - Free plan enforces TLS → prefix with `rediss://` if TLS is enabled.
- **Keys missing/expired:** Keys are stored with 24h TTL. If decryption fails after 24h, resend the email to generate fresh keys.
- **Multiple KMEs not sharing keys:** Ensure both KMEs point to the same `REDIS_URL` and `SHARED_POOL_ENABLED=true`.

## 4. CORS / Electron Integration

- Backend FastAPI must allow Electron origins:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=['*'],  # or qumail://* if you register protocol
      allow_methods=['*'],
      allow_headers=['*']
  )
  ```
- If the Electron app shows `Network Error`, confirm `QUMAIL_API_BASE_URL` matches the Render backend URL **including** `/api/v1` suffix.
- Custom protocol flow: ensure `app.setAsDefaultProtocolClient('qumail')` succeeds and that the OS registers the handler.

## 5. Environment Variable Debugging

1. In Render dashboard open the service → **Environment** tab; verify every variable has the expected value.
2. Use Render shell (`Connect → Shell`) and run `env | sort` to confirm what the process sees.
3. For Electron, run the app with `DEBUG=qumail:*` (set in PowerShell `set DEBUG=qumail:*`) to log resolved URLs.
4. Keep `.env.template` updated; treat it as the canonical list of required keys.

## 6. Backend Health Failures

- Run `python scripts/check_render_deployment.py ...` to see exactly which dependency failed.
- If `/health` logs mention KMEs unreachable, ensure `KME1_URL`/`KME2_URL` include `https://` and the services are not sleeping (Render free tier may spin down—first request wakes them up).

## 7. Gmail OAuth Problems

- Double-check Google Cloud Console → OAuth consent → Authorized redirect URI (`qumail://auth/callback` or `http://localhost:3000/auth/callback`).
- Ensure the backend has `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GMAIL_SCOPES` set.
- If the OAuth popup closes immediately, inspect backend logs for `/auth/google/callback` errors (missing code, incorrect redirect, clock skew).

Keep this guide in sync with production incidents—append new scenarios as they arise.
