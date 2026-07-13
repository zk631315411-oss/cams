import argparse
import json
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


CODEX_HOME = Path(r"C:\Users\hp\.codex")
CC_SWITCH_DB = Path(r"C:\Users\hp\.cc-switch\cc-switch.db")
CODEX_CONFIG = CODEX_HOME / "config.toml"
STATE_NEW = CODEX_HOME / "sqlite" / "state_5.sqlite"
STATE_OLD = CODEX_HOME / "state_5.sqlite"
RESCUE_ROOT = Path(r"D:\ai-math\codex抢救")


def rewrite_provider_toml(text: str, base_url_mode: str | None = None) -> tuple[str, list[str]]:
    changes: list[str] = []
    new = re.sub(
        r'(?m)^model_provider\s*=\s*"[^"]+"',
        'model_provider = "cc_switch"',
        text,
        count=1,
    )
    if new != text:
        changes.append("model_provider -> cc_switch")
    text = new

    new = re.sub(
        r"(?m)^\[model_providers\.[^\]]+\]",
        "[model_providers.cc_switch]",
        text,
        count=1,
    )
    if new != text:
        changes.append("[model_providers.*] -> [model_providers.cc_switch]")
    text = new

    section_match = re.search(r"(?ms)(^\[model_providers\.cc_switch\]\n)(.*?)(?=^\[|\Z)", text)
    if section_match:
        section = section_match.group(2)
        new_section = re.sub(
            r'(?m)^name\s*=\s*"[^"]+"',
            'name = "cc_switch"',
            section,
            count=1,
        )
        if new_section != section:
            changes.append("model provider section name -> cc_switch")
        if base_url_mode == "local_proxy":
            newer_section = re.sub(
                r'(?m)^base_url\s*=\s*"[^"]+"',
                'base_url = "http://127.0.0.1:15721/v1"',
                new_section,
                count=1,
            )
            if newer_section != new_section:
                changes.append("base_url -> local proxy")
            new_section = newer_section
        text = text[: section_match.start(2)] + new_section + text[section_match.end(2) :]
    return text, changes


def make_backup(items: list[tuple[Path, str]], apply: bool) -> Path | None:
    if not apply:
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = RESCUE_ROOT / f"current_before_provider_patch_{ts}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path, dest_name in items:
        if path.exists():
            shutil.copy2(path, backup_dir / dest_name)
    return backup_dir


def patch_config(apply: bool) -> dict:
    text = CODEX_CONFIG.read_text(encoding="utf-8")
    new_text, changes = rewrite_provider_toml(text, base_url_mode="local_proxy")
    if apply and new_text != text:
        CODEX_CONFIG.write_text(new_text, encoding="utf-8")
    return {"path": str(CODEX_CONFIG), "changed": new_text != text, "changes": changes}


def patch_proxy_live_backup(apply: bool) -> dict:
    con = sqlite3.connect(CC_SWITCH_DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("select app_type, original_config from proxy_live_backup").fetchall()
    details = []
    changed = 0
    for row in rows:
        if row["app_type"] != "codex":
            continue
        data = json.loads(row["original_config"])
        config = data.get("config", "")
        new_config, changes = rewrite_provider_toml(config)
        row_changed = new_config != config
        details.append({"app_type": row["app_type"], "changed": row_changed, "changes": changes})
        if row_changed:
            changed += 1
            data["config"] = new_config
            if apply:
                con.execute(
                    "update proxy_live_backup set original_config=? where app_type='codex'",
                    (json.dumps(data, ensure_ascii=False),),
                )
    if apply and changed:
        con.commit()
    con.close()
    return {"path": str(CC_SWITCH_DB), "changed_rows": changed, "details": details}


def patch_threads(apply: bool) -> list[dict]:
    out = []
    for db in [STATE_NEW, STATE_OLD]:
        if not db.exists():
            out.append({"path": str(db), "exists": False})
            continue
        con = sqlite3.connect(db)
        before = con.execute(
            "select model_provider, count(*) from threads group by model_provider order by model_provider"
        ).fetchall()
        xmai_ids = con.execute(
            "select id, title from threads where model_provider='xmai'"
        ).fetchall()
        if apply and xmai_ids:
            con.execute("update threads set model_provider='cc_switch' where model_provider='xmai'")
            con.commit()
        after = con.execute(
            "select model_provider, count(*) from threads group by model_provider order by model_provider"
        ).fetchall()
        con.close()
        out.append(
            {
                "path": str(db),
                "exists": True,
                "xmai_threads": [{"id": i, "title": t} for i, t in xmai_ids],
                "before": before,
                "after": after,
                "changed": bool(xmai_ids),
            }
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes; default is dry-run")
    args = parser.parse_args()

    backup = make_backup(
        [
            (CC_SWITCH_DB, "cc-switch.db"),
            (CODEX_CONFIG, "config.toml"),
            (STATE_NEW, "state_5_new.sqlite"),
            (STATE_NEW.with_suffix(".sqlite-wal"), "state_5_new.sqlite-wal"),
            (STATE_NEW.with_suffix(".sqlite-shm"), "state_5_new.sqlite-shm"),
            (STATE_OLD, "state_5_old.sqlite"),
            (STATE_OLD.with_suffix(".sqlite-wal"), "state_5_old.sqlite-wal"),
            (STATE_OLD.with_suffix(".sqlite-shm"), "state_5_old.sqlite-shm"),
            (CODEX_HOME / "session_index.jsonl", "session_index.jsonl"),
            (CODEX_HOME / ".codex-global-state.json", ".codex-global-state.json"),
            (CODEX_HOME / ".codex-global-state.json.bak", ".codex-global-state.json.bak"),
        ],
        args.apply,
    )

    result = {
        "mode": "apply" if args.apply else "dry-run",
        "backup_dir": str(backup) if backup else None,
        "config": patch_config(args.apply),
        "proxy_live_backup": patch_proxy_live_backup(args.apply),
        "threads": patch_threads(args.apply),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
