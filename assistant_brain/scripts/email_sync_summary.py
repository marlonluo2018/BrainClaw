"""Render the deterministic skeleton of the email-sync summary.

Generates every part of EMAIL_SYNC_FORMAT.md that follows mechanically from
latest-applied.json and the task files (geo grouping, Updated blocks, email
lines, open asks, ignored table, stale tasks, sync audit), and leaves
{{placeholder}} markers where the classifier must add semantic content
(email one-line summaries, non-task suggestions, priority-action ordering).

Usage:
    py -3 assistant_brain/scripts/email_sync_summary.py
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from followup import find_stale_tasks, parse_task_file
from shared_config import BRAIN_DIR, configure_utf8_stdio, safe_read, _parse_date_field

configure_utf8_stdio()

SYNC_RESULTS_DIR = BRAIN_DIR / "sync_results"
DEFAULT_APPLIED_FILE = SYNC_RESULTS_DIR / "latest-applied.json"
DEFAULT_CANDIDATES_FILE = SYNC_RESULTS_DIR / "latest-candidates.json"
FLAG_MAP = {
    "China": "🇨🇳",
    "Philippines": "🇵🇭",
    "India": "🇮🇳",
    "Singapore": "🇸🇬",
    "Global": "🌐",
}

ASK_MY_ACTION = re.compile(r"^- \[.\]\s*\{Due: ([^}]+)\}\s*🎯 (?:(?:to )?(.+?): )?(.+)$")
ASK_WAITING = re.compile(r"^- \{Due: ([^}]+)\}\s*⏳ (.+?): (.+)$")


def _display_date(raw: str) -> str:
    parsed = _parse_date_field(raw)
    if parsed:
        return parsed.strftime("%a %b %d, %Y")
    return raw


def _due_label(due: str, today: date) -> str:
    parsed = _parse_date_field(due)
    if not parsed:
        return due or "TBD"
    if parsed < today:
        return f"{parsed.isoformat()} ({(today - parsed).days}d overdue)"
    return f"{parsed.isoformat()} (in {(parsed - today).days}d)"


def _ask_age(due: str, today: date) -> str | None:
    parsed = _parse_date_field(due)
    return f"{(today - parsed).days}d" if parsed and parsed < today else None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _email_lines(entry_ids: set[str], candidates: dict[str, dict[str, Any]]) -> list[str]:
    lines = []
    for number in sorted(candidates):
        email = candidates[number]
        if email["entry_id"] not in entry_ids:
            continue
        arrow = "←" if email["direction"] == "out" else "→"
        target = email.get("sender", "") if arrow == "→" else _first_recipient(email)
        when = email["received_time"][:16].replace("T", " ")
        lines.append(f"{arrow} #{number} — {when} — {target}: {{{{summary #{number}}}}}")
    return lines


def _first_recipient(email: dict[str, Any]) -> str:
    recipients = email.get("to_recipients") or []
    if recipients:
        return recipients[0].get("name") or recipients[0].get("address") or ""
    return email.get("sender", "")


def _task_actions(parsed: dict[str, Any], today: date) -> list[str]:
    lines = []
    for ask in parsed["asks_out"]:
        due, person, what = ask["date"], ask["person"], ask["what"]
        age = _ask_age(due, today)
        urgency = f"ask: {age} ago" if age else _due_label(due, today)
        contact = f" — Contact: {person}" if person and person != "Me" else ""
        lines.append(f"🎯 {what}{contact} | {urgency}")
    for ask in parsed["asks_in"]:
        due, person, what = ask["date"], ask["person"], ask["what"]
        age = _ask_age(due, today)
        urgency = f"ask: {age} ago" if age else _due_label(due, today)
        lines.append(f"⏳ {what} — Contact: {person} | {urgency}")
    return lines


def _parse_open_asks(content: str) -> dict[str, Any]:
    """Extract open asks with due-brace support, reusing followup section logic."""
    result = {"asks_in": [], "asks_out": [], "last_timeline_date": None}
    section = None
    for line in content.splitlines():
        if line.strip() in ("### Owed to me", "### Waiting on Others"):
            section = "asks_in"
            continue
        if line.strip() in ("### Owed by me", "### My Actions"):
            section = "asks_out"
            continue
        if line.startswith("## ") or line.strip() == "---":
            if section:
                section = None
            continue
        if line.strip().startswith("- ~~") or line.strip().startswith(("- [x]", "- [✅]")):
            continue
        if section == "asks_in":
            match = ASK_WAITING.match(line)
            if match:
                result["asks_in"].append(
                    {"date": match.group(1).strip(), "person": match.group(2).strip(), "what": match.group(3).strip()}
                )
        elif section == "asks_out":
            match = ASK_MY_ACTION.match(line)
            if match:
                result["asks_out"].append(
                    {
                        "date": match.group(1).strip(),
                        "person": (match.group(2) or "Me").strip(),
                        "what": match.group(3).strip(),
                    }
                )

    timeline_match = re.search(
        r"^## Timeline\s*\n(.*?)(?=^## |\Z)", content, re.MULTILINE | re.DOTALL
    )
    if timeline_match:
        dates = re.findall(r"^- \*\*(\d{4}-\d{2}-\d{2})\*\*", timeline_match.group(1), re.MULTILINE)
        if dates:
            result["last_timeline_date"] = dates[0]
    return result


def build_summary(applied: dict[str, Any], candidates: dict[str, Any], today: date) -> str:
    by_entry = {e["entry_id"]: e for e in candidates.get("emails", [])}
    number_by_entry = {e["entry_id"]: e["number"] for e in candidates.get("emails", [])}
    email_by_number = {e["number"]: e for e in candidates.get("emails", [])}

    # ---- task sections grouped by geo -------------------------------------
    updates_by_task: dict[str, list[dict[str, Any]]] = {}
    for update in applied.get("task_updates", []):
        updates_by_task.setdefault(update["task"], []).append(update)

    catalog_by_task = {t["task"]: t for t in candidates.get("task_catalog", [])}
    evaluated = {item["task"]: item for item in applied.get("evaluated_tasks", [])}

    # Only tasks with at least one linked email (matched, not rejected) appear.
    task_geo: dict[str, list[str]] = {}
    task_blocks: dict[str, list[str]] = {}
    for task_id in sorted(updates_by_task):
        entry_ids = {u["entry_id"] for u in updates_by_task[task_id]}
        catalog = catalog_by_task.get(task_id)
        if not catalog:
            continue
        geo = catalog.get("geo") or "Other"
        task_geo.setdefault(geo, []).append(task_id)

        evaluated_report = evaluated.get(task_id, {})
        applied_changes = evaluated_report.get("changes", [])
        content = safe_read(BRAIN_DIR.parent / catalog["path"])
        parsed = _parse_open_asks(content) if content else {"asks_in": [], "asks_out": []}
        parsed_last_activity = None
        if content:
            full = parse_task_file(content)
            parsed_last_activity = full.get("last_timeline_date")

        lines = [f"**[{task_id}]({catalog['path']}) {catalog['title']}** | Due: {catalog['due'] or 'TBD'} | Last activity: {parsed_last_activity or '{{last activity ' + task_id + '}}'}", ""]
        if applied_changes:
            lines.append("Updated:")
            lines.extend(f"- {change}" for change in applied_changes)
        else:
            lines.append("Updated: no changes — already up to date.")
        email_lines = _email_lines(entry_ids, email_by_number)
        if email_lines:
            lines.append("")
            lines.append("Emails:")
            lines.extend(f"- {line}" for line in email_lines)
        action_lines = _task_actions(parsed, today)
        if action_lines:
            lines.append("")
            lines.append("Actions:")
            lines.extend(f"- {line}" for line in action_lines)
        elif not parsed["asks_in"] and not parsed["asks_out"]:
            lines.append("")
            lines.append("Actions:")
            lines.append("- ⚠️ No next step recorded — please tell me what this task is waiting on.")
        task_blocks.setdefault(geo, []).append("\n".join(lines))

    out: list[str] = []
    snapshot = candidates.get("snapshot", {})
    fetched = str(snapshot.get("fetched_at") or "")[:10]
    out.append(f"## Email Sync Summary ({fetched} snapshot) — {len(candidates.get('emails', []))} emails")
    out.append("")
    for geo in sorted(task_geo):
        out.append(f"### {FLAG_MAP.get(geo, '🌐')} {geo}")
        out.append("")
        blocks = task_blocks[geo]
        out.append("\n\n&nbsp;\n\n".join(blocks))
        out.append("")

    # ---- unresolved (non-task) emails -------------------------------------
    unresolved = applied.get("unresolved", [])
    out.append("---")
    out.append("")
    out.append("### ❌ Non-Task Emails")
    out.append("")
    if unresolved:
        out.append("**Action needed (requires user action; some are small one-offs, some are big tasks):**")
        for item in unresolved:
            number = number_by_entry.get(item["entry_id"], "?")
            email = by_entry.get(item["entry_id"], {})
            arrow = "←" if email.get("direction") == "out" else "→"
            when = str(email.get("received_time") or "")[:16].replace("T", " ")
            sender = email.get("sender", "")
            out.append("")
            out.append(f"- {arrow} #{number} — {when} — {sender}: {{{{suggestion #{number}}}}}")
            out.append(f"  - 🎯/⏳ Suggested: {{{{suggestion #{number}}}}}")
            out.append(f"  - 💡 Create task? {{{{create-task #{number}}}}}")
    else:
        out.append("*No unresolved emails this run.*")
    out.append("")

    # ---- ignored / filtered ------------------------------------------------
    out.append("---")
    out.append("")
    out.append("### 🚫 Ignored / Filtered Emails")
    out.append("")
    ignored = applied.get("ignored", [])
    out.append(
        "**Ignored Emails (Informational — read by AI and judged as requiring no action/task; taken from `latest-applied.json`):**"
    )
    if ignored:
        out.append("| # | Sender | Subject | Reason | Entry ID |")
        out.append("|---|--------|---------|--------|----------|")
        for item in ignored:
            number = number_by_entry.get(item["entry_id"], "?")
            out.append(
                f"| **#{number}** | {item.get('sender', '')} | `{item.get('subject', '')}` "
                f"| {item.get('reason', '')} | `{item['entry_id']}` |"
            )
    else:
        out.append("*None this run.*")
    out.append("")
    out.append(
        "*How to restore (\"take it back\"):* `py -3 assistant_brain/scripts/manage_ignore_candidates.py restore <entry_id>` or tell the assistant \"restore email #X\"."
    )
    out.append("")
    filtered_count = sum(
        1 for e in candidates.get("emails", []) if e.get("review_status") == "filtered"
    )
    out.append(
        "**Filtered Emails (Silently filtered system noise — auto-replies, OTP passcodes, calendar reminders, generic system noise):**"
    )
    out.append(f"- Total: {filtered_count} emails filtered by script.")
    out.append("")

    # ---- process observations (semantic) -----------------------------------
    out.append("---")
    out.append("")
    out.append("### 📝 Process Observations")
    out.append("")
    out.append("{{process observations — only if new findings; else delete this section}}")
    out.append("")

    # ---- stale tasks --------------------------------------------------------
    stale = find_stale_tasks(today)
    out.append("---")
    out.append("")
    out.append("### ⚠️ Stale Tasks")
    out.append("")
    if stale:
        for entry in stale:
            out.append(
                f"- [{entry['task_id']}]({entry['path']}) {entry['title']} — {entry['days_inactive']}d no activity "
                f"({entry['priority']}, threshold {entry['threshold']}d) | stuck at: {{{{stale detail {entry['task_id']}}}}}"
            )
            for tl in entry.get("timeline_tail") or []:
                tag = f"[{tl['tag']}] " if tl.get("tag") else ""
                out.append(f"  - ⏱ {tl['date']} {tag}{tl['description']}")
            if entry.get("action_type") == "contact":
                out.append(f"  - ⚠️ No open ask recorded — key contact: {entry.get('suggested_recipient', 'n/a')}")
            elif entry.get("suggested_recipient"):
                # Show the full ask text, not just the person — the person field
                # can be truncated when the ask line lacks a "to Person:" prefix
                # (the parser then splits on the first colon inside the ask).
                ask = entry.get("suggested_ask") or ""
                suffix = f": {ask}" if ask else ""
                out.append(f"  - 🎯 Follow up: {entry['suggested_recipient']}{suffix}")
    else:
        out.append("*No tasks exceed their stale threshold.*")
    out.append("")

    # ---- priority actions (semantic) ---------------------------------------
    out.append("---")
    out.append("")
    out.append("### ✅ Priority Actions")
    out.append("")
    out.append("{{priority actions table — see EMAIL_SYNC_FORMAT.md rule 11}}")
    out.append("")

    # ---- sync audit ----------------------------------------------------------
    out.append("---")
    out.append("")
    out.append("### 📋 Sync Audit — Files Modified")
    out.append("")
    out.append("| File | Changes |")
    out.append("|------|---------|")
    modified = unchanged = 0
    for item in applied.get("evaluated_tasks", []):
        if item.get("updated"):
            modified += 1
            changes = "; ".join(item.get("changes", [])) or "no changes"
            out.append(f"| `{item['file']}` | {changes} |")
        else:
            unchanged += 1
            out.append(f"| `{item['file']}` | no changes |")
    audit = applied.get("audit", {})
    out.append("")
    out.append(
        f"Total: {modified} files modified, {unchanged} unchanged. "
        f"(Also: {audit.get('ignore_candidates_added', 0)} emails added to the incremental ignore pool; "
        f"{audit.get('unresolved_count', len(unresolved))} emails unresolved for user review.)"
    )
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the deterministic email-sync summary skeleton")
    parser.add_argument("--applied-file", default=str(DEFAULT_APPLIED_FILE))
    parser.add_argument("--candidates-file", default=str(DEFAULT_CANDIDATES_FILE))
    parser.add_argument("--output-file", default=None, help="Write the skeleton here instead of stdout")
    args = parser.parse_args()

    applied = _load_json(Path(args.applied_file))
    candidates = _load_json(Path(args.candidates_file))
    if str(applied.get("snapshot_id", "")) != str(candidates.get("snapshot_id", " ")):
        raise SystemExit(
            "applied snapshot_id does not match candidates snapshot_id — refusing to render"
        )

    today = datetime.now().date()
    summary = build_summary(applied, candidates, today)
    if args.output_file:
        Path(args.output_file).write_text(summary, encoding="utf-8")
        print(args.output_file)
    else:
        print(summary)


if __name__ == "__main__":
    main()
