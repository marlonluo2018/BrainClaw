"""BrainClaw startup script — replaces prompt-driven startup with deterministic Python."""

import sys
import io
import os
import re
import argparse
import glob as glob_mod
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BRAIN_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BRAIN_DIR.parent
EVENTS_WINDOW_DAYS = 14
MAX_CONTACTS_DISPLAY = 10

STATUS_ICONS = {"Not Started": "📋", "In Progress": "⏳", "Blocked": "🔴"}
ICON_TO_STATUS = {"📋": "Not Started", "⏳": "In Progress", "🔴": "Blocked"}

FLAG_MAP = {
    "China": "🇨🇳",
    "Philippines": "🇵🇭",
    "India": "🇮🇳",
    "Singapore": "🇸🇬",
    "Global": "🌐",
}


@dataclass
class Task:
    id: str
    title: str
    status: str
    priority: str
    geo: str
    due: str
    path: str
    parent: str = ""
    subtask_ids: list = field(default_factory=list)
    subtasks: list = field(default_factory=list)
    asks_out: list = field(default_factory=list)
    asks_in: list = field(default_factory=list)
    is_master: bool = False


@dataclass
class Event:
    date_str: str
    icon: str
    description: str
    raw_line: str


@dataclass
class RecurringTask:
    id: str
    name: str
    schedule: str
    last_completed: str
    last_period: str = ""


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except FileNotFoundError:
        print(f"⚠️ Missing: {path.relative_to(PROJECT_ROOT)}", file=sys.stderr)
        return ""
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding='utf-8-sig')
        except Exception:
            return ""


# --- Parsers ---

def parse_queue(content: str):
    tasks = []
    events = []
    lines = content.split('\n')

    # Parse events
    event_pattern = re.compile(r'^- \*\*(\d{4}-\d{2}-\d{2})\*\*: (.+)$')
    for line in lines:
        m = event_pattern.match(line)
        if m:
            events.append(Event(
                date_str=m.group(1),
                icon=m.group(2)[:1] if m.group(2) else "",
                description=m.group(2),
                raw_line=line
            ))

    # Parse tasks
    task_heading = re.compile(
        r'^(##|### ↳)\s+T(\d+)\s+(📋|⏳|🔴)\s+(.+?)\s+\[`?([^`\]]+)`?\]\(([^)]+)\)'
    )

    current_task = None
    in_master_section = False

    for line in lines:
        if line.strip() == '## Master Task with Subtasks':
            in_master_section = True
            continue

        m = task_heading.match(line)
        if m:
            level = m.group(1)
            tid = f"T{m.group(2)}"
            icon = m.group(3)
            title = m.group(4).strip()
            filename = m.group(5)
            path = m.group(6)

            display_path = path.replace('./', 'assistant_brain/tasks/')

            task = Task(
                id=tid,
                title=title,
                status=ICON_TO_STATUS.get(icon, "Unknown"),
                priority="",
                geo="",
                due="",
                path=display_path,
            )

            if level == "### ↳":
                task.parent = current_task.id if current_task else ""
            elif in_master_section and level == "##":
                task.is_master = True

            current_task = task
            tasks.append(task)
            continue

        if current_task and line.startswith('- **'):
            kv = re.match(r'^- \*\*(.+?):\*\*\s*(.+)$', line)
            if kv:
                key = kv.group(1)
                val = kv.group(2).strip()
                if key == "Priority":
                    current_task.priority = val
                elif key == "Geo":
                    current_task.geo = val
                elif key == "Due":
                    current_task.due = val
                elif key == "Subtasks":
                    current_task.subtask_ids = [f"T{x.strip().lstrip('T')}" for x in val.split(',')]
                elif key == "Parent Task":
                    current_task.parent = f"T{val.strip().lstrip('T')}"

    return tasks, events


def parse_asks_from_file(content: str):
    asks_out = []
    asks_in = []
    lines = content.split('\n')
    section = None

    for line in lines:
        if line.strip() == '### Owed by me':
            section = 'out'
            continue
        elif line.strip() == '### Owed to me':
            section = 'in'
            continue
        elif line.startswith('## ') or line.startswith('---'):
            if section:
                section = None
            continue

        if section == 'out':
            # Only unchecked items
            m = re.match(r'^- \[ \] (.+?) → (.+?): (.+)$', line)
            if m:
                asks_out.append(f"{m.group(1)} → {m.group(2)}: {m.group(3)}")
        elif section == 'in':
            # Skip struck-through
            if line.strip().startswith('- ~~'):
                continue
            m = re.match(r'^- (.+?) ← (.+?): (.+)$', line)
            if m:
                asks_in.append(f"{m.group(1)} ← {m.group(2)}: {m.group(3)}")

    return asks_out, asks_in


