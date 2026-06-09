"""BrainClaw follow-up automation — scans for stale tasks and outputs structured data for follow-up drafting."""

import sys
import io
import os
import re
import json
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from shared_config import BRAIN_DIR, PROJECT_ROOT, STALE_THRESHOLDS, PROCESS_MATCH_RULES, safe_read


def parse_queue_tasks(content: str) -> list:
    tasks = []
    task_heading = re.compile(
        r'^(##|### ↳)\s+T(\d+)\s+(📋|⏳|🔴)\s+(.+?)\s+\[`?([^`\]]+)`?\]\(([^)]+)\)'
    )
    current = None

    for line in content.split('\n'):
        m = task_heading.match(line)
        if m:
            current = {
                "id": f"T{m.group(2)}",
                "title": m.group(4).strip(),
                "status_icon": m.group(3),
                "path": m.group(6).replace('./', 'assistant_brain/tasks/'),
                "priority": "",
                "geo": "",
                "category": "",
                "due": "",
                "is_subtask": m.group(1) == "### ↳",
            }
            tasks.append(current)
            continue

        if current and line.startswith('- **'):
            kv = re.match(r'^- \*\*(.+?):\*\*\s*(.+)$', line)
            if kv:
                key, val = kv.group(1), kv.group(2).strip()
                if key == "Priority":
                    current["priority"] = val
                elif key == "Geo":
                    current["geo"] = val
                elif key == "Due":
                    current["due"] = val

    return tasks


def parse_task_file(content: str) -> dict:
    """Extract timeline, asks, category, and current state from a task file."""
    result = {
        "category": "",
        "geo": "",
        "last_timeline_date": None,
        "timeline_entries": [],
        "asks_in": [],
        "asks_out": [],
        "current_state_items": [],
        "contacts": [],
    }

    lines = content.split('\n')
    section = None

    for line in lines:
        # Header fields
        cat_m = re.match(r'^\*\*Category:\*\*\s*(.+)$', line)
        if cat_m:
            result["category"] = cat_m.group(1).strip()
            continue

        geo_m = re.match(r'^\*\*Geo:\*\*\s*(.+)$', line)
        if geo_m:
            result["geo"] = geo_m.group(1).strip()
            continue

        # Section tracking
        if line.strip() == '## Timeline':
            section = 'timeline'
            continue
        elif line.strip() == '### Owed to me':
            section = 'asks_in'
            continue
        elif line.strip() == '### Owed by me':
            section = 'asks_out'
            continue
        elif line.strip() == '## Current State':
            section = 'current_state'
            continue
        elif line.strip() == '## Contacts':
            section = 'contacts'
            continue
        elif line.startswith('## ') or line.strip() == '---':
            if section:
                section = None
            continue

        # Parse timeline entries
        if section == 'timeline':
            tm = re.match(r'^- \*\*(\d{4}-\d{2}-\d{2})\*\*\s*\[(.+?)\]:?\s*(.+)$', line)
            if not tm:
                tm = re.match(r'^- \*\*(\d{4}-\d{2}-\d{2})\*\*\s+(.+)$', line)
                if tm:
                    result["timeline_entries"].append({
                        "date": tm.group(1),
                        "tag": "",
                        "description": tm.group(2),
                    })
            else:
                result["timeline_entries"].append({
                    "date": tm.group(1),
                    "tag": tm.group(2),
                    "description": tm.group(3),
                })

        # Parse owed-to-me asks
        elif section == 'asks_in':
            if line.strip().startswith('- ~~'):
                continue
            am = re.match(r'^- (.+?) ← (.+?): (.+)$', line)
            if am:
                result["asks_in"].append({
                    "date": am.group(1).strip(),
                    "person": am.group(2).strip(),
                    "what": am.group(3).strip(),
                })

        # Parse owed-by-me asks
        elif section == 'asks_out':
            if line.strip().startswith('- ~~') or line.strip().startswith('- [x]'):
                continue
            am = re.match(r'^- \[.\]\s*(.+?) → (.+?): (.+)$', line)
            if am:
                result["asks_out"].append({
                    "date": am.group(1).strip(),
                    "person": am.group(2).strip(),
                    "what": am.group(3).strip(),
                })

        # Parse current state
        elif section == 'current_state':
            cs_checked = re.match(r'^- \[(x|✅)\]\s+(.+)$', line)
            cs_unchecked = re.match(r'^- \[( |⏳)\]\s+(.+)$', line)
            if cs_checked:
                result["current_state_items"].append({"done": True, "text": cs_checked.group(2)})
            elif cs_unchecked:
                result["current_state_items"].append({"done": False, "text": cs_unchecked.group(2)})

        # Parse contacts
        elif section == 'contacts':
            cm = re.match(r'^- \*\*(.+?):\*\*\s*(.+?)(?:\s*\((.+?)\))?$', line)
            if cm:
                name_email = cm.group(2).strip()
                email_m = re.search(r'<(.+?)>|\((.+?@.+?)\)', name_email)
                email = email_m.group(1) or email_m.group(2) if email_m else ""
                name = re.sub(r'\s*[<(].+?[>)]', '', name_email).strip()
                result["contacts"].append({
                    "role": cm.group(1).strip(),
                    "name": name,
                    "email": email,
                })

    # Determine last timeline date
    if result["timeline_entries"]:
        result["last_timeline_date"] = result["timeline_entries"][-1]["date"]

    return result


