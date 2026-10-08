"""Validate BrainClaw task Markdown against the published task-file Schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from shared_config import BRAIN_DIR, configure_utf8_stdio

configure_utf8_stdio()

DEFAULT_TASK_DIR = BRAIN_DIR / "tasks"
DEFAULT_SCHEMA_FILE = BRAIN_DIR / "formats" / "task_file.schema.json"
HEADER_RE = re.compile(r"^\*\*([^*]+):\*\*\s*(.*)$")
TITLE_RE = re.compile(r"^#\s+(T\d{3}):\s*(.+?)\s*$", re.IGNORECASE)
FILENAME_ID_RE = re.compile(r"^(T\d{3})(?:-|\.md$)", re.IGNORECASE)
EMAIL_RE = re.compile(r"^[^@\s<>()[\],;:]+@[^@\s<>()[\],;:]+\.[^@\s<>()[\],;:]+$")
EMAIL_CANDIDATE_RE = re.compile(r"[A-Z0-9._%+\-'’]+@[A-Z0-9.-]+", re.IGNORECASE)
EMAIL_MARKER_RE = re.compile(r"<!--\s*email:([^>]+?)\s*-->", re.IGNORECASE)
CONVERSATION_MARKER_RE = re.compile(r"<!--\s*conversation:([^>]+?)\s*-->", re.IGNORECASE)
REQUIRED_HEADERS = ("Status", "Created", "Priority", "Category", "Geo", "Due", "EPD", "Scope", "Exclude")
SECTION_HEADINGS = {
    "contacts": "## Contacts",
    "stakeholders": "## Stakeholders",
    "raci": "### RACI Matrix",
    "tags": "## Tags",
    "asks": "## Asks",
    "my_actions": "### My Actions",
    "waiting_on_others": "### Waiting on Others",
    "timeline": "## Timeline",
    "current_state": "## Current State",
    "notes": "## Notes",
}
PLACEHOLDERS = {"", "-", "—", "tbd", "todo", "n/a", "na", "none", "placeholder"}


def _schema_path(error: Any) -> str:
    path = "$"
    for part in error.absolute_path:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path


def _section_bounds(lines: list[str], heading: str) -> tuple[int, int] | None:
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        return None
    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].lstrip()
        if not stripped.startswith("#"):
            continue
        next_level = len(stripped) - len(stripped.lstrip("#"))
        if next_level <= level:
            end = index
            break
    return start, end


def extract_task(path: Path) -> tuple[dict[str, Any], list[str], list[str]]:
    """Extract the machine-validated task contract and local diagnostics."""
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    errors: list[str] = []
    warnings: list[str] = []

    title_match = next((TITLE_RE.match(line) for line in lines if TITLE_RE.match(line)), None)
    task_id = title_match.group(1).upper() if title_match else ""
    title = title_match.group(2).strip() if title_match else ""
    filename_match = FILENAME_ID_RE.match(path.name)
    filename_task_id = filename_match.group(1).upper() if filename_match else ""
    if not title_match:
        errors.append("missing or malformed '# T###: Title' heading")
    if not filename_match:
        errors.append("filename must begin with T###-")
    elif task_id and filename_task_id != task_id:
        errors.append(f"filename Task ID {filename_task_id} does not match heading {task_id}")

    headers: dict[str, str] = {}
    for line in lines:
        match = HEADER_RE.match(line.strip())
        if match:
            headers[match.group(1).strip()] = match.group(2).strip()
    for field in REQUIRED_HEADERS:
        if field not in headers:
            errors.append(f"missing required header field: {field}")
    scope = headers.get("Scope", "")
    if scope.strip().lower() in PLACEHOLDERS:
        errors.append("Scope must be a positive, non-placeholder boundary statement")

    sections = {key: _section_bounds(lines, heading) is not None for key, heading in SECTION_HEADINGS.items()}
    for key, present in sections.items():
        if not present:
            errors.append(f"missing required section: {SECTION_HEADINGS[key]}")

    tags: list[str] = []
    tag_bounds = _section_bounds(lines, "## Tags")
    if tag_bounds:
        for line in lines[tag_bounds[0] + 1:tag_bounds[1]]:
            tags.extend(value.strip() for value in re.findall(r"`([^`]+)`", line) if value.strip())
        folded = [tag.casefold() for tag in tags]
        if len(folded) != len(set(folded)):
            errors.append("Tags must be unique (case-insensitive)")

    for heading in ("## Contacts", "### RACI Matrix"):
        bounds = _section_bounds(lines, heading)
        if not bounds:
            continue
        for line_number in range(bounds[0] + 1, bounds[1]):
            line = lines[line_number]
            if "@" not in line:
                if heading == "## Contacts" and line.lstrip().startswith("-"):
                    warnings.append(f"line {line_number + 1}: contact has no email address")
                continue
            candidates = EMAIL_CANDIDATE_RE.findall(line)
            if not candidates or any(not EMAIL_RE.fullmatch(candidate) for candidate in candidates):
                errors.append(f"line {line_number + 1}: malformed contact email")

    timeline_bounds = _section_bounds(lines, "## Timeline")
    missing_conversation_lines: list[int] = []
    if timeline_bounds:
        for line_number in range(timeline_bounds[0] + 1, timeline_bounds[1]):
            line = lines[line_number]
            email_markers = EMAIL_MARKER_RE.findall(line)
            if not email_markers:
                continue
            if any(not marker.strip() or "\n" in marker or "\r" in marker for marker in email_markers):
                errors.append(f"line {line_number + 1}: malformed email EntryID marker")
            if not CONVERSATION_MARKER_RE.search(line):
                missing_conversation_lines.append(line_number + 1)
    if missing_conversation_lines:
        sample = ", ".join(str(number) for number in missing_conversation_lines[:5])
        suffix = ", ..." if len(missing_conversation_lines) > 5 else ""
        warnings.append(
            f"{len(missing_conversation_lines)} email timeline entr"
            f"{'y has' if len(missing_conversation_lines) == 1 else 'ies have'} no ConversationID "
            f"(legacy allowed; lines {sample}{suffix})"
        )

    record = {
        "task_id": task_id,
        "filename_task_id": filename_task_id,
        "title": title,
        "status": headers.get("Status", ""),
        "created": headers.get("Created", ""),
        "priority": headers.get("Priority", ""),
        "category": headers.get("Category", ""),
        "geo": headers.get("Geo", ""),
        "due": headers.get("Due", ""),
        "epd": headers.get("EPD", ""),
        "scope": scope,
        "exclude": headers.get("Exclude", ""),
        "sections": sections,
        "tags": tags,
    }
    return record, errors, warnings


def errors_and_warnings(
    task_dir: Path = DEFAULT_TASK_DIR,
    schema_file: Path = DEFAULT_SCHEMA_FILE,
) -> tuple[list[str], list[str]]:
    try:
        schema = json.loads(schema_file.read_text(encoding="utf-8-sig"))
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        return [f"Task schema is invalid: {exc}"], []
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    warnings: list[str] = []
    paths = sorted(task_dir.glob("T*.md")) if task_dir.is_dir() else [task_dir]
    if not paths:
        return [f"No task Markdown files found at {task_dir}"], []
    for path in paths:
        try:
            record, local_errors, local_warnings = extract_task(path)
        except OSError as exc:
            errors.append(f"{path}: could not read task: {exc}")
            continue
        prefix = path.as_posix()
        errors.extend(f"{prefix}: {message}" for message in local_errors)
        warnings.extend(f"{prefix}: {message}" for message in local_warnings)
        schema_errors = sorted(
            validator.iter_errors(record),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
        errors.extend(
            f"{prefix}: schema {_schema_path(error)}: {error.message}"
            for error in schema_errors
        )
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate active BrainClaw task Markdown files")
    parser.add_argument("--task-dir", type=Path, default=DEFAULT_TASK_DIR)
    parser.add_argument("--schema-file", type=Path, default=DEFAULT_SCHEMA_FILE)
    parser.add_argument("--warnings-as-errors", action="store_true")
    args = parser.parse_args()
    errors, warnings = errors_and_warnings(args.task_dir, args.schema_file)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors or (warnings and args.warnings_as_errors):
        print(f"Task validation failed: {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    print(f"Task validation passed with {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