def parse_recurring_tasks(content: str):
    tasks = []
    in_yaml = False
    current = {}

    for line in content.split('\n'):
        if line.strip() == '```yaml':
            in_yaml = True
            continue
        elif line.strip() == '```' and in_yaml:
            if current:
                tasks.append(_build_recurring(current))
            break

        if not in_yaml:
            continue

        # New record (handles "  - id:" format)
        if re.match(r'^\s+-\s+id:', line):
            if current:
                tasks.append(_build_recurring(current))
            current = {}

        kv = re.match(r'^\s+-?\s*(\w+):\s+"?([^"#]+?)"?\s*(?:#.*)?$', line)
        if kv:
            current[kv.group(1)] = kv.group(2)

    return tasks


def _build_recurring(data: dict) -> RecurringTask:
    return RecurringTask(
        id=data.get('id', ''),
        name=data.get('name', ''),
        schedule=data.get('schedule', ''),
        last_completed=data.get('last_completed', ''),
        last_period=data.get('last_period', ''),
    )


def parse_skill_frontmatter(content: str) -> str:
    lines = content.split('\n')
    if not lines or lines[0].strip() != '---':
        return ""
    for line in lines[1:]:
        if line.strip() == '---':
            break
        m = re.match(r'^name:\s*(.+)$', line)
        if m:
            return m.group(1).strip().strip('"')
    return ""


def parse_contacts(content: str) -> list:
    names = []
    for line in content.split('\n'):
        m = re.match(r'^- \*\*(.+?)\*\*', line)
        if m:
            names.append(m.group(1))
    return names


def parse_processes(content: str) -> list:
    processes = []
    for line in content.split('\n'):
        m = re.match(r'^\|\s*([^|]+?)\s*\|\s*\[', line)
        if m:
            name = m.group(1).strip()
            if name and name != 'Process':
                processes.append(name)
    return processes


# --- Business Logic ---

def archive_old_events(events: list, today: date):
    kept = []
    archived = {}
    cutoff = today - timedelta(days=EVENTS_WINDOW_DAYS)

    for ev in events:
        try:
            ev_date = date.fromisoformat(ev.date_str)
        except ValueError:
            kept.append(ev)
            continue

        if ev_date < cutoff:
            month_key = ev.date_str[:7]  # YYYY-MM
            archived.setdefault(month_key, []).append(ev)
        else:
            kept.append(ev)

    return kept, archived


def write_archived_events(archived: dict, dry_run: bool = False):
    for month_key, events in archived.items():
        year, month = int(month_key[:4]), int(month_key[5:7])
        quarter = (month - 1) // 3 + 1
        quarter_dir = BRAIN_DIR / 'tasks' / 'history' / f'{year}-Q{quarter}'
        timeline_file = quarter_dir / f'timeline_{month_key}.md'

        if dry_run:
            print(f"  [dry-run] Would archive {len(events)} events to {timeline_file.relative_to(PROJECT_ROOT)}", file=sys.stderr)
            continue

        quarter_dir.mkdir(parents=True, exist_ok=True)

        if not timeline_file.exists():
            timeline_file.write_text(
                f"# Timeline {month_key}\n\n> Archived events from queue.md\n\n",
                encoding='utf-8'
            )

        with open(timeline_file, 'a', encoding='utf-8') as f:
            for ev in events:
                f.write(ev.raw_line + '\n')


def rewrite_queue_events(queue_path: Path, content: str, kept_events: list, dry_run: bool = False):
    if dry_run:
        return content

    lines = content.split('\n')
    new_lines = []
    event_pattern = re.compile(r'^- \*\*(\d{4}-\d{2}-\d{2})\*\*: (.+)$')
    kept_dates = {ev.raw_line for ev in kept_events}

    for line in lines:
        if event_pattern.match(line):
            if line in kept_dates:
                new_lines.append(line)
        else:
            new_lines.append(line)

    new_content = '\n'.join(new_lines)
    queue_path.write_text(new_content, encoding='utf-8')
    return new_content


