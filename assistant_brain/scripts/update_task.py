"""Validated, field-idempotent updates for BrainClaw task Markdown files."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

from shared_config import BRAIN_DIR, configure_utf8_stdio

configure_utf8_stdio()

TASKS_DIR = BRAIN_DIR / "tasks"
VALID_TIMELINE_TAGS = {
    "created", "update", "email-in", "email-out", "decision", "milestone",
    "delivery", "ask", "waiting", "blocker", "resolved", "deadline",
    "slack", "meeting",
}
SUPPORTED_FIELDS = {"Status", "Priority", "Category", "Geo", "Due", "EPD", "Scope", "Exclude"}
MATCHING_REVIEW_KEYS = {"scope", "exclude", "tags", "contacts", "identifiers"}
MATCHING_REVIEW_STATES = {"checked-no-change", "updated", "not-applicable"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RACI_ROLE_RE = re.compile(r"^[RACI](?:[/,][RACI])*$")


class TaskUpdateError(ValueError):
    """Raised when a structured task update is unsafe or invalid."""


def find_task_file(
    task_ref: str,
    tasks_dir: Path = TASKS_DIR,
    *,
    include_history: bool = False,
) -> Path:
    ref = task_ref.strip().lower()
    if ref.endswith(".md"):
        ref = ref[:-3]
    match_tid = re.search(r"t\d{3}", ref)
    tid = match_tid.group(0).upper() if match_tid else ""

    def matching(paths: list[Path]) -> list[Path]:
        matches = []
        for path in paths:
            name = path.name.upper()
            if tid and (name == f"{tid}.MD" or name.startswith(f"{tid}-")):
                matches.append(path)
            elif path.stem.lower().startswith(ref):
                matches.append(path)
        return matches

    active_matches = matching(list(tasks_dir.glob("T*.md")))
    if len(active_matches) == 1:
        return active_matches[0]
    if len(active_matches) > 1:
        raise TaskUpdateError(f"Task reference '{task_ref}' matched multiple active files")

    if include_history:
        history_matches = matching(list((tasks_dir / "history").rglob("T*.md")))
        if len(history_matches) == 1:
            return history_matches[0]
        if len(history_matches) > 1:
            raise TaskUpdateError(f"Task reference '{task_ref}' matched multiple archived files")

    raise FileNotFoundError(f"Could not locate task file for '{task_ref}' in {tasks_dir}")


def parse_source_datetime(value: str) -> datetime:
    raw = value.strip()
    if not raw:
        raise TaskUpdateError("source.received_at is required")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TaskUpdateError(f"Invalid source.received_at: {value}") from exc
    return parsed


def format_task_date(value: str) -> str:
    parsed = parse_source_datetime(value)
    return f"{parsed:%a %b} {parsed.day}, {parsed.year}"


def _clean_inline(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if "\n" in text or "\r" in text:
        raise TaskUpdateError(f"{field} must be one line")
    return text


def validate_task_update(update: dict) -> None:
    if not isinstance(update, dict):
        raise TaskUpdateError("Each task update must be an object")
    if not _clean_inline(update.get("task"), "task"):
        raise TaskUpdateError("task is required")
    source = update.get("source")
    if not isinstance(source, dict):
        raise TaskUpdateError("source is required")
    entry_id = _clean_inline(source.get("entry_id"), "source.entry_id")
    if not entry_id:
        raise TaskUpdateError("source.entry_id is required")
    direction = source.get("direction")
    if direction not in {"in", "out", "calendar"}:
        raise TaskUpdateError("source.direction must be in, out, or calendar")
    parse_source_datetime(str(source.get("received_at", "")))
    _clean_inline(source.get("conversation_id", ""), "source.conversation_id")

    timeline = update.get("timeline")
    if timeline is not None:
        if not isinstance(timeline, dict):
            raise TaskUpdateError("timeline must be an object")
        tag = _clean_inline(timeline.get("tag"), "timeline.tag")
        if tag not in VALID_TIMELINE_TAGS:
            raise TaskUpdateError(f"Invalid timeline tag: {tag}")
        summary = _clean_inline(timeline.get("summary"), "timeline.summary")
        if not summary:
            raise TaskUpdateError("timeline.summary is required")
        if tag == "email-in" and direction != "in":
            raise TaskUpdateError("email-in tag requires source.direction=in")
        if tag == "email-out" and direction != "out":
            raise TaskUpdateError("email-out tag requires source.direction=out")

    asks = update.get("asks", {})
    if asks is not None and not isinstance(asks, dict):
        raise TaskUpdateError("asks must be an object")
    for key in ("add_my_actions", "add_waiting"):
        items = (asks or {}).get(key, [])
        if not isinstance(items, list):
            raise TaskUpdateError(f"asks.{key} must be an array")
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise TaskUpdateError(f"asks.{key}[{index}] must be an object")
            if not _clean_inline(item.get("text"), f"asks.{key}[{index}].text"):
                raise TaskUpdateError(f"asks.{key}[{index}].text is required")
            _clean_inline(item.get("contact", ""), f"asks.{key}[{index}].contact")
            _clean_inline(item.get("due", "TBD"), f"asks.{key}[{index}].due")
    for key in ("complete_my_actions", "remove_waiting"):
        items = (asks or {}).get(key, [])
        if not isinstance(items, list) or any(not isinstance(item, str) or not item.strip() for item in items):
            raise TaskUpdateError(f"asks.{key} must be an array of non-empty strings")

    current_state = update.get("current_state", {})
    if current_state is not None and not isinstance(current_state, dict):
        raise TaskUpdateError("current_state must be an object")
    for key in ("add", "complete"):
        items = (current_state or {}).get(key, [])
        if not isinstance(items, list) or any(not isinstance(item, str) or not item.strip() for item in items):
            raise TaskUpdateError(f"current_state.{key} must be an array of non-empty strings")

    fields = update.get("fields", {})
    if fields is not None and not isinstance(fields, dict):
        raise TaskUpdateError("fields must be an object")
    unsupported = set(fields or {}) - SUPPORTED_FIELDS
    if unsupported:
        raise TaskUpdateError(f"Unsupported task field(s): {', '.join(sorted(unsupported))}")
    for field, value in (fields or {}).items():
        clean = _clean_inline(value, f"fields.{field}")
        if not clean:
            raise TaskUpdateError(f"fields.{field} must not be empty")
        if field == "Priority" and not re.fullmatch(r"P[1-3]", clean):
            raise TaskUpdateError("fields.Priority must be P1, P2, or P3")
        if field == "Scope":
            if clean.casefold() in {"-", "—", "tbd", "todo", "n/a", "na", "none", "placeholder"}:
                raise TaskUpdateError("fields.Scope must be a positive, non-placeholder boundary")
            if re.search(r"\bNOT\b", clean, re.IGNORECASE):
                raise TaskUpdateError("fields.Scope must use positive wording; put exclusions in fields.Exclude")

    matching_review = update.get("matching_review")
    if not isinstance(matching_review, dict):
        raise TaskUpdateError("matching_review is required")
    if set(matching_review) != MATCHING_REVIEW_KEYS:
        raise TaskUpdateError(
            "matching_review must contain exactly: " + ", ".join(sorted(MATCHING_REVIEW_KEYS))
        )
    for key, value in matching_review.items():
        if value not in MATCHING_REVIEW_STATES:
            raise TaskUpdateError(f"matching_review.{key} has invalid state: {value}")

    tags = update.get("tags", {})
    if tags is not None and not isinstance(tags, dict):
        raise TaskUpdateError("tags must be an object")
    for key in ("add", "remove"):
        values = (tags or {}).get(key, [])
        if not isinstance(values, list) or any(not _clean_inline(value, f"tags.{key}") for value in values):
            raise TaskUpdateError(f"tags.{key} must be an array of non-empty one-line strings")

    for section in ("contacts", "raci"):
        changes = update.get(section, {})
        if changes is not None and not isinstance(changes, dict):
            raise TaskUpdateError(f"{section} must be an object")
        for index, item in enumerate((changes or {}).get("upsert", [])):
            if not isinstance(item, dict):
                raise TaskUpdateError(f"{section}.upsert[{index}] must be an object")
            name = _clean_inline(item.get("name"), f"{section}.upsert[{index}].name")
            email = _clean_inline(item.get("email"), f"{section}.upsert[{index}].email").lower()
            role = _clean_inline(item.get("role"), f"{section}.upsert[{index}].role")
            if not name or not role or not EMAIL_RE.fullmatch(email):
                raise TaskUpdateError(f"{section}.upsert[{index}] requires name, role, and a valid email")
            if section == "raci" and not RACI_ROLE_RE.fullmatch(role.upper()):
                raise TaskUpdateError(f"raci.upsert[{index}].role must contain only R/A/C/I")
        remove = (changes or {}).get("remove", [])
        if not isinstance(remove, list) or any(not EMAIL_RE.fullmatch(str(value).strip().lower()) for value in remove):
            raise TaskUpdateError(f"{section}.remove must be an array of valid email addresses")

    notes = update.get("notes", {})
    if notes is not None and not isinstance(notes, dict):
        raise TaskUpdateError("notes must be an object")
    additions = (notes or {}).get("add", [])
    if not isinstance(additions, list) or any(not _clean_inline(value, "notes.add") for value in additions):
        raise TaskUpdateError("notes.add must be an array of non-empty one-line strings")

    tag_changed = any((tags or {}).get(key) for key in ("add", "remove"))
    contact_changed = any(
        (update.get(section) or {}).get(key)
        for section in ("contacts", "raci")
        for key in ("upsert", "remove")
    )
    expected_changes = {
        "scope": "Scope" in (fields or {}),
        "exclude": "Exclude" in (fields or {}),
        "tags": tag_changed,
        "contacts": contact_changed,
    }
    for key, has_change in expected_changes.items():
        state = matching_review[key]
        if has_change and state != "updated":
            raise TaskUpdateError(f"matching_review.{key} must be updated when its metadata changes")
        if state == "updated" and not has_change:
            raise TaskUpdateError(f"matching_review.{key}=updated requires a corresponding metadata change")
    identifier_changed = "EPD" in (fields or {})
    if identifier_changed and matching_review["identifiers"] != "updated":
        raise TaskUpdateError("matching_review.identifiers must be updated when EPD changes")
    if matching_review["identifiers"] == "updated" and not (identifier_changed or tag_changed):
        raise TaskUpdateError(
            "matching_review.identifiers=updated requires an EPD or identifier-tag change"
        )


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


def _ensure_asks(lines: list[str]) -> list[str]:
    if _section_bounds(lines, "## Asks"):
        asks_start, asks_end = _section_bounds(lines, "## Asks") or (0, 0)
        section = lines[asks_start:asks_end]
        insertion = asks_end
        if not any(line.strip() == "### My Actions" for line in section):
            lines[insertion:insertion] = ["", "### My Actions"]
            insertion += 2
        asks_start, asks_end = _section_bounds(lines, "## Asks") or (0, len(lines))
        section = lines[asks_start:asks_end]
        if not any(line.strip() == "### Waiting on Others" for line in section):
            lines[asks_end:asks_end] = ["", "### Waiting on Others"]
        return lines

    timeline = _section_bounds(lines, "## Timeline")
    insert_at = timeline[0] if timeline else len(lines)
    block = ["## Asks", "", "### My Actions", "", "### Waiting on Others", ""]
    if insert_at > 0 and lines[insert_at - 1].strip():
        block.insert(0, "")
    lines[insert_at:insert_at] = block
    return lines


def _insert_after_heading(lines: list[str], heading: str, line: str) -> None:
    bounds = _section_bounds(lines, heading)
    if not bounds:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([heading, line])
        return
    lines.insert(bounds[0] + 1, line)


def _due_token(raw: str) -> str:
    due = raw.strip() or "TBD"
    if due.startswith("{") and due.endswith("}"):
        return due
    if due.lower().startswith("due:"):
        due = due.split(":", 1)[1].strip()
    return f"{{Due: {due}}}"


def _ask_line(kind: str, item: dict) -> str:
    due = _due_token(str(item.get("due", "TBD")))
    contact = _clean_inline(item.get("contact", ""), "ask.contact")
    text = _clean_inline(item.get("text"), "ask.text")
    if kind == "my":
        target = f"to {contact}: " if contact else ""
        return f"- [ ] {due} 🎯 {target}{text}"
    target = f"{contact}: " if contact else ""
    return f"- {due} ⏳ {target}{text}"


def _add_unique_to_subsection(lines: list[str], heading: str, new_line: str) -> bool:
    bounds = _section_bounds(lines, heading)
    if not bounds:
        raise TaskUpdateError(f"Missing subsection {heading}")
    normalized = re.sub(r"\s+", " ", new_line).strip().lower()
    for existing in lines[bounds[0] + 1:bounds[1]]:
        if re.sub(r"\s+", " ", existing).strip().lower() == normalized:
            return False
    lines.insert(bounds[0] + 1, new_line)
    return True


def _find_unique_line(lines: list[str], heading: str, needle: str) -> int:
    """Return the one line in `heading` containing `needle`; reject zero or several matches.

    A silent miss would let a plan claim an ask was closed when nothing changed.
    """
    bounds = _section_bounds(lines, heading)
    if not bounds:
        raise TaskUpdateError(f"'{needle}' cannot be matched: section {heading} not found")
    matches = [index for index in range(bounds[0] + 1, bounds[1]) if needle.lower() in lines[index].lower()]
    if len(matches) > 1:
        raise TaskUpdateError(f"'{needle}' matched multiple lines in {heading}")
    if not matches:
        raise TaskUpdateError(f"'{needle}' matched no line in {heading}; use a fragment of the existing text")
    return matches[0]


FIELD_ORDER = ["Status", "Created", "Completed", "Priority", "Category", "Geo", "Due", "EPD", "Scope", "Exclude", "Recurring Task ID"]


def _set_header_field(lines: list[str], field: str, value: str) -> bool:
    pattern = re.compile(rf"^\*\*{re.escape(field)}:\*\*.*$")
    matches = [index for index, line in enumerate(lines) if pattern.match(line)]
    replacement = f"**{field}:** {value}"
    if len(matches) > 1:
        raise TaskUpdateError(f"Expected at most one **{field}:** field")
    if matches:
        if lines[matches[0]] == replacement:
            return False
        lines[matches[0]] = replacement
        return True

    target_order = FIELD_ORDER.index(field)
    for later in FIELD_ORDER[target_order + 1:]:
        later_pattern = re.compile(rf"^\*\*{re.escape(later)}:\*\*")
        for index, line in enumerate(lines):
            if later_pattern.match(line):
                lines.insert(index, replacement)
                return True
    insert_at = next(
        (index for index, line in enumerate(lines) if line.strip() == "---" or line.startswith("## ")),
        len(lines),
    )
    lines.insert(insert_at, replacement)
    return True


def _ensure_section(lines: list[str], heading: str, *, before: str | None = None) -> tuple[int, int]:
    bounds = _section_bounds(lines, heading)
    if bounds:
        return bounds
    insert_at = len(lines)
    if before:
        before_bounds = _section_bounds(lines, before)
        if before_bounds:
            insert_at = before_bounds[0]
    block = [heading, ""]
    if insert_at > 0 and lines[insert_at - 1].strip():
        block.insert(0, "")
    lines[insert_at:insert_at] = block
    bounds = _section_bounds(lines, heading)
    if not bounds:
        raise TaskUpdateError(f"Could not create section {heading}")
    return bounds


def _apply_tags(lines: list[str], changes: dict) -> bool:
    if not any(changes.get(key) for key in ("add", "remove")):
        return False
    start, end = _ensure_section(lines, "## Tags", before="## Asks")
    existing = []
    for line in lines[start + 1:end]:
        existing.extend(re.findall(r"`([^`]+)`", line))
    remove = {str(value).strip().lower() for value in changes.get("remove", [])}
    result = [value for value in existing if value.lower() not in remove]
    known = {value.lower() for value in result}
    for value in changes.get("add", []):
        clean = str(value).strip()
        if clean.lower() not in known:
            result.append(clean)
            known.add(clean.lower())
    if not result:
        raise TaskUpdateError("A task must contain at least 1 tag")
    if len(result) > 4:
        raise TaskUpdateError("A task may contain at most 4 tags")
    if any("`" in value or "\n" in value or "\r" in value for value in result):
        raise TaskUpdateError("Tags must be one-line values without backticks")
    replacement = ", ".join(f"`{value}`" for value in result)
    old = lines[start + 1:end]
    new = [replacement, ""] if replacement else [""]
    if old == new:
        return False
    lines[start + 1:end] = new
    return True


def _apply_contacts(lines: list[str], changes: dict) -> bool:
    if not any(changes.get(key) for key in ("upsert", "remove")):
        return False
    start, end = _ensure_section(lines, "## Contacts", before="## Stakeholders")
    changed = False
    remove = {str(value).strip().lower() for value in changes.get("remove", [])}
    for index in range(end - 1, start, -1):
        line_lower = lines[index].lower()
        if any(email in line_lower for email in remove):
            lines.pop(index)
            changed = True
    for item in changes.get("upsert", []):
        email = str(item["email"]).strip().lower()
        replacement = f"- **{item['role'].strip()}:** {item['name'].strip()} <{email}>"
        start, end = _section_bounds(lines, "## Contacts") or (start, len(lines))
        matches = [index for index in range(start + 1, end) if email in lines[index].lower()]
        if len(matches) > 1:
            raise TaskUpdateError(f"Contact email appears multiple times: {email}")
        if matches:
            if lines[matches[0]] != replacement:
                lines[matches[0]] = replacement
                changed = True
        else:
            lines.insert(start + 1, replacement)
            changed = True
    return changed


def _ensure_raci_section(lines: list[str]) -> tuple[int, int]:
    bounds = _section_bounds(lines, "### RACI Matrix")
    if bounds:
        return bounds
    stakeholder_bounds = _ensure_section(lines, "## Stakeholders", before="## Tags")
    insert_at = stakeholder_bounds[0] + 1
    block = [
        "",
        "### RACI Matrix",
        "",
        "| Stakeholder | Role |",
        "|-------------|------|",
        "",
    ]
    lines[insert_at:insert_at] = block
    bounds = _section_bounds(lines, "### RACI Matrix")
    if not bounds:
        raise TaskUpdateError("Could not create RACI Matrix")
    return bounds


def _apply_raci(lines: list[str], changes: dict) -> bool:
    if not any(changes.get(key) for key in ("upsert", "remove")):
        return False
    start, end = _ensure_raci_section(lines)
    changed = False
    remove = {str(value).strip().lower() for value in changes.get("remove", [])}
    for index in range(end - 1, start, -1):
        line_lower = lines[index].lower()
        if any(email in line_lower for email in remove):
            lines.pop(index)
            changed = True
    for item in changes.get("upsert", []):
        email = str(item["email"]).strip().lower()
        role = str(item["role"]).strip().upper()
        replacement = f"| {item['name'].strip()} <{email}> | {role} |"
        start, end = _section_bounds(lines, "### RACI Matrix") or (start, len(lines))
        matches = [index for index in range(start + 1, end) if email in lines[index].lower()]
        if len(matches) > 1:
            raise TaskUpdateError(f"RACI email appears multiple times: {email}")
        if matches:
            if lines[matches[0]] != replacement:
                lines[matches[0]] = replacement
                changed = True
        else:
            separator = next(
                (index for index in range(start + 1, end) if re.match(r"^\|[-:| ]+\|$", lines[index])),
                None,
            )
            lines.insert((separator + 1) if separator is not None else start + 1, replacement)
            changed = True
    return changed


def _apply_notes(lines: list[str], additions: list[str]) -> bool:
    if not additions:
        return False
    start, end = _ensure_section(lines, "## Notes")
    existing = {
        re.sub(r"\s+", " ", line.removeprefix("- ")).strip().lower()
        for line in lines[start + 1:end]
        if line.strip()
    }
    changed = False
    for value in additions:
        clean = str(value).strip()
        normalized = re.sub(r"\s+", " ", clean).lower()
        if normalized not in existing:
            lines.insert(start + 1, f"- {clean}")
            existing.add(normalized)
            changed = True
    return changed


def plan_task_update(content: str, update: dict) -> tuple[str, dict]:
    validate_task_update(update)
    lines = content.splitlines()
    changes: list[str] = []
    source = update["source"]
    entry_id = source["entry_id"].strip()
    conversation_id = str(source.get("conversation_id", "")).strip()

    timeline = update.get("timeline")
    if timeline:
        marker = f"<!-- email:{entry_id} -->"
        if marker not in content:
            date_text = format_task_date(source["received_at"])
            conversation_marker = f" <!-- conversation:{conversation_id} -->" if conversation_id else ""
            line = f"- **{date_text}** [{timeline['tag']}] {timeline['summary'].strip()} {marker}{conversation_marker}"
            _insert_after_heading(lines, "## Timeline", line)
            changes.append(f"+Timeline {date_text} [{timeline['tag']}]")

    asks = update.get("asks") or {}
    if any(asks.get(key) for key in ("add_my_actions", "add_waiting", "complete_my_actions", "remove_waiting")):
        lines = _ensure_asks(lines)
    for item in asks.get("add_my_actions", []):
        if _add_unique_to_subsection(lines, "### My Actions", _ask_line("my", item)):
            changes.append("+Ask My Actions")
    for item in asks.get("add_waiting", []):
        if _add_unique_to_subsection(lines, "### Waiting on Others", _ask_line("waiting", item)):
            changes.append("+Ask Waiting on Others")
    for needle in asks.get("complete_my_actions", []):
        index = _find_unique_line(lines, "### My Actions", needle)
        if "[ ]" in lines[index]:
            lines[index] = lines[index].replace("[ ]", "[x]", 1)
            changes.append(f"✅ Ask completed: {needle}")
    for needle in asks.get("remove_waiting", []):
        index = _find_unique_line(lines, "### Waiting on Others", needle)
        lines.pop(index)
        changes.append(f"-Waiting resolved: {needle}")

    current_state = update.get("current_state") or {}
    for item in current_state.get("add", []):
        text = _clean_inline(item, "current_state.add")
        line = f"- [ ] {text}"
        if _add_unique_to_subsection(lines, "## Current State", line):
            changes.append("+Current State")
    for needle in current_state.get("complete", []):
        index = _find_unique_line(lines, "## Current State", needle)
        if "[ ]" in lines[index]:
            lines[index] = lines[index].replace("[ ]", "[x]", 1)
            changes.append(f"✅ State: {needle}")

    fields = update.get("fields") or {}
    for field, value in fields.items():
        if field not in SUPPORTED_FIELDS:
            raise TaskUpdateError(f"Unsupported task field: {field}")
        new_value = _clean_inline(value, f"fields.{field}")
        if _set_header_field(lines, field, new_value):
            changes.append(f"Field {field}")

    if _apply_tags(lines, update.get("tags") or {}):
        changes.append("Tags")
    if _apply_contacts(lines, update.get("contacts") or {}):
        changes.append("Contacts")
    if _apply_raci(lines, update.get("raci") or {}):
        changes.append("RACI")
    if _apply_notes(lines, (update.get("notes") or {}).get("add", [])):
        changes.append("Notes")

    updated = "\n".join(lines).rstrip() + "\n"
    return updated, {"updated": updated != content, "changes": changes}


def atomic_write_text(path: Path, text: str) -> None:
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def apply_structured_task_update(task_file: Path, update: dict) -> dict:
    original = task_file.read_text(encoding="utf-8")
    updated, report = plan_task_update(original, update)
    if report["updated"]:
        atomic_write_text(task_file, updated)
    return {"task": task_file.name, **report}


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply one validated email-sourced task update")
    parser.add_argument("--task", required=True)
    parser.add_argument("--entry-id", required=True)
    parser.add_argument("--conversation-id", default="")
    parser.add_argument("--received-at", required=True)
    parser.add_argument("--direction", choices=["in", "out", "calendar"], required=True)
    parser.add_argument("--timeline")
    parser.add_argument("--tag", choices=sorted(VALID_TIMELINE_TAGS))
    parser.add_argument("--ask-my-action")
    parser.add_argument("--ask-waiting")
    args = parser.parse_args()

    if bool(args.timeline) != bool(args.tag):
        parser.error("--timeline and --tag must be supplied together")
    update = {
        "task": args.task,
        "source": {
            "entry_id": args.entry_id,
            "conversation_id": args.conversation_id,
            "received_at": args.received_at,
            "direction": args.direction,
        },
        "timeline": {"tag": args.tag, "summary": args.timeline} if args.timeline else None,
        "asks": {
            "add_my_actions": ([{"due": "TBD", "contact": "", "text": args.ask_my_action}]
                               if args.ask_my_action else []),
            "add_waiting": ([{"due": "TBD", "contact": "", "text": args.ask_waiting}]
                            if args.ask_waiting else []),
        },
        "matching_review": {
            "scope": "checked-no-change",
            "exclude": "checked-no-change",
            "tags": "checked-no-change",
            "contacts": "checked-no-change",
            "identifiers": "checked-no-change",
        },
    }
    try:
        task_file = find_task_file(args.task)
        result = apply_structured_task_update(task_file, update)
    except (OSError, TaskUpdateError, FileNotFoundError) as exc:
        print(f"Error updating task: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
