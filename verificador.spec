# verificador.spec
import sys
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = (
    collect_submodules('PyQt5')
    + collect_submodules('requests')
    + collect_submodules('pytz')
)

# Inclui a pasta 'fotos'
datas = [
    ('fotos', 'fotos')
]

block_cipher = None

a = Analysis(
    ['verificador.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='verificador',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,     # ← sem console
    disable_windowed_traceback=False,
    target_arch=None,
    icon=None,
)

# MODO ONEFILE
coll = None