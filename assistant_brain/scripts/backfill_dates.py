"""Bulk-convert ALL ISO dates (YYYY-MM-DD) in task files to Wkd Mon DD, YYYY format."""

import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TASKS_DIR = PROJECT_ROOT / "assistant_brain" / "tasks"

# Match any YYYY-MM-DD that looks like a real date (not inside a URL or path)
ISO_DATE_RE = re.compile(r'(?<!\w)(\d{4}-\d{2}-\d{2})(?!\w)')

def convert_iso_date(match):
    iso_str = match.group(1)
    try:
        d = datetime.strptime(iso_str, '%Y-%m-%d')
        return d.strftime('%a %b %d, %Y')
    except ValueError:
        return match.group(0)

count = 0
for task_file in sorted(TASKS_DIR.rglob('T*.md')):
    content = task_file.read_text(encoding='utf-8')
    new_content = ISO_DATE_RE.sub(convert_iso_date, content)
    if new_content != content:
        task_file.write_text(new_content, encoding='utf-8')
        count += 1
        print(f"  Updated: {task_file.relative_to(PROJECT_ROOT)}")

print(f"\nDone. {count} files updated.")
