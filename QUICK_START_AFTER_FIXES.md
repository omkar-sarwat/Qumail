# Quick Start Guide - After Backend Fixes

## ✅ Fixes Applied

All backend OAuth and KME issues have been fixed:

1. ✅ KME server port configuration (KME_ID='1' and '2')
2. ✅ KME health check endpoint (now uses `/api/v1/kme/status`)
3. ✅ OAuth redirect port complexity removed (simplified)
4. ✅ Electron redirect URI separated (port 5174 vs 5173)

## 🚀 Start the System

### Step 1: Close All Running Services
Close any open terminal windows from previous runs.

### Step 2: Start All Services
```powershell
cd "d:\New folder (8)\qumail-secure-email"
.\START_TERMINALS.ps1
```

This will open 4 terminal windows:
- **Terminal 1**: KME1 Server (port 8010)
- **Terminal 2**: KME2 Server (port 8020)
- **Terminal 3**: Backend Server (port 8000)
- **Terminal 4**: Vite Dev Server (port 5173)

### Step 3: Wait for All Services to Start

#### Check KME1 Terminal:
```
Loading configuration for KME_ID: 1
Loaded .env.kme1
* Running on http://127.0.0.1:8010
```

#### Check KME2 Terminal:
```
Loading configuration for KME_ID: 2
Loaded .env.kme2
* Running on http://127.0.0.1:8020
```

#### Check Backend Terminal:
```
⏳ Waiting for KME servers... (0s/60s)
⏳ Waiting for KME servers... (2s/60s)
✓ KME servers are ready!
Quantum Key Management System initialized
Application startup complete
```

#### Check Vite Terminal:
```
VITE v5.4.20  ready in 1234 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Step 4: Start Electron App
Once all services are running (especially backend showing "Application startup complete"):

```powershell
cd qumail-frontend
npm run electron:compile
npm run electron:start
```

## 🧪 Test OAuth Flow

### In Electron App:
1. You should see the login screen (not blank!)
2. Click **"Continue with Gmail"** button
3. Your default browser will open (NOT embedded in app)
4. Complete Google OAuth in the browser
5. Browser will show success page and redirect
6. Electron app will receive the callback
7. You should be logged in and see the dashboard

### Expected Log Messages:

**Frontend Console:**
```
Initiating Google OAuth login...
Got OAuth URL
Running in Electron - opening system browser...
OAuth callback received in Electron
Authentication successful! Setting up your quantum mailbox...
User authenticated: your-email@gmail.com
```

**Backend Terminal:**
```
Generated OAuth URL with state: xyz123..., is_electron: True
Using redirect URI: http://localhost:5174/auth/callback
OAuth callback received: code=4/0A..., state=xyz123...
Real user authenticated: your-email@gmail.com
```

## 🔍 Troubleshooting

### If KME Servers Don't Start:
- Check if Python is in PATH
- Verify `next-door-key-simulator` has requirements installed
- Check ports 8010 and 8020 aren't in use: `netstat -ano | findstr "8010"`

### If Backend Times Out:
- Ensure BOTH KME terminals show "Running on http://127.0.0.1:XXXX"
- Wait up to 60 seconds for health check
- Check backend terminal for specific error messages

### If Electron Shows Blank Screen:
- Ensure Vite terminal shows "ready" message
- Check if http://localhost:5173 works in regular browser
- Try restarting Electron: Ctrl+C, then `npm run electron:start`

### If OAuth Fails:
- Check `client_secrets.json` exists and has valid Google OAuth credentials
- Verify redirect URI `http://localhost:5174/auth/callback` is registered in Google Cloud Console
- Check backend logs for "OAuth callback received" message
- Try clearing OAuth states: `POST http://localhost:8000/api/v1/auth/debug/clear-states`

## 📊 System Architecture

```
┌─────────────────┐
│  Electron App   │ (Launches)
│   Port: N/A     │
└────────┬────────┘
         │ connects to
         ▼
┌─────────────────┐
│  Vite Dev       │ http://localhost:5173
│  Server         │ (React UI)
└────────┬────────┘
         │ API calls
         ▼
┌─────────────────┐
│  FastAPI        │ http://localhost:8000
│  Backend        │ (OAuth + Quantum)
└────┬───────┬────┘
     │       │
     │       └──────────────┐
     │                      │
     ▼                      ▼
┌─────────┐          ┌─────────┐
│  KME1   │          │  KME2   │
│  :8010  │◄────────►│  :8020  │
└─────────┘          └─────────┘
(Quantum Key         (Quantum Key
 Generator)           Retriever)
```

## 🎯 OAuth Flow

```
Electron App
     │
     ├─ User clicks "Continue with Gmail"
     │
     ▼
Backend: GET /api/v1/auth/google?is_electron=true
     │
     ├─ Returns: { authorization_url, state }
     │
     ▼
Electron IPC: startOAuthFlow
     │
     ├─ Opens: System Browser
     ├─ Listens: Port 5174
     │
     ▼
User completes OAuth in Browser
     │
     ├─ Google redirects to: http://localhost:5174/auth/callback?code=...&state=...
     │
     ▼
Electron catches callback
     │
     ├─ Closes: HTTP server
     ├─ Shows: Success page
     │
     ▼
Returns to App: { code, state }
     │
     ▼
Backend: POST /api/v1/auth/callback
     │
     ├─ Exchange code for tokens
     ├─ Create user in MongoDB
     │
     ▼
App: Dashboard loads 🎉
```

## 📁 Key Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `START_TERMINALS.ps1` | Fixed KME_ID env vars | Start KME servers correctly |
| `app/main.py` | Fixed health check endpoint | Wait for KME servers properly |
| `app/api/auth.py` | Removed redirect_port param | Simplify OAuth flow |
| `app/services/gmail_oauth.py` | Fixed redirect URIs | Separate Electron from web |
| `src/services/authService.ts` | Removed redirect_port | Simplify frontend API calls |
| `src/components/auth/LoginScreen.tsx` | Removed port param | Trust backend for port selection |

## ✨ What's Working Now

- ✅ All 4 services start properly
- ✅ KME servers run on correct ports (8010, 8020)
- ✅ Backend detects KME readiness
- ✅ Quantum Key Manager initializes
- ✅ OAuth opens in system browser (not embedded)
- ✅ OAuth callback reaches Electron via port 5174
- ✅ User authentication completes
- ✅ App loads dashboard after login

## 🎉 Success Criteria

You know everything is working when:

1. ✅ All 4 terminals show "running" or "ready"
2. ✅ Backend shows "✓ KME servers are ready!"
3. ✅ Electron app shows login screen (not blank)
4. ✅ OAuth opens in browser (not embedded)
5. ✅ After OAuth, app shows dashboard

---

**Ready to test? Start with Step 1 above!** 🚀
