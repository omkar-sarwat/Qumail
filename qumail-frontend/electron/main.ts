import { app, BrowserWindow, ipcMain, shell, dialog, Notification, Menu, Tray, nativeImage } from 'electron'
import { join } from 'node:path'
import { spawn, ChildProcess } from 'child_process'
import axios from 'axios'
import * as http from 'http'

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
let backendProcess: ChildProcess | null = null
let kme1Process: ChildProcess | null = null
let kme2Process: ChildProcess | null = null
let isQuitting = false
let callbackServer: http.Server | null = null

// 🚧 Use ['ENV_NAME'] avoid vite:define plugin - Vite@2.x
const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']
const isDev = !app.isPackaged
const BACKEND_PORT = 8000
const KME1_PORT = 8010
const KME2_PORT = 8020

// Get resource paths
function getResourcePath(relativePath: string): string {
  if (isDev) {
    return join(__dirname, '..', '..', relativePath)
  }
  return join(process.resourcesPath, relativePath)
}

// Python executable path
function getPythonPath(): string {
  if (isDev) {
    return process.platform === 'win32' ? 'python' : 'python3'
  }
  const pythonExe = process.platform === 'win32' ? 'python.exe' : 'python'
  return join(process.resourcesPath, 'python', pythonExe)
}

// Start Python backend server
async function startBackendServer(): Promise<void> {
  return new Promise((resolve, reject) => {
    const backendPath = getResourcePath('qumail-backend')
    const pythonPath = getPythonPath()
    
    console.log('[Backend] Starting FastAPI server...')
    console.log('[Backend] Path:', backendPath)
    console.log('[Backend] Python:', pythonPath)

    const env = {
      ...process.env,
      PYTHONUNBUFFERED: '1',
      QUMAIL_ENV: 'electron',
      BACKEND_PORT: BACKEND_PORT.toString(),
      KME1_URL: `http://localhost:${KME1_PORT}`,
      KME2_URL: `http://localhost:${KME2_PORT}`,
    }

    const args = ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', BACKEND_PORT.toString()]

    backendProcess = spawn(pythonPath, args, {
      cwd: backendPath,
      env,
      shell: true,
    })

    backendProcess.stdout?.on('data', (data) => {
      console.log('[Backend]', data.toString().trim())
    })

    backendProcess.stderr?.on('data', (data) => {
      console.error('[Backend Error]', data.toString().trim())
    })

    backendProcess.on('error', (error) => {
      console.error('[Backend] Failed to start:', error)
      reject(error)
    })

    // Wait for backend to be ready
    const maxRetries = 30
    let retries = 0
    const checkBackend = setInterval(async () => {
      try {
        const response = await axios.get(`http://localhost:${BACKEND_PORT}/health`, { timeout: 2000 })
        if (response.status === 200) {
          clearInterval(checkBackend)
          console.log('[Backend] Server is ready!')
          resolve()
        }
      } catch (error) {
        retries++
        if (retries >= maxRetries) {
          clearInterval(checkBackend)
          reject(new Error('Backend server failed to start within timeout'))
        }
      }
    }, 1000)
  })
}

// Start KME simulators
async function startKMEServers(): Promise<void> {
  return new Promise((resolve) => {
    const kmePath = getResourcePath('next-door-key-simulator')
    const pythonPath = getPythonPath()

    console.log('[KME] Starting quantum key management servers...')

    const kme1Env = {
      ...process.env,
      PYTHONUNBUFFERED: '1',
      KME_PORT: KME1_PORT.toString(),
      KME_ID: 'KME1',
    }

    kme1Process = spawn(pythonPath, ['app.py'], {
      cwd: kmePath,
      env: kme1Env,
      shell: true,
    })

    kme1Process.stdout?.on('data', (data) => {
      console.log('[KME1]', data.toString().trim())
    })

    const kme2Env = {
      ...process.env,
      PYTHONUNBUFFERED: '1',
      KME_PORT: KME2_PORT.toString(),
      KME_ID: 'KME2',
    }

    kme2Process = spawn(pythonPath, ['app.py'], {
      cwd: kmePath,
      env: kme2Env,
      shell: true,
    })

    kme2Process.stdout?.on('data', (data) => {
      console.log('[KME2]', data.toString().trim())
    })

    setTimeout(() => {
      console.log('[KME] Servers started')
      resolve()
    }, 5000)
  })
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
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
      devTools: true,
      backgroundThrottling: false,
      disableBlinkFeatures: 'Auxclick',
    },
    show: false, // Don't show until ready
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
    win?.show()
    win?.focus()
    console.log('[Window] Window shown and focused')
    // Don't auto-open DevTools - user can press F12 if needed
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
    const indexPath = join(process.env.DIST!, 'index.html')
    console.log('[Window] Loading production file:', indexPath)
    win.loadFile(indexPath)
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
  
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
  
  if (kme1Process) {
    kme1Process.kill()
    kme1Process = null
  }
  
  if (kme2Process) {
    kme2Process.kill()
    kme2Process = null
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
    
    if (isDev) {
      // In dev mode, backend and KME run separately
      console.log('[App] Development mode - expecting external backend')
    } else {
      // In production, start embedded backend
      await startKMEServers()
      await startBackendServer()
    }
    
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
    const fullUrl = `http://localhost:${BACKEND_PORT}${url}`
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
    const response = await axios.get(`http://localhost:${BACKEND_PORT}/health`, { timeout: 2000 })
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
