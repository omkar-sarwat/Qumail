# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Next Door Key Simulator (KME)
Bundles KME server into standalone executable
"""

import sys
import os

block_cipher = None

# Collect all KME modules
kme_path = os.path.abspath('.')

hiddenimports = [
    'flask',
    'flask_cors',
    'cryptography',
    'werkzeug',
    'jinja2',
    'click',
    'itsdangerous',
]

datas = [
    ('server', 'server'),
    ('router', 'router'),
    ('network', 'network'),
    ('certs', 'certs'),
    ('keys', 'keys'),
]

a = Analysis(
    ['app.py'],
    pathex=[kme_path],
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
    name='kme-server',
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
    name='kme-server',
)
