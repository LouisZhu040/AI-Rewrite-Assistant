# build.spec
# 用法：pyinstaller build.spec

block_cipher = None

a = Analysis(
    ['ai_rewrite_tool.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pyperclip',
        'keyboard',
        'pystray',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'winreg',
        'requests',
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
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
    name='AI改写助手',           # exe 文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                    # 压缩体积（需安装 UPX）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,               # 不显示终端窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico',           # 取消注释并放一个 icon.ico 文件可自定义图标
    uac_admin=True,              # 请求管理员权限（keyboard 库需要）
)