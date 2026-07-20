# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    [r"D:\game\aetherforge\aetherforge\main.py"],
    pathex=[r"D:\game\aetherforge"],
    binaries=[],
    datas=[
        (r"D:\game\aetherforge\aetherforge\static\index.html", "static"),
    ],
    hiddenimports=[
        "flask", "jinja2", "werkzeug", "markupsafe",
        "click", "itsdangerous",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "torch", "torchvision", "torchaudio", "torchmetrics",
        "triton", "xformers",
        "diffusers", "transformers", "sentencepiece", "tokenizers",
        "accelerate", "safetensors", "regex",
        "numba", "llvmlite",
        "scipy",
        "opencv_python", "cv2",
        "pandas", "matplotlib", "seaborn", "plotly",
        "PyOpenGL", "OpenGL",
        "PIL", "Pillow",
        "numpy",
        "tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6",
        "setuptools._distutils", "pkg_resources",
        "IPython", "jupyter",
        "notebook", "nbformat",
        "pytest", "unittest",
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
    name="AetherForge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
