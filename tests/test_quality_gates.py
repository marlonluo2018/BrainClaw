from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "assistant_brain" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_links  # noqa: E402
import generate_prompts  # noqa: E402
import validate_processes  # noqa: E402
import validate_tasks  # noqa: E402
from ooxml_workbook import (  # noqa: E402
    pack_workbook,
    prepare_workbook_tree,
    sheet_xml,
    SharedStrings,
    write_styles,
    write_workbook_parts,
)
from followup import parse_task_file  # noqa: E402
from shared_config import _parse_task_frontmatter  # noqa: E402


class QualityGateTests(unittest.TestCase):
    def test_generated_prompts_are_current(self) -> None:
        self.assertEqual([], generate_prompts.out_of_sync())

    def test_process_schema_and_index(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "process"
        errors, warnings = validate_processes.errors_and_warnings(fixture)
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_task_schema(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "tasks"
        errors, warnings = validate_tasks.errors_and_warnings(fixture)
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_markdown_links(self) -> None:
        checked, broken = check_links.broken_links()
        self.assertGreater(checked, 0)
        self.assertEqual([], broken)

    def test_deleted_architecture_terms_are_absent(self) -> None:
        paths = [ROOT / "README.md", ROOT / "README_CN.md", ROOT / "ARCHITECTURE.md"]
        paths.extend((ROOT / "assistant_brain" / "scripts").glob("*.py"))
        for path in paths:
            text = path.read_text(encoding="utf-8")
            relative = path.relative_to(ROOT).as_posix()
            self.assertNotIn("minimax-xlsx", text, relative)
            self.assertNotIn("tasks/queue.md", text, relative)

    def test_task_frontmatter_parser(self) -> None:
        content = """# T999: Parser Test

**Status:** ⏳ In Progress
**Created:** 2026-09-20
**Priority:** P2
**Geo:** Global
**Due:** TBD
"""
        task = _parse_task_frontmatter(content, "assistant_brain/tasks/T999-parser-test.md")
        self.assertIsNotNone(task)
        assert task is not None
        self.assertEqual("T999", task.id)
        self.assertEqual("In Progress", task.status)
        self.assertEqual("P2", task.priority)

    def test_followup_parser_extracts_structured_sections(self) -> None:
        content = """**Category:** Email
**Geo:** Global
## Asks
### My Actions
- [ ] {Due: Sun Sep 20, 2026} 🎯 to Alex: Send update
### Waiting on Others
- {Due: Mon Sep 21, 2026} ⏳ Casey: Approve
## Timeline
- **2026-09-19** [email-in] Update received
## Current State
- [ ] Review update
"""
        parsed = parse_task_file(content)
        self.assertEqual("Email", parsed["category"])
        self.assertEqual("Global", parsed["geo"])
        self.assertTrue(parsed["timeline_entries"])

    def test_xlsx_packaging_has_required_ooxml_parts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work_dir = root / "workbook"
            output = root / "fixture.xlsx"
            prepare_workbook_tree(work_dir)
            write_workbook_parts(work_dir, ["Summary", "Review", "Confirmed"])
            write_styles(work_dir / "xl" / "styles.xml")
            shared = SharedStrings()
            for index in range(1, 4):
                rows = [[(f"Sheet {index}", 0, None)]]
                (work_dir / "xl" / "worksheets" / f"sheet{index}.xml").write_text(
                    sheet_xml(shared, rows, [20], selected=index == 1),
                    encoding="utf-8",
                )
            (work_dir / "xl" / "sharedStrings.xml").write_text(shared.xml(), encoding="utf-8")
            pack_workbook(work_dir, output)

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertTrue(
                {
                    "[Content_Types].xml",
                    "_rels/.rels",
                    "xl/workbook.xml",
                    "xl/_rels/workbook.xml.rels",
                    "xl/styles.xml",
                    "xl/sharedStrings.xml",
                    "xl/worksheets/sheet1.xml",
                    "xl/worksheets/sheet2.xml",
                    "xl/worksheets/sheet3.xml",
                }
                <= names
            )

    def test_private_paths_and_task_scripts_are_ignored(self) -> None:
        ignored = [
            "assistant_brain/skills/example-skill/SKILL.md",
            "assistant_brain/contacts.md",
            "assistant_brain/scripts/private_delivery.py",
            "assistant_brain/workflows/REDHAT_MANUAL_WORK_GUIDE.md",
            "scripts/temporary.py",
        ]
        for relative in ignored:
            result = subprocess.run(
                ["git", "check-ignore", "--no-index", "-q", relative],
                cwd=ROOT,
                check=False,
            )
            self.assertEqual(0, result.returncode, relative)

        visible = [
            "assistant_brain/process/process.schema.json",
            "assistant_brain/tasks/FORMATS.md",
            "assistant_brain/scripts/run_email_sync.py",
            "assistant_brain/scripts/ooxml_workbook.py",
        ]
        for relative in visible:
            result = subprocess.run(
                ["git", "check-ignore", "--no-index", "-q", relative],
                cwd=ROOT,
                check=False,
            )
            self.assertEqual(1, result.returncode, relative)

    def test_assistant_scripts_match_explicit_allowlist(self) -> None:
        prefix = "!assistant_brain/scripts/"
        allowlisted = {
            line[len(prefix) :]
            for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
            if line.startswith(prefix)
        }
        present = {
            path.relative_to(SCRIPTS).as_posix()
            for path in SCRIPTS.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        self.assertEqual(allowlisted, present)
    def test_repository_text_files_have_no_utf8_bom(self) -> None:
        candidates = [
            ROOT / ".gitattributes",
            ROOT / ".gitignore",
            ROOT / "AGENTS.md",
            ROOT / "CLAUDE.md",
            ROOT / "README.md",
            ROOT / "README_CN.md",
            ROOT / "ARCHITECTURE.md",
            ROOT / "pyproject.toml",
            ROOT / "requirements-dev.txt",
            ROOT / "assistant_brain" / "contacts.example.md",
            ROOT / "assistant_brain" / "process" / "process.schema.json",
            ROOT / "assistant_brain" / "formats" / "task_file.schema.json",
            ROOT / "assistant_brain" / "prompts" / "SYSTEM_PROMPT.md",
        ]
        for directory in (SCRIPTS, ROOT / "assistant_brain" / "workflows", ROOT / "tests"):
            candidates.extend(
                path
                for path in directory.rglob("*")
                if path.is_file() and path.suffix.lower() in {".py", ".md", ".json", ".toml", ".yml", ".yaml", ".txt"}
            )
        for path in candidates:
            self.assertFalse(path.read_bytes().startswith(b"\xef\xbb\xbf"), path.relative_to(ROOT).as_posix())

    def test_task_validator_runs_with_non_utf8_parent_console(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "validate_tasks.py"),
                "--task-dir",
                str(ROOT / "tests" / "fixtures" / "tasks"),
            ],
            cwd=ROOT,
            capture_output=True,
            env={**__import__("os").environ, "PYTHONIOENCODING": "cp1252"},
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr.decode(errors="replace"))

    def test_validator_runs_with_non_utf8_parent_console(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "validate_processes.py"),
                "--process-dir",
                str(ROOT / "tests" / "fixtures" / "process"),
            ],
            cwd=ROOT,
            capture_output=True,
            env={**__import__("os").environ, "PYTHONIOENCODING": "cp1252"},
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr.decode(errors="replace"))


if __name__ == "__main__":
    unittest.main()
