"""BrainClaw email-sync evidence processor.

The processor deliberately does not assign emails to tasks. It builds a
structured task catalog, prepares explicit evidence for the semantic classifier,
filters only strict deterministic noise, and renders a diagnostic Markdown view.

Usage:
    py -3 assistant_brain/scripts/email_sync.py --input-file INPUT.json
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from email_sync_candidates import prepare_candidate_payload, render_diagnostic
from email_sync_catalog import build_task_catalog
from manage_ignore_candidates import cleanup_candidates
from shared_config import BRAIN_DIR, configure_utf8_stdio

configure_utf8_stdio()

SYNC_RESULTS_DIR = BRAIN_DIR / "sync_results"
IGNORE_CANDIDATES_FILE = SYNC_RESULTS_DIR / "ignore_candidates.json"
DEFAULT_CANDIDATES_FILE = SYNC_RESULTS_DIR / "latest-candidates.json"
DEFAULT_CANDIDATES_SCHEMA = BRAIN_DIR / "formats" / "email_sync_candidates.schema.json"


class EvidenceBundleError(ValueError):
    """Raised when an evidence bundle cannot be generated safely."""


def _resolve_path(raw: str | None, default: Path) -> Path:
    path = Path(raw) if raw else default
    return path if path.is_absolute() else (BRAIN_DIR.parent / path).resolve()


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def load_ignore_candidates(path: Path = IGNORE_CANDIDATES_FILE) -> dict[str, Any]:
    if not path.exists():
        return {"updated_at": None, "candidates": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {"updated_at": None, "candidates": {}}
    if not isinstance(data, dict):
        return {"updated_at": None, "candidates": {}}
    candidates = data.get("candidates", {})
    if not isinstance(candidates, dict):
        candidates = {}
    return {"updated_at": data.get("updated_at"), "candidates": cleanup_candidates(candidates)}


def cleanup_old_results(days: int = 14) -> None:
    if not SYNC_RESULTS_DIR.exists():
        return
    protected = {
        "ignore_candidates.json",
        "latest.md",
        "latest-input.json",
        "latest-meta.json",
        "latest-run.json",
        "latest-candidates.json",
        "latest-plan.json",
        "latest-applied.json",
    }
    cutoff = datetime.now() - timedelta(days=days)
    for path in SYNC_RESULTS_DIR.iterdir():
        if path.is_file() and path.name not in protected and path.stat().st_mtime < cutoff.timestamp():
            path.unlink()


def _load_snapshot(path: Path) -> tuple[list[dict[str, Any]], str]:
    try:
        raw = path.read_text(encoding="utf-8-sig")
        payload = json.loads(raw)
    except FileNotFoundError as exc:
        raise EvidenceBundleError(f"Snapshot does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceBundleError(f"Could not read snapshot: {exc}") from exc
    if not isinstance(payload, list):
        raise EvidenceBundleError("Snapshot must be a JSON list")
    seen: set[str] = set()
    for index, email in enumerate(payload, 1):
        if not isinstance(email, dict):
            raise EvidenceBundleError(f"Snapshot item {index} must be an object")
        entry_id = str(email.get("entry_id", "")).strip()
        if not entry_id:
            raise EvidenceBundleError(f"Snapshot item {index} has no entry_id")
        if "conversation_id" not in email:
            raise EvidenceBundleError(f"Snapshot item {index} has no conversation_id field")
        if entry_id in seen:
            raise EvidenceBundleError(f"Snapshot contains duplicate entry_id: {entry_id}")
        seen.add(entry_id)
    normalized = raw.lstrip("\ufeff")
    snapshot_id = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return payload, snapshot_id


def _load_metadata(path: Path, actual_snapshot_id: str, email_count: int) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": 1,
            "snapshot_id": actual_snapshot_id,
            "fetched_at": "",
            "source": "direct-email-sync-invocation",
            "stale": False,
            "stale_reason": "",
            "email_count": email_count,
        }
    try:
        metadata = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceBundleError(f"Could not read snapshot metadata: {exc}") from exc
    if not isinstance(metadata, dict):
        raise EvidenceBundleError("Snapshot metadata must be a JSON object")
    if metadata.get("schema_version") != 1:
        raise EvidenceBundleError("Snapshot metadata schema_version must be 1")
    if not isinstance(metadata.get("stale"), bool):
        raise EvidenceBundleError("Snapshot metadata stale flag must be a boolean")
    recorded_count = metadata.get("email_count")
    if recorded_count is not None and recorded_count != email_count:
        raise EvidenceBundleError(
            f"Snapshot metadata email_count {recorded_count} does not match snapshot count {email_count}"
        )
    recorded = str(metadata.get("snapshot_id", "")).strip()
    if recorded and recorded != actual_snapshot_id:
        raise EvidenceBundleError(
            f"Snapshot content hash {actual_snapshot_id} does not match metadata snapshot_id {recorded}"
        )
    metadata["snapshot_id"] = actual_snapshot_id
    return metadata


def validate_candidate_payload(
    payload: dict[str, Any],
    schema_path: Path = DEFAULT_CANDIDATES_SCHEMA,
) -> None:
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8-sig"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
    except FileNotFoundError as exc:
        raise EvidenceBundleError(f"Candidate schema does not exist: {schema_path}") from exc
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        raise EvidenceBundleError(f"Invalid candidate schema: {exc}") from exc
    errors = sorted(
        validator.iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}"
            for part in error.absolute_path
        )
        raise EvidenceBundleError(f"Candidate schema validation failed at {location}: {error.message}")

    if payload["snapshot"]["email_count"] != len(payload["emails"]):
        raise EvidenceBundleError("Candidate snapshot.email_count must equal the number of email records")
    numbers = [item["number"] for item in payload["emails"]]
    if numbers != list(range(1, len(numbers) + 1)):
        raise EvidenceBundleError("Candidate email numbers must be consecutive and preserve snapshot order")


def build_evidence_bundle(
    snapshot_file: Path,
    metadata_file: Path,
    ignore_file: Path = IGNORE_CANDIDATES_FILE,
    schema_file: Path = DEFAULT_CANDIDATES_SCHEMA,
) -> dict[str, Any]:
    emails, actual_snapshot_id = _load_snapshot(snapshot_file)
    metadata = _load_metadata(metadata_file, actual_snapshot_id, len(emails))
    ignore_payload = load_ignore_candidates(ignore_file)
    catalog = build_task_catalog()
    payload = prepare_candidate_payload(
        emails,
        catalog,
        metadata,
        set(ignore_payload["candidates"]),
    )
    validate_candidate_payload(payload, schema_file)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare structured evidence for semantic email classification")
    parser.add_argument("--input-file", required=True, help="Outlook JSON snapshot")
    parser.add_argument("--metadata-file", help="Snapshot metadata JSON")
    parser.add_argument("--output-file", help="Human-readable diagnostic Markdown")
    parser.add_argument("--candidates-file", help="Structured candidate evidence JSON")
    parser.add_argument("--ignore-file", default=str(IGNORE_CANDIDATES_FILE))
    parser.add_argument("--candidates-schema-file", default=str(DEFAULT_CANDIDATES_SCHEMA))
    args = parser.parse_args()

    input_path = _resolve_path(args.input_file, SYNC_RESULTS_DIR / "latest-input.json")
    metadata_path = _resolve_path(args.metadata_file, input_path.with_name("latest-meta.json"))
    output_path = _resolve_path(args.output_file, SYNC_RESULTS_DIR / "latest.md")
    candidates_path = _resolve_path(args.candidates_file, DEFAULT_CANDIDATES_FILE)
    ignore_path = _resolve_path(args.ignore_file, IGNORE_CANDIDATES_FILE)
    schema_path = _resolve_path(args.candidates_schema_file, DEFAULT_CANDIDATES_SCHEMA)

    try:
        payload = build_evidence_bundle(input_path, metadata_path, ignore_path, schema_path)
        rendered = render_diagnostic(payload)
        _atomic_write(candidates_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        _atomic_write(output_path, rendered)
        cleanup_old_results()
    except (OSError, EvidenceBundleError) as exc:
        print(f"Email sync evidence generation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if not args.output_file:
        print(rendered)
        print(f"\nStructured evidence: {candidates_path}")


if __name__ == "__main__":
    main()
