"""Build on the target OS. Developer-only; distributed apps include Python/Tk."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deps", type=Path, help="Optional pip --target folder")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "dist-desktop")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    out = args.output.resolve()
    if sys.platform not in {"win32", "darwin"}:
        raise SystemExit("Build Windows on Windows and macOS on macOS.")
    if args.deps:
        deps = str(args.deps.resolve())
        sys.path.insert(0, deps)
        os.environ["PYTHONPATH"] = deps
    # Keep packager caches and build intermediates inside the task directory.
    os.environ["PYINSTALLER_CONFIG_DIR"] = str(out / "cache")
    import PyInstaller.__main__
    from PIL import Image, ImageDraw
    out.mkdir(parents=True, exist_ok=True)
    icon = Image.new("RGBA", (1024, 1024), "#F5F2EA")
    pen = ImageDraw.Draw(icon)
    pen.ellipse((130, 130, 894, 894), fill="#243B35")
    for box in [(180, 180, 844, 844), (220, 220, 804, 804)]:
        pen.ellipse(box, outline="#597367", width=6)
    pen.ellipse((338, 338, 686, 686), fill="#D9B473")
    pen.ellipse((480, 480, 544, 544), fill="#F5F2EA")
    icon_path = out / ("homecookin.ico" if sys.platform == "win32" else "homecookin.icns")
    icon.save(icon_path)
    options = [str(root / "gui.py"), "--name", "HomeCookinUnlocker", "--windowed", "--noconfirm",
               "--clean", "--distpath", str(out / "app"), "--workpath", str(out / "build"),
               "--specpath", str(out), "--paths", str(root), "--icon", str(icon_path)]
    if sys.platform == "win32":
        options += ["--onefile"]
    else:
        # onedir APP avoids onefile's extraction overhead and supports signing.
        options += ["--onedir", "--osx-bundle-identifier", "org.homecookin.saveunlocker"]
        identity = os.environ.get("MAC_CODESIGN_IDENTITY")
        if identity:
            options += ["--codesign-identity", identity]
    PyInstaller.__main__.run(options)
    arch = platform.machine().lower().replace("amd64", "x64").replace("x86_64", "x64")
    label = ("Windows-" if sys.platform == "win32" else "macOS-") + arch
    bundle = out / ("HomeCookinUnlocker-" + label)
    bundle.mkdir(exist_ok=True)
    if sys.platform == "win32":
        shutil.copy2(out / "app/HomeCookinUnlocker.exe", bundle / "HomeCookinUnlocker.exe")
    else:
        source = out / "app/HomeCookinUnlocker.app"
        target = bundle / "HomeCookinUnlocker.app"
        if target.exists():
            raise SystemExit("Output APP already exists; choose a fresh --output.")
        shutil.copytree(source, target, symlinks=True)
    shutil.copy2(root / "QUICK_START.txt", bundle / "使用說明.txt")
    metadata = {"version": "0.3.0", "platform": label, "python": platform.python_version(),
                "signed": bool(os.environ.get("MAC_CODESIGN_IDENTITY")) if sys.platform == "darwin" else False,
                "gameplay_verified": False}
    (bundle / "build-info.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    archive = out / (bundle.name + ".zip")
    if sys.platform == "darwin":
        # ditto preserves macOS bundle symlinks and executable permissions.
        subprocess.run(["/usr/bin/ditto", "-c", "-k", "--keepParent", str(bundle), str(archive)], check=True)
    else:
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
            for path in bundle.rglob("*"):
                if path.is_file():
                    package.write(path, path.relative_to(bundle.parent))
    (out / (archive.name + ".sha256")).write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + "\n")
    print("Desktop package:", archive)


if __name__ == "__main__":
    main()
