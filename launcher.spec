# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for DMP Launcher
#
# Build command:
#   pyinstaller launcher.spec
#
# Or use simple build without spec file:
#   pyinstaller --onefile --windowed --name "DMP Launcher" launcher.py

import os

block_cipher = None

# Get absolute path to project directory
project_dir = os.path.dirname(os.path.abspath(SPEC))

# Check for icon file
icon_file = os.path.join(project_dir, 'static', 'favicon.ico')
if not os.path.exists(icon_file):
    icon_file = None

# Data files to include
datas = []
if icon_file:
    datas.append((icon_file, 'static'))

a = Analysis(
    ['launcher.py'],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=['pystray', 'PIL', 'PIL.Image', 'PIL.ImageDraw'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy Django dependencies not needed for launcher
        'django',
        'numpy',
        'pandas',
        'matplotlib',
        'scipy',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DMP Launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
    version_info={
        'CompanyName': 'DMP',
        'FileDescription': 'DMP Server Launcher',
        'FileVersion': '1.0.0',
        'InternalName': 'DMP Launcher',
        'OriginalFilename': 'DMP Launcher.exe',
        'ProductName': 'DMP - Device Management Platform',
        'ProductVersion': '1.0.0',
    } if os.name == 'nt' else None,
)
