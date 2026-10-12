"""Native desktop smoke test; only synthetic temporary saves are touched."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).parents[1]))
import tkinter as tk
import gui
import unlock as core


def wait(root, predicate, seconds=45):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        root.update()
        if predicate():
            return
        time.sleep(0.03)
    raise AssertionError("Desktop operation did not finish")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="homecookin-ui-test-") as directory:
        path = Path(directory) / "save.dat"
        fixture = {"chapter": 3, "isMember": False, "items": ["phone"], "triggeredEvents": []}
        original = core.encode(fixture)
        path.write_bytes(original)
        gui.enable_dpi_awareness()
        root = tk.Tk()
        app = gui.UnlockApp(root, path)
        errors = []
        gui.messagebox.showerror = lambda *a, **k: errors.append(a)
        gui.messagebox.showinfo = lambda *a, **k: None
        gui.messagebox.askyesno = lambda *a, **k: True
        try:
            wait(root, lambda: app.view is not None and not app.busy)
            assert app.view.state == "eligible"
            assert str(app.primary["state"]) == "disabled"
            app.closed.set(True)
            app.update_buttons()
            assert str(app.primary["state"]) == "normal"
            root.update()
            assert app.primary.winfo_y() + app.primary.winfo_height() <= app.primary.master.winfo_height()
            if args.screenshot:
                from PIL import ImageGrab
                root.update()
                root.lift()
                time.sleep(0.3)
                bbox = (root.winfo_rootx(), root.winfo_rooty(),
                        root.winfo_rootx() + root.winfo_width(), root.winfo_rooty() + root.winfo_height())
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                ImageGrab.grab(bbox=bbox).save(args.screenshot)
            app.primary.invoke()
            wait(root, lambda: not app.busy)
            assert not errors, errors
            assert app.view.state == "ready"
            assert core.decode(path.read_bytes()) == dict(fixture, isMember=True)
            backups = list((path.parent / core.BACKUP_FOLDER).iterdir())
            assert len(backups) == 1
            assert (backups[0] / "save.dat").read_bytes() == original
            assert str(app.primary["state"]) == "disabled"
            app.show_backups()
            wait(root, lambda: not app.busy)
            assert app.restore_window is not None
            def descendants(widget):
                for child in widget.winfo_children():
                    yield child
                    yield from descendants(child)
            children = list(descendants(app.restore_window))
            listing = next(w for w in children if isinstance(w, tk.Listbox))
            check = next(w for w in children if isinstance(w, gui.ttk.Checkbutton))
            restore_button = next(w for w in children if isinstance(w, gui.ttk.Button)
                                  and w.cget("text") == "還原選取的備份")
            assert str(restore_button["state"]) == "disabled"
            listing.selection_set(0)
            listing.event_generate("<<ListboxSelect>>")
            check.invoke()
            assert str(restore_button["state"]) == "normal"
            restore_button.invoke()
            wait(root, lambda: not app.busy)
            assert not errors, errors
            assert path.read_bytes() == original
            assert app.view.state == "eligible"
            # Missing-file and blocked states must both keep the action disabled.
            path.write_bytes(core.encode(dict(fixture, chapter=5)))
            app.refresh()
            wait(root, lambda: not app.busy)
            assert app.view.state == "blocked"
            assert str(app.primary["state"]) == "disabled"
            path.unlink()
            app.refresh()
            wait(root, lambda: not app.busy)
            assert app.view.state == "missing"
            assert not errors, errors
            print(json.dumps({"gui_smoke": "passed", "synthetic_saves_only": True,
                              "states": ["eligible", "ready", "blocked", "missing"],
                              "backup_dialog_and_restore": "passed"}))
        finally:
            root.destroy()


if __name__ == "__main__":
    main()
