# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules
imports = ["sys", "os", "pathlib", "PyQt5", "selenium", "json", "urllib", "re", "undetected_chromedriver"]
seleniumSubs = collect_submodules("selenium")
qtSubs = collect_submodules("PyQt5")
urllibSubs = collect_submodules("urllib")

import shutil



a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('targets.json', '.'), ('styles.qss', '.')],
    hiddenimports=imports+seleniumSubs+qtSubs+urllibSubs,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CouponFinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
shutil.copyfile('README.md', '{0}/README.md'.format(DISTPATH))