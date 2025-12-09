import { app, BrowserWindow, ipcMain, shell, dialog, Notification, Menu, Tray, nativeImage } from 'electron'
import { join } from 'node:path'
import { ChildProcess } from 'child_process'
import axios from 'axios'
import * as http from 'http'
import * as database from './database'

// The built directory structure
//
// ├─┬─┬ dist
// │ │ └── index.html
// │ │
// │ ├─┬ dist-electron
// │ │ ├── main.js
// │ │ └── preload.js
// │
process.env.DIST = join(__dirname, '../dist')
process.env.VITE_PUBLIC = app.isPackaged ? process.env.DIST : join(process.env.DIST, '../public')

let win: BrowserWindow | null = null
let tray: Tray | null = null
let isQuitting = false
let callbackServer: http.Server | null = null
let backendProcess: ChildProcess | null = null

// 🚧 Use ['ENV_NAME'] avoid vite:define plugin - Vite@2.x
const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']
const isDev = !app.isPackaged

// Ignore certificate errors for localhost in development (self-signed certs)
if (isDev) {
  app.commandLine.appendSwitch('ignore-certificate-errors', 'true')
  app.commandLine.appendSwitch('allow-insecure-localhost', 'true')
}

// Backend URL - always use Render backend (no local backend needed)
const BACKEND_URL = 'https://qumail-backend-gwec.onrender.com'

// KME servers are on Render (cloud) - not local
const KME1_URL = 'https://qumail-kme1-brzq.onrender.com'
const KME2_URL = 'https://qumail-kme2-brzq.onrender.com'

// Check if Render backend is available (no local backend needed)
async function checkBackendServer(): Promise<void> {
  console.log('[Backend] Using Render backend:', BACKEND_URL)
  console.log('[Backend] Using KME1:', KME1_URL)
  console.log('[Backend] Using KME2:', KME2_URL)
  
  try {
    const response = await axios.get(`${BACKEND_URL}/health`, { timeout: 10000 })
    if (response.status === 200) {
      console.log('[Backend] Render backend is available!')
    }
  } catch (error) {
    console.log('[Backend] Render backend check failed, but continuing...')
  }
}

// Create system tray
function createTray() {
  try {
    const iconPath = join(process.env.VITE_PUBLIC || join(__dirname, '../public'), 'icon.png')
    const fs = require('fs')
    if (!fs.existsSync(iconPath)) {
      console.log('[Tray] Icon not found, skipping tray creation')
      return
    }
    const icon = nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 })
    
    tray = new Tray(icon)
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show QuMail',
      click: () => win?.show(),
    },
    {
      label: 'New Email',
      click: () => {
        win?.show()
        win?.webContents.send('new-email')
      },
    },
    { type: 'separator' },
    {
      label: 'Settings',
      click: () => {
        win?.show()
        win?.webContents.send('open-settings')
      },
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        isQuitting = true
        app.quit()
      },
    },
  ])

    tray.setToolTip('QuMail Secure Email')
    tray.setContextMenu(contextMenu)
    tray.on('click', () => win?.show())
  } catch (error) {
    console.log('[Tray] Failed to create tray:', error)
  }
}

// Create application menu (DISABLED - frameless modern UI)
function createMenu() {
  // Hide menu bar for modern frameless look
  Menu.setApplicationMenu(null)
}

