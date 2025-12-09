# Yahoo OAuth Integration for QuMail

## Overview

This document describes the Yahoo OAuth 2.0 integration that allows QuMail users to authenticate with their Yahoo accounts and access Yahoo Mail through the QuMail platform.

## Important Note: Yahoo HTTPS Requirement

**Yahoo requires HTTPS redirect URIs**. Unlike Google which allows `http://localhost`, Yahoo only accepts:
- HTTPS URLs with valid SSL certificates
- The special `127.0.0.1` address (which Yahoo treats differently from `localhost`)

For local development, we use: `https://127.0.0.1:5173/auth/yahoo/callback`

## Setup Instructions

### 1. Create Yahoo Developer Application

1. Go to [Yahoo Developer Console](https://developer.yahoo.com/apps/)
2. Sign in with your Yahoo account
3. Click "Create an App"
4. Fill in the application details:
   - **Application Name**: QuMail
   - **Application Type**: Web Application
   - **Redirect URI(s)**: 
     - `https://127.0.0.1:5173/auth/yahoo/callback` (for local development)
     - `https://your-production-domain.com/auth/yahoo/callback` (for production)
   - **API Permissions**: Select "Yahoo Mail" API access
5. Click "Create App"
6. Copy the **Client ID** and **Client Secret**

### 2. Configure Environment Variables

Add the following to your `.env` file in the `qumail-backend` directory:

```env
YAHOO_CLIENT_ID=your_yahoo_client_id_here
YAHOO_CLIENT_SECRET=your_yahoo_client_secret_here
YAHOO_REDIRECT_URI=https://127.0.0.1:5173/auth/yahoo/callback
```

### 3. Local Development HTTPS Setup

Since Yahoo requires HTTPS, you have two options for local development:

#### Option A: Use Vite's HTTPS mode (Recommended)

Update your `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    https: true,
    host: '127.0.0.1',
    port: 5173
  }
})
```

Vite will generate a self-signed certificate. Accept the browser warning when first accessing the app.

#### Option B: Generate self-signed certificates

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=127.0.0.1"
```

Then configure Vite to use these certificates.

## API Endpoints

### Authentication Routes (`/api/v1/auth/yahoo/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | Check if Yahoo OAuth is configured |
| `/login` | GET | Start OAuth flow, returns authorization URL |
| `/callback` | GET | Handle OAuth callback, exchange code for tokens |
| `/refresh` | POST | Refresh expired access token |
| `/revoke` | POST | Revoke OAuth tokens |

### Email Routes (`/api/v1/yahoo/mail/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/folders` | GET | Get list of mail folders |
| `/messages` | GET | Get messages from a folder |
| `/messages/{id}` | GET | Get full message details |
| `/send` | POST | Send an email |
| `/messages/{id}/read` | POST | Mark message as read |
| `/messages/{id}/unread` | POST | Mark message as unread |
| `/messages/{id}` | DELETE | Delete a message |
| `/messages/{id}/move` | POST | Move message to folder |
| `/search` | GET | Search messages |
| `/drafts` | POST | Create a draft |

## OAuth Flow

1. User clicks "Continue with Yahoo" on login page
2. Frontend calls `GET /api/v1/auth/yahoo/login` to get authorization URL
3. Frontend stores OAuth state in localStorage for CSRF protection
4. User is redirected to Yahoo login page
5. After user authorizes, Yahoo redirects to callback URL with authorization code
6. Frontend `YahooOAuthCallback` component captures the code
7. Frontend calls `GET /api/v1/auth/yahoo/callback?code=xxx&state=xxx`
8. Backend exchanges code for tokens via Yahoo API
9. Backend stores encrypted tokens in user's MongoDB document
10. User is redirected to dashboard

## Yahoo OAuth Scopes

The following scopes are requested:

- `openid` - OpenID Connect authentication
- `email` - Access to user's email address
- `profile` - Access to user's profile information
- `mail-r` - Read access to Yahoo Mail
- `mail-w` - Write access to Yahoo Mail (send emails)

## Security Considerations

1. **Token Encryption**: All OAuth tokens are encrypted using Fernet symmetric encryption before storage
2. **CSRF Protection**: OAuth state parameter prevents cross-site request forgery
3. **Token Refresh**: Access tokens are automatically refreshed when expired
4. **HTTPS Required**: Yahoo OAuth only works over HTTPS connections

## Files Created/Modified

### Backend

- `app/services/yahoo_oauth.py` - Yahoo OAuth service class
- `app/services/yahoo_mail_service.py` - Yahoo Mail API service
- `app/api/yahoo_auth_routes.py` - Yahoo OAuth API routes
- `app/api/yahoo_email_routes.py` - Yahoo Mail API routes
- `app/config.py` - Added Yahoo configuration settings
- `app/main.py` - Registered Yahoo routers
- `app/mongo_models.py` - Added `yahoo_tokens` field to UserDocument

### Frontend

- `src/components/auth/YahooOAuthCallback.tsx` - OAuth callback handler
- `src/components/auth/LoginScreen.tsx` - Added Yahoo login button
- `src/services/api.ts` - Added Yahoo API methods
- `src/App.tsx` - Added Yahoo callback route

## Troubleshooting

### "Yahoo OAuth not configured" Error

Ensure `YAHOO_CLIENT_ID` and `YAHOO_CLIENT_SECRET` are set in your `.env` file.

### "Invalid redirect URI" Error

Make sure the redirect URI in Yahoo Developer Console exactly matches your configured `YAHOO_REDIRECT_URI`.

### "SSL Certificate Error" in Local Development

When using self-signed certificates:
1. Open `https://127.0.0.1:5173` directly in your browser
2. Accept the security warning / add exception
3. Then try the OAuth flow again

### Token Refresh Failures

If token refresh fails repeatedly, the user may need to re-authorize the application.
