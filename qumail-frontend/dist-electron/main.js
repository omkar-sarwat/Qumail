"use strict";
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
var electron_1 = require("electron");
var node_path_1 = require("node:path");
var axios_1 = __importDefault(require("axios"));
var http = __importStar(require("http"));
var database = __importStar(require("./database"));
// The built directory structure
//
// ├─┬─┬ dist
// │ │ └── index.html
// │ │
// │ ├─┬ dist-electron
// │ │ ├── main.js
// │ │ └── preload.js
// │
process.env.DIST = (0, node_path_1.join)(__dirname, '../dist');
process.env.VITE_PUBLIC = electron_1.app.isPackaged ? process.env.DIST : (0, node_path_1.join)(process.env.DIST, '../public');
var win = null;
var tray = null;
var isQuitting = false;
var callbackServer = null;
var backendProcess = null;
// 🚧 Use ['ENV_NAME'] avoid vite:define plugin - Vite@2.x
var VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL'];
var isDev = !electron_1.app.isPackaged;
// Ignore certificate errors for localhost in development (self-signed certs)
if (isDev) {
    electron_1.app.commandLine.appendSwitch('ignore-certificate-errors', 'true');
    electron_1.app.commandLine.appendSwitch('allow-insecure-localhost', 'true');
}
// Backend URL - use localhost for dev, Render for production
var BACKEND_URL = isDev ? 'http://localhost:8000' : 'https://qumail-backend-gwec.onrender.com';
// KME servers are on Render (cloud) - not local
var KME1_URL = 'https://qumail-kme1-brzq.onrender.com';
var KME2_URL = 'https://qumail-kme2-brzq.onrender.com';
// Check if Render backend is available (no local backend needed)
function checkBackendServer() {
    return __awaiter(this, void 0, void 0, function () {
        var response, error_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    console.log('[Backend] Using Render backend:', BACKEND_URL);
                    console.log('[Backend] Using KME1:', KME1_URL);
                    console.log('[Backend] Using KME2:', KME2_URL);
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 3, , 4]);
                    return [4 /*yield*/, axios_1.default.get("".concat(BACKEND_URL, "/health"), { timeout: 10000 })];
                case 2:
                    response = _a.sent();
                    if (response.status === 200) {
                        console.log('[Backend] Render backend is available!');
                    }
                    return [3 /*break*/, 4];
                case 3:
                    error_1 = _a.sent();
                    console.log('[Backend] Render backend check failed, but continuing...');
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    });
}
// Create system tray
function createTray() {
    try {
        var iconPath = (0, node_path_1.join)(process.env.VITE_PUBLIC || (0, node_path_1.join)(__dirname, '../public'), 'icon.png');
        var fs = require('fs');
        if (!fs.existsSync(iconPath)) {
            console.log('[Tray] Icon not found, skipping tray creation');
            return;
        }
        var icon = electron_1.nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 });
        tray = new electron_1.Tray(icon);
        var contextMenu = electron_1.Menu.buildFromTemplate([
            {
                label: 'Show QuMail',
                click: function () { return win === null || win === void 0 ? void 0 : win.show(); },
            },
            {
                label: 'New Email',
                click: function () {
                    win === null || win === void 0 ? void 0 : win.show();
                    win === null || win === void 0 ? void 0 : win.webContents.send('new-email');
                },
            },
            { type: 'separator' },
            {
                label: 'Settings',
                click: function () {
                    win === null || win === void 0 ? void 0 : win.show();
                    win === null || win === void 0 ? void 0 : win.webContents.send('open-settings');
                },
            },
            { type: 'separator' },
            {
                label: 'Quit',
                click: function () {
                    isQuitting = true;
                    electron_1.app.quit();
                },
            },
        ]);
        tray.setToolTip('QuMail Secure Email');
        tray.setContextMenu(contextMenu);
        tray.on('click', function () { return win === null || win === void 0 ? void 0 : win.show(); });
    }
    catch (error) {
        console.log('[Tray] Failed to create tray:', error);
    }
}
// Create application menu (DISABLED - frameless modern UI)
function createMenu() {
    // Hide menu bar for modern frameless look
    electron_1.Menu.setApplicationMenu(null);
}
function createWindow() {
    var windowOptions = {
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
            preload: (0, node_path_1.join)(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
            webSecurity: true,
            devTools: true,
            backgroundThrottling: false,
            disableBlinkFeatures: 'Auxclick',
        },
    };
    // Add icon if it exists
    try {
        var iconPath = (0, node_path_1.join)(process.env.VITE_PUBLIC || (0, node_path_1.join)(__dirname, '../public'), 'icon.png');
        var fs = require('fs');
        if (fs.existsSync(iconPath)) {
            windowOptions.icon = iconPath;
        }
    }
    catch (e) {
        // Icon not found, continue without it
    }
    console.log('[Window] Creating new BrowserWindow...');
    console.log('[Window] Current window count before creation:', electron_1.BrowserWindow.getAllWindows().length);
    win = new electron_1.BrowserWindow(windowOptions);
    console.log('[Window] BrowserWindow created successfully');
    console.log('[Window] Window ID:', win.id);
    console.log('[Window] Current window count after creation:', electron_1.BrowserWindow.getAllWindows().length);
    win.once('ready-to-show', function () {
        console.log('[Window] Window ready-to-show event fired');
        win === null || win === void 0 ? void 0 : win.maximize(); // Start maximized
        win === null || win === void 0 ? void 0 : win.show();
        win === null || win === void 0 ? void 0 : win.focus();
        console.log('[Window] Window shown maximized and focused');
    });
    win.webContents.on('did-finish-load', function () {
        console.log('[Window] Content finished loading');
        win === null || win === void 0 ? void 0 : win.webContents.send('main-process-message', new Date().toLocaleString());
    });
    win.webContents.on('did-fail-load', function (_event, errorCode, errorDescription, validatedURL) {
        console.error('[Window] Failed to load:', errorDescription);
        console.error('[Window] Error code:', errorCode);
        console.error('[Window] URL:', validatedURL);
    });
    win.webContents.on('did-start-loading', function () {
        console.log('[Window] Started loading content');
    });
    if (VITE_DEV_SERVER_URL) {
        console.log('[Window] Environment VITE_DEV_SERVER_URL:', VITE_DEV_SERVER_URL);
        console.log('[Window] Loading dev server URL:', VITE_DEV_SERVER_URL);
        win.loadURL(VITE_DEV_SERVER_URL).then(function () {
            console.log('[Window] loadURL completed successfully');
        }).catch(function (error) {
            console.error('[Window] loadURL error:', error);
        });
    }
    else {
        // In production, load from the dist folder relative to __dirname
        var indexPath = (0, node_path_1.join)(__dirname, '../dist/index.html');
        console.log('[Window] Loading production file:', indexPath);
        console.log('[Window] __dirname:', __dirname);
        win.loadFile(indexPath).then(function () {
            console.log('[Window] loadFile completed successfully');
        }).catch(function (error) {
            console.error('[Window] loadFile error:', error);
        });
    }
    win.webContents.setWindowOpenHandler(function (_a) {
        var url = _a.url;
        electron_1.shell.openExternal(url);
        return { action: 'deny' };
    });
    win.on('close', function (event) {
        if (!isQuitting) {
            event.preventDefault();
            win === null || win === void 0 ? void 0 : win.hide();
        }
    });
}
// Cleanup on exit
function cleanup() {
    console.log('[Cleanup] Shutting down services...');
    // Close database
    database.closeDatabase();
    // Kill backend process
    if (backendProcess) {
        console.log('[Cleanup] Stopping backend server...');
        backendProcess.kill();
        backendProcess = null;
    }
}
// OAuth callback handling - removed custom protocol, using localhost redirect instead
// App lifecycle
electron_1.app.commandLine.appendSwitch('disable-gpu');
electron_1.app.commandLine.appendSwitch('disable-software-rasterizer');
electron_1.app.commandLine.appendSwitch('disable-gpu-compositing');
electron_1.app.whenReady().then(function () { return __awaiter(void 0, void 0, void 0, function () {
    var gotTheLock, error_2;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 3, , 4]);
                console.log('[App] =================================================');
                console.log('[App] Starting QuMail Secure Email...');
                console.log('[App] Process ID:', process.pid);
                console.log('[App] Is Dev Mode:', isDev);
                console.log('[App] =================================================');
                // Initialize local SQLite database (sql.js is async)
                console.log('[App] Initializing local database...');
                return [4 /*yield*/, database.initDatabaseAsync()];
            case 1:
                _a.sent();
                console.log('[App] Local database initialized!');
                gotTheLock = electron_1.app.requestSingleInstanceLock();
                if (!gotTheLock) {
                    console.log('[App] Another instance is already running. Exiting...');
                    electron_1.app.quit();
                    return [2 /*return*/];
                }
                electron_1.app.on('second-instance', function () {
                    console.log('[App] Second instance detected - focusing main window');
                    if (win) {
                        if (win.isMinimized())
                            win.restore();
                        win.focus();
                    }
                });
                // Check Render backend availability (no local backend needed)
                console.log('[App] Using Render backend:', BACKEND_URL);
                console.log('[App] KME servers on Render:', KME1_URL, KME2_URL);
                return [4 /*yield*/, checkBackendServer()];
            case 2:
                _a.sent();
                console.log('[App] Backend check complete!');
                console.log('[App] Creating main window...');
                createWindow();
                createTray();
                createMenu();
                console.log('[App] QuMail is ready!');
                return [3 /*break*/, 4];
            case 3:
                error_2 = _a.sent();
                console.error('[App] Failed to start:', error_2);
                electron_1.dialog.showErrorBox('Startup Error', 'Failed to start QuMail backend services. Please check the logs and try again.');
                electron_1.app.quit();
                return [3 /*break*/, 4];
            case 4: return [2 /*return*/];
        }
    });
}); });
electron_1.app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        electron_1.app.quit();
        win = null;
    }
});
electron_1.app.on('activate', function () {
    if (electron_1.BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
    else {
        win === null || win === void 0 ? void 0 : win.show();
    }
});
electron_1.app.on('before-quit', function () {
    isQuitting = true;
    cleanup();
});
electron_1.app.on('will-quit', function () {
    cleanup();
});
// IPC Handlers
electron_1.ipcMain.handle('api-request', function (_event_1, _a) { return __awaiter(void 0, [_event_1, _a], void 0, function (_event, _b) {
    var fullUrl, response, error_3;
    var _c, _d;
    var method = _b.method, url = _b.url, data = _b.data, headers = _b.headers;
    return __generator(this, function (_e) {
        switch (_e.label) {
            case 0:
                _e.trys.push([0, 2, , 3]);
                fullUrl = "".concat(BACKEND_URL).concat(url);
                return [4 /*yield*/, (0, axios_1.default)({
                        method: method,
                        url: fullUrl,
                        data: data,
                        headers: headers,
                        timeout: 30000,
                    })];
            case 1:
                response = _e.sent();
                return [2 /*return*/, { success: true, data: response.data, status: response.status }];
            case 2:
                error_3 = _e.sent();
                return [2 /*return*/, {
                        success: false,
                        error: error_3.message,
                        status: ((_c = error_3.response) === null || _c === void 0 ? void 0 : _c.status) || 500,
                        data: (_d = error_3.response) === null || _d === void 0 ? void 0 : _d.data,
                    }];
            case 3: return [2 /*return*/];
        }
    });
}); });
electron_1.ipcMain.handle('get-app-info', function () {
    return {
        version: electron_1.app.getVersion(),
        name: electron_1.app.getName(),
        platform: process.platform,
        isDev: isDev,
    };
});
electron_1.ipcMain.handle('show-notification', function (_, _a) {
    var title = _a.title, body = _a.body, _b = _a.silent, silent = _b === void 0 ? false : _b;
    if (electron_1.Notification.isSupported()) {
        var notification = new electron_1.Notification({
            title: title,
            body: body,
            silent: silent,
            icon: (0, node_path_1.join)(process.env.VITE_PUBLIC, 'icon.png'),
        });
        notification.show();
        return true;
    }
    return false;
});
electron_1.ipcMain.handle('show-save-dialog', function (_, options) { return __awaiter(void 0, void 0, void 0, function () {
    var result;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                if (!win)
                    return [2 /*return*/, { canceled: true }];
                return [4 /*yield*/, electron_1.dialog.showSaveDialog(win, __assign({ title: 'Save Email Attachment', defaultPath: options.defaultPath || 'download', filters: options.filters || [
                            { name: 'All Files', extensions: ['*'] }
                        ] }, options))];
            case 1:
                result = _a.sent();
                return [2 /*return*/, result];
        }
    });
}); });
electron_1.ipcMain.handle('show-open-dialog', function (_, options) { return __awaiter(void 0, void 0, void 0, function () {
    var result;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                if (!win)
                    return [2 /*return*/, { canceled: true }];
                return [4 /*yield*/, electron_1.dialog.showOpenDialog(win, __assign({ title: 'Select Files to Attach', properties: ['openFile', 'multiSelections'], filters: [
                            { name: 'All Files', extensions: ['*'] },
                            { name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'gif', 'bmp'] },
                            { name: 'Documents', extensions: ['pdf', 'doc', 'docx', 'txt', 'rtf'] },
                            { name: 'Archives', extensions: ['zip', 'rar', '7z', 'tar', 'gz'] },
                        ] }, options))];
            case 1:
                result = _a.sent();
                return [2 /*return*/, result];
        }
    });
}); });
electron_1.ipcMain.handle('read-file', function (_event, filePath) { return __awaiter(void 0, void 0, void 0, function () {
    var fs, content, error_4;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 2, , 3]);
                fs = require('fs').promises;
                return [4 /*yield*/, fs.readFile(filePath, 'utf-8')];
            case 1:
                content = _a.sent();
                return [2 /*return*/, { success: true, content: content }];
            case 2:
                error_4 = _a.sent();
                return [2 /*return*/, { success: false, error: error_4.message }];
            case 3: return [2 /*return*/];
        }
    });
}); });
electron_1.ipcMain.handle('write-file', function (_event, filePath, content) { return __awaiter(void 0, void 0, void 0, function () {
    var fs, error_5;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 2, , 3]);
                fs = require('fs').promises;
                return [4 /*yield*/, fs.writeFile(filePath, content, 'utf-8')];
            case 1:
                _a.sent();
                return [2 /*return*/, { success: true }];
            case 2:
                error_5 = _a.sent();
                return [2 /*return*/, { success: false, error: error_5.message }];
            case 3: return [2 /*return*/];
        }
    });
}); });
electron_1.ipcMain.handle('get-backend-status', function () { return __awaiter(void 0, void 0, void 0, function () {
    var response, error_6;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 2, , 3]);
                return [4 /*yield*/, axios_1.default.get("".concat(BACKEND_URL, "/health"), { timeout: 5000 })];
            case 1:
                response = _a.sent();
                return [2 /*return*/, { online: true, data: response.data }];
            case 2:
                error_6 = _a.sent();
                return [2 /*return*/, { online: false }];
            case 3: return [2 /*return*/];
        }
    });
}); });
electron_1.ipcMain.handle('get-app-version', function () {
    return electron_1.app.getVersion();
});
electron_1.ipcMain.handle('minimize-window', function () {
    win === null || win === void 0 ? void 0 : win.minimize();
});
electron_1.ipcMain.handle('maximize-window', function () {
    if (win === null || win === void 0 ? void 0 : win.isMaximized()) {
        win.unmaximize();
    }
    else {
        win === null || win === void 0 ? void 0 : win.maximize();
    }
});
electron_1.ipcMain.handle('close-window', function () {
    win === null || win === void 0 ? void 0 : win.close();
});
electron_1.ipcMain.handle('is-maximized', function () {
    return (win === null || win === void 0 ? void 0 : win.isMaximized()) || false;
});
electron_1.ipcMain.handle('open-external', function (_, url) {
    electron_1.shell.openExternal(url);
});
electron_1.ipcMain.handle('start-oauth-flow', function (_1, _a) { return __awaiter(void 0, [_1, _a], void 0, function (_, _b) {
    var authUrl = _b.authUrl, state = _b.state;
    return __generator(this, function (_c) {
        console.log('[OAuth] Starting browser-based OAuth flow');
        console.log('[OAuth] State:', state);
        return [2 /*return*/, new Promise(function (resolve, reject) {
                // Use port 5174 to avoid conflict with Vite on 5173
                var PORT = 5174;
                callbackServer = http.createServer(function (req, res) {
                    var url = new URL(req.url || '', "http://localhost:".concat(PORT));
                    if (url.pathname === '/auth/callback') {
                        var code = url.searchParams.get('code');
                        var returnedState = url.searchParams.get('state');
                        var error = url.searchParams.get('error');
                        if (error) {
                            res.writeHead(200, { 'Content-Type': 'text/html' });
                            res.end("\n            <!DOCTYPE html>\n            <html>\n            <head>\n              <title>QuMail - Authentication Failed</title>\n              <style>\n                body { font-family: system-ui; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }\n                .container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); text-align: center; max-width: 400px; }\n                .error { color: #dc2626; margin: 20px 0; }\n                h1 { color: #1f2937; margin: 0 0 20px 0; }\n              </style>\n            </head>\n            <body>\n              <div class=\"container\">\n                <h1>\u274C Authentication Failed</h1>\n                <p class=\"error\">".concat(error, "</p>\n                <p>You can close this window and try again.</p>\n              </div>\n            </body>\n            </html>\n          "));
                            // Close server and reject
                            callbackServer === null || callbackServer === void 0 ? void 0 : callbackServer.close();
                            callbackServer = null;
                            reject(new Error(error));
                            return;
                        }
                        if (code && returnedState === state) {
                            // Success! Send beautiful success page
                            res.writeHead(200, { 'Content-Type': 'text/html' });
                            res.end("\n            <!DOCTYPE html>\n            <html>\n            <head>\n              <title>QuMail - Authentication Successful</title>\n              <style>\n                body { font-family: system-ui; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }\n                .container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); text-align: center; max-width: 400px; }\n                .success { color: #059669; font-size: 64px; margin: 20px 0; }\n                h1 { color: #1f2937; margin: 0 0 20px 0; }\n                p { color: #6b7280; }\n                @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }\n                .container { animation: fadeIn 0.5s ease-out; }\n              </style>\n            </head>\n            <body>\n              <div class=\"container\">\n                <div class=\"success\">\u2705</div>\n                <h1>Authentication Successful!</h1>\n                <p>You can now close this window and return to QuMail.</p>\n                <p style=\"margin-top: 20px; font-size: 14px; color: #9ca3af;\">This window will close automatically in 3 seconds...</p>\n              </div>\n              <script>\n                setTimeout(() => window.close(), 3000);\n              </script>\n            </body>\n            </html>\n          ");
                            console.log('[OAuth] Callback received successfully');
                            console.log('[OAuth] Code:', code.substring(0, 10) + '...');
                            // Close server and resolve
                            callbackServer === null || callbackServer === void 0 ? void 0 : callbackServer.close();
                            callbackServer = null;
                            resolve({ code: code, state: returnedState });
                        }
                        else {
                            res.writeHead(400, { 'Content-Type': 'text/html' });
                            res.end("\n            <!DOCTYPE html>\n            <html>\n            <head>\n              <title>QuMail - Invalid Request</title>\n              <style>\n                body { font-family: system-ui; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }\n                .container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); text-align: center; max-width: 400px; }\n              </style>\n            </head>\n            <body>\n              <div class=\"container\">\n                <h1>\u26A0\uFE0F Invalid Request</h1>\n                <p>Missing or invalid OAuth parameters.</p>\n                <p>You can close this window and try again.</p>\n              </div>\n            </body>\n            </html>\n          ");
                            callbackServer === null || callbackServer === void 0 ? void 0 : callbackServer.close();
                            callbackServer = null;
                            reject(new Error('Invalid OAuth callback parameters'));
                        }
                    }
                    else {
                        res.writeHead(404);
                        res.end('Not Found');
                    }
                });
                callbackServer.listen(PORT, function () {
                    console.log("[OAuth] Callback server listening on http://localhost:".concat(PORT));
                    console.log('[OAuth] Opening browser with URL:', authUrl.substring(0, 150) + '...');
                    // Open in system browser - authUrl already has correct redirect_uri from backend
                    electron_1.shell.openExternal(authUrl);
                });
                callbackServer.on('error', function (error) {
                    console.error('[OAuth] Callback server error:', error);
                    callbackServer === null || callbackServer === void 0 ? void 0 : callbackServer.close();
                    callbackServer = null;
                    reject(error);
                });
                // Timeout after 5 minutes
                setTimeout(function () {
                    if (callbackServer) {
                        console.log('[OAuth] Timeout - closing callback server');
                        callbackServer.close();
                        callbackServer = null;
                        reject(new Error('OAuth timeout - please try again'));
                    }
                }, 5 * 60 * 1000);
            })];
    });
}); });
// ==================== DATABASE IPC HANDLERS ====================
// Get emails from local database
electron_1.ipcMain.handle('db-get-emails', function (_event, folder, limit, offset) {
    try {
        return { success: true, data: database.getEmails(folder, limit || 100, offset || 0) };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Get email by ID
electron_1.ipcMain.handle('db-get-email', function (_event, id) {
    try {
        return { success: true, data: database.getEmailById(id) };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Get email by flow ID
electron_1.ipcMain.handle('db-get-email-by-flow-id', function (_event, flowId) {
    try {
        return { success: true, data: database.getEmailByFlowId(flowId) };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Save email to local database
electron_1.ipcMain.handle('db-save-email', function (_event, email) {
    try {
        database.saveEmail(email);
        return { success: true };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Save multiple emails
electron_1.ipcMain.handle('db-save-emails', function (_event, emails) {
    try {
        database.saveEmails(emails);
        return { success: true };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Update email status
electron_1.ipcMain.handle('db-update-email', function (_event, id, updates) {
    try {
        database.updateEmailStatus(id, updates);
        return { success: true };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Delete email
electron_1.ipcMain.handle('db-delete-email', function (_event, id) {
    try {
        database.deleteEmail(id);
        return { success: true };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Get email counts
electron_1.ipcMain.handle('db-get-email-counts', function () {
    try {
        return { success: true, data: database.getEmailCounts() };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Get unread counts
electron_1.ipcMain.handle('db-get-unread-counts', function () {
    try {
        return { success: true, data: database.getUnreadCounts() };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Search emails
electron_1.ipcMain.handle('db-search-emails', function (_event, query, folder) {
    try {
        return { success: true, data: database.searchEmails(query, folder) };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Add to sync queue
electron_1.ipcMain.handle('db-add-to-sync-queue', function (_event, operation, emailId, data) {
    try {
        database.addToSyncQueue(operation, emailId, data);
        return { success: true };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Get pending sync items
electron_1.ipcMain.handle('db-get-pending-sync', function (_event, limit) {
    try {
        return { success: true, data: database.getPendingSyncItems(limit) };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Complete sync item
electron_1.ipcMain.handle('db-complete-sync-item', function (_event, id) {
    try {
        database.completeSyncItem(id);
        return { success: true };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Fail sync item
electron_1.ipcMain.handle('db-fail-sync-item', function (_event, id, error) {
    try {
        database.failSyncItem(id, error);
        return { success: true };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Get sync queue count
electron_1.ipcMain.handle('db-get-sync-queue-count', function () {
    try {
        return { success: true, data: database.getSyncQueueCount() };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Get cached decryption
electron_1.ipcMain.handle('db-get-cached-decryption', function (_event, emailId) {
    try {
        return { success: true, data: database.getCachedDecryption(emailId) };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Cache decrypted content
electron_1.ipcMain.handle('db-cache-decryption', function (_event, cache) {
    try {
        database.cacheDecryptedContent(cache);
        return { success: true };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Get/set settings
electron_1.ipcMain.handle('db-get-setting', function (_event, key) {
    try {
        return { success: true, data: database.getSetting(key) };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
electron_1.ipcMain.handle('db-set-setting', function (_event, key, value) {
    try {
        database.setSetting(key, value);
        return { success: true };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Sync metadata
electron_1.ipcMain.handle('db-get-last-sync', function () {
    try {
        return { success: true, data: database.getLastSyncTime() };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
electron_1.ipcMain.handle('db-set-last-sync', function (_event, time) {
    try {
        database.setLastSyncTime(time);
        return { success: true };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Get database stats
electron_1.ipcMain.handle('db-get-stats', function () {
    try {
        return { success: true, data: database.getDatabaseStats() };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Clear all data (for logout)
electron_1.ipcMain.handle('db-clear-all', function () {
    try {
        database.clearAllData();
        return { success: true };
    }
    catch (error) {
        return { success: false, error: error.message };
    }
});
// Security: Prevent new window creation
electron_1.app.on('web-contents-created', function (_, contents) {
    contents.setWindowOpenHandler(function () {
        return { action: 'deny' };
    });
});
// Handle unhandled errors
process.on('uncaughtException', function (error) {
    console.error('[Uncaught Exception]', error);
});
process.on('unhandledRejection', function (error) {
    console.error('[Unhandled Rejection]', error);
});