function createWindow(): void {
  const windowOptions: any = {
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 600,
    frame: false, // Frameless for modern look
    transparent: false,
    title: 'QuMail Secure Email',
    backgroundColor: '#0f172a',
    center: true, // Center window on screen
    autoHideMenuBar: true,
    show: false, // Don't show until ready
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
      devTools: true,
      backgroundThrottling: false,
      disableBlinkFeatures: 'Auxclick',
    },
  }

  // Add icon if it exists
  try {
    const iconPath = join(process.env.VITE_PUBLIC || join(__dirname, '../public'), 'icon.png')
    const fs = require('fs')
    if (fs.existsSync(iconPath)) {
      windowOptions.icon = iconPath
    }
  } catch (e) {
    // Icon not found, continue without it
  }

  console.log('[Window] Creating new BrowserWindow...')
  console.log('[Window] Current window count before creation:', BrowserWindow.getAllWindows().length)
  
  win = new BrowserWindow(windowOptions)
  
  console.log('[Window] BrowserWindow created successfully')
  console.log('[Window] Window ID:', win.id)
  console.log('[Window] Current window count after creation:', BrowserWindow.getAllWindows().length)

  win.once('ready-to-show', () => {
    console.log('[Window] Window ready-to-show event fired')
    win?.maximize() // Start maximized
    win?.show()
    win?.focus()
    console.log('[Window] Window shown maximized and focused')
  })

  win.webContents.on('did-finish-load', () => {
    console.log('[Window] Content finished loading')
    win?.webContents.send('main-process-message', new Date().toLocaleString())
  })

  win.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL) => {
    console.error('[Window] Failed to load:', errorDescription)
    console.error('[Window] Error code:', errorCode)
    console.error('[Window] URL:', validatedURL)
  })

  win.webContents.on('did-start-loading', () => {
    console.log('[Window] Started loading content')
  })

  if (VITE_DEV_SERVER_URL) {
    console.log('[Window] Environment VITE_DEV_SERVER_URL:', VITE_DEV_SERVER_URL)
    console.log('[Window] Loading dev server URL:', VITE_DEV_SERVER_URL)
    win.loadURL(VITE_DEV_SERVER_URL).then(() => {
      console.log('[Window] loadURL completed successfully')
    }).catch((error) => {
      console.error('[Window] loadURL error:', error)
    })
  } else {
    // In production, load from the dist folder relative to __dirname
    const indexPath = join(__dirname, '../dist/index.html')
    console.log('[Window] Loading production file:', indexPath)
    console.log('[Window] __dirname:', __dirname)
    win.loadFile(indexPath).then(() => {
      console.log('[Window] loadFile completed successfully')
    }).catch((error) => {
      console.error('[Window] loadFile error:', error)
    })
  }

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  win.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault()
      win?.hide()
    }
  })
}

// Cleanup on exit
function cleanup() {
  console.log('[Cleanup] Shutting down services...')
  
  // Close database
  database.closeDatabase()
  
  // Kill backend process
  if (backendProcess) {
    console.log('[Cleanup] Stopping backend server...')
    backendProcess.kill()
    backendProcess = null
  }
}

// OAuth callback handling - removed custom protocol, using localhost redirect instead

// App lifecycle
app.commandLine.appendSwitch('disable-gpu')
app.commandLine.appendSwitch('disable-software-rasterizer')
app.commandLine.appendSwitch('disable-gpu-compositing')

app.whenReady().then(async () => {
  try {
    console.log('[App] =================================================')
    console.log('[App] Starting QuMail Secure Email...')
    console.log('[App] Process ID:', process.pid)
    console.log('[App] Is Dev Mode:', isDev)
    console.log('[App] =================================================')
    
    // Initialize local SQLite database (sql.js is async)
    console.log('[App] Initializing local database...')
    await database.initDatabaseAsync()
    console.log('[App] Local database initialized!')
    
    // Ensure we're the only instance
    const gotTheLock = app.requestSingleInstanceLock()
    if (!gotTheLock) {
      console.log('[App] Another instance is already running. Exiting...')
      app.quit()
      return
    }
    
    app.on('second-instance', () => {
      console.log('[App] Second instance detected - focusing main window')
      if (win) {
        if (win.isMinimized()) win.restore()
        win.focus()
      }
    })
    
    // Check Render backend availability (no local backend needed)
    console.log('[App] Using Render backend:', BACKEND_URL)
    console.log('[App] KME servers on Render:', KME1_URL, KME2_URL)
    await checkBackendServer()
    console.log('[App] Backend check complete!')
    
    console.log('[App] Creating main window...')
    createWindow()
    createTray()
    createMenu()
    
    console.log('[App] QuMail is ready!')
  } catch (error) {
    console.error('[App] Failed to start:', error)
    dialog.showErrorBox(
      'Startup Error',
      'Failed to start QuMail backend services. Please check the logs and try again.'
    )
    app.quit()
  }
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
    win = null
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  } else {
    win?.show()
  }
})

