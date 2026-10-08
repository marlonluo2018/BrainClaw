"""Validate BrainClaw process metadata, content, and README indexing.

The metadata contract is declared in ``assistant_brain/process/process.schema.json``.
This validator intentionally uses only the Python standard library so it can run in a
fresh checkout before optional dependencies are installed.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from shared_config import BRAIN_DIR, configure_utf8_stdio

configure_utf8_stdio()

PROCESS_DIR = BRAIN_DIR / "process"
README = PROCESS_DIR / "README.md"
SCHEMA_FILE = PROCESS_DIR / "process.schema.json"
REQUIRED_SECTIONS = ("When This Applies", "Steps", "Key Rules")


def readme_rows(process_dir: Path = PROCESS_DIR) -> list[dict[str, Any]]:
    """Parse the authoritative process index table."""
    rows: list[dict[str, Any]] = []
    readme = process_dir / "README.md"
    if not readme.exists():
        return rows
    section = None
    for line in readme.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^##\s+(.+)$", line)
        if heading:
            section = heading.group(1).strip()
            continue
        match = re.match(
            r"^\|\s*([^|]+?)\s*\|\s*\[`([^`]+)`\]\(([^)]+)\)\s*\|\s*([^|]+)\|",
            line,
        )
        if match:
            rows.append(
                {
                    "section": section,
                    "name": match.group(2).strip(),
                    "file": match.group(3).strip(),
                    "keywords": [item.strip() for item in match.group(4).split(",") if item.strip()],
                }
            )
    return rows


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse the small YAML-compatible subset used by process files."""
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("missing closing frontmatter delimiter") from exc

    data: dict[str, Any] = {}
    current_list: str | None = None
    for line_number, raw in enumerate(lines[1:end], start=2):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s+-\s+(.+)$", raw)
        if item:
            if current_list is None:
                raise ValueError(f"line {line_number}: list item without a key")
            data[current_list].append(item.group(1).strip())
            continue
        pair = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$", raw)
        if not pair:
            raise ValueError(f"line {line_number}: unsupported frontmatter syntax")
        key, value = pair.group(1), (pair.group(2) or "").strip()
        if key in data:
            raise ValueError(f"line {line_number}: duplicate key '{key}'")
        if value == "":
            data[key] = []
            current_list = key
        else:
            current_list = None
            if value == "null":
                data[key] = None
            elif re.fullmatch(r"\d+", value):
                data[key] = int(value)
            else:
                data[key] = value.strip('"\'')
    return data, "\n".join(lines[end + 1 :])


