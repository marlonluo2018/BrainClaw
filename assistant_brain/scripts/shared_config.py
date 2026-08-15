"""Shared configuration for BrainClaw scripts.

Source of truth for thresholds: ../views_config.md
If views_config.md changes, update this file to match.
"""

import re
from datetime import date, datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path


def _parse_date_field(raw: str):
    """Parse a date field value supporting both YYYY-MM-DD and Wkd Mon DD, YYYY formats."""
    raw = raw.strip()
    # Try ISO first
    m = re.match(r'(\d{4}-\d{2}-\d{2})', raw)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            pass
    # Try new format: Wkd Mon DD, YYYY
    m2 = re.match(r'[A-Z][a-z]{2} [A-Z][a-z]{2} \d{2}, \d{4}', raw)
    if m2:
        try:
            return datetime.strptime(m2.group(0), '%a %b %d, %Y').date()
        except ValueError:
            pass
    return None

BRAIN_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BRAIN_DIR.parent

# Staleness thresholds (days) — aligned with views_config.md
STALE_THRESHOLDS = {"P1": 3, "P2": 7, "P3": 14}

# Process matching rules — used by followup.py and dashboard.py.
# Single authoritative source: process/README.md index table.
# Parsed at import time; do NOT hardcode process mappings here.
def _build_process_match_rules() -> list:
    rules = []
    readme = BRAIN_DIR / 'process' / 'README.md'
    if not readme.exists():
        return rules
    current_geo = None
    for line in readme.read_text(encoding='utf-8').split('\n'):
        hdr = re.match(r'^##\s+(.+)$', line)
        if hdr:
            section = hdr.group(1).strip()
            current_geo = None if section == 'Global' else section
            continue
        m = re.match(r'^\|\s*([^|]+?)\s*\|\s*\[`([^`]+)`\]\(([^)]+)\)\s*\|\s*([^|]+)\|', line)
        if m:
            file_path = m.group(3).strip()
            keywords = [k.strip().lower() for k in m.group(4).split(',') if k.strip()]
            if file_path and keywords:
                rules.append({"keywords": keywords, "geo": current_geo, "file": file_path})
    return rules


PROCESS_MATCH_RULES = _build_process_match_rules()


# Timeline tag alias mapping — normalises legacy tags to canonical form
TAG_ALIASES = {
    "Email Sent": "email-out",
    "Email Forwarded": "email-out",
    "email sent": "email-out",
    "Email-out": "email-out",
    "Email Received": "email-in",
    "Email-in": "email-in",
    "email received": "email-in",
    "Email": "email-in",
    "Slack": "slack",
    "Slack-in": "slack",
    "slack-in": "slack",
    "Slack-out": "slack",
    "Slack from Tao Han": "slack",
    "Call/Meeting": "meeting",
    "Meeting": "meeting",
    "Meeting Scheduled": "meeting",
    "Update": "update",
    "Action": "update",
    "Task Created": "created",
    "Created": "created",
    "Decision": "decision",
    "Decision Received": "decision",
    "Completed": "milestone",
    "Completion": "milestone",
}


def normalize_tag(raw_tag: str) -> str:
    """Return canonical lowercase-kebab tag, resolving legacy aliases."""
    return TAG_ALIASES.get(raw_tag, raw_tag.lower())


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except (FileNotFoundError, UnicodeDecodeError):
        return ""


# --- Task scanning (replaces queue.md parsing) ---

EVENTS_WINDOW_DAYS = 14

STATUS_ICONS = {"Not Started": "📋", "In Progress": "⏳", "Blocked": "🔴"}
ICON_TO_STATUS = {"📋": "Not Started", "⏳": "In Progress", "🔴": "Blocked"}


@dataclass
class ScannedTask:
    id: str
    title: str
    status: str
    priority: str
    geo: str
    due: str
    path: str
    created: str = ""
    completed: str = ""
    parent: str = ""
    subtask_ids: list = field(default_factory=list)
    is_master: bool = False
    recurring_id: str = ""


@dataclass
class ScannedEvent:
    date_str: str
    icon: str
    description: str
    raw_line: str


