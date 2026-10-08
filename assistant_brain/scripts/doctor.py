"""Report whether the local BrainClaw runtime is ready."""

from __future__ import annotations

import importlib.util
import platform
import subprocess
import sys

from shared_config import PROJECT_ROOT, configure_utf8_stdio

configure_utf8_stdio()

MIN_VERSION = (3, 11)
OPTIONAL_MODULES = {
    "win32com": "Outlook COM integration (Windows only)",
    "openpyxl": "Excel task-specific utilities",
    "docx": "Word document task-specific utilities",
}
QUALITY_GATES = (
    ("prompt sync", PROJECT_ROOT / "assistant_brain" / "scripts" / "generate_prompts.py", "--check"),
    ("process schema", PROJECT_ROOT / "assistant_brain" / "scripts" / "validate_processes.py"),
    ("task schema", PROJECT_ROOT / "assistant_brain" / "scripts" / "validate_tasks.py"),
    ("Markdown links", PROJECT_ROOT / "assistant_brain" / "scripts" / "check_links.py"),
)


def main() -> int:
    failures = 0
    version = sys.version_info[:3]
    version_ok = version >= MIN_VERSION
    print(f"Python: {platform.python_version()} ({'OK' if version_ok else 'FAIL; need 3.11+'})")
    failures += 0 if version_ok else 1
    print(f"Platform: {platform.platform()}")

    for module, purpose in OPTIONAL_MODULES.items():
        available = importlib.util.find_spec(module) is not None
        print(f"Optional {module}: {'available' if available else 'not installed'} - {purpose}")

    print("\nQuality gates:")
    for name, script, *args in QUALITY_GATES:
        result = subprocess.run(
            [sys.executable, str(script), *args],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        print(f"  {name}: {'PASS' if result.returncode == 0 else 'FAIL'}")
        if result.returncode:
            failures += 1
            detail = (result.stdout + result.stderr).strip()
            if detail:
                print("    " + detail.replace("\n", "\n    "))

    if failures:
        print(f"\nDoctor found {failures} required issue(s).")
        return 1
    print("\nBrainClaw core runtime is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
