"""Generate tool-specific prompt files from the canonical BrainClaw prompt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
SOURCE = PROJECT_ROOT / "assistant_brain" / "prompts" / "SYSTEM_PROMPT.md"
TARGETS = (PROJECT_ROOT / "AGENTS.md", PROJECT_ROOT / "CLAUDE.md")
GENERATED_HEADER = "<!-- GENERATED from assistant_brain/prompts/SYSTEM_PROMPT.md; do not edit directly. -->\n\n"


def expected_content() -> str:
    prompt_text = SOURCE.read_text(encoding="utf-8").lstrip("\ufeff")
    
    # Load profile content
    profile_path = PROJECT_ROOT / "assistant_brain" / "profile.md"
    if not profile_path.exists():
        profile_path = PROJECT_ROOT / "assistant_brain" / "profile.example.md"
        
    profile_text = ""
    if profile_path.exists():
        profile_text = profile_path.read_text(encoding="utf-8").lstrip("\ufeff")
        
    # Replace the placeholder paragraph in SYSTEM_PROMPT.md with the profile content
    target_placeholder = (
        "> User identity, current role, and active portfolios are configured in `assistant_brain/profile.md` "
        "(template: `assistant_brain/profile.example.md`). Read `assistant_brain/profile.md` on demand "
        "for the user's name, email, role, primary geo, and active/inactive portfolio ownership."
    )
    
    if target_placeholder in prompt_text:
        prompt_text = prompt_text.replace(target_placeholder, profile_text)
    else:
        # Fallback if text differs slightly
        prompt_text = prompt_text.replace("## User", f"## User\n\n{profile_text}")
        
    return GENERATED_HEADER + prompt_text


def out_of_sync() -> list[Path]:
    expected = expected_content()
    return [path for path in TARGETS if not path.exists() or path.read_text(encoding="utf-8") != expected]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail when generated prompts are stale")
    args = parser.parse_args()

    stale = out_of_sync()
    if args.check:
        if stale:
            print("Prompt files are out of sync: " + ", ".join(path.name for path in stale), file=sys.stderr)
            return 1
        print("Prompt files are synchronized.")
        return 0

    expected = expected_content()
    for path in TARGETS:
        path.write_text(expected, encoding="utf-8", newline="\n")
        print(f"Generated {path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
