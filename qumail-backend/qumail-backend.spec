# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for QuMail Backend
Bundles FastAPI backend into standalone executable
"""

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

# Collect all backend modules
backend_path = os.path.abspath('.')
app_path = os.path.join(backend_path, 'app')

# Collect all submodules
hiddenimports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'fastapi.routing',
    'pydantic',
    'pydantic_settings',
    'sqlalchemy',
    'cryptography',
    'liboqs',
    'google.oauth2',
    'google.auth',
    'googleapiclient',
    'aiohttp',
    'httpx',
    'multipart',
]

# Collect all app modules
app_modules = []
for root, dirs, files in os.walk(app_path):
    for file in files:
        if file.endswith('.py') and not file.startswith('__'):
            rel_path = os.path.relpath(os.path.join(root, file), backend_path)
            module = rel_path.replace(os.sep, '.')[:-3]
            app_modules.append(module)

hiddenimports.extend(app_modules)

# Data files to include
datas = [
    ('app', 'app'),
    ('client_secrets.json', '.'),
    ('.env', '.'),
]

# Add certificates if they exist
if os.path.exists('../certs'):
    datas.append(('../certs', 'certs'))

a = Analysis(
    ['app/main.py'],
    pathex=[backend_path],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='qumail-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='qumail-backend',
)
