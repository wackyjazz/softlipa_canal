"""Read-only presentation data shared by the desktop UI and its tests."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import unlock as core


@dataclass(frozen=True)
class SaveView:
    path: Path
    state: str
    title: str
    description: str
    chapter: int | None = None
    sha256: str | None = None
    details: str = ""


def inspect_save(path):
    path = core.save_path(path)
    if not path.exists():
        return SaveView(path, "missing", "還沒找到存檔",
                        "請先在遊戲中跳過登入，開始遊戲並存檔，再關閉遊戲。\n"
                        "已經有存檔？可以按「選擇存檔」指定檔案。")
    try:
        raw = core.read_bytes(path)
    except (OSError, core.UnlockError) as exc:
        return SaveView(path, "invalid", "目前無法讀取存檔",
                        "請確認檔案可以讀取，或重新選擇存檔。", details=str(exc))
    sha = core.digest(raw)
    try:
        data = core.decode(raw)
    except (OSError, ValueError, core.UnlockError, RecursionError) as exc:
        return SaveView(path, "invalid", "這份存檔無法安全修改",
                        "檔案可能不完整或版本尚未支援。你可以選擇另一份存檔，或還原先前的備份。",
                        sha256=sha, details=str(exc))
    events = set(data["triggeredEvents"])
    allowed, reason = core.assess(data)
    common = dict(path=path, chapter=data["chapter"], sha256=sha, details=reason)
    if "time_traveler" in events:
        return SaveView(state="completed", title="這份存檔已有彩蛋紀錄",
                        description="謎之男子事件已經觸發過。工具會保留目前進度，不會重設事件。", **common)
    if not allowed:
        return SaveView(state="blocked", title="需要較早的存檔",
                        description="這份進度已超過彩蛋分岔點，或走進另一條分支。\n"
                        "請選擇第四章分岔前的存檔；目前進度會保持原樣。", **common)
    if data["isMember"]:
        return SaveView(state="ready", title="彩蛋資格已開啟",
                        description="不用再次解鎖。請回到遊戲選擇「繼續遊戲」，依第四章原本流程探索。", **common)
    return SaveView(state="eligible", title="這份存檔可以解鎖",
                    description="開啟謎之男子彩蛋的出現資格。\n"
                    "劇情、道具和任務進度都會保留；修改前會自動備份。", **common)


@dataclass(frozen=True)
class BackupView:
    folder: Path
    label: str
    chapter: int
    member: bool


def list_backups(path):
    path = core.save_path(path)
    root = path.parent / core.BACKUP_FOLDER
    if not root.is_dir():
        return []
    results = []
    for folder in sorted(root.iterdir(), reverse=True):
        if not folder.is_dir() or folder.is_symlink():
            continue
        try:
            metadata = core.parse_json(core.read_bytes(folder / "manifest.json").decode("utf-8"))
            if (not isinstance(metadata, dict) or metadata.get("tool") != "homecookin-unlocker"
                    or metadata.get("version") != 1 or metadata.get("target") != str(path)):
                continue
            raw = core.read_bytes(folder / "save.dat")
            if core.digest(raw) != metadata.get("backup_sha256"):
                continue
            data = core.decode(raw)
            time = datetime.strptime(metadata["created_utc"], "%Y%m%dT%H%M%S.%fZ")
            time = time.replace(tzinfo=timezone.utc).astimezone()
            action = "解鎖前" if metadata.get("action") == "unlock" else "還原前"
            member = "資格已開啟" if data["isMember"] else "資格未開啟"
            label = f'{time:%Y/%m/%d %H:%M:%S}  ·  第 {data["chapter"]} 章  ·  {action}  ·  {member}'
            results.append(BackupView(folder, label, data["chapter"], data["isMember"]))
        except (OSError, ValueError, KeyError, TypeError, core.UnlockError, RecursionError):
            continue  # Only verified, readable backups can be selected.
    return results
