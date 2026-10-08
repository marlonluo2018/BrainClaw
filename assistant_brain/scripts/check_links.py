"""Check local Markdown links in the BrainClaw repository."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from shared_config import PROJECT_ROOT, configure_utf8_stdio

configure_utf8_stdio()

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "downloads",
    "backups",
    "memory",
    "sync_results",
    "logs",
}
EXCLUDED_PREFIXES = (("assistant_brain", "skills"),)
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


@dataclass(frozen=True)
class BrokenLink:
    source: Path
    line: int
    target: str
    resolved: Path


def markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in PROJECT_ROOT.rglob("*.md"):
        relative = path.relative_to(PROJECT_ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if any(relative.parts[: len(prefix)] == prefix for prefix in EXCLUDED_PREFIXES):
            continue
        files.append(path)
    return sorted(files)


def without_fenced_code(text: str) -> list[str]:
    output: list[str] = []
    in_fence = False
    marker = ""
    for line in text.splitlines():
        match = re.match(r"^\s*(```+|~~~+)", line)
        if match:
            token = match.group(1)
            if not in_fence:
                in_fence, marker = True, token[0]
            elif token[0] == marker:
                in_fence, marker = False, ""
            output.append("")
        else:
            if in_fence:
                output.append("")
            else:
                output.append(re.sub(r"`[^`]*`", "", line))
    return output


def normalize_target(raw: str) -> str | None:
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    # Optional Markdown title: (path "title")
    target = re.split(r"\s+[\"']", target, maxsplit=1)[0]
    if not target or target.startswith("#"):
        return None
    if re.match(r"^(?:https?|mailto|tel|data):", target, re.IGNORECASE):
        return None
    target = unquote(target.split("#", 1)[0].split("?", 1)[0]).replace("\\", "/")
    return target or None


def resolve(source: Path, target: str) -> Path:
    candidate = Path(target)
    if candidate.is_absolute():
        return candidate
    if target.startswith("assistant_brain/") or target in {
        "AGENTS.md",
        "CLAUDE.md",
        "README.md",
        "README_CN.md",
        "ARCHITECTURE.md",
    }:
        return PROJECT_ROOT / candidate
    return source.parent / candidate


def broken_links() -> tuple[int, list[BrokenLink]]:
    checked = 0
    broken: list[BrokenLink] = []
    for source in markdown_files():
        try:
            lines = without_fenced_code(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(lines, start=1):
            for match in LINK_RE.finditer(line):
                target = normalize_target(match.group(1))
                if target is None:
                    continue
                checked += 1
                resolved = resolve(source, target).resolve()
                if not resolved.exists():
                    broken.append(BrokenLink(source, line_number, match.group(1), resolved))
    return checked, broken


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    checked, broken = broken_links()
    print(f"Markdown links checked: {checked}")
    if broken:
        for item in broken:
            source = item.source.relative_to(PROJECT_ROOT)
            try:
                resolved = item.resolved.relative_to(PROJECT_ROOT)
            except ValueError:
                resolved = item.resolved
            print(f"{source}:{item.line}: {item.target} -> {resolved}")
        print(f"FAIL - {len(broken)} broken local link(s).")
        return 1
    print("PASS - no broken local Markdown links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
