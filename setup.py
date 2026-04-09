import subprocess
from setuptools import setup


def _find_libffi():
    """Locate libffi dynamically so the path isn't hardcoded."""
    try:
        out = subprocess.check_output(
            ["find", "/opt/homebrew", "/opt/anaconda3", "/usr/local",
             "-name", "libffi*.dylib", "-maxdepth", "8"],
            stderr=subprocess.DEVNULL,
        ).decode().splitlines()
        return [out[0]] if out else []
    except Exception:
        return []


APP = ["app.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "timerpro.icns",
    "frameworks": _find_libffi(),
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