app.on('before-quit', () => {
  isQuitting = true
  cleanup()
})

app.on('will-quit', () => {
  cleanup()
})

// IPC Handlers
ipcMain.handle('api-request', async (_event, { method, url, data, headers }) => {
  try {
    const fullUrl = `${BACKEND_URL}${url}`
    const response = await axios({
      method,
      url: fullUrl,
      data,
      headers,
      timeout: 30000,
    })
    return { success: true, data: response.data, status: response.status }
  } catch (error: any) {
    return {
      success: false,
      error: error.message,
      status: error.response?.status || 500,
      data: error.response?.data,
    }
  }
})

ipcMain.handle('get-app-info', () => {
  return {
    version: app.getVersion(),
    name: app.getName(),
    platform: process.platform,
    isDev,
  }
})

ipcMain.handle('show-notification', (_, { title, body, silent = false }) => {
  if (Notification.isSupported()) {
    const notification = new Notification({
      title,
      body,
      silent,
      icon: join(process.env.VITE_PUBLIC!, 'icon.png'),
    })
    
    notification.show()
    return true
  }
  return false
})

ipcMain.handle('show-save-dialog', async (_, options) => {
  if (!win) return { canceled: true }
  
  const result = await dialog.showSaveDialog(win, {
    title: 'Save Email Attachment',
    defaultPath: options.defaultPath || 'download',
    filters: options.filters || [
      { name: 'All Files', extensions: ['*'] }
    ],
    ...options
  })
  
  return result
})

ipcMain.handle('show-open-dialog', async (_, options) => {
  if (!win) return { canceled: true }
  
  const result = await dialog.showOpenDialog(win, {
    title: 'Select Files to Attach',
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'All Files', extensions: ['*'] },
      { name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'gif', 'bmp'] },
      { name: 'Documents', extensions: ['pdf', 'doc', 'docx', 'txt', 'rtf'] },
      { name: 'Archives', extensions: ['zip', 'rar', '7z', 'tar', 'gz'] },
    ],
    ...options
  })
  
  return result
})

