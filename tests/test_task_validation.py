from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "assistant_brain" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_tasks  # noqa: E402


VALID_FIXTURE = ROOT / "tests" / "fixtures" / "tasks" / "T001-valid-task.md"


class TaskValidationTests(unittest.TestCase):
    def test_valid_fixture_executes_task_schema(self) -> None:
        errors, warnings = validate_tasks.errors_and_warnings(VALID_FIXTURE.parent)
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_missing_required_metadata_and_sections_fail(self) -> None:
        content = VALID_FIXTURE.read_text(encoding="utf-8")
        content = content.replace("**Exclude:** Production work and private contact data.\n", "")
        content = content.replace("## Contacts\n- **Requester:** Alex Example <alex@example.com>\n\n", "")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "T001-invalid.md"
            path.write_text(content, encoding="utf-8")
            errors, _ = validate_tasks.errors_and_warnings(Path(temp_dir))
        self.assertTrue(any("missing required header field: Exclude" in error for error in errors))
        self.assertTrue(any("missing required section: ## Contacts" in error for error in errors))

    def test_filename_mismatch_and_malformed_email_fail(self) -> None:
        content = VALID_FIXTURE.read_text(encoding="utf-8").replace(
            "alex@example.com", "alex@example", 1
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "T002-invalid.md"
            path.write_text(content, encoding="utf-8")
            errors, _ = validate_tasks.errors_and_warnings(Path(temp_dir))
        self.assertTrue(any("does not match heading" in error for error in errors))
        self.assertTrue(any("malformed contact email" in error for error in errors))

    def test_legacy_email_without_conversation_id_is_warning_only(self) -> None:
        content = VALID_FIXTURE.read_text(encoding="utf-8").replace(" <!-- conversation:C1 -->", "")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "T001-warning.md"
            path.write_text(content, encoding="utf-8")
            errors, warnings = validate_tasks.errors_and_warnings(Path(temp_dir))
        self.assertEqual([], errors)
        self.assertTrue(any("legacy allowed" in warning for warning in warnings))

    def test_scope_placeholder_and_too_many_tags_fail_schema(self) -> None:
        content = VALID_FIXTURE.read_text(encoding="utf-8")
        content = content.replace(
            "**Scope:** Validate task creation and matching-metadata maintenance behavior.",
            "**Scope:** TBD",
        ).replace("`Task Schema`, `Fixture`", "`A`, `B`, `C`, `D`, `E`")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "T001-invalid.md"
            path.write_text(content, encoding="utf-8")
            errors, _ = validate_tasks.errors_and_warnings(Path(temp_dir))
        self.assertTrue(any("Scope must be a positive" in error for error in errors))
        self.assertTrue(any("too long" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
