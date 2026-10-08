"""Validate and atomically apply an email-classifier JSON plan.

The classifier decides meaning; this module owns all mutations. It rejects stale
or mismatched snapshots, requires an outcome for every email marked for review,
validates every requested task update before writing, and emits an
applied-result report that downstream summaries can trust.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from manage_ignore_candidates import add_candidate, cleanup_candidates, load_pool
from shared_config import BRAIN_DIR, configure_utf8_stdio
from update_task import TaskUpdateError, find_task_file, plan_task_update

configure_utf8_stdio()

SYNC_RESULTS_DIR = BRAIN_DIR / "sync_results"
DEFAULT_PLAN_FILE = SYNC_RESULTS_DIR / "latest-plan.json"
DEFAULT_SNAPSHOT_FILE = SYNC_RESULTS_DIR / "latest-input.json"
DEFAULT_METADATA_FILE = SYNC_RESULTS_DIR / "latest-meta.json"
DEFAULT_CANDIDATES_FILE = SYNC_RESULTS_DIR / "latest-candidates.json"
DEFAULT_IGNORE_FILE = SYNC_RESULTS_DIR / "ignore_candidates.json"
DEFAULT_APPLIED_FILE = SYNC_RESULTS_DIR / "latest-applied.json"
DEFAULT_SCHEMA_FILE = BRAIN_DIR / "formats" / "email_sync_plan.schema.json"
SCHEMA_VERSION = 1


class SyncPlanError(ValueError):
    """Raised when a classifier plan cannot be applied safely."""


def _read_json(path: Path, expected_type: type, label: str) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise SyncPlanError(f"{label} does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise SyncPlanError(f"Could not read {label}: {exc}") from exc
    if not isinstance(payload, expected_type):
        raise SyncPlanError(f"{label} must be a JSON {expected_type.__name__}")
    return payload


def _read_snapshot(path: Path) -> tuple[list[dict[str, Any]], str]:
    try:
        raw = path.read_text(encoding="utf-8-sig")
        payload = json.loads(raw)
    except FileNotFoundError as exc:
        raise SyncPlanError(f"Snapshot does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise SyncPlanError(f"Could not read Snapshot: {exc}") from exc
    if not isinstance(payload, list):
        raise SyncPlanError("Snapshot must be a JSON list")
    normalized = raw.lstrip("\ufeff")
    snapshot_id = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return payload, snapshot_id


def _schema_error_path(error: Any) -> str:
    path = "$"
    for part in error.absolute_path:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path


def validate_plan_shape(
    plan: dict[str, Any],
    *,
    schema: dict[str, Any] | None = None,
    schema_path: Path = DEFAULT_SCHEMA_FILE,
) -> None:
    """Validate the published JSON Schema, then enforce cross-record invariants."""
    active_schema = schema if schema is not None else _read_json(schema_path, dict, "Plan schema")
    try:
        Draft202012Validator.check_schema(active_schema)
        validator = Draft202012Validator(active_schema)
    except SchemaError as exc:
        raise SyncPlanError(f"Invalid plan schema: {exc.message}") from exc

    errors = sorted(
        validator.iter_errors(plan),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        raise SyncPlanError(
            f"Plan schema validation failed at {_schema_error_path(error)}: {error.message}"
        )

    evaluated_tasks = set(plan["evaluated_tasks"])
    task_update_keys: list[tuple[str, str]] = []
    for index, update in enumerate(plan["task_updates"]):
        if update["task"] not in evaluated_tasks:
            raise SyncPlanError(f"task_updates[{index}].task must be listed in evaluated_tasks")
        task_update_keys.append((update["task"].strip(), update["source"]["entry_id"].strip()))
    if len(task_update_keys) != len(set(task_update_keys)):
        raise SyncPlanError("Each (task, entry_id) pair may appear in at most one task update")

    ignore_entry_ids = [item["entry_id"].strip() for item in plan["ignore"]]
    if len(ignore_entry_ids) != len(set(ignore_entry_ids)):
        raise SyncPlanError("ignore must not contain duplicate entry_id values")

    unresolved_entry_ids = [item["entry_id"].strip() for item in plan.get("unresolved", [])]
    if len(unresolved_entry_ids) != len(set(unresolved_entry_ids)):
        raise SyncPlanError("unresolved must not contain duplicate entry_id values")


def _snapshot_index(snapshot: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, email in enumerate(snapshot):
        if not isinstance(email, dict):
            raise SyncPlanError(f"Snapshot item {index} must be an object")
        entry_id = str(email.get("entry_id") or email.get("id") or "").strip()
        if not entry_id:
            raise SyncPlanError(f"Snapshot item {index} has no entry_id")
        if entry_id in result:
            raise SyncPlanError(f"Snapshot contains duplicate entry_id: {entry_id}")
        result[entry_id] = email
    return result


def _validate_source_against_snapshot(update: dict[str, Any], snapshot_by_id: dict[str, dict[str, Any]]) -> None:
    source = update.get("source") or {}
    entry_id = str(source.get("entry_id", "")).strip()
    email = snapshot_by_id.get(entry_id)
    if email is None:
        raise SyncPlanError(f"Task update entry_id is not in the current snapshot: {entry_id}")

    snapshot_conversation = str(email.get("conversation_id", "") or "").strip()
    planned_conversation = str(source.get("conversation_id", "") or "").strip()
    if snapshot_conversation and planned_conversation != snapshot_conversation:
        raise SyncPlanError(
            f"ConversationID mismatch for {entry_id}: plan={planned_conversation!r}, "
            f"snapshot={snapshot_conversation!r}"
        )

    received_at = str(source.get("received_at", "") or "").strip()
    snapshot_time = str(email.get("received_time") or email.get("start_time") or "").strip()
    if snapshot_time and received_at != snapshot_time:
        raise SyncPlanError(
            f"Received timestamp mismatch for {entry_id}: plan={received_at!r}, snapshot={snapshot_time!r}"
        )

    folder = str(email.get("folder", "") or "").lower()
    direction = source.get("direction")
    if "sent" in folder and direction != "out":
        raise SyncPlanError(f"Sent Items message {entry_id} must use source.direction=out")
    if ("inbox" in folder or "收件" in folder) and direction == "out":
        raise SyncPlanError(f"Inbox message {entry_id} cannot use source.direction=out")


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _stage_and_commit(payloads: dict[Path, bytes]) -> None:
    originals: dict[Path, bytes | None] = {}
    temp_paths: dict[Path, Path] = {}
    committed: list[Path] = []
    try:
        for path, data in payloads.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            originals[path] = path.read_bytes() if path.exists() else None
            temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
            temp.write_bytes(data)
            temp_paths[path] = temp
        for path, temp in temp_paths.items():
            temp.replace(path)
            committed.append(path)
    except Exception:
        for temp in temp_paths.values():
            if temp.exists():
                temp.unlink()
        for path in reversed(committed):
            original = originals[path]
            if original is None:
                path.unlink(missing_ok=True)
            else:
                rollback = path.with_name(f".{path.name}.{os.getpid()}.rollback")
                rollback.write_bytes(original)
                rollback.replace(path)
        raise


def build_application(
    plan: dict[str, Any],
    snapshot: list[dict[str, Any]],
    metadata: dict[str, Any],
    *,
    tasks_dir: Path,
    ignore_file: Path,
    schema: dict[str, Any] | None = None,
    review_entry_ids: set[str] | None = None,
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    """Validate the complete plan and return staged file payloads plus its report."""
    validate_plan_shape(plan, schema=schema)
    if metadata.get("schema_version") != SCHEMA_VERSION:
        raise SyncPlanError(f"Snapshot metadata schema_version must be {SCHEMA_VERSION}")
    if not isinstance(metadata.get("stale"), bool):
        raise SyncPlanError("Snapshot metadata stale flag must be a boolean")
    snapshot_id = str(metadata.get("snapshot_id", "")).strip()
    if not snapshot_id:
        raise SyncPlanError("Snapshot metadata has no snapshot_id")
    if plan["snapshot_id"] != snapshot_id:
        raise SyncPlanError(
            f"Plan snapshot_id {plan['snapshot_id']} does not match current snapshot_id {snapshot_id}"
        )
    if metadata.get("stale"):
        reason = metadata.get("stale_reason") or "snapshot metadata is marked stale"
        raise SyncPlanError(f"Refusing to mutate from a stale snapshot: {reason}")

    snapshot_by_id = _snapshot_index(snapshot)
    task_entry_ids: set[str] = set()
    ignore_entry_ids: set[str] = set()
    task_states: dict[Path, str] = {}
    task_reports: list[dict[str, Any]] = []
    evaluated_paths: dict[str, Path] = {}

    for index, task_ref in enumerate(plan["evaluated_tasks"]):
        try:
            task_file = find_task_file(task_ref, tasks_dir, include_history=False)
            content = task_file.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError, TaskUpdateError) as exc:
            raise SyncPlanError(f"Invalid evaluated_tasks[{index}]: {exc}") from exc
        if task_file in evaluated_paths.values():
            raise SyncPlanError(f"evaluated_tasks contains duplicate references to {task_file.name}")
        evaluated_paths[task_ref] = task_file
        task_states[task_file] = content

    # Plan every task change in memory first. Repeated updates to one task are
    # evaluated sequentially but written once.
    for index, update in enumerate(plan["task_updates"]):
        if not isinstance(update, dict):
            raise SyncPlanError(f"task_updates[{index}] must be an object")
        try:
            _validate_source_against_snapshot(update, snapshot_by_id)
            task_file = evaluated_paths[str(update.get("task", ""))]
            history_dir = (tasks_dir / "history").resolve()
            if history_dir in task_file.resolve().parents:
                raise SyncPlanError(
                    f"Archived task {task_file.name} is read-only during email sync; create/reopen an active task first"
                )
            original = task_states[task_file]
            updated, change_report = plan_task_update(original, update)
        except (FileNotFoundError, OSError, TaskUpdateError) as exc:
            raise SyncPlanError(f"Invalid task_updates[{index}]: {exc}") from exc
        task_states[task_file] = updated
        entry_id = str(update["source"]["entry_id"]).strip()
        task_entry_ids.add(entry_id)
        task_reports.append({
            "task": str(update["task"]),
            "file": task_file.relative_to(BRAIN_DIR.parent).as_posix()
            if task_file.is_relative_to(BRAIN_DIR.parent) else str(task_file),
            "entry_id": entry_id,
            "updated": change_report["updated"],
            "changes": change_report["changes"],
        })

    try:
        pool = load_pool(ignore_file, strict=True)
    except ValueError as exc:
        raise SyncPlanError(f"Invalid ignore pool: {exc}") from exc
    new_pool = deepcopy(pool)
    ignored_reports: list[dict[str, Any]] = []
    for index, item in enumerate(plan["ignore"]):
        entry_id = item["entry_id"].strip()
        if entry_id not in snapshot_by_id:
            raise SyncPlanError(f"ignore[{index}] entry_id is not in the current snapshot: {entry_id}")
        ignore_entry_ids.add(entry_id)
        candidate = add_candidate(new_pool, snapshot_by_id[entry_id], item["reason"])
        ignored_reports.append({
            "entry_id": entry_id,
            "subject": candidate.get("subject", ""),
            "sender": candidate.get("sender", ""),
            "reason": candidate.get("reason", ""),
        })

    overlap = task_entry_ids & ignore_entry_ids
    if overlap:
        raise SyncPlanError(f"The same email cannot update a task and be ignored: {', '.join(sorted(overlap))}")

    unresolved_reports: list[dict[str, Any]] = []
    for item in plan.get("unresolved", []):
        entry_id = item["entry_id"].strip()
        if entry_id not in snapshot_by_id:
            raise SyncPlanError(f"Unresolved entry_id is not in the current snapshot: {entry_id}")
        if entry_id in task_entry_ids or entry_id in ignore_entry_ids:
            raise SyncPlanError(f"Email {entry_id} cannot also be unresolved")
        unresolved_reports.append(deepcopy(item))

    if review_entry_ids is not None:
        decided = task_entry_ids | ignore_entry_ids | {item["entry_id"].strip() for item in unresolved_reports}
        missing = sorted(review_entry_ids - decided)
        if missing:
            shown = "; ".join(
                f"{entry_id} ({snapshot_by_id.get(entry_id, {}).get('subject', '?')})" for entry_id in missing[:5]
            )
            raise SyncPlanError(
                f"{len(missing)} review email(s) have no outcome (task update, ignore, or unresolved): {shown}"
            )

    payloads: dict[Path, bytes] = {}
    for task_file, updated in task_states.items():
        current = task_file.read_text(encoding="utf-8")
        if updated != current:
            payloads[task_file] = updated.encode("utf-8")

    if ignored_reports:
        new_pool["candidates"] = cleanup_candidates(new_pool.get("candidates", {}))
        new_pool["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        payloads[ignore_file] = _json_bytes(new_pool)

    changes_by_file: dict[str, list[str]] = {}
    for item in task_reports:
        changes_by_file.setdefault(item["file"], []).extend(item["changes"])
    evaluated_reports = []
    for task_ref, task_file in evaluated_paths.items():
        relative = task_file.relative_to(BRAIN_DIR.parent).as_posix() if task_file.is_relative_to(BRAIN_DIR.parent) else str(task_file)
        evaluated_reports.append({
            "task": task_ref,
            "file": relative,
            "updated": task_file in payloads,
            "changes": changes_by_file.get(relative, []),
        })

    report = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "applied_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "snapshot_stale": bool(metadata.get("stale")),
        "evaluated_tasks": evaluated_reports,
        "task_updates": task_reports,
        "ignored": ignored_reports,
        "unresolved": unresolved_reports,
        "audit": {
            "task_files_evaluated": len(evaluated_reports),
            "task_files_modified": sum(1 for item in evaluated_reports if item["updated"]),
            "task_updates_requested": len(task_reports),
            "ignore_candidates_added": len(ignored_reports),
            "unresolved_count": len(unresolved_reports),
        },
    }
    return payloads, report


def apply_plan(
    plan_file: Path = DEFAULT_PLAN_FILE,
    snapshot_file: Path = DEFAULT_SNAPSHOT_FILE,
    metadata_file: Path = DEFAULT_METADATA_FILE,
    ignore_file: Path = DEFAULT_IGNORE_FILE,
    applied_file: Path = DEFAULT_APPLIED_FILE,
    *,
    schema_file: Path = DEFAULT_SCHEMA_FILE,
    tasks_dir: Path | None = None,
    candidates_file: Path | None = None,
) -> dict[str, Any]:
    plan = _read_json(plan_file, dict, "Plan")
    schema = _read_json(schema_file, dict, "Plan schema")
    snapshot, actual_snapshot_id = _read_snapshot(snapshot_file)
    metadata = _read_json(metadata_file, dict, "Snapshot metadata")
    metadata_snapshot_id = str(metadata.get("snapshot_id", "")).strip()
    if metadata_snapshot_id and actual_snapshot_id != metadata_snapshot_id:
        raise SyncPlanError(
            f"Snapshot content hash {actual_snapshot_id} does not match metadata snapshot_id {metadata_snapshot_id}"
        )
    review_entry_ids = None
    if candidates_file is not None:
        candidates = _read_json(candidates_file, dict, "Candidates")
        if str(candidates.get("snapshot_id", "")).strip() != metadata_snapshot_id:
            raise SyncPlanError(
                f"Candidates snapshot_id {candidates.get('snapshot_id')} does not match metadata snapshot_id {metadata_snapshot_id}"
            )
        review_entry_ids = {
            str(email.get("entry_id", "")).strip()
            for email in candidates.get("emails", [])
            if email.get("review_status") == "review"
        }
    payloads, report = build_application(
        plan,
        snapshot,
        metadata,
        tasks_dir=tasks_dir or (BRAIN_DIR / "tasks"),
        ignore_file=ignore_file,
        schema=schema,
        review_entry_ids=review_entry_ids,
    )
    payloads[applied_file] = _json_bytes(report)
    _stage_and_commit(payloads)
    return report


def _build_apply_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and atomically apply an email sync plan")
    parser.add_argument("--plan-file", default=str(DEFAULT_PLAN_FILE))
    parser.add_argument("--snapshot-file", default=str(DEFAULT_SNAPSHOT_FILE))
    parser.add_argument("--metadata-file", default=str(DEFAULT_METADATA_FILE))
    parser.add_argument("--candidates-file", default=str(DEFAULT_CANDIDATES_FILE))
    parser.add_argument("--ignore-file", default=str(DEFAULT_IGNORE_FILE))
    parser.add_argument("--applied-file", default=str(DEFAULT_APPLIED_FILE))
    parser.add_argument("--schema-file", default=str(DEFAULT_SCHEMA_FILE))
    return parser


def _parse_apply_args(argv: list[str]) -> argparse.Namespace:
    return _build_apply_parser().parse_args(argv)


def main() -> None:
    args = _parse_apply_args(sys.argv[1:])
    try:
        report = apply_plan(
            Path(args.plan_file),
            Path(args.snapshot_file),
            Path(args.metadata_file),
            Path(args.ignore_file),
            Path(args.applied_file),
            schema_file=Path(args.schema_file),
            candidates_file=Path(args.candidates_file),
        )
    except (OSError, SyncPlanError) as exc:
        print(f"Email sync plan rejected: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
