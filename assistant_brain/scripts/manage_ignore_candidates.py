"""Manage the semantic email-sync ignore pool without contacting Outlook."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sys

from shared_config import BRAIN_DIR, configure_utf8_stdio

configure_utf8_stdio()

SYNC_RESULTS_DIR = BRAIN_DIR / "sync_results"
IGNORE_CANDIDATES_FILE = SYNC_RESULTS_DIR / "ignore_candidates.json"
DEFAULT_SNAPSHOT_FILE = SYNC_RESULTS_DIR / "latest-input.json"
IGNORE_CANDIDATE_TTL_DAYS = 14
IGNORE_CANDIDATE_MAX_ITEMS = 500


def load_pool(path: Path = IGNORE_CANDIDATES_FILE, *, strict: bool = False) -> dict:
    if not path.exists():
        return {"updated_at": None, "candidates": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        if strict:
            raise ValueError(f"Could not read {path}: {exc}") from exc
        return {"updated_at": None, "candidates": {}}
    if not isinstance(data, dict):
        if strict:
            raise ValueError("Ignore pool must be a JSON object")
        return {"updated_at": None, "candidates": {}}
    candidates = data.get("candidates", {})
    if not isinstance(candidates, dict):
        if strict:
            raise ValueError("Ignore pool candidates must be a JSON object")
        candidates = {}
    return {"updated_at": data.get("updated_at"), "candidates": candidates}


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return parsed


def cleanup_candidates(candidates: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now().astimezone()
    kept = {}
    for entry_id, item in candidates.items():
        if not entry_id or not isinstance(item, dict):
            continue
        last_seen = _parse_time(item.get("last_seen_at"))
        if last_seen and now - last_seen > timedelta(days=IGNORE_CANDIDATE_TTL_DAYS):
            continue
        kept[entry_id] = item
    if len(kept) > IGNORE_CANDIDATE_MAX_ITEMS:
        ordered = sorted(
            kept.items(),
            key=lambda pair: _parse_time(pair[1].get("last_seen_at")) or datetime.min.astimezone(),
            reverse=True,
        )[:IGNORE_CANDIDATE_MAX_ITEMS]
        kept = dict(ordered)
    return kept


def save_pool(pool: dict, path: Path = IGNORE_CANDIDATES_FILE) -> None:
    pool["candidates"] = cleanup_candidates(pool.get("candidates", {}))
    pool["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    _atomic_write_json(path, pool)


def load_snapshot(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Snapshot file does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
        raise ValueError("Snapshot must be a JSON list of email objects")
    return payload


def find_email_in_snapshot(entry_id: str, snapshot_file: Path = DEFAULT_SNAPSHOT_FILE) -> dict | None:
    for email in load_snapshot(snapshot_file):
        if email.get("entry_id") == entry_id:
            return email
    return None


def add_candidate(pool: dict, email: dict, reason: str, source: str = "semantic_classifier") -> dict:
    entry_id = str(email.get("entry_id", "")).strip()
    if not entry_id:
        raise ValueError("Ignore candidate requires a non-empty entry_id")
    reason = reason.strip()
    if not reason:
        raise ValueError("Ignore candidate requires a specific semantic reason")

    now_iso = datetime.now().astimezone().isoformat(timespec="seconds")
    candidates = pool.setdefault("candidates", {})
    existing = candidates.get(entry_id) if isinstance(candidates.get(entry_id), dict) else {}
    candidates[entry_id] = {
        "entry_id": entry_id,
        "conversation_id": email.get("conversation_id", ""),
        "subject": email.get("subject", ""),
        "sender": email.get("sender", ""),
        "received_time": email.get("received_time", ""),
        "folder": email.get("folder", ""),
        "body_preview": (email.get("body_preview", "") or "").replace("\r\n", " ").replace("\n", " ").strip(),
        "reason": reason,
        "source_section": source,
        "suggested_action": "restore_if_task_related",
        "task_candidates": email.get("task_candidates", []),
        "first_seen_at": existing.get("first_seen_at", now_iso),
        "last_seen_at": now_iso,
        "seen_count": int(existing.get("seen_count", 0) or 0) + 1,
    }
    return candidates[entry_id]


def cmd_show(pool: dict) -> int:
    candidates = pool.get("candidates", {})
    print(f"Ignore candidates updated_at: {pool.get('updated_at') or '?'}")
    print(f"Count: {len(candidates)}\n")
    for item in sorted(candidates.values(), key=lambda value: value.get("last_seen_at", ""), reverse=True):
        print(f"ENTRY_ID: {item.get('entry_id', '')}")
        print(f"Subject: {item.get('subject', '')}")
        print(f"Sender: {item.get('sender', '')}")
        print(f"Received: {item.get('received_time', '')}")
        print(f"Reason: {item.get('reason', '')}")
        print(f"Source: {item.get('source_section', '')}")
        print("---")
    if not candidates:
        print("No ignore candidates.")
    return 0


def cmd_restore(pool: dict, entry_id: str | None, subject: str | None) -> int:
    candidates = pool.get("candidates", {})
    if entry_id:
        target_ids = [entry_id] if entry_id in candidates else []
    elif subject:
        keyword = subject.lower()
        target_ids = [eid for eid, item in candidates.items() if keyword in item.get("subject", "").lower()]
    else:
        print("Either entry_id or --subject is required.", file=sys.stderr)
        return 1
    if not target_ids:
        print("No ignore candidates matched.", file=sys.stderr)
        return 1
    for target_id in target_ids:
        candidates.pop(target_id, None)
        print(f"Restored from ignore candidates: {target_id}")
    save_pool(pool)
    return 0


def cmd_add(pool: dict, entry_id: str, reason: str, snapshot_file: Path) -> int:
    try:
        email = find_email_in_snapshot(entry_id, snapshot_file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error reading snapshot: {exc}", file=sys.stderr)
        return 1
    if not email:
        print(
            f"Entry {entry_id} is not present in {snapshot_file}. "
            "Refusing to query Outlook from the classifier; run a fresh sync first.",
            file=sys.stderr,
        )
        return 1
    try:
        candidate = add_candidate(pool, email, reason)
        save_pool(pool)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Added semantic ignore candidate: {candidate['entry_id']}")
    print(f"Subject: {candidate['subject']}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage BrainClaw semantic ignore candidates")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("show", help="Show current ignore candidates")

    add_parser = subparsers.add_parser("add", help="Add a snapshot email after semantic classification")
    add_parser.add_argument("entry_id", help="Exact snapshot entry_id")
    add_parser.add_argument("--reason", required=True, help="Specific reason the email needs no action or task")
    add_parser.add_argument("--snapshot-file", default=str(DEFAULT_SNAPSHOT_FILE))

    restore_parser = subparsers.add_parser("restore", help="Restore by entry_id or subject keyword")
    restore_parser.add_argument("entry_id", nargs="?")
    restore_parser.add_argument("--subject")

    args = parser.parse_args()
    pool = load_pool()
    if args.command == "show":
        raise SystemExit(cmd_show(pool))
    if args.command == "add":
        raise SystemExit(cmd_add(pool, args.entry_id, args.reason, Path(args.snapshot_file)))
    raise SystemExit(cmd_restore(pool, args.entry_id, args.subject))


if __name__ == "__main__":
    main()