def check_recurring_due(recurring: list, tasks: list, today: date, queue_content: str = "") -> list:
    due = []

    for rt in recurring:
        # Check if already in queue via "Recurring Task ID: R00X"
        if f"Recurring Task ID:** {rt.id}" in queue_content:
            continue

        is_due = False
        if rt.schedule == "last week of every quarter":
            quarter_month = ((today.month - 1) // 3 + 1) * 3
            quarter_end = date(today.year, quarter_month, 1) + timedelta(days=31)
            quarter_end = quarter_end.replace(day=1) - timedelta(days=1)
            days_to_end = (quarter_end - today).days
            current_quarter = f"{today.year}-Q{(today.month - 1) // 3 + 1}"
            is_due = days_to_end <= 7 and rt.last_period < current_quarter

        elif rt.schedule == "beginning of every month":
            prev_month = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
            is_due = today.day <= 7 and rt.last_period < prev_month

        if is_due:
            due.append(rt)

    return due


def compute_overdue_days(due_str: str, today: date):
    if not due_str or 'TBD' in due_str:
        return None
    try:
        due_date = date.fromisoformat(due_str.strip()[:10])
        delta = (today - due_date).days
        return delta if delta > 0 else None
    except ValueError:
        return None


# --- Output Formatting ---

def format_brief(tasks, skills, processes, contacts, today, recurring_due, events=None, dry_run_msg=""):
    weekday = today.strftime('%A')
    date_str = today.strftime('%Y-%m-%d %H:%M')
    lines = []

    lines.append(f"## ✅ Ready | {weekday} {date_str} | User: Marlon Luo | OS: Windows 11")
    lines.append("")

    # Info lines
    skills_str = ' · '.join(f'`{s}`' for s in skills) if skills else '(none)'
    lines.append(f"Skills: {skills_str}")

    proc_str = ' · '.join(f'`{p}`' for p in processes) if processes else '(none)'
    lines.append(f"Processes: {proc_str}")

    if len(contacts) > MAX_CONTACTS_DISPLAY:
        contact_str = ' · '.join(f'`{c}`' for c in contacts[:MAX_CONTACTS_DISPLAY])
        contact_str += f" (+{len(contacts) - MAX_CONTACTS_DISPLAY} more)"
    else:
        contact_str = ' · '.join(f'`{c}`' for c in contacts)
    lines.append(f"Contacts: {contact_str}")

    # Task counts
    standalone_tasks = [t for t in tasks if not t.parent]
    all_tasks_flat = tasks
    overdue_count = sum(1 for t in all_tasks_flat if compute_overdue_days(t.due, today.date()))
    owed_out = sum(len(t.asks_out) for t in all_tasks_flat)
    owed_in = sum(len(t.asks_in) for t in all_tasks_flat)

    counts = f"Tasks: {len(all_tasks_flat)} active"
    if overdue_count:
        counts += f" · {overdue_count} overdue"
    if owed_out:
        counts += f" · {owed_out} owed"
    if owed_in:
        counts += f" · {owed_in} waiting"
    lines.append(counts)

    # Recurring due warnings
    if recurring_due:
        lines.append("")
        for rt in recurring_due:
            lines.append(f"⚠️ Recurring due: {rt.id} - {rt.name}")

    if dry_run_msg:
        lines.append("")
        lines.append(dry_run_msg)

    lines.append("")
    lines.append("---")
    lines.append("")

    # Recent events
    if events:
        lines.append(f"### Recent Events ({len(events)})")
        lines.append("")
        for ev in events:
            fixed_line = re.sub(
                r'\]\(\./(.+?)\)',
                r'](assistant_brain/tasks/\1)',
                ev.raw_line
            )
            lines.append(fixed_line)
        lines.append("")
        lines.append("---")
        lines.append("")

    # Group by country
    geo_groups = {}
    for t in tasks:
        if t.parent:
            continue
        geo = t.geo or "Other"
        geo_groups.setdefault(geo, []).append(t)

    # Sort countries by count descending, then alphabetical
    sorted_geos = sorted(geo_groups.keys(), key=lambda g: (-len(geo_groups[g]), g))

    for geo in sorted_geos:
        flag = FLAG_MAP.get(geo, "🌐")
        geo_tasks = geo_groups[geo]
        lines.append(f"### {flag} {geo} ({len(geo_tasks)})")
        lines.append("")

        # Group by priority
        prio_groups = {}
        for t in geo_tasks:
            p = t.priority or "P3"
            prio_groups.setdefault(p, []).append(t)

        for prio in sorted(prio_groups.keys()):
            prio_tasks = prio_groups[prio]
            lines.append(f"**{prio} · {len(prio_tasks)}**")

            for t in prio_tasks:
                task_line = format_task_line(t, today.date())
                lines.append(task_line)

                # Asks
                for ask in t.asks_out:
                    lines.append(f"  - → {ask}")
                for ask in t.asks_in:
                    lines.append(f"  - ← {ask}")

                # Subtasks
                for sub in t.subtasks:
                    sub_line = format_task_line(sub, today.date(), indent="  ")
                    lines.append(sub_line)
                    for ask in sub.asks_out:
                        lines.append(f"    - → {ask}")
                    for ask in sub.asks_in:
                        lines.append(f"    - ← {ask}")

            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("→ `status T###` · `pending` · `pending out` · `pending in` · `before {person}` · `review` · `taskboard`")

    return '\n'.join(lines)


def format_task_line(task: Task, today: date, indent: str = "") -> str:
    icon = STATUS_ICONS.get(task.status, "📋")
    master_suffix = " (Master)" if task.is_master and "(Master)" not in task.title else ""
    prefix = "↳ " if task.parent else ""

    overdue = compute_overdue_days(task.due, today)
    if overdue:
        due_str = f"— was due {task.due[:10]} (**{overdue}d overdue**)"
    elif task.due and 'TBD' not in task.due:
        due_str = f"— Due {task.due[:10]}"
    elif task.due:
        due_str = f"— Due {task.due}"
    else:
        due_str = ""

    return f"{indent}- {prefix}{icon} [{task.id}]({task.path}) {task.title}{master_suffix} {due_str}".rstrip()


# --- Pending Views Formatting ---

def _collect_asks_by_task(tasks, direction):
    """Group asks by task. direction: 'out' or 'in'."""
    grouped = []
    for t in tasks:
        asks = list(t.asks_out if direction == 'out' else t.asks_in)
        for sub in t.subtasks:
            asks.extend(sub.asks_out if direction == 'out' else sub.asks_in)
        if asks:
            grouped.append((t, asks))
    return grouped


def _render_ask_section(lines, grouped, arrow, count):
    if not grouped:
        lines.append("(none)")
        return
    for t, asks in grouped:
        lines.append(f"- [{t.id}]({t.path}) {t.title}")
        for ask in asks:
            lines.append(f"  - {arrow} {ask}")
    lines.append("")


def format_pending_all(tasks, today):
    lines = []
    date_str = today.strftime('%Y-%m-%d')
    lines.append(f"## Pending Asks | {date_str}")
    lines.append("")

    grouped_out = _collect_asks_by_task(tasks, 'out')
    grouped_in = _collect_asks_by_task(tasks, 'in')
    count_out = sum(len(asks) for _, asks in grouped_out)
    count_in = sum(len(asks) for _, asks in grouped_in)

    lines.append(f"### → Owed by me ({count_out})")
    lines.append("")
    _render_ask_section(lines, grouped_out, "→", count_out)

    lines.append(f"### ← Owed to me ({count_in})")
    lines.append("")
    _render_ask_section(lines, grouped_in, "←", count_in)

    return '\n'.join(lines)


def format_pending_out(tasks, today):
    lines = []
    date_str = today.strftime('%Y-%m-%d')
    grouped = _collect_asks_by_task(tasks, 'out')
    count = sum(len(asks) for _, asks in grouped)

    lines.append(f"## → Owed by me ({count}) | {date_str}")
    lines.append("")
    _render_ask_section(lines, grouped, "→", count)

    return '\n'.join(lines)


def format_pending_in(tasks, today):
    lines = []
    date_str = today.strftime('%Y-%m-%d')
    grouped = _collect_asks_by_task(tasks, 'in')
    count = sum(len(asks) for _, asks in grouped)

    lines.append(f"## ← Owed to me ({count}) | {date_str}")
    lines.append("")
    _render_ask_section(lines, grouped, "←", count)

    return '\n'.join(lines)


# --- Shared Data Loading ---

def load_tasks_with_asks():
    queue_path = BRAIN_DIR / 'tasks' / 'queue.md'
    queue_content = safe_read(queue_path)
    if not queue_content:
        print("ERROR: Cannot read tasks/queue.md", file=sys.stderr)
        sys.exit(1)

    tasks, events = parse_queue(queue_content)

    # Extract pending asks
    for task in tasks:
        task_file = PROJECT_ROOT / task.path
        if task_file.exists():
            content = safe_read(task_file)
            if content:
                task.asks_out, task.asks_in = parse_asks_from_file(content)

    # Link subtasks to parents
    task_map = {t.id: t for t in tasks}
    for t in tasks:
        if t.parent and t.parent in task_map:
            parent = task_map[t.parent]
            parent.subtasks.append(t)

    return tasks, events, queue_content, queue_path


# --- Events View ---

EVENT_FILTERS = {
    'all': None,
    'created': '📋',
    'closed': '✅',
    'blocked': '🔴',
}


def format_events(events, filter_name, today):
    lines = []
    date_str = today.strftime('%Y-%m-%d')
    icon_filter = EVENT_FILTERS.get(filter_name)

    if icon_filter:
        filtered = [ev for ev in events if ev.description.startswith(icon_filter)]
    else:
        filtered = events

    label = filter_name.capitalize() if filter_name != 'all' else 'All'
    lines.append(f"## Recent Events — {label} ({len(filtered)}) | {date_str}")
    lines.append("")

    if not filtered:
        lines.append("(none)")
    else:
        for ev in filtered:
            fixed_line = re.sub(
                r'\]\(\./(.+?)\)',
                r'](assistant_brain/tasks/\1)',
                ev.raw_line
            )
            lines.append(fixed_line)

    lines.append("")
    lines.append(f"Filters: `all` · `created` · `closed` · `blocked`")

    return '\n'.join(lines)


def run_events(filter_name, today):
    _, events, _, _ = load_tasks_with_asks()

    if filter_name not in EVENT_FILTERS:
        print(f"Unknown filter: {filter_name}. Use: all, created, closed, blocked", file=sys.stderr)
        filter_name = 'all'

    print(format_events(events, filter_name, today))


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description='BrainClaw task dashboard')
    parser.add_argument('--dry-run', action='store_true', help='No file writes, show what would be archived')
    parser.add_argument('--no-archive', action='store_true', help='Skip archival step')
    parser.add_argument('command', nargs='?', default='startup',
                        choices=['startup', 'pending', 'pending-out', 'pending-in', 'taskboard', 'events'],
                        help='Command to run (default: startup)')
    parser.add_argument('filter', nargs='?', default='all',
                        help='Filter for events command: all, created, closed, blocked')

    args = parser.parse_args()
    today = datetime.now()

    if args.command in (None, 'startup'):
        run_startup(args, today)
    elif args.command == 'taskboard':
        args.no_archive = True
        args.dry_run = False
        run_startup(args, today)
    elif args.command in ('pending', 'pending-out', 'pending-in'):
        run_pending(args.command, today)
    elif args.command == 'events':
        run_events(args.filter, today)