def match_process(category: str, geo: str) -> str | None:
    cat_lower = category.lower() if category else ""
    geo_lower = geo.lower() if geo else ""

    for rule in PROCESS_MATCH_RULES:
        if rule["geo"] and rule["geo"].lower() != geo_lower:
            continue
        if any(kw in cat_lower for kw in rule["keywords"]):
            return rule["file"]

    return None


def get_process_step_info(process_file: str, current_state: list) -> dict | None:
    process_path = BRAIN_DIR / 'process' / process_file
    content = safe_read(process_path)
    if not content:
        return None

    steps = []
    in_steps = False
    for line in content.split('\n'):
        if line.strip() == '## Steps':
            in_steps = True
            continue
        if in_steps and line.startswith('## '):
            break
        if in_steps:
            sm = re.match(r'^\d+\.\s+\*\*(.+?)\*\*\s*[—–-]\s*(.+)$', line)
            if sm:
                steps.append({"name": sm.group(1), "description": sm.group(2)})

    if not steps:
        return None

    # Determine current step from current_state checkboxes
    completed_count = sum(1 for item in current_state if item["done"])
    current_step_idx = min(completed_count, len(steps) - 1)

    return {
        "total_steps": len(steps),
        "current_step": current_step_idx + 1,
        "step_name": steps[current_step_idx]["name"],
        "step_description": steps[current_step_idx]["description"],
    }


def find_stale_tasks(today: date, target_task: str = None) -> list:
    queue_path = BRAIN_DIR / 'tasks' / 'queue.md'
    queue_content = safe_read(queue_path)
    if not queue_content:
        print("ERROR: Cannot read tasks/queue.md", file=sys.stderr)
        return []

    queue_tasks = parse_queue_tasks(queue_content)
    results = []

    for qt in queue_tasks:
        # Skip if targeting a specific task
        if target_task and qt["id"] != target_task:
            continue

        task_file = PROJECT_ROOT / qt["path"]
        content = safe_read(task_file)
        if not content:
            continue

        parsed = parse_task_file(content)
        priority = qt["priority"] or "P3"
        threshold = STALE_THRESHOLDS.get(priority, 10)

        # Calculate days since last activity
        last_date_str = parsed["last_timeline_date"]
        if not last_date_str:
            continue

        try:
            last_date = date.fromisoformat(last_date_str)
        except ValueError:
            continue

        days_inactive = (today - last_date).days

        # For targeted task, skip stale check
        if not target_task and days_inactive <= threshold:
            continue

        # Build result
        entry = {
            "task_id": qt["id"],
            "title": qt["title"],
            "path": qt["path"],
            "priority": priority,
            "geo": qt["geo"],
            "days_inactive": days_inactive,
            "threshold": threshold,
            "last_activity": last_date_str,
        }

        # All pending asks owed to me
        if parsed["asks_in"]:
            entry["waiting_on"] = []
            for ask in parsed["asks_in"]:
                ask_date = ask["date"]
                try:
                    ask_days = (today - date.fromisoformat(ask_date)).days
                except ValueError:
                    ask_days = None
                entry["waiting_on"].append({
                    "person": ask["person"],
                    "ask": ask["what"],
                    "since": ask_date,
                    "days_waiting": ask_days,
                })

        # Process step info
        category = parsed["category"] or qt.get("category", "")
        geo = parsed["geo"] or qt["geo"]
        process_file = match_process(category, geo)

        if process_file:
            step_info = get_process_step_info(process_file, parsed["current_state_items"])
            if step_info:
                entry["process_step"] = f"Step {step_info['current_step']}/{step_info['total_steps']}: {step_info['step_description']}"
                entry["process_file"] = process_file

        # All pending actions I owe (from asks_out)
        if parsed["asks_out"]:
            entry["owed_by_me"] = []
            for ask in parsed["asks_out"]:
                out_date = ask["date"]
                try:
                    out_days = (today - date.fromisoformat(out_date)).days
                except ValueError:
                    out_days = None
                entry["owed_by_me"].append({
                    "person": ask["person"],
                    "ask": ask["what"],
                    "since": out_date,
                    "days_pending": out_days,
                })

        # Suggested recipient: prioritize asks_out (action I need to take)
        # over asks_in (chase someone else) — action items are more urgent
        if entry.get("owed_by_me"):
            entry["suggested_recipient"] = entry["owed_by_me"][0]["person"]
            entry["action_type"] = "owed_by_me"
        elif entry.get("waiting_on"):
            entry["suggested_recipient"] = entry["waiting_on"][0]["person"]
            entry["action_type"] = "waiting_on"
        elif parsed["contacts"]:
            for c in parsed["contacts"]:
                if c["role"] not in ("Requester",):
                    entry["suggested_recipient"] = c["name"]
                    if c["email"]:
                        entry["suggested_email"] = c["email"]
                    entry["action_type"] = "contact"
                    break

        results.append(entry)

    # Sort by priority (P1 first), then by days_inactive descending
    priority_order = {"P1": 0, "P2": 1, "P3": 2}
    results.sort(key=lambda x: (priority_order.get(x["priority"], 9), -x["days_inactive"]))

    return results


def main():
    parser = argparse.ArgumentParser(description='BrainClaw follow-up scanner')
    parser.add_argument('--task', type=str, help='Focus on a specific task (e.g., T041)')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Output JSON only (default)')
    args = parser.parse_args()

    today = date.today()
    results = find_stale_tasks(today, target_task=args.task)

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