ipcMain.handle('read-file', async (_event, filePath) => {
  try {
    const fs = require('fs').promises
    const content = await fs.readFile(filePath, 'utf-8')
    return { success: true, content }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('write-file', async (_event, filePath, content) => {
  try {
    const fs = require('fs').promises
    await fs.writeFile(filePath, content, 'utf-8')
    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('get-backend-status', async () => {
  try {
    const response = await axios.get(`${BACKEND_URL}/health`, { timeout: 5000 })
    return { online: true, data: response.data }
  } catch (error) {
    return { online: false }
  }
})

ipcMain.handle('get-app-version', () => {
  return app.getVersion()
})

ipcMain.handle('minimize-window', () => {
  win?.minimize()
})

ipcMain.handle('maximize-window', () => {
  if (win?.isMaximized()) {
    win.unmaximize()
  } else {
    win?.maximize()
  }
})

ipcMain.handle('close-window', () => {
  win?.close()
})

ipcMain.handle('is-maximized', () => {
  return win?.isMaximized() || false
})

ipcMain.handle('open-external', (_, url) => {
  shell.openExternal(url)
})

ipcMain.handle('start-oauth-flow', async (_, { authUrl, state }) => {
  console.log('[OAuth] Starting browser-based OAuth flow')
  console.log('[OAuth] State:', state)
  
  return new Promise((resolve, reject) => {
    // Use port 5174 to avoid conflict with Vite on 5173
    const PORT = 5174
    
    callbackServer = http.createServer((req, res) => {
      const url = new URL(req.url || '', `http://localhost:${PORT}`)
      
      if (url.pathname === '/auth/callback') {
        const code = url.searchParams.get('code')
        const returnedState = url.searchParams.get('state')
        const error = url.searchParams.get('error')
        
        if (error) {
          res.writeHead(200, { 'Content-Type': 'text/html' })
          res.end(`
            <!DOCTYPE html>
            <html>
            <head>
              <title>QuMail - Authentication Failed</title>
              <style>
                body { font-family: system-ui; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
                .container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); text-align: center; max-width: 400px; }
                .error { color: #dc2626; margin: 20px 0; }
                h1 { color: #1f2937; margin: 0 0 20px 0; }
              </style>
            </head>
            <body>
              <div class="container">
                <h1>❌ Authentication Failed</h1>
                <p class="error">${error}</p>
                <p>You can close this window and try again.</p>
              </div>
            </body>
            </html>
          `)
          
          // Close server and reject
          callbackServer?.close()
          callbackServer = null
          reject(new Error(error))
          return
        }
        
        if (code && returnedState === state) {
          // Success! Send beautiful success page
          res.writeHead(200, { 'Content-Type': 'text/html' })
          res.end(`
            <!DOCTYPE html>
            <html>
            <head>
              <title>QuMail - Authentication Successful</title>
              <style>
                body { font-family: system-ui; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
                .container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); text-align: center; max-width: 400px; }
                .success { color: #059669; font-size: 64px; margin: 20px 0; }
                h1 { color: #1f2937; margin: 0 0 20px 0; }
                p { color: #6b7280; }
                @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
                .container { animation: fadeIn 0.5s ease-out; }
              </style>
            </head>
            <body>
              <div class="container">
                <div class="success">✅</div>
                <h1>Authentication Successful!</h1>
                <p>You can now close this window and return to QuMail.</p>
                <p style="margin-top: 20px; font-size: 14px; color: #9ca3af;">This window will close automatically in 3 seconds...</p>
              </div>
              <script>
                setTimeout(() => window.close(), 3000);
              </script>
            </body>
            </html>
          `)
          
          console.log('[OAuth] Callback received successfully')
          console.log('[OAuth] Code:', code.substring(0, 10) + '...')
          
          // Close server and resolve
          callbackServer?.close()
          callbackServer = null
          resolve({ code, state: returnedState })
        } else {
          res.writeHead(400, { 'Content-Type': 'text/html' })
          res.end(`
            <!DOCTYPE html>
            <html>
            <head>
              <title>QuMail - Invalid Request</title>
              <style>
                body { font-family: system-ui; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
                .container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); text-align: center; max-width: 400px; }
              </style>
            </head>
            <body>
              <div class="container">
                <h1>⚠️ Invalid Request</h1>
                <p>Missing or invalid OAuth parameters.</p>
                <p>You can close this window and try again.</p>
              </div>
            </body>
            </html>
          `)
          
          callbackServer?.close()
          callbackServer = null
          reject(new Error('Invalid OAuth callback parameters'))
        }
      } else {
        res.writeHead(404)
        res.end('Not Found')
      }
    })
    
    callbackServer.listen(PORT, () => {
      console.log(`[OAuth] Callback server listening on http://localhost:${PORT}`)
      console.log('[OAuth] Opening browser with URL:', authUrl.substring(0, 150) + '...')
      
      // Open in system browser - authUrl already has correct redirect_uri from backend
      shell.openExternal(authUrl)
    })
    
    callbackServer.on('error', (error) => {
      console.error('[OAuth] Callback server error:', error)
      callbackServer?.close()
      callbackServer = null
      reject(error)
    })
    
    // Timeout after 5 minutes
    setTimeout(() => {
      if (callbackServer) {
        console.log('[OAuth] Timeout - closing callback server')
        callbackServer.close()
        callbackServer = null
        reject(new Error('OAuth timeout - please try again'))
      }
    }, 5 * 60 * 1000)
  })
})

// ==================== DATABASE IPC HANDLERS ====================

// Get emails from local database
ipcMain.handle('db-get-emails', (_event, folder: string, limit?: number, offset?: number) => {
  try {
    return { success: true, data: database.getEmails(folder, limit || 100, offset || 0) }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Get email by ID
ipcMain.handle('db-get-email', (_event, id: string) => {
  try {
    return { success: true, data: database.getEmailById(id) }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Get email by flow ID
ipcMain.handle('db-get-email-by-flow-id', (_event, flowId: string) => {
  try {
    return { success: true, data: database.getEmailByFlowId(flowId) }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Save email to local database
ipcMain.handle('db-save-email', (_event, email: any) => {
  try {
    database.saveEmail(email)
    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Save multiple emails
ipcMain.handle('db-save-emails', (_event, emails: any[]) => {
  try {
    database.saveEmails(emails)
    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Update email status
ipcMain.handle('db-update-email', (_event, id: string, updates: any) => {
  try {
    database.updateEmailStatus(id, updates)
    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Delete email
ipcMain.handle('db-delete-email', (_event, id: string) => {
  try {
    database.deleteEmail(id)
    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Get email counts
ipcMain.handle('db-get-email-counts', () => {
  try {
    return { success: true, data: database.getEmailCounts() }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Get unread counts
ipcMain.handle('db-get-unread-counts', () => {
  try {
    return { success: true, data: database.getUnreadCounts() }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Search emails
ipcMain.handle('db-search-emails', (_event, query: string, folder?: string) => {
  try {
    return { success: true, data: database.searchEmails(query, folder) }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Add to sync queue
ipcMain.handle('db-add-to-sync-queue', (_event, operation: string, emailId: string, data?: any) => {
  try {
    database.addToSyncQueue(operation as any, emailId, data)
    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Get pending sync items
ipcMain.handle('db-get-pending-sync', (_event, limit?: number) => {
  try {
    return { success: true, data: database.getPendingSyncItems(limit) }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Complete sync item
ipcMain.handle('db-complete-sync-item', (_event, id: number) => {
  try {
    database.completeSyncItem(id)
    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Fail sync item
ipcMain.handle('db-fail-sync-item', (_event, id: number, error: string) => {
  try {
    database.failSyncItem(id, error)
    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Get sync queue count
ipcMain.handle('db-get-sync-queue-count', () => {
  try {
    return { success: true, data: database.getSyncQueueCount() }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Get cached decryption
ipcMain.handle('db-get-cached-decryption', (_event, emailId: string) => {
  try {
    return { success: true, data: database.getCachedDecryption(emailId) }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Cache decrypted content
ipcMain.handle('db-cache-decryption', (_event, cache: any) => {
  try {
    database.cacheDecryptedContent(cache)
    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Get/set settings
ipcMain.handle('db-get-setting', (_event, key: string) => {
  try {
    return { success: true, data: database.getSetting(key) }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('db-set-setting', (_event, key: string, value: string) => {
  try {
    database.setSetting(key, value)
    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Sync metadata
ipcMain.handle('db-get-last-sync', () => {
  try {
    return { success: true, data: database.getLastSyncTime() }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('db-set-last-sync', (_event, time: string) => {
  try {
    database.setLastSyncTime(time)
    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Get database stats
ipcMain.handle('db-get-stats', () => {
  try {
    return { success: true, data: database.getDatabaseStats() }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Clear all data (for logout)
ipcMain.handle('db-clear-all', () => {
  try {
    database.clearAllData()
    return { success: true }
  } catch (error: any) {
    return { success: false, error: error.message }
  }
})

// Security: Prevent new window creation
app.on('web-contents-created', (_, contents) => {
  contents.setWindowOpenHandler(() => {
    return { action: 'deny' }
  })
})

// Handle unhandled errors
process.on('uncaughtException', (error) => {
  console.error('[Uncaught Exception]', error)
})

process.on('unhandledRejection', (error) => {
  console.error('[Unhandled Rejection]', error)
})
