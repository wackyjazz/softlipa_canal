#!/usr/bin/env python3
"""A self-contained desktop front end; players use the packaged EXE / APP."""
import argparse
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import desktop_model as model
import unlock as core

VERSION = "0.2.0"
BG = "#F5F2EA"
CARD = "#FFFFFF"
INK = "#243B35"
MUTED = "#66766E"
GREEN = "#27634E"
PALE = "#E5EDE5"


class UnlockApp:
    def __init__(self, root, initial_path=None):
        self.root = root
        self.view = None
        self.busy = False
        self.results = queue.Queue()
        self.closed = tk.BooleanVar(value=False)
        self.path = None
        self.restore_window = None
        root.title("家常音樂 · 彩蛋解鎖工具")
        root.geometry("820x720")
        root.minsize(min(760, root.winfo_screenwidth() - 60), min(680, root.winfo_screenheight() - 100))
        root.configure(background=BG)
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.font = "Microsoft JhengHei" if sys.platform == "win32" else "PingFang TC"
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TButton", font=(self.font, 11), padding=(14, 10),
                        background=PALE, foreground=INK, borderwidth=0)
        style.map("TButton", background=[("active", "#D6E4D8"), ("disabled", "#ECEDE8")],
                  foreground=[("disabled", "#8C948D")])
        style.configure("Primary.TButton", background=GREEN, foreground="white", font=(self.font, 13, "bold"))
        style.map("Primary.TButton", background=[("disabled", "#D6DFD5"), ("active", "#194D3B")],
                  foreground=[("disabled", "#849287"), ("!disabled", "white")])
        style.configure("TCheckbutton", background=BG, foreground=INK, font=(self.font, 11))
        style.configure("TProgressbar", background=GREEN, troughcolor=BG, borderwidth=0)

        scrollbar = ttk.Scrollbar(root, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        viewport = tk.Canvas(root, bg=BG, highlightthickness=0, yscrollcommand=scrollbar.set)
        viewport.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=viewport.yview)
        outer = tk.Frame(viewport, bg=BG, padx=34, pady=24)
        panel = viewport.create_window((0, 0), window=outer, anchor="nw")
        outer.bind("<Configure>", lambda _: viewport.configure(scrollregion=viewport.bbox("all")))
        viewport.bind("<Configure>", lambda event: viewport.itemconfigure(panel, width=event.width))
        root.bind("<MouseWheel>", lambda event: viewport.yview_scroll(
            -int(event.delta / 120) if abs(event.delta) >= 120 else -event.delta, "units"))
        top = tk.Frame(outer, bg=BG)
        top.pack(fill="x")
        words = tk.Frame(top, bg=BG)
        words.pack(side="left", fill="x", expand=True)
        self.label(words, "HOME COOKIN’  /  運河", 10, MUTED).pack(anchor="w")
        self.label(words, "讓謎之男子登場", 25, bold=True).pack(anchor="w", pady=(6, 5))
        self.label(words, "開啟彩蛋資格，接著回到原本的冒險。", 11, MUTED).pack(anchor="w")
        vinyl = tk.Canvas(top, width=100, height=100, bg=BG, highlightthickness=0)
        vinyl.pack(side="right", padx=(12, 0))
        vinyl.create_oval(6, 6, 94, 94, fill=INK, outline=INK)
        for radius in (33, 38):
            vinyl.create_oval(50-radius, 50-radius, 50+radius, 50+radius, outline="#597367")
        vinyl.create_oval(30, 30, 70, 70, fill="#D9B473", outline="#D9B473")
        vinyl.create_oval(46, 46, 54, 54, fill=BG, outline=BG)

        steps = tk.Frame(outer, bg=PALE, padx=16, pady=10)
        steps.pack(fill="x", pady=(22, 18))
        self.label(steps, "01  找到存檔     →     02  開啟資格     →     03  繼續遊戲", 11,
                   bg=PALE).pack(anchor="w")

        card = tk.Frame(outer, bg=CARD, padx=22, pady=18)
        card.pack(fill="both", expand=True)
        self.caption = self.label(card, "正在尋找你的存檔", 10, MUTED, bg=CARD)
        self.caption.pack(anchor="w")
        self.title = self.label(card, "準備檢查…", 19, bold=True, bg=CARD)
        self.title.pack(anchor="w", pady=(8, 8))
        self.description = self.label(card, "", 11, MUTED, bg=CARD)
        self.description.configure(wraplength=670, justify="left", height=4)
        self.description.pack(anchor="w", fill="x")
        tk.Frame(card, bg="#EBEEE8", height=1).pack(fill="x", pady=(18, 12))
        self.path_label = self.label(card, "", 9, MUTED, bg=CARD)
        self.path_label.configure(wraplength=670, justify="left", height=2)
        self.path_label.pack(anchor="w", fill="x")
        actions = tk.Frame(card, bg=CARD)
        actions.pack(anchor="w", pady=(12, 0))
        self.choose_button = ttk.Button(actions, text="選擇存檔", command=self.choose_save)
        self.choose_button.pack(side="left")
        self.refresh_button = ttk.Button(actions, text="重新檢查", command=self.refresh)
        self.refresh_button.pack(side="left", padx=8)
        self.detect_button = ttk.Button(actions, text="自動尋找", command=self.detect)
        self.detect_button.pack(side="left")

        self.check = ttk.Checkbutton(outer, text="我已完全關閉遊戲", variable=self.closed,
                                     command=self.update_buttons)
        self.check.pack(anchor="w", pady=(18, 10))
        self.primary = ttk.Button(outer, text="備份並開啟彩蛋資格", style="Primary.TButton",
                                  command=self.unlock_clicked)
        self.primary.pack(fill="x", ipady=3)
        self.progress = ttk.Progressbar(outer, mode="indeterminate")
        self.progress.pack(fill="x", pady=(8, 6))
        bottom = tk.Frame(outer, bg=BG)
        bottom.pack(fill="x")
        self.restore_button = ttk.Button(bottom, text="還原備份…", command=self.show_backups)
        self.restore_button.pack(side="left")
        self.details_button = ttk.Button(bottom, text="查看詳情", command=self.show_details)
        self.details_button.pack(side="left", padx=8)
        self.label(bottom, "本機處理 · 自動備份 · 保留原版內容", 9, MUTED).pack(side="right")
        self.controls = [self.choose_button, self.refresh_button, self.detect_button,
                         self.restore_button, self.details_button, self.check]
        root.update_idletasks()
        # Tk scales fonts with display DPI. Size the initial window to the actual
        # content instead of clipping the primary action on a scaled display.
        width = min(max(820, outer.winfo_reqwidth() + 18), root.winfo_screenwidth() - 60)
        height = min(max(720, outer.winfo_reqheight()), root.winfo_screenheight() - 100)
        root.geometry(f"{width}x{height}")
        self.update_buttons()
        root.after(60, self.poll)
        if initial_path is not None:
            self.path = Path(initial_path)
            root.after(100, self.refresh)
        else:
            root.after(100, self.detect)

    def label(self, parent, text, size, color=INK, bold=False, bg=BG):
        return tk.Label(parent, text=text, font=(self.font, size, "bold" if bold else "normal"),
                        fg=color, bg=bg, anchor="w")

    def update_buttons(self):
        eligible = self.view is not None and self.view.state == "eligible"
        for control in getattr(self, "controls", []):
            control.configure(state="disabled" if self.busy else "normal")
        if hasattr(self, "primary"):
            self.primary.configure(state="normal" if eligible and self.closed.get() and not self.busy else "disabled")
            self.restore_button.configure(state="normal" if self.path and not self.busy else "disabled")

    def start_job(self, fn, done):
        if self.busy:
            return
        self.busy = True
        self.update_buttons()
        self.progress.start(12)

        def work():
            try:
                result = fn()
                self.results.put((done, result, None))
            except Exception as exc:
                self.results.put((done, None, exc))
        threading.Thread(target=work, daemon=False).start()

    def poll(self):
        try:
            done, value, error = self.results.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            self.progress.stop()
            if error:
                self.view = None
                self.title.configure(text="這次操作未能完成")
                self.description.configure(text="請查看下方說明，處理後按「重新檢查」。")
                self.closed.set(False)
                messagebox.showerror("操作未能完成", str(error), parent=self.root)
            else:
                done(value)
            self.update_buttons()
        self.root.after(60, self.poll)

    def show_view(self, view):
        self.view = view
        self.path = view.path
        self.caption.configure(text=f"你的存檔  ·  第 {view.chapter} 章" if view.chapter is not None else "你的存檔")
        self.title.configure(text=view.title)
        self.description.configure(text=view.description)
        self.path_label.configure(text=str(view.path))
        self.update_buttons()

    def detect(self):
        if self.busy:
            return
        try:
            self.path = core.default_save()
        except core.UnlockError:
            self.view = None
            self.title.configure(text="請選擇遊戲存檔")
            self.description.configure(text="按「選擇存檔」，選取遊戲的 save.dat 檔案。")
            self.caption.configure(text="尚未選擇存檔")
            self.update_buttons()
            return
        self.closed.set(False)
        self.refresh()

    def choose_save(self):
        chosen = filedialog.askopenfilename(parent=self.root, title="選擇《運河》的遊戲存檔",
                                             filetypes=[("遊戲存檔", "*.dat"), ("所有檔案", "*")])
        if chosen:
            self.path = Path(chosen)
            self.closed.set(False)
            self.refresh()

    def refresh(self):
        if self.busy:
            return
        if self.path is None:
            self.detect()
            return
        path = self.path
        self.view = None
        self.title.configure(text="正在檢查存檔…")
        self.start_job(lambda: model.inspect_save(path), self.show_view)

    def unlock_clicked(self):
        if self.busy or not self.view or self.view.state != "eligible" or not self.closed.get():
            return
        view = self.view
        self.title.configure(text="正在備份並開啟資格…")
        self.description.configure(text="請稍候，並保持遊戲關閉。")

        def work():
            backup = core.unlock(view.path, True, expected_sha256=view.sha256)
            return model.inspect_save(view.path), backup

        def finished(result):
            updated, backup = result
            self.show_view(updated)
            if updated.state == "ready":
                self.title.configure(text="完成！彩蛋資格已開啟")
                self.description.configure(text="現在可以關閉工具，回到遊戲選擇「繼續遊戲」。\n"
                                           "第四章向唱片行詢問《家常音樂》，再回到街道探索。\n"
                                           "需要復原時，可從下方「還原備份」找回原本進度。")
            self.closed.set(False)
        self.start_job(work, finished)

    def show_backups(self):
        if self.busy or self.path is None:
            return
        path = self.path
        self.start_job(lambda: model.list_backups(path), self.backup_dialog)

    def backup_dialog(self, backups):
        if not backups:
            messagebox.showinfo("還沒有可還原的備份", "此存檔尚無可驗證的工具備份。成功解鎖前會自動建立備份。",
                                parent=self.root)
            return
        dialog = tk.Toplevel(self.root)
        self.restore_window = dialog
        dialog.title("還原遊戲存檔")
        dialog.geometry("740x380")
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.grab_set()
        self.label(dialog, "選擇要回到的進度", 18, bold=True).pack(anchor="w", padx=24, pady=(20, 8))
        self.label(dialog, "還原會回到當時的整份進度。目前存檔也會先備份。", 11, MUTED).pack(anchor="w", padx=24)
        listing = tk.Listbox(dialog, font=(self.font, 10), bg=CARD, fg=INK, selectbackground=GREEN,
                             selectforeground="white", activestyle="none", exportselection=False)
        listing.pack(fill="both", expand=True, padx=24, pady=16)
        for backup in backups:
            listing.insert("end", backup.label)
        # Deliberately no preselected backup: the user picks the progress to restore.
        confirmed = tk.BooleanVar(value=False)
        check = ttk.Checkbutton(dialog, text="我已完全關閉遊戲", variable=confirmed)
        check.pack(anchor="w", padx=24)
        row = tk.Frame(dialog, bg=BG)
        row.pack(fill="x", padx=24, pady=16)
        restore_btn = ttk.Button(row, text="還原選取的備份", state="disabled")
        restore_btn.pack(side="right")
        ttk.Button(row, text="取消", command=dialog.destroy).pack(side="right", padx=10)

        def update(*_):
            restore_btn.configure(state="normal" if listing.curselection() and confirmed.get() else "disabled")
        listing.bind("<<ListboxSelect>>", update)
        confirmed.trace_add("write", update)

        def restore_selected():
            selection = listing.curselection()
            if not selection or not confirmed.get():
                return
            backup = backups[selection[0]]
            if not messagebox.askyesno("確認還原進度", f"將還原到：\n{backup.label}\n\n"
                                      "之後取得的道具與任務進度會回到當時狀態。要繼續嗎？", parent=dialog):
                return
            path = self.path
            expected = self.view.sha256 if self.view else None
            dialog.destroy()
            self.title.configure(text="正在備份並還原…")

            def work():
                core.restore(path, backup.folder, True, expected_sha256=expected)
                return model.inspect_save(path)

            def finished(view):
                self.show_view(view)
                self.closed.set(False)
                messagebox.showinfo("已還原備份", "進度已回到選取的備份。請回到遊戲選擇「繼續遊戲」。", parent=self.root)
            self.start_job(work, finished)
        restore_btn.configure(command=restore_selected)

    def show_details(self):
        text = f"家常音樂彩蛋解鎖工具 {VERSION}\n\n"
        if self.view:
            text += f"存檔：{self.view.path}\n\n{self.view.details}\n\n"
        text += "適用依據：Windows 原版 1.0.0 的存檔格式。\n"
        text += "只修改彩蛋資格；不改遊戲程式、道具或事件紀錄。\n"
        text += "Mac 相容性與遊戲內彩蛋仍待實機驗證。"
        messagebox.showinfo("版本與檢查詳情", text, parent=self.root)

    def on_close(self):
        if self.busy:
            messagebox.showinfo("正在處理", "請等待目前操作完成，再關閉視窗。", parent=self.root)
            return
        self.root.destroy()


def enable_dpi_awareness():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass


def main():
    parser = argparse.ArgumentParser(description="家常音樂彩蛋解鎖工具")
    parser.add_argument("--save", help="開發測試或自訂存檔路徑")
    args = parser.parse_args()
    enable_dpi_awareness()
    root = tk.Tk()
    UnlockApp(root, args.save)
    root.mainloop()


if __name__ == "__main__":
    main()
