from setuptools import setup

APP = ["app.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "timerpro.icns",
    "frameworks": [],
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
