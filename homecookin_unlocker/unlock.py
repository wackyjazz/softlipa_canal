#!/usr/bin/env python3
"""Offline, conservative save unlocker for Canal Legend 1.0.0 / CLSAVE2."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import gzip
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import uuid
import zlib

MAGIC = b"CLSAVE2\0"
SECRET = b"canal-legend-save:online.rsdr.canalLegend:v2"
MAX_SIZE = 16 * 1024 * 1024
BACKUP_FOLDER = "homecookin-backups"


class UnlockError(Exception):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise UnlockError("JSON 含有重複欄位，停止處理。")
        result[key] = value
    return result


def reject_constant(value):
    raise UnlockError("JSON 含有非標準數值：" + value)


def parse_json(raw):
    try:
        return json.loads(raw, object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise UnlockError("無法解析 JSON。") from exc


def validate(data):
    if not isinstance(data, dict):
        raise UnlockError("存檔不是 JSON 物件。")
    if type(data.get("chapter")) is not int or not 0 <= data["chapter"] <= 12:
        raise UnlockError("章節欄位不符合已知格式。")
    if type(data.get("isMember")) is not bool:
        raise UnlockError("isMember 欄位不符合已知格式。")
    for name in ("items", "triggeredEvents"):
        values = data.get(name)
        if not isinstance(values, list) or any(type(v) is not str for v in values):
            raise UnlockError(name + " 欄位不符合已知格式。")


def decode(raw):
    if len(raw) > MAX_SIZE or len(raw) <= len(MAGIC) + 32:
        raise UnlockError("存檔大小異常。")
    if not raw.startswith(MAGIC):
        raise UnlockError("僅支援 CLSAVE2 save.dat；舊版 save.json 請先由遊戲讀取並存檔。")
    signature = raw[len(MAGIC):len(MAGIC) + 32]
    payload = raw[len(MAGIC) + 32:]
    if not hmac.compare_digest(signature, hmac.digest(SECRET, payload, "sha256")):
        raise UnlockError("存檔驗證失敗，沒有修改檔案。")
    try:
        decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
        unpacked = decompressor.decompress(payload, MAX_SIZE + 1)
        if (len(unpacked) > MAX_SIZE or not decompressor.eof
                or decompressor.unused_data or decompressor.unconsumed_tail):
            raise UnlockError("壓縮資料過大、不完整或含有額外內容。")
        data = parse_json(unpacked.decode("utf-8"))
    except (zlib.error, UnicodeError) as exc:
        raise UnlockError("存檔壓縮內容無法讀取。") from exc
    validate(data)
    return data


def encode(data):
    validate(data)
    unpacked = json.dumps(data, ensure_ascii=False, separators=(",", ":"),
                          allow_nan=False).encode("utf-8")
    if len(unpacked) > MAX_SIZE:
        raise UnlockError("存檔內容過大。")
    payload = gzip.compress(unpacked, mtime=0)
    result = MAGIC + hmac.digest(SECRET, payload, "sha256") + payload
    if decode(result) != data:
        raise UnlockError("存檔編碼驗證失敗。")
    return result


def assess(data):
    """Return eligibility and a player-facing explanation; never reset events."""
    validate(data)
    events, items = set(data["triggeredEvents"]), set(data["items"])
    if "time_traveler" in events:
        return False, "已有 time_traveler 紀錄；可能已觸發或完成彩蛋，不重設事件。"
    if "complete" in events or data["chapter"] > 4:
        return False, "已超過第四章；請使用第四章分支前的存檔。"
    if "home-cookin" in items or "old_man_talk_home_cookin" in events:
        return False, "已取得《家常音樂》或走過老人分支；請使用較早存檔。"
    branch_flags = sorted(events & {
        "find_home_cookin", "ask_old_man_home_cookin", "ask_home_cookin_repeat_again",
    })
    if branch_flags:
        return False, "已有分支紀錄（" + ", ".join(branch_flags) + "）；不自動清除，請使用較早存檔。"
    if data["isMember"]:
        return True, "資格已啟用；分岔前可解除，也可直接繼續原本第四章流程。"
    if data["chapter"] < 4:
        return True, "可解鎖；之後在第四章依原劇情向唱片行詢問《家常音樂》。"
    if "ask_home_cookin" not in events:
        return True, "可解鎖；讀檔後先向唱片行詢問《家常音樂》。"
    return True, "可解鎖；讀檔後回到台南街道，依原版事件條件觸發彩蛋。"


def default_save():
    if sys.platform == "win32":
        folder = os.environ.get("APPDATA")
        if not folder:
            raise UnlockError("找不到 APPDATA，請用 --save 指定存檔。")
        base = Path(folder)
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        raise UnlockError("此系統僅供開發測試，請用 --save 明確指定測試存檔。")
    return base / "canal-legend" / "gameData" / "save.dat"


def save_path(value):
    path = Path(value).expanduser().absolute()
    if path.is_symlink():
        raise UnlockError("不處理符號連結存檔，請指定實際檔案。")
    return path.resolve()


def read_bytes(path):
    if path.is_symlink() or not path.is_file():
        raise UnlockError("找不到一般存檔檔案：" + str(path))
    with path.open("rb") as stream:
        raw = stream.read(MAX_SIZE + 1)
    if len(raw) > MAX_SIZE:
        raise UnlockError("檔案過大，停止處理。")
    return raw


def ensure_closed(path, acknowledged):
    if not acknowledged:
        raise UnlockError("請先完全關閉遊戲；命令列寫入須加上 --game-closed。")
    if path.with_name(path.name + ".tmp").exists():
        raise UnlockError("發現遊戲的 save.dat.tmp；可能正在存檔或曾中斷，請先確認遊戲狀態。")
    # Name detection is a second guard. Renamed executables still require the
    # user's explicit closed-game acknowledgement; no process is terminated.
    try:
        if sys.platform == "win32":
            command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                       "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
                       "Get-Process | ForEach-Object { $_.ProcessName }"]
        elif sys.platform == "darwin":
            command = ["/bin/ps", "-A", "-o", "comm="]
        else:
            return  # Explicit-path developer/test mode only.
        options = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)} if sys.platform == "win32" else {}
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=15,
                                check=True, **options)
    except (OSError, subprocess.SubprocessError) as exc:
        raise UnlockError("無法檢查遊戲程序，停止寫入。") from exc
    if re.search(r"canal[- ]legend|運河.*南都|運河.*GorDoN", result.stdout, re.I):
        raise UnlockError("偵測到遊戲仍在執行，請關閉遊戲後重試。")


@contextmanager
def locked(path):
    lock = path.with_name(path.name + ".homecookin.lock")
    try:
        stream = lock.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise UnlockError("已有工具鎖定檔；請關閉其他解鎖工具。若曾當機，確認無工具執行後才移除：" + str(lock)) from exc
    try:
        with stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        lock.unlink()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def durable_write(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def make_backup(path, raw, action, output):
    root = path.parent / BACKUP_FOLDER
    root.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    folder = root / (stamp + "-" + uuid.uuid4().hex[:8])
    folder.mkdir()
    durable_write(folder / "save.dat", raw)
    metadata = {
        "tool": "homecookin-unlocker", "version": 1, "action": action,
        "created_utc": stamp, "target": str(path),
        "backup_sha256": digest(raw), "output_sha256": digest(output),
        "changed_fields": ["isMember"] if action in {"unlock", "disable"} else ["whole_save"],
    }
    durable_write(folder / "manifest.json",
                  json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8"))
    if read_bytes(folder / "save.dat") != raw:
        raise UnlockError("備份驗證失敗，沒有修改原存檔。")
    return folder


def replace_save(path, before, after, action, acknowledged):
    decode(after)
    ensure_closed(path, acknowledged)
    if read_bytes(path) != before:
        raise UnlockError("存檔在操作期間改變，沒有覆寫。")
    backup = make_backup(path, before, action, after)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".homecookin-",
                                         suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(after)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
        if read_bytes(temporary) != after:
            raise UnlockError("暫存檔驗證失敗。")
        ensure_closed(path, acknowledged)
        if read_bytes(path) != before:
            raise UnlockError("存檔在操作期間改變，沒有覆寫。")
        os.replace(temporary, path)
        if read_bytes(path) != after:
            raise UnlockError("寫入後內容不一致，請保持遊戲關閉並檢查備份。")
    except (OSError, UnlockError) as exc:
        raise UnlockError(str(exc) + "\n原檔備份：" + str(backup)) from exc
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return backup


def set_membership(path, enabled, acknowledged=False, *, expected_sha256=None):
    """Change eligibility only before the branch point, in either direction."""
    if type(enabled) is not bool:
        raise UnlockError("彩蛋資格必須是布林值。")
    ensure_closed(path, acknowledged)
    with locked(path):
        before = read_bytes(path)
        if expected_sha256 is not None and digest(before) != expected_sha256:
            raise UnlockError("存檔已變更，請重新檢查後再切換彩蛋。")
        data = decode(before)
        allowed, reason = assess(data)
        if not allowed:
            raise UnlockError(reason)
        if data["isMember"] == enabled:
            return None
        updated = dict(data)
        updated["isMember"] = enabled
        after = encode(updated)
        # Only this field may differ. All unrecognized fields are preserved.
        verified = decode(after)
        verified["isMember"] = data["isMember"]
        if verified != data:
            raise UnlockError("偵測到非預期欄位變動，沒有修改原存檔。")
        return replace_save(path, before, after, "unlock" if enabled else "disable", acknowledged)


def unlock(path, acknowledged=False, *, expected_sha256=None):
    return set_membership(path, True, acknowledged, expected_sha256=expected_sha256)


def disable(path, acknowledged=False, *, expected_sha256=None):
    return set_membership(path, False, acknowledged, expected_sha256=expected_sha256)


def restore(path, folder, acknowledged=False, *, expected_sha256=None):
    ensure_closed(path, acknowledged)
    with locked(path):
        folder = Path(folder).expanduser().resolve()
        metadata = parse_json(read_bytes(folder / "manifest.json").decode("utf-8"))
        if (not isinstance(metadata, dict)
                or metadata.get("tool") != "homecookin-unlocker"
                or metadata.get("version") != 1
                or metadata.get("target") != str(path)):
            raise UnlockError("備份不屬於此存檔路徑或不是此工具建立的備份。")
        after = read_bytes(folder / "save.dat")
        if digest(after) != metadata.get("backup_sha256"):
            raise UnlockError("備份雜湊不一致，停止還原。")
        decode(after)
        before = read_bytes(path)
        if expected_sha256 is not None and digest(before) != expected_sha256:
            raise UnlockError("存檔已變更，請重新檢查後再還原。")
        if before == after:
            return None
        # Save the current bytes first, even if that current file is damaged.
        return replace_save(path, before, after, "restore", acknowledged)


def print_status(path):
    data = decode(read_bytes(path))
    allowed, reason = assess(data)
    print("存檔：", path)
    print("格式：CLSAVE2（依原版 1.0.0 分析；原遊戲內流程仍待驗證）")
    print("章節：", data["chapter"], "／isMember：", data["isMember"])
    print("判定：", reason)
    if allowed and not data["isMember"]:
        print("可啟用彩蛋：isMember: false → true；其他欄位保持原值。")
    elif allowed:
        print("可解除彩蛋：isMember: true → false；其他欄位保持原值。")
    return data, allowed


def menu(path):
    print("家常音樂彩蛋切換工具 v0.3\n1. 檢查存檔\n2. 啟用彩蛋\n3. 還原備份\n4. 解除彩蛋\n0. 離開")
    choice = input("選擇：").strip()
    if choice == "0":
        return
    if choice not in {"1", "2", "3", "4"}:
        raise UnlockError("無效選項。")
    if choice in {"1", "2", "4"}:
        data, allowed = print_status(path)
        if choice == "1" or not allowed or data["isMember"] == (choice == "2"):
            return
    folder = None
    if choice == "3":
        print("還原會回到備份當時的整份進度；目前存檔也會先備份。")
        print("備份目錄：", path.parent / BACKUP_FOLDER)
        folder = input("要還原的備份資料夾完整路徑：").strip().strip('"').strip("'")
        if not folder:
            raise UnlockError("未指定備份，沒有修改。")
    if input("請完全關閉遊戲；確認執行請輸入 YES：").strip() != "YES":
        print("已取消，沒有修改。")
        return
    if choice == "3":
        backup = restore(path, folder, True)
    else:
        backup = set_membership(path, choice == "2", True)
    print("已完成。" if backup else "內容已符合，不需要修改。")
    if backup:
        print("操作前備份：", backup)
    if choice in {"2", "4"}:
        print("請使用「繼續遊戲」讀檔；新遊戲需重新解鎖。")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="menu",
                        choices=["menu", "status", "unlock", "disable", "restore"])
    parser.add_argument("--save", help="save.dat 完整路徑；省略則尋找原版預設位置")
    parser.add_argument("--backup", help="還原用的備份資料夾（含 manifest.json）")
    parser.add_argument("--game-closed", action="store_true", help="確認遊戲已完全關閉")
    args = parser.parse_args(argv)
    try:
        path = save_path(args.save if args.save else default_save())
        if not path.exists():
            raise UnlockError("找不到存檔：" + str(path)
                              + "\n請先跳過登入、開始遊戲並完成一次存檔，再完全關閉遊戲。")
        if args.action == "menu":
            menu(path)
        elif args.action == "status":
            print_status(path)
        elif args.action in {"unlock", "disable"}:
            print_status(path)
            enabled = args.action == "unlock"
            backup = set_membership(path, enabled, args.game_closed)
            label = "啟用" if enabled else "解除"
            print(f"彩蛋資格已{label}，請繼續遊戲讀檔。" if backup else "資格已符合，沒有重複修改。")
            if backup:
                print("原檔備份：", backup)
        else:
            if not args.backup:
                raise UnlockError("還原須用 --backup 指定備份資料夾；會回到當時整份進度。")
            backup = restore(path, args.backup, args.game_closed)
            print("已還原整份存檔。操作前備份：" + str(backup) if backup else "內容相同，沒有修改。")
        return 0
    except (UnlockError, OSError, ValueError, EOFError, RecursionError) as exc:
        print("停止：" + str(exc), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n已中止；如已進入寫入階段，請檢查存檔與備份。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