def run_pending(mode, today):
    tasks, _, _, _ = load_tasks_with_asks()

    # Only use top-level tasks (subtasks are nested inside)
    top_tasks = [t for t in tasks if not t.parent]

    if mode == 'pending':
        print(format_pending_all(top_tasks, today))
    elif mode == 'pending-out':
        print(format_pending_out(top_tasks, today))
    elif mode == 'pending-in':
        print(format_pending_in(top_tasks, today))


def run_startup(args, today):
    tasks, events, queue_content, queue_path = load_tasks_with_asks()

    # Archive old events
    dry_run_msg = ""
    dry_run = getattr(args, 'dry_run', False)
    no_archive = getattr(args, 'no_archive', False)

    if not no_archive:
        kept_events, archived = archive_old_events(events, today.date())
        if archived:
            total_archived = sum(len(v) for v in archived.values())
            if dry_run:
                dry_run_msg = f"[dry-run] Would archive {total_archived} events"
                write_archived_events(archived, dry_run=True)
            else:
                write_archived_events(archived, dry_run=False)
                queue_content = rewrite_queue_events(queue_path, queue_content, kept_events)
                dry_run_msg = f"📦 Archived {total_archived} event(s) older than {EVENTS_WINDOW_DAYS} days from queue.md"
        events = kept_events

    # Parse recurring tasks
    recurring_path = BRAIN_DIR / 'recurring_tasks.md'
    recurring_content = safe_read(recurring_path)
    recurring = parse_recurring_tasks(recurring_content) if recurring_content else []
    recurring_due = check_recurring_due(recurring, tasks, today.date(), queue_content)

    # Scan skills
    skills = []
    skills_dir = BRAIN_DIR / 'skills'
    if skills_dir.exists():
        for skill_path in sorted(skills_dir.glob('*/SKILL.md')):
            name = parse_skill_frontmatter(safe_read(skill_path))
            if name:
                skills.append(name)

    # Parse contacts
    contacts = parse_contacts(safe_read(BRAIN_DIR / 'contacts.md'))

    # Parse processes
    processes = parse_processes(safe_read(BRAIN_DIR / 'process' / 'README.md'))

    # Output brief
    brief = format_brief(tasks, skills, processes, contacts, today, recurring_due, events, dry_run_msg)
    print(brief)


if __name__ == "__main__":
    main()
