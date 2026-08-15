"""Validate the integrity of process/ files and the process/README.md index.

Single authoritative index: process/README.md (parsed by shared_config.py at import).
This script is the safety net for process add/update: run it after ANY change to
process files or the README index table. Exit code 1 if any ERROR is found.

Checks (ERROR = breaks matching / indexing, exit 1):
  1. Dead link: every README table row points to an existing process file
  2. Orphan: every process/*.md file is registered in the README index
  3. Keywords: every README row has at least one non-empty keyword
  4. Keyword overlap: within the same geo, no row's keyword set is a subset of another's
     (a rule earlier in the list would shadow it and matching becomes ambiguous)

Checks (WARNING = format/consistency, does not fail):
  5. Geo mismatch: row's geo folder does not match the README section it lives in
  6. Required sections: process file missing ## When This Applies / ## Steps / ## Key Rules
  7. Metadata: process file missing **Effective:** or **Geo:**

Usage:
    py -3 assistant_brain/scripts/validate_processes.py
"""

import re
import sys
from pathlib import Path

BRAIN_DIR = Path(__file__).resolve().parent.parent
PROCESS_DIR = BRAIN_DIR / 'process'
README = PROCESS_DIR / 'README.md'

REQUIRED_SECTIONS = ('When This Applies', 'Steps', 'Key Rules')


def readme_rows():
    """Parse README index table into rows.

    Returns list of dicts: {section, name, file, keywords(list), description}.
    """
    rows = []
    if not README.exists():
        return rows
    section = None
    for line in README.read_text(encoding='utf-8').split('\n'):
        hdr = re.match(r'^##\s+(.+)$', line)
        if hdr:
            section = hdr.group(1).strip()
            continue
        m = re.match(r'^\|\s*([^|]+?)\s*\|\s*\[`([^`]+)`\]\(([^)]+)\)\s*\|\s*([^|]+)\|', line)
        if m:
            rows.append({
                'section': section,
                'name': m.group(2).strip(),
                'file': m.group(3).strip(),
                'keywords': [k.strip() for k in m.group(4).split(',') if k.strip()],
            })
    return rows


def errors_and_warnings():
    rows = readme_rows()
    errors, warnings = [], []

    if not README.exists():
        return [f"README index missing: {README}"], []

    # Collect all process .md files (excluding README.md)
    process_files = {
        p.relative_to(PROCESS_DIR).as_posix()
        for p in PROCESS_DIR.rglob('*.md') if p.name != 'README.md'
    }

    # 1. Dead links (registered but file missing)
    for row in rows:
        if row['file'] not in process_files:
            errors.append(
                f"Dead link: README '{row['name']}' -> {row['file']} does not exist"
            )

    # 2. Orphans (file exists but not registered)
    registered = {row['file'] for row in rows}
    for f in sorted(process_files - registered):
        errors.append(f"Orphan: process file {f} is not registered in README")

    # 3. Empty keywords
    for row in rows:
        if not row['keywords']:
            errors.append(
                f"Empty keywords: README row '{row['name']}' ({row['file']}) has no keywords"
            )

    # 4. Keyword overlap within same geo (subset shadows)
    by_section = {}
    for row in rows:
        by_section.setdefault(row['section'], []).append(row)
    for section, srows in by_section.items():
        srows = [r for r in srows if r['keywords']]
        for i, a in enumerate(srows):
            for b in srows[i + 1:]:
                ka, kb = set(a['keywords']), set(b['keywords'])
                if ka and kb and (ka <= kb or kb <= ka):
                    errors.append(
                        f"Keyword overlap in '{section}': '{a['name']}' {sorted(ka)} "
                        f"and '{b['name']}' {sorted(kb)} — earlier rule would shadow the later"
                    )

    # 5-7. Per-file format checks
    for row in rows:
        path = PROCESS_DIR / row['file']
        if not path.exists():
            continue
        content = path.read_text(encoding='utf-8')
        # 5. Geo folder vs section
        geo_folder = row['file'].split('/')[0] if '/' in row['file'] else ''
        if geo_folder and geo_folder.lower() != (row['section'] or '').lower():
            warnings.append(
                f"Geo mismatch: {row['file']} sits in '{geo_folder}/' but README section is '{row['section']}'"
            )
        # 6. Required sections
        for sec in REQUIRED_SECTIONS:
            if not re.search(rf'^##\s+{re.escape(sec)}\s*$', content, re.MULTILINE):
                warnings.append(f"{row['file']} missing section '## {sec}'")
        # 7. Metadata
        if not re.search(r'^\*\*Effective:\*\*', content, re.MULTILINE):
            warnings.append(f"{row['file']} missing '**Effective:**'")
        if not re.search(r'^\*\*Geo:\*\*', content, re.MULTILINE):
            warnings.append(f"{row['file']} missing '**Geo:**'")

    return errors, warnings


def main():
    errors, warnings = errors_and_warnings()

    print(f"Process integrity check — README rows: {len(readme_rows())}, process files found: "
          f"{len(set(p.relative_to(PROCESS_DIR).as_posix() for p in PROCESS_DIR.rglob('*.md') if p.name != 'README.md'))}\n")

    if errors:
        print("ERRORS (must fix):")
        for e in errors:
            print(f"  - {e}")
    else:
        print("ERRORS: none ✓")

    print()
    if warnings:
        print("WARNINGS (format only):")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("WARNINGS: none ✓")

    print()
    if errors:
        print(f"FAIL — {len(errors)} error(s), {len(warnings)} warning(s). Fix before proceeding.")
        return 1
    print(f"PASS — {len(warnings)} warning(s). Index is consistent.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
