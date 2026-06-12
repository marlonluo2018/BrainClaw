"""One-shot script: backfill **Completed:** field into history task files.

Uses the last Timeline entry date as the completion date.
Run once, then delete this script.
"""

import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BRAIN_DIR = Path(__file__).resolve().parent.parent
HISTORY_DIR = BRAIN_DIR / 'tasks' / 'history'


def extract_last_timeline_date(content: str) -> str | None:
    dates = re.findall(r'^\- \*\*(\d{4}-\d{2}-\d{2})\*\*', content, re.MULTILINE)
    return dates[-1] if dates else None


def backfill_file(path: Path) -> str | None:
    content = path.read_text(encoding='utf-8')

    if '**Completed:**' in content:
        return None

    if '**Status:** ✅' not in content:
        return None

    completion_date = extract_last_timeline_date(content)
    if not completion_date:
        created_m = re.search(r'^\*\*Created:\*\*\s*(\d{4}-\d{2}-\d{2})', content, re.MULTILINE)
        completion_date = created_m.group(1) if created_m else '2026-01-01'

    new_content = re.sub(
        r'(\*\*Created:\*\*\s*.+\n)',
        r'\1**Completed:** ' + completion_date + '\n',
        content,
        count=1
    )

    path.write_text(new_content, encoding='utf-8')
    return completion_date


def main():
    updated = 0
    skipped = 0

    for task_file in sorted(HISTORY_DIR.rglob('T*.md')):
        result = backfill_file(task_file)
        if result:
            print(f"  ✓ {task_file.name} → Completed: {result}")
            updated += 1
        else:
            skipped += 1

    print(f"\nDone. Updated: {updated}, Skipped: {skipped}")


if __name__ == '__main__':
    main()
