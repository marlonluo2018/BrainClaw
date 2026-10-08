"""Stable entry point for BrainClaw email sync.

This wrapper fetches recent emails as JSON, saves a BOM-safe snapshot to
`assistant_brain/sync_results/latest-input.json`, then runs `email_sync.py`
and atomically saves `latest-candidates.json` plus the diagnostic `latest.md`.

The wrapper is intentionally conservative for agent/Codex execution:
- print short progress lines before slow COM/subprocess stages
- fetch Outlook data through a timeout-controlled subprocess by default
- validate Outlook JSON before replacing the stable input snapshot
- stage snapshot, metadata, structured evidence, and diagnostic output together; promote only after success
- accept a verified empty Outlook result as a valid fresh snapshot by default
- block overlapping top-level fetches; a lock older than FETCH_LOCK_MAX_AGE_SECONDS
  is treated as abandoned (e.g. a killed process) and ignored
- on any failure, stop without touching the last good snapshot (no fallback)

Usage:
    py -3 assistant_brain/scripts/run_email_sync.py
    py -3 assistant_brain/scripts/run_email_sync.py --days 3
    py -3 assistant_brain/scripts/run_email_sync.py inspect <number|entry_id>
    py -3 assistant_brain/scripts/run_email_sync.py search <keyword>
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from shared_config import BRAIN_DIR, configure_utf8_stdio

configure_utf8_stdio()

SYNC_RESULTS_DIR = BRAIN_DIR / "sync_results"
DEFAULT_INPUT_FILE = SYNC_RESULTS_DIR / "latest-input.json"
DEFAULT_OUTPUT_FILE = SYNC_RESULTS_DIR / "latest.md"
DEFAULT_CANDIDATES_FILE = SYNC_RESULTS_DIR / "latest-candidates.json"
DEFAULT_METADATA_FILE = SYNC_RESULTS_DIR / "latest-meta.json"
DEFAULT_RUN_STATE_FILE = SYNC_RESULTS_DIR / "latest-run.json"
MAX_AUTO_DAYS = 30
# Longer than a full fetch + processing run (90s + 90s timeouts plus margin).
FETCH_LOCK_MAX_AGE_SECONDS = 300
OUTLOOK_SKILL_ROOT = BRAIN_DIR / "skills" / "outlook_com_skill"
OUTLOOK_SKILL = OUTLOOK_SKILL_ROOT / "scripts" / "outlook_skill.py"
EMAIL_SYNC = BRAIN_DIR / "scripts" / "email_sync.py"


def log(message: str, verbose: bool = False) -> None:
    if verbose:
        print(f"[email-sync] {message}", file=sys.stderr, flush=True)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(BRAIN_DIR.parent))
    except ValueError:
        return str(path)


def _load_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _auto_determine_days(metadata_path: Path, fallback_output_path: Path, max_days: int = MAX_AUTO_DAYS) -> int:
    """Calculate lookback from the last successful Outlook fetch watermark."""
    metadata = _load_metadata(metadata_path)
    raw_watermark = metadata.get("last_successful_fetch_at") or metadata.get("fetched_at")
    watermark = None
    if raw_watermark:
        try:
            watermark = datetime.fromisoformat(str(raw_watermark).replace("Z", "+00:00"))
            if watermark.tzinfo is None:
                watermark = watermark.replace(tzinfo=timezone.utc)
        except ValueError:
            watermark = None

    if watermark is not None:
        elapsed_seconds = max(0.0, (datetime.now(timezone.utc) - watermark.astimezone(timezone.utc)).total_seconds())
    elif fallback_output_path.exists():
        # Migration fallback for repositories without latest-meta.json yet.
        elapsed_seconds = max(0.0, time.time() - fallback_output_path.stat().st_mtime)
    else:
        return 1

    elapsed_days = elapsed_seconds / 86400.0
    requested = max(1, int(elapsed_days) + 1)
    return min(requested, max_days)


def _resolve_output_path(raw: str | None) -> Path:
    if not raw:
        return DEFAULT_OUTPUT_FILE
    path = Path(raw)
    if not path.is_absolute():
        path = (BRAIN_DIR.parent / path).resolve()
    return path


def _tmp_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.{os.getpid()}.tmp")


def _atomic_write_text(path: Path, text: str) -> None:
    tmp = _tmp_path(path)
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _write_run_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _parse_state_time(raw: Any) -> datetime | None:
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def ensure_single_fetch_allowed(run_state_path: Path, *, now: datetime | None = None) -> None:
    """Block only an overlapping active fetch, not a later explicit sync request.

    A "fetching" lock older than FETCH_LOCK_MAX_AGE_SECONDS (or without a readable
    start time) belongs to an abandoned run and no longer blocks.
    """
    if not run_state_path.exists():
        return
    state = _load_metadata(run_state_path)
    if state.get("status") != "fetching":
        return
    started_at = _parse_state_time(state.get("started_at"))
    if started_at is None:
        return
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    age_seconds = max(
        0,
        int((current.astimezone(timezone.utc) - started_at.astimezone(timezone.utc)).total_seconds()),
    )
    run_id = state.get("run_id", "unknown")
    if age_seconds >= FETCH_LOCK_MAX_AGE_SECONDS:
        print(
            f"[email-sync] Ignoring abandoned fetch lock (started {age_seconds}s ago, run_id={run_id}).",
            file=sys.stderr,
        )
        return
    raise RuntimeError(
        "Overlapping email-sync fetch blocked: another top-level fetch is still active "
        f"(started {age_seconds}s ago, run_id={run_id}). "
        f"Wait for it to finish; the lock expires after {FETCH_LOCK_MAX_AGE_SECONDS}s."
    )


def _stage_path(path: Path, label: str) -> Path:
    return path.with_name(f".{path.name}.{os.getpid()}.{label}.stage")


def _commit_staged_files(staged: dict[Path, Path]) -> None:
    """Promote a set of staged files together, rolling back partial commits."""
    originals: dict[Path, bytes | None] = {}
    committed: list[Path] = []
    try:
        for target, stage in staged.items():
            if not stage.exists():
                raise RuntimeError(f"Missing staged sync artifact: {stage}")
            originals[target] = target.read_bytes() if target.exists() else None
        for target, stage in staged.items():
            stage.replace(target)
            committed.append(target)
    except Exception:
        for target in reversed(committed):
            original = originals[target]
            if original is None:
                target.unlink(missing_ok=True)
            else:
                rollback = _stage_path(target, "rollback")
                rollback.write_bytes(original)
                rollback.replace(target)
        raise
    finally:
        for stage in staged.values():
            stage.unlink(missing_ok=True)


def persist_sync_artifacts(
    raw_json: str,
    metadata: dict[str, Any],
    input_path: Path,
    metadata_path: Path,
    output_path: Path,
    candidates_path: Path | None = None,
    *,
    replace_input: bool,
    timeout_seconds: int,
    verbose: bool = False,
) -> None:
    """Render staged evidence, then promote the complete snapshot bundle together."""
    effective_candidates_path = candidates_path or DEFAULT_CANDIDATES_FILE
    staged_input = _stage_path(input_path, "input")
    staged_metadata = _stage_path(metadata_path, "metadata")
    staged_output = _stage_path(output_path, "output")
    staged_candidates = _stage_path(effective_candidates_path, "candidates")
    stage_paths = (staged_input, staged_metadata, staged_output, staged_candidates)
    for stage in stage_paths:
        stage.unlink(missing_ok=True)

    try:
        if replace_input:
            staged_input.write_text(raw_json, encoding="utf-8")
            processor_input = staged_input
        else:
            if not input_path.exists():
                raise RuntimeError(f"Input file does not exist: {input_path}")
            processor_input = input_path
        staged_metadata.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        run_email_sync(
            processor_input,
            staged_metadata,
            staged_output,
            candidates_output_path=staged_candidates,
            timeout_seconds=timeout_seconds,
            verbose=verbose,
        )
        staged = {
            metadata_path: staged_metadata,
            output_path: staged_output,
            effective_candidates_path: staged_candidates,
        }
        if replace_input:
            staged = {input_path: staged_input, **staged}
        _commit_staged_files(staged)
    finally:
        for stage in stage_paths:
            stage.unlink(missing_ok=True)


def _validate_email_json(raw_json: str) -> list[dict]:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        snippet = raw_json[:500].replace("\r", "\\r").replace("\n", "\\n")
        raise RuntimeError(f"Outlook JSON parse failed: {exc}. Output starts with: {snippet}") from exc

    if not isinstance(payload, list):
        raise RuntimeError(f"Outlook JSON must be a list, got {type(payload).__name__}")

    bad_items = [idx for idx, item in enumerate(payload, 1) if not isinstance(item, dict)]
    if bad_items:
        shown = ", ".join(str(i) for i in bad_items[:5])
        raise RuntimeError(f"Outlook JSON list contains non-object item(s) at position(s): {shown}")

    return payload


def fetch_recent_json_subprocess(days: int, timeout_seconds: int, verbose: bool = False) -> tuple[str, int]:
    """Fetch through the Outlook skill's stable public JSON interface."""
    cmd = [
        sys.executable,
        str(OUTLOOK_SKILL),
        "find-recent",
        "--days",
        str(days),
        "--json",
    ]
    env = os.environ.copy()
    # Let the skill's own child-process guard return first, while this wrapper
    # remains the final timeout boundary for the complete public CLI call.
    env["OUTLOOK_SKILL_TIMEOUT"] = str(max(timeout_seconds - 5, 1))
    log(f"fetching Outlook recent mail via public skill CLI: days={days}", verbose=verbose)
    try:
        result = subprocess.run(
            cmd,
            cwd=str(OUTLOOK_SKILL_ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Outlook fetch timed out after {timeout_seconds}s") from exc

    if result.returncode != 0:
        if result.stdout:
            sys.stderr.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        raise RuntimeError(f"Outlook skill fetch failed with exit code {result.returncode}")

    raw_json = result.stdout.lstrip("\ufeff")
    emails = _validate_email_json(raw_json)
    missing_contract = [
        index
        for index, email in enumerate(emails, 1)
        if "entry_id" not in email or "conversation_id" not in email
    ]
    if missing_contract:
        shown = ", ".join(str(index) for index in missing_contract[:5])
        raise RuntimeError(
            "Outlook skill JSON contract is missing entry_id/conversation_id "
            f"at position(s): {shown}. Update outlook_com_skill before running email sync."
        )
    log(f"fetched {len(emails)} Outlook item(s)", verbose=verbose)
    return raw_json, len(emails)


def fetch_recent_json(args: argparse.Namespace) -> tuple[str, int, dict[str, Any]]:
    raw_json, count = fetch_recent_json_subprocess(
        args.days,
        timeout_seconds=args.fetch_timeout,
        verbose=args.verbose,
    )
    fetched_at = datetime.now().astimezone().isoformat(timespec="seconds")
    return raw_json, count, {
        "source": "outlook-skill-cli",
        # Kept for the metadata/candidates schema; every snapshot is a fresh fetch.
        "stale": False,
        "stale_reason": "",
        "fetched_at": fetched_at,
        "last_successful_fetch_at": fetched_at,
    }


def build_snapshot_metadata(raw_json: str, count: int, days: int, fetch_state: dict[str, Any]) -> dict[str, Any]:
    normalized = raw_json.lstrip("\ufeff")
    metadata = {
        "schema_version": 1,
        "snapshot_id": hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16],
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "days": days,
        "email_count": count,
        **fetch_state,
    }
    return metadata


def run_email_sync(
    input_path: Path,
    metadata_path: Path,
    output_path: Path,
    timeout_seconds: int,
    verbose: bool = False,
    candidates_output_path: Path | None = None,
) -> None:
    tmp_output_path = _tmp_path(output_path)
    candidate_path = candidates_output_path or DEFAULT_CANDIDATES_FILE
    tmp_candidates_path = _tmp_path(candidate_path)
    tmp_output_path.unlink(missing_ok=True)
    tmp_candidates_path.unlink(missing_ok=True)

    cmd = [
        sys.executable,
        str(EMAIL_SYNC),
        "--input-file",
        str(input_path),
        "--output-file",
        str(tmp_output_path),
        "--metadata-file",
        str(metadata_path),
        "--candidates-file",
        str(tmp_candidates_path),
    ]
    log("running structured evidence processor", verbose=verbose)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        tmp_output_path.unlink(missing_ok=True)
        tmp_candidates_path.unlink(missing_ok=True)
        raise RuntimeError(f"email_sync.py timed out after {timeout_seconds}s") from exc

    if result.returncode != 0:
        tmp_output_path.unlink(missing_ok=True)
        tmp_candidates_path.unlink(missing_ok=True)
        if result.stderr:
            sys.stderr.write(result.stderr)
        raise RuntimeError(f"email_sync.py failed with exit code {result.returncode}")

    if not tmp_output_path.exists() or not tmp_candidates_path.exists():
        tmp_output_path.unlink(missing_ok=True)
        tmp_candidates_path.unlink(missing_ok=True)
        raise RuntimeError("email_sync.py did not create both Markdown and structured evidence artifacts")

    tmp_output_path.replace(output_path)
    tmp_candidates_path.replace(candidate_path)
    log(f"saved diagnostic result: {display_path(output_path)}", verbose=verbose)
    log(f"saved structured evidence: {display_path(candidate_path)}", verbose=verbose)


def _add_sync_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--days", type=int, default=None, help="How many recent days to fetch (auto-calculated from the last successful fetch watermark if omitted)")
    parser.add_argument("--input-file", type=str, default=str(DEFAULT_INPUT_FILE), help="Where to save/read the JSON snapshot")
    parser.add_argument("--output-file", type=str, default=str(DEFAULT_OUTPUT_FILE), help="Where to save the latest sync markdown output")
    parser.add_argument("--metadata-file", type=str, default=str(DEFAULT_METADATA_FILE), help="Where to save snapshot freshness metadata")
    parser.add_argument("--candidates-file", type=str, default=str(DEFAULT_CANDIDATES_FILE), help="Where to save structured classifier evidence")
    parser.add_argument("--run-state-file", type=str, default=str(DEFAULT_RUN_STATE_FILE), help="State file used to block overlapping active Outlook fetches")
    parser.add_argument("--fetch-timeout", type=int, default=90, help="Timeout in seconds for the Outlook skill public CLI")
    parser.add_argument("--process-timeout", type=int, default=90, help="Timeout in seconds for email_sync.py processing")
    parser.add_argument("--verbose", action="store_true", help="Print verbose log messages to stderr")


def _parse_sync_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stable wrapper for BrainClaw email sync")
    _add_sync_arguments(parser)
    return parser.parse_args(argv)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) > 1 and sys.argv[1] in ("inspect", "search"):
        subcmd = sys.argv[1]
        input_path = DEFAULT_INPUT_FILE
        if not input_path.exists():
            print(f"Error: Snapshot file {display_path(input_path)} does not exist.", file=sys.stderr)
            raise SystemExit(1)
        raw_json = input_path.read_text(encoding="utf-8-sig")
        try:
            emails = json.loads(raw_json)
        except Exception as exc:
            print(f"Error reading JSON: {exc}", file=sys.stderr)
            raise SystemExit(1)

        if subcmd == "inspect":
            if len(sys.argv) < 3:
                print("Usage: py -3 run_email_sync.py inspect <number|entry_id>", file=sys.stderr)
                raise SystemExit(1)
            target = sys.argv[2].lstrip("#")
            found = None
            index_num = None
            if target.isdigit():
                idx = int(target) - 1
                if 0 <= idx < len(emails):
                    found = emails[idx]
                    index_num = int(target)
            else:
                for idx, email in enumerate(emails, 1):
                    if (email.get("entry_id") or email.get("id")) == target:
                        found = email
                        index_num = idx
                        break

            if not found:
                print(f"Email '{target}' not found in latest input snapshot ({len(emails)} items).", file=sys.stderr)
                raise SystemExit(1)

            entry_id = found.get("entry_id") or found.get("id", "")
            sender = found.get("sender", "")
            subject = found.get("subject", "")
            rec_time = found.get("received_time", "")
            folder = found.get("folder", "")
            to_recips = ", ".join(r.get("name") or r.get("address", "") for r in found.get("to_recipients", []))
            cc_recips = ", ".join(r.get("name") or r.get("address", "") for r in found.get("cc_recipients", []))
            preview = found.get("body_preview", "")

            print(f"Email #{index_num}")
            print(f"Entry ID : {entry_id}")
            print(f"Sender   : {sender}")
            print(f"Subject  : {subject}")
            print(f"Received : {rec_time}")
            if folder:
                print(f"Folder   : {folder}")
            if to_recips:
                print(f"To       : {to_recips}")
            if cc_recips:
                print(f"CC       : {cc_recips}")
            print("\nBody Preview:")
            print(preview)
            return

        if subcmd == "search":
            if len(sys.argv) < 3:
                print("Usage: py -3 run_email_sync.py search <keyword>", file=sys.stderr)
                raise SystemExit(1)
            query = " ".join(sys.argv[2:]).lower()
            matches = []
            for idx, email in enumerate(emails, 1):
                entry_id = (email.get("entry_id") or email.get("id") or "").lower()
                sender = email.get("sender", "").lower()
                subject = email.get("subject", "").lower()
                preview = email.get("body_preview", "").lower()
                to_str = " ".join(r.get("name", "") + " " + r.get("address", "") for r in email.get("to_recipients", [])).lower()
                cc_str = " ".join(r.get("name", "") + " " + r.get("address", "") for r in email.get("cc_recipients", [])).lower()

                if query in entry_id or query in sender or query in subject or query in preview or query in to_str or query in cc_str:
                    matches.append((idx, email))

            if not matches:
                print(f"No emails matching '{query}' found in latest input snapshot ({len(emails)} items).")
                return

            print(f"Found {len(matches)} matching email(s) for '{query}':\n")
            for idx, email in matches:
                entry_id = email.get("entry_id") or email.get("id", "")
                sender = email.get("sender", "")
                subject = email.get("subject", "")
                rec_time = email.get("received_time", "")
                print(f"[#{idx}] {rec_time} — {sender}")
                print(f"     Subject: {subject}")
                print(f"     EntryID: {entry_id}\n")
            return

    args = _parse_sync_args(sys.argv[1:])

    input_path = _resolve_output_path(args.input_file)
    output_path = _resolve_output_path(args.output_file)
    metadata_path = _resolve_output_path(args.metadata_file)
    candidates_path = _resolve_output_path(args.candidates_file)
    run_state_path = _resolve_output_path(args.run_state_file)

    if args.days is None:
        args.days = _auto_determine_days(metadata_path, output_path)
        print(
            f"[email-sync] Syncing Outlook emails for the last {args.days} day(s) "
            f"(auto-calculated from last successful fetch; max {MAX_AUTO_DAYS})...",
            file=sys.stderr,
        )
    else:
        print(f"[email-sync] Syncing Outlook emails for the last {args.days} day(s)...", file=sys.stderr)

    input_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    candidates_path.parent.mkdir(parents=True, exist_ok=True)
    run_state_path.parent.mkdir(parents=True, exist_ok=True)

    run_id = ""
    try:
        ensure_single_fetch_allowed(run_state_path)
        run_id = uuid.uuid4().hex
        _write_run_state(run_state_path, {
            "schema_version": 1,
            "run_id": run_id,
            "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "fetching",
            "days": args.days,
            "owner": "root-agent",
        })

        raw_json, count, fetch_state = fetch_recent_json(args)
        metadata = build_snapshot_metadata(raw_json, count, args.days, fetch_state)
        persist_sync_artifacts(
            raw_json,
            metadata,
            input_path,
            metadata_path,
            output_path,
            candidates_path,
            replace_input=True,
            timeout_seconds=args.process_timeout,
            verbose=args.verbose,
        )
        _write_run_state(run_state_path, {
            "schema_version": 1,
            "run_id": run_id,
            "started_at": _load_metadata(run_state_path).get("started_at"),
            "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "snapshot-ready",
            "days": args.days,
            "email_count": count,
            "snapshot_id": metadata.get("snapshot_id", ""),
            "owner": "root-agent",
        })
        log(f"saved stable input: {display_path(input_path)}", verbose=args.verbose)
        print(display_path(output_path))
    except RuntimeError as exc:
        if run_id:
            current_state = _load_metadata(run_state_path)
            current_state.update({
                "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "status": "failed",
                "error": str(exc),
            })
            _write_run_state(run_state_path, current_state)
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()



