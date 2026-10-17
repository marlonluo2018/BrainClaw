from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "assistant_brain" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import screen_outgoing_body as scanner  # noqa: E402


def categories(result: list[dict]) -> set[str]:
    return {item["category"] for item in result}


def matches(result: list[dict], category: str) -> list[str]:
    return [item["match"] for item in result if item["category"] == category]


class ScreenOutgoingBodyTests(unittest.TestCase):
    def test_clean_body_has_no_findings(self) -> None:
        body = "<p>Thanks for confirming the November dates. I will arrange the invitations once the list is final.</p>"
        self.assertEqual([], scanner.findings(body))

    def test_detects_epd_number_with_label(self) -> None:
        result = scanner.findings("The class is tracked under EPD 1037482 in the plan.")
        self.assertEqual(["EPD 1037482"], matches(result, "epd-number"))
        self.assertEqual("high", result[0]["severity"])

    def test_epd_labelled_number_is_not_duplicated(self) -> None:
        result = scanner.findings("EPD 1037482 covers the GenAI class.")
        self.assertEqual(1, len(matches(result, "epd-number")))

    def test_detects_bare_seven_digit_number_as_low_severity(self) -> None:
        result = scanner.findings("Budget row 1037484 was approved yesterday.")
        self.assertEqual(["1037484"], matches(result, "epd-number"))
        self.assertEqual("low", result[0]["severity"])

    def test_detects_brainclaw_task_id(self) -> None:
        result = scanner.findings("Please see task T160 for the latest state.")
        self.assertEqual(["T160"], matches(result, "task-id"))

    def test_detects_po_number(self) -> None:
        result = scanner.findings("The vendor invoice references PO 4X12345.")
        self.assertEqual(["PO 4X12345"], matches(result, "po-number"))

    def test_detects_class_id(self) -> None:
        result = scanner.findings("Enrollment opens for Class ID CW101 once confirmed.")
        self.assertIn("Class CW101", matches(result, "class-id"))

    def test_detects_internal_link_hosts(self) -> None:
        body = "Details at https://w3.ibm.com/learning and https://ibm.ent.box.com/file/x."
        result = scanner.findings(body)
        self.assertIn("w3.ibm.com", matches(result, "internal-link"))
        self.assertIn("ibm.ent.box.com", matches(result, "internal-link"))

    def test_external_link_is_not_flagged(self) -> None:
        result = scanner.findings("Course outline: https://www.redhat.com/en/services/training/do188")
        self.assertNotIn("internal-link", categories(result))

    def test_detects_deliberation_wording_as_low(self) -> None:
        result = scanner.findings("As suggested by Huan Xu, we will run the class locally.")
        self.assertIn("deliberation-wording", categories(result))
        self.assertEqual("low", [f for f in result if f["category"] == "deliberation-wording"][0]["severity"])

    def test_subject_with_epd_is_high(self) -> None:
        result = scanner.findings("Body text.", subject="Q4 plan — EPD 1037482")
        self.assertIn("subject-identifier", categories(result))
        self.assertEqual("high", [f for f in result if f["category"] == "subject-identifier"][0]["severity"])

    def test_html_tags_and_comments_are_stripped(self) -> None:
        body = '<p>Approved.</p><!-- EPD 1037482 --><style>a{color:red}</style>'
        stripped = scanner.strip_html(body)
        self.assertNotIn("1037482", stripped)
        self.assertIn("Approved.", stripped)

    def test_html_entities_are_unescaped(self) -> None:
        stripped = scanner.strip_html("<p>Q3&nbsp;&amp;&nbsp;Q4</p>")
        self.assertIn("Q3\xa0&\xa0Q4", stripped)

    def test_cli_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            body_file = Path(temp_dir) / "T160-test.html"
            body_file.write_text("<p>EPD 1037482 approved.</p>", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "screen_outgoing_body.py"), str(body_file), "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(0, completed.returncode)
        payload = json.loads(completed.stdout)
        self.assertIn("findings", payload)
        self.assertEqual("epd-number", payload["findings"][0]["category"])

    def test_cli_missing_file_exits_nonzero(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "screen_outgoing_body.py"), "Z:/no-such-file.html"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(1, completed.returncode)
        self.assertIn("could not read", completed.stdout)


if __name__ == "__main__":
    unittest.main()