def validate_metadata(metadata: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Validate the JSON Schema features used by process.schema.json."""
    errors: list[str] = []
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    for key in required:
        if key not in metadata:
            errors.append(f"missing required metadata '{key}'")
    if schema.get("additionalProperties") is False:
        for key in sorted(set(metadata) - set(properties)):
            errors.append(f"unknown metadata '{key}'")

    for key, value in metadata.items():
        rules = properties.get(key)
        if not rules:
            continue
        expected = rules.get("type")
        allowed = expected if isinstance(expected, list) else [expected]
        type_ok = any(
            (kind == "null" and value is None)
            or (kind == "string" and isinstance(value, str))
            or (kind == "integer" and isinstance(value, int) and not isinstance(value, bool))
            or (kind == "array" and isinstance(value, list))
            for kind in allowed
        )
        if not type_ok:
            errors.append(f"metadata '{key}' has invalid type")
            continue
        if value is None:
            continue
        if "enum" in rules and value not in rules["enum"]:
            errors.append(f"metadata '{key}' must be one of {rules['enum']}")
        if isinstance(value, str):
            if len(value) < rules.get("minLength", 0):
                errors.append(f"metadata '{key}' is empty")
            if "pattern" in rules and not re.fullmatch(rules["pattern"], value):
                errors.append(f"metadata '{key}' does not match {rules['pattern']}")
            if rules.get("format") == "date":
                try:
                    date.fromisoformat(value)
                except ValueError:
                    errors.append(f"metadata '{key}' is not an ISO date")
        if isinstance(value, int) and value < rules.get("minimum", value):
            errors.append(f"metadata '{key}' must be >= {rules['minimum']}")
        if isinstance(value, list):
            if len(value) < rules.get("minItems", 0):
                errors.append(f"metadata '{key}' must contain at least {rules['minItems']} item(s)")
            if rules.get("uniqueItems") and len(value) != len(set(value)):
                errors.append(f"metadata '{key}' contains duplicates")
            item_rules = rules.get("items", {})
            for index, item in enumerate(value):
                if item_rules.get("type") == "string" and not isinstance(item, str):
                    errors.append(f"metadata '{key}[{index}]' must be a string")
                elif isinstance(item, str) and len(item) < item_rules.get("minLength", 0):
                    errors.append(f"metadata '{key}[{index}]' is empty")
    return errors


def errors_and_warnings(
    process_dir: Path = PROCESS_DIR, schema_file: Path = SCHEMA_FILE
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    readme = process_dir / "README.md"
    if not readme.exists():
        return [f"README index missing: {readme}"], warnings
    if not schema_file.exists():
        return [f"Process schema missing: {schema_file}"], warnings
    try:
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Cannot read process schema: {exc}"], warnings

    rows = readme_rows(process_dir)
    process_files = {
        path.relative_to(process_dir).as_posix()
        for path in process_dir.rglob("*.md")
        if path.name != "README.md"
    }
    registered = {row["file"] for row in rows}

    for row in rows:
        if row["file"] not in process_files:
            errors.append(f"Dead link: README '{row['name']}' -> {row['file']} does not exist")
        if not row["keywords"]:
            errors.append(f"Empty keywords: README row '{row['name']}' ({row['file']})")
    for relative in sorted(process_files - registered):
        errors.append(f"Orphan: process file {relative} is not registered in README")

    by_section: dict[str | None, list[dict[str, Any]]] = {}
    for row in rows:
        by_section.setdefault(row["section"], []).append(row)
    for section, section_rows in by_section.items():
        for index, left in enumerate(section_rows):
            for right in section_rows[index + 1 :]:
                left_keys = {key.casefold() for key in left["keywords"]}
                right_keys = {key.casefold() for key in right["keywords"]}
                if left_keys and right_keys and (left_keys <= right_keys or right_keys <= left_keys):
                    errors.append(
                        f"Keyword overlap in '{section}': '{left['name']}' {sorted(left_keys)} "
                        f"and '{right['name']}' {sorted(right_keys)}"
                    )

    for row in rows:
        path = process_dir / row["file"]
        if not path.exists():
            continue
        try:
            metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            errors.append(f"{row['file']}: {exc}")
            continue
        for message in validate_metadata(metadata, schema):
            errors.append(f"{row['file']}: {message}")

        geo_folder = row["file"].split("/", 1)[0]
        expected_id = f"{geo_folder}-{Path(row['file']).stem}"
        if metadata.get("id") != expected_id:
            errors.append(f"{row['file']}: metadata id must be '{expected_id}'")
        if str(metadata.get("geo", "")).casefold() != str(row["section"] or "").casefold():
            errors.append(f"{row['file']}: metadata geo does not match README section '{row['section']}'")
        metadata_keywords = {item.casefold() for item in metadata.get("keywords", []) if isinstance(item, str)}
        readme_keywords = {item.casefold() for item in row["keywords"]}
        if metadata_keywords != readme_keywords:
            errors.append(f"{row['file']}: metadata keywords do not match README index")
        for section in REQUIRED_SECTIONS:
            if not re.search(rf"^##\s+{re.escape(section)}\s*$", body, re.MULTILINE):
                errors.append(f"{row['file']}: missing required section '## {section}'")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--process-dir",
        type=Path,
        default=PROCESS_DIR,
        help="Directory containing README.md and process Markdown files.",
    )
    args = parser.parse_args()
    process_dir = args.process_dir.resolve()

    errors, warnings = errors_and_warnings(process_dir)
    process_count = sum(1 for path in process_dir.rglob("*.md") if path.name != "README.md")
    print(
        f"Process validation - README rows: {len(readme_rows(process_dir))}, "
        f"process files: {process_count}"
    )
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("ERRORS: none")
    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("WARNINGS: none")
    if errors:
        print(f"FAIL - {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    print("PASS - process metadata and index satisfy the schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())