# QuMail Electron Desktop Client

Cross-platform Electron application for sending and decrypting quantum-secured emails via the QuMail cloud backend.

## Prerequisites

- Node.js 18+
- npm 9+
- Render-hosted backend/KMEs/Redis per project instructions

## Environment Variables

Create a `.env` (or set environment variables) with:

- `QUMAIL_API_BASE_URL`: e.g. `https://qumail-backend.onrender.com/api/v1`
- `QUMAIL_OAUTH_REDIRECT`: `http://localhost:3000/auth/callback` or your custom protocol
- `QUMAIL_STORE_KEY`: optional symmetric key for encrypting electron-store config

### Switching between Local & Cloud Backends

The runtime reads configuration in the following priority order:

1. Explicit environment variables (`QUMAIL_API_BASE_URL`, `QUMAIL_OAUTH_REDIRECT`).
2. `config/config.production.js` overrides (committed for cloud builds).
3. Local defaults (`http://localhost:8000/api/v1`, `http://localhost:3000/auth/callback`).

To target Render in production builds, edit `config.production.js`:

```js
module.exports = {
	apiBaseUrl: 'https://qumail-backend.onrender.com/api/v1',
	oauthRedirect: 'qumail://auth/callback'
};
```

Delete or rename the file to fall back to local development values.

## Install Dependencies

```bash
cd qumail-electron
npm install
```

## Local Development

```bash
npm run dev
```

This launches the Vite renderer dev server and Electron in parallel. Renderer hot-reloads while Electron reloads the window.

## Build Installers

```bash
# Build renderer bundle + all installers
npm run build

# Platform-specific packages
npm run build:win
npm run build:mac
npm run build:linux
```

Installers are emitted under `build/`.

## Project Structure

```
qumail-electron/
├── electron.js          # Electron main process
├── preload.js           # Secure bridge to renderer
├── src/
│   ├── main/            # Desktop services
│   │   ├── api.js       # REST integration with backend
│   │   ├── oauth.js     # Google OAuth helper
│   │   └── storage.js   # Electron-store session cache
│   └── renderer/        # React UI (Vite)
│       ├── App.jsx      # Dashboard shell
│       ├── components/  # Login, Inbox, Compose, Decrypt
│       └── styles.css
├── dist/renderer        # Vite build output (generated)
├── build/               # Electron-builder artifacts (generated)
└── package.json         # Scripts + dependencies
```

## Next Steps

1. Configure backend Render URLs in `QUMAIL_API_BASE_URL`.
2. Run `npm run dev` and sign in with Google; session stored via `electron-store` per device.
3. Use `npm run build:<platform>` to generate installers for distribution.