def _parse_task_frontmatter(content: str, rel_path: str) -> ScannedTask | None:
    """Parse frontmatter fields from a task file."""
    title_m = re.match(r'^#\s+T(\d+):\s*(.+)$', content, re.MULTILINE)
    if not title_m:
        return None

    tid = f"T{title_m.group(1)}"
    title = title_m.group(2).strip()

    def field_val(name):
        m = re.search(rf'^\*\*{name}:\*\*\s*(.+)$', content, re.MULTILINE)
        return m.group(1).strip() if m else ""

    status_raw = field_val("Status")
    status = "Unknown"
    for icon, st in ICON_TO_STATUS.items():
        if icon in status_raw:
            status = st
            break
    if "✅" in status_raw:
        status = "Completed"

    parent_raw = field_val("Parent Task")
    parent = ""
    if parent_raw:
        pm = re.match(r'T?(\d+)', parent_raw)
        if pm:
            parent = f"T{pm.group(1)}"

    subtask_ids = []
    sub_raw = field_val("Subtasks")
    if sub_raw:
        subtask_ids = [f"T{x.strip().lstrip('T')}" for x in sub_raw.split(',') if x.strip()]

    is_master = "(Master)" in title

    recurring_id = field_val("Recurring Task ID")
    if recurring_id in ('—', ''):
        recurring_id = ""

    return ScannedTask(
        id=tid,
        title=title,
        status=status,
        priority=field_val("Priority"),
        geo=field_val("Geo"),
        due=field_val("Due"),
        path=rel_path,
        created=field_val("Created"),
        completed=field_val("Completed"),
        parent=parent,
        subtask_ids=subtask_ids,
        is_master=is_master,
        recurring_id=recurring_id,
    )


def scan_tasks(window_days: int = EVENTS_WINDOW_DAYS) -> tuple[list, list, str]:
    """Scan task files to build task list and derive Recent Events.

    Returns: (active_tasks: list[ScannedTask], events: list[ScannedEvent], last_task_id: str)
    """
    tasks_dir = BRAIN_DIR / 'tasks'
    history_dir = tasks_dir / 'history'
    today = date.today()
    cutoff = today - timedelta(days=window_days)

    active_tasks = []
    events = []
    max_id = 0

    # Scan active task files
    for task_file in sorted(tasks_dir.glob('T*.md')):
        content = safe_read(task_file)
        if not content:
            continue
        rel_path = f"assistant_brain/tasks/{task_file.name}"
        task = _parse_task_frontmatter(content, rel_path)
        if not task:
            continue

        num = int(re.search(r'\d+', task.id).group())
        if num > max_id:
            max_id = num

        active_tasks.append(task)

        # Generate "Created" event if within window
        if task.created:
            created_date = _parse_date_field(task.created)
            if created_date and created_date >= cutoff:
                display_date = created_date.strftime('%a %b %d, %Y')
                raw = f"- **{display_date}**: 📋 Created [{task.id}]({rel_path}) - {task.title}"
                events.append(ScannedEvent(
                    date_str=created_date.isoformat(),
                    icon="📋",
                    description=f"📋 Created [{task.id}]({rel_path}) - {task.title}",
                    raw_line=raw
                ))

    # Scan history for recently-completed tasks
    for task_file in sorted(history_dir.rglob('T*.md')):
        content = safe_read(task_file)
        if not content:
            continue

        # Determine relative path
        rel_parts = task_file.relative_to(PROJECT_ROOT)
        rel_path = str(rel_parts).replace('\\', '/')

        task = _parse_task_frontmatter(content, rel_path)
        if not task:
            continue

        num = int(re.search(r'\d+', task.id).group())
        if num > max_id:
            max_id = num

        # Generate "Completed" event if within window
        if task.completed and task.completed != '—':
            completed_date = _parse_date_field(task.completed)
            if completed_date and completed_date >= cutoff:
                display_date = completed_date.strftime('%a %b %d, %Y')
                raw = f"- **{display_date}**: ✅ Completed [{task.id}]({rel_path}) - {task.title}"
                events.append(ScannedEvent(
                    date_str=completed_date.isoformat(),
                    icon="✅",
                    description=f"✅ Completed [{task.id}]({rel_path}) - {task.title}",
                    raw_line=raw
                ))

        # Also check Created date for recently-created history tasks
        if task.created:
            created_date = _parse_date_field(task.created)
            if created_date and created_date >= cutoff:
                display_date = created_date.strftime('%a %b %d, %Y')
                raw = f"- **{display_date}**: 📋 Created [{task.id}]({rel_path}) - {task.title}"
                events.append(ScannedEvent(
                    date_str=created_date.isoformat(),
                    icon="📋",
                    description=f"📋 Created [{task.id}]({rel_path}) - {task.title}",
                    raw_line=raw
                ))

    # Sort events by date descending
    events.sort(key=lambda e: e.date_str, reverse=True)

    last_task_id = f"T{max_id:03d}"

    return active_tasks, events, last_task_id
