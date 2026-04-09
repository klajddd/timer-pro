from setuptools import setup

APP = ["app.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "timerpro.icns",
    "frameworks": [
        "/opt/anaconda3/envs/cursor/lib/libffi.8.dylib",
    ],
    "plist": {
        "CFBundleName": "TimerPro",
        "CFBundleDisplayName": "TimerPro",
        "CFBundleIdentifier": "com.timerpro.app",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0",
        "LSUIElement": False,
        "NSHighResolutionCapable": True,
    },
    "packages": ["PyQt6"],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
