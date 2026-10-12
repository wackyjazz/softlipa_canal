"""Validate the built native macOS bundle using a temporary synthetic save."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).parents[1]))
import unlock as core


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("app", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != "darwin":
        raise SystemExit("macOS only")
    app = args.app.resolve()
    info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
    executable = app / "Contents/MacOS" / info["CFBundleExecutable"]
    assert executable.is_file() and os.access(executable, os.X_OK)
    subprocess.run(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(app)], check=True)
    arch = subprocess.check_output(["/usr/bin/lipo", "-archs", str(executable)], text=True).strip()
    with tempfile.TemporaryDirectory(prefix="homecookin-app-test-") as directory:
        save = Path(directory) / "save.dat"
        original = core.encode({"chapter": 3, "isMember": False, "items": [], "triggeredEvents": []})
        save.write_bytes(original)
        env = dict(os.environ)
        for key in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
            env.pop(key, None)
        env["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
        process = subprocess.Popen([str(executable), "--save", str(save)], env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            # Source-level UI test exercises controls; this checks the packaged
            # interpreter/Tcl/Tk can stay running without the build Python env.
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    raise AssertionError("App exited early: " + stderr.decode(errors="replace"))
                time.sleep(0.2)
            assert save.read_bytes() == original, "Startup changed the synthetic save"
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate(timeout=5)
        if b"Traceback" in stderr or b"Failed to execute script" in stderr:
            raise AssertionError(stderr.decode(errors="replace"))
    report = {"native_architecture": arch, "bundle_integrity": "passed",
              "packaged_startup_without_build_python": "passed", "startup_read_only": True,
              "synthetic_saves_only": True, "developer_id_signed": False,
              "notarized": False, "real_gameplay_verified": False}
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
