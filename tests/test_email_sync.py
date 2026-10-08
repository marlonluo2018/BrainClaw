from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "assistant_brain" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import email_sync  # noqa: E402
import email_sync_apply  # noqa: E402
import email_sync_candidates  # noqa: E402
from email_sync_catalog import TaskCatalog  # noqa: E402
import manage_ignore_candidates  # noqa: E402
import run_email_sync  # noqa: E402
import update_task  # noqa: E402


TASK_TEMPLATE = """# T001: Email Sync Test

**Status:** In Progress
**Created:** 2026-09-01
**Priority:** P2
**Category:** Email
**Geo:** Global
**Due:** TBD
**EPD:** —
**Scope:** Fixture review communications and approvals.
**Exclude:** Production task data.

---

## Contacts
- **Requester:** Alex <alex@example.com>

## Stakeholders

### RACI Matrix

| Stakeholder | Role |
|-------------|------|
| Alex <alex@example.com> | A |

**Legend:** R=Responsible, A=Accountable, C=Consulted, I=Informed

## Tags
`Fixture`, `Review`

---

## Asks

### My Actions

### Waiting on Others

## Timeline

## Current State
- [ ] Review request

## Notes
- Test fixture.
"""


def snapshot_email(entry_id: str = "E1", conversation_id: str = "C1", folder: str = "Inbox") -> dict:
    return {
        "entry_id": entry_id,
        "conversation_id": conversation_id,
        "subject": "Fixture subject",
        "sender": "Alex <alex@example.com>",
        "to_recipients": [],
        "cc_recipients": [],
        "received_time": "2026-09-18T10:30:00+08:00",
        "folder": folder,
        "body_preview": "Please review the fixture.",
    }


def valid_update(entry_id: str = "E1", conversation_id: str = "C1") -> dict:
    return {
        "task": "T001",
        "source": {
            "entry_id": entry_id,
            "conversation_id": conversation_id,
            "received_at": "2026-09-18T10:30:00+08:00",
            "direction": "in",
        },
        "timeline": {"tag": "email-in", "summary": "Alex requested fixture review."},
        "asks": {
            "add_my_actions": [{"due": "TBD", "contact": "Alex", "text": "Review fixture"}],
            "add_waiting": [],
            "complete_my_actions": [],
            "remove_waiting": [],
        },
        "current_state": {"add": [], "complete": []},
        "fields": {},
        "matching_review": {
            "scope": "checked-no-change",
            "exclude": "checked-no-change",
            "tags": "checked-no-change",
            "contacts": "checked-no-change",
            "identifiers": "checked-no-change",
        },
    }


class FetchWrapperTests(unittest.TestCase):
    def test_fetch_uses_public_outlook_skill_json_contract(self) -> None:
        payload = json.dumps([snapshot_email()])
        completed = mock.Mock(returncode=0, stdout=payload, stderr="")
        with mock.patch.object(run_email_sync.subprocess, "run", return_value=completed) as runner:
            raw, count = run_email_sync.fetch_recent_json_subprocess(
                days=3,
                timeout_seconds=90,
            )

        command = runner.call_args.args[0]
        self.assertEqual(sys.executable, command[0])
        self.assertEqual(str(run_email_sync.OUTLOOK_SKILL), command[1])
        self.assertEqual(["find-recent", "--days", "3", "--json"], command[2:])
        self.assertEqual(str(run_email_sync.OUTLOOK_SKILL_ROOT), runner.call_args.kwargs["cwd"])
        self.assertEqual("85", runner.call_args.kwargs["env"]["OUTLOOK_SKILL_TIMEOUT"])
        self.assertEqual(1, count)
        self.assertEqual("C1", json.loads(raw)[0]["conversation_id"])

    def test_fetch_rejects_outdated_skill_json_contract(self) -> None:
        payload = json.dumps([{"entry_id": "E1"}])
        completed = mock.Mock(returncode=0, stdout=payload, stderr="")
        with (
            mock.patch.object(run_email_sync.subprocess, "run", return_value=completed),
            self.assertRaisesRegex(RuntimeError, "missing entry_id/conversation_id"),
        ):
            run_email_sync.fetch_recent_json_subprocess(
                days=1,
                timeout_seconds=90,
            )

    def test_sync_has_no_maintenance_modes(self) -> None:
        normal = run_email_sync._parse_sync_args(["--days", "2"])
        self.assertEqual(2, normal.days)
        for removed in (["maintenance", "force-new-run"], ["--skip-fetch"]):
            with self.assertRaises(SystemExit):
                run_email_sync._parse_sync_args(removed)

    def test_artifacts_promote_together_after_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "latest-input.json"
            metadata_path = root / "latest-meta.json"
            output_path = root / "latest.md"

            candidates_path = root / "latest-candidates.json"

            def render(_input: Path, _metadata: Path, output: Path, **kwargs: object) -> None:
                output.write_text("new evidence view", encoding="utf-8")
                candidate_output = kwargs["candidates_output_path"]
                assert isinstance(candidate_output, Path)
                candidate_output.write_text("{}", encoding="utf-8")

            with mock.patch.object(run_email_sync, "run_email_sync", side_effect=render):
                run_email_sync.persist_sync_artifacts(
                    "[]",
                    {"schema_version": 1, "snapshot_id": "S1", "stale": False},
                    input_path,
                    metadata_path,
                    output_path,
                    candidates_path,
                    replace_input=True,
                    timeout_seconds=1,
                )
            self.assertEqual("[]", input_path.read_text(encoding="utf-8"))
            self.assertEqual("S1", json.loads(metadata_path.read_text(encoding="utf-8"))["snapshot_id"])
            self.assertEqual("new evidence view", output_path.read_text(encoding="utf-8"))
            self.assertEqual("{}", candidates_path.read_text(encoding="utf-8"))

    def test_artifact_failure_preserves_last_good_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "latest-input.json"
            metadata_path = root / "latest-meta.json"
            output_path = root / "latest.md"
            input_path.write_text("old input", encoding="utf-8")
            metadata_path.write_text("old metadata", encoding="utf-8")
            output_path.write_text("old output", encoding="utf-8")

            with mock.patch.object(run_email_sync, "run_email_sync", side_effect=RuntimeError("fixture")):
                with self.assertRaises(RuntimeError):
                    run_email_sync.persist_sync_artifacts(
                        "new input",
                        {"schema_version": 1, "snapshot_id": "S2", "stale": False},
                        input_path,
                        metadata_path,
                        output_path,
                        replace_input=True,
                        timeout_seconds=1,
                    )
            self.assertEqual("old input", input_path.read_text(encoding="utf-8"))
            self.assertEqual("old metadata", metadata_path.read_text(encoding="utf-8"))
            self.assertEqual("old output", output_path.read_text(encoding="utf-8"))

    def test_auto_days_uses_watermark_and_caps_at_30(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            meta = root / "latest-meta.json"
            output = root / "latest.md"
            watermark = datetime.now(timezone.utc) - timedelta(days=45)
            meta.write_text(json.dumps({"last_successful_fetch_at": watermark.isoformat()}), encoding="utf-8")
            self.assertEqual(30, run_email_sync._auto_determine_days(meta, output))

    def test_active_run_state_blocks_overlap_until_lock_expires(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state = Path(temp_dir) / "latest-run.json"
            now = datetime.now(timezone.utc)
            state.write_text(json.dumps({
                "run_id": "RUN1",
                "started_at": now.isoformat(),
                "status": "fetching",
            }), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Overlapping email-sync fetch blocked"):
                run_email_sync.ensure_single_fetch_allowed(state, now=now)
            later = now + timedelta(seconds=run_email_sync.FETCH_LOCK_MAX_AGE_SECONDS)
            run_email_sync.ensure_single_fetch_allowed(state, now=later)

    def test_completed_run_does_not_block_new_explicit_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state = Path(temp_dir) / "latest-run.json"
            now = datetime.now(timezone.utc)
            state.write_text(json.dumps({
                "run_id": "RUN0",
                "started_at": now.isoformat(),
                "status": "snapshot-ready",
            }), encoding="utf-8")
            run_email_sync.ensure_single_fetch_allowed(state, now=now)

    def test_main_allows_one_invocation_for_each_completed_explicit_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "latest-input.json"
            metadata_path = root / "latest-meta.json"
            output_path = root / "latest.md"
            run_state_path = root / "latest-run.json"
            argv = [
                "run_email_sync.py",
                "--days", "1",
                "--input-file", str(input_path),
                "--metadata-file", str(metadata_path),
                "--output-file", str(output_path),
                "--run-state-file", str(run_state_path),
            ]
            def fake_fetch(args: object) -> tuple[str, int, dict[str, object]]:
                return "[]", 0, {
                    "source": "outlook",
                    "stale": False,
                    "stale_reason": "",
                    "fetched_at": "2026-09-20T10:00:00+08:00",
                    "last_successful_fetch_at": "2026-09-20T10:00:00+08:00",
                }

            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(run_email_sync, "fetch_recent_json", side_effect=fake_fetch) as fetch_mock,
                mock.patch.object(run_email_sync, "persist_sync_artifacts"),
            ):
                run_email_sync.main()
                self.assertEqual("snapshot-ready", json.loads(run_state_path.read_text(encoding="utf-8"))["status"])
                run_email_sync.main()

            self.assertEqual(2, fetch_mock.call_count)

    def test_main_blocks_recorded_active_fetch_before_outlook(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_state_path = root / "latest-run.json"
            run_state_path.write_text(json.dumps({
                "run_id": "ACTIVE",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "status": "fetching",
            }), encoding="utf-8")
            argv = [
                "run_email_sync.py",
                "--days", "1",
                "--input-file", str(root / "latest-input.json"),
                "--metadata-file", str(root / "latest-meta.json"),
                "--output-file", str(root / "latest.md"),
                "--run-state-file", str(run_state_path),
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(run_email_sync, "fetch_recent_json") as fetch_mock,
                self.assertRaises(SystemExit) as blocked,
            ):
                run_email_sync.main()
            self.assertEqual(1, blocked.exception.code)
            fetch_mock.assert_not_called()


class EvidencePreparationTests(unittest.TestCase):
    def _catalog(self) -> TaskCatalog:
        return TaskCatalog(
            tasks={
                "T001": {
                    "task": "T001",
                    "title": "DO188 India delivery",
                    "path": "assistant_brain/tasks/T001-do188.md",
                    "lifecycle": "active",
                    "status": "In Progress",
                    "priority": "P1",
                    "geo": "India",
                    "due": "2026-10-01",
                    "scope": "Q4 India DO188",
                    "exclude": "China",
                    "contacts": [{"name": "Alex", "email": "alex@example.com", "role": "Vendor"}],
                    "identifiers": {"DO188"},
                    "lexical_terms": {"india", "delivery", "DO188"},
                    "exclusion_terms": {"china"},
                    "entry_ids": set(),
                    "conversation_ids": {"C1"},
                },
                "T099": {
                    "task": "T099",
                    "title": "Archived fixture",
                    "path": "assistant_brain/tasks/history/T099-fixture.md",
                    "lifecycle": "archived",
                    "status": "Completed",
                    "priority": "",
                    "geo": "",
                    "due": "",
                    "scope": "",
                    "exclude": "",
                    "contacts": [],
                    "identifiers": set(),
                    "lexical_terms": set(),
                    "exclusion_terms": set(),
                    "entry_ids": {"OLD"},
                    "conversation_ids": {"C99"},
                },
            },
            email_to_tasks={"alex@example.com": {"T001"}},
            name_to_tasks={"alex": {"T001"}},
        )

    def test_conversation_and_contact_are_evidence_not_confidence(self) -> None:
        email = {**snapshot_email(), "subject": "DO188 India schedule"}
        payload = email_sync_candidates.prepare_candidate_payload(
            [email], self._catalog(), {"snapshot_id": "S1", "stale": False}, set()
        )
        item = payload["emails"][0]
        self.assertEqual("review", item["review_status"])
        self.assertEqual(["T001"], item["evidence"]["conversation_tasks"])
        self.assertEqual("T001", item["candidate_tasks"][0]["task"])
        self.assertTrue(any("ConversationID" in reason for reason in item["candidate_tasks"][0]["reasons"]))
        self.assertNotIn("confidence", item["candidate_tasks"][0])

    def test_entry_id_seeds_conversation_migration(self) -> None:
        catalog = self._catalog()
        catalog.tasks["T001"]["entry_ids"] = {"E1"}
        catalog.tasks["T001"]["conversation_ids"] = set()
        mapping = email_sync_candidates.build_conversation_index([snapshot_email()], catalog)
        self.assertEqual({"T001"}, mapping["C1"])

    def test_archived_exact_entry_is_filtered_without_task_evaluation(self) -> None:
        email = {
            **snapshot_email("OLD", "C99"),
            "sender": "Casey <casey@example.com>",
            "subject": "Archived follow-up",
        }
        payload = email_sync_candidates.prepare_candidate_payload(
            [email], self._catalog(), {"snapshot_id": "S1", "stale": False}, set()
        )
        item = payload["emails"][0]
        self.assertEqual("filtered", item["review_status"])
        self.assertEqual(["T099"], item["evidence"]["archived_entry_tasks"])
        self.assertEqual([], item["candidate_tasks"])

    def test_archived_conversation_is_context_only_not_a_candidate(self) -> None:
        email = {
            **snapshot_email("NEW", "C99"),
            "sender": "Casey <casey@example.com>",
            "subject": "New action on completed thread",
        }
        payload = email_sync_candidates.prepare_candidate_payload(
            [email], self._catalog(), {"snapshot_id": "S1", "stale": False}, set()
        )
        item = payload["emails"][0]
        self.assertEqual("review", item["review_status"])
        self.assertEqual(["T099"], item["evidence"]["archived_conversation_tasks"])
        self.assertEqual([], item["candidate_tasks"])
        self.assertNotIn("T099", item["evidence"]["conversation_tasks"])

    def test_only_strict_noise_is_filtered_and_calendar_stays_visible(self) -> None:
        emails = [
            {**snapshot_email("N1", "CN"), "subject": "Automatic reply: out of office"},
            {
                **snapshot_email("CAL", "CC"),
                "subject": "Invitation: DO188 planning",
                "message_class": "IPM.Schedule.Meeting.Request",
                "meeting_status": "meeting_request",
            },
            snapshot_email("U1", "CU"),
            {
                **snapshot_email("WEB", "CW"),
                "subject": "You're invited: webinar for learning leaders",
                "sender": "noreply@example.com",
            },
        ]
        payload = email_sync_candidates.prepare_candidate_payload(
            emails, self._catalog(), {"snapshot_id": "S1", "stale": False}, set()
        )
        self.assertEqual("filtered", payload["emails"][0]["review_status"])
        self.assertEqual("review", payload["emails"][1]["review_status"])
        self.assertEqual("calendar", payload["emails"][1]["message_type"])
        self.assertEqual("review", payload["emails"][2]["review_status"])
        self.assertEqual("review", payload["emails"][3]["review_status"])

    def test_exact_ignore_pool_entry_is_suppressed_but_unmatched_is_not(self) -> None:
        emails = [snapshot_email("IGN", "CI"), snapshot_email("OPEN", "CO")]
        empty = TaskCatalog(tasks={}, email_to_tasks={}, name_to_tasks={})
        payload = email_sync_candidates.prepare_candidate_payload(
            emails, empty, {"snapshot_id": "S1", "stale": False}, {"IGN"}
        )
        self.assertEqual("ignored", payload["emails"][0]["review_status"])
        self.assertEqual("review", payload["emails"][1]["review_status"])
        self.assertEqual([], payload["emails"][1]["candidate_tasks"])

    def test_snapshot_metadata_count_must_match_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            snapshot = root / "input.json"
            metadata = root / "meta.json"
            raw = json.dumps([snapshot_email()])
            snapshot.write_text(raw, encoding="utf-8")
            metadata.write_text(json.dumps({
                "schema_version": 1,
                "snapshot_id": hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16],
                "stale": False,
                "email_count": 2,
            }), encoding="utf-8")
            with self.assertRaisesRegex(email_sync.EvidenceBundleError, "email_count"):
                email_sync.build_evidence_bundle(snapshot, metadata)

    def test_generated_candidate_contract_is_schema_valid(self) -> None:
        payload = email_sync_candidates.prepare_candidate_payload(
            [snapshot_email()], self._catalog(), {"snapshot_id": "S1", "stale": False}, set()
        )
        email_sync.validate_candidate_payload(payload)

    def test_processor_does_not_write_ignore_pool(self) -> None:
        emails = [
            snapshot_email("UNMATCHED", "CU"),
            {**snapshot_email("NOISE", "CN"), "subject": "Automatic reply: out of office"},
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_file = root / "input.json"
            output_file = root / "output.md"
            candidates_file = root / "candidates.json"
            input_file.write_text(json.dumps(emails), encoding="utf-8")
            sentinel_pool = {"updated_at": None, "candidates": {}}
            empty = TaskCatalog(tasks={}, email_to_tasks={}, name_to_tasks={})
            with (
                mock.patch.object(email_sync, "build_task_catalog", return_value=empty),
                mock.patch.object(email_sync, "load_ignore_candidates", return_value=sentinel_pool),
                mock.patch.object(email_sync, "cleanup_old_results"),
                mock.patch.object(
                    sys,
                    "argv",
                    [
                        "email_sync.py", "--input-file", str(input_file),
                        "--output-file", str(output_file),
                        "--candidates-file", str(candidates_file),
                    ],
                ),
            ):
                email_sync.main()
            bundle = json.loads(candidates_file.read_text(encoding="utf-8"))
            self.assertEqual(["review", "filtered"], [item["review_status"] for item in bundle["emails"]])
            self.assertEqual({}, sentinel_pool["candidates"])


class TaskUpdateTests(unittest.TestCase):
    def test_timestamp_tag_entry_and_conversation_marker(self) -> None:
        updated, report = update_task.plan_task_update(TASK_TEMPLATE, valid_update())
        self.assertTrue(report["updated"])
        self.assertIn("**Fri Sep 18, 2026** [email-in]", updated)
        self.assertIn("<!-- email:E1 --> <!-- conversation:C1 -->", updated)
        self.assertIn("🎯 to Alex: Review fixture", updated)

    def test_entry_id_and_direction_tag_consistency_are_required(self) -> None:
        missing = valid_update()
        missing["source"]["entry_id"] = ""
        with self.assertRaises(update_task.TaskUpdateError):
            update_task.validate_task_update(missing)
        wrong_direction = valid_update()
        wrong_direction["source"]["direction"] = "out"
        with self.assertRaises(update_task.TaskUpdateError):
            update_task.validate_task_update(wrong_direction)

    def test_duplicate_timeline_still_allows_new_ask_and_is_idempotent(self) -> None:
        first_update = valid_update()
        first_update["asks"]["add_my_actions"] = []
        once, _ = update_task.plan_task_update(TASK_TEMPLATE, first_update)
        second_update = valid_update()
        twice, report = update_task.plan_task_update(once, second_update)
        self.assertEqual(1, twice.count("<!-- email:E1 -->"))
        self.assertIn("+Ask My Actions", report["changes"])
        third, third_report = update_task.plan_task_update(twice, second_update)
        self.assertEqual(twice, third)
        self.assertFalse(third_report["updated"])

    def test_matching_review_is_mandatory_and_strict(self) -> None:
        missing = valid_update()
        del missing["matching_review"]
        with self.assertRaisesRegex(update_task.TaskUpdateError, "matching_review is required"):
            update_task.validate_task_update(missing)

        invalid = valid_update()
        invalid["matching_review"]["scope"] = "skipped"
        with self.assertRaisesRegex(update_task.TaskUpdateError, "matching_review.scope"):
            update_task.validate_task_update(invalid)

    def test_matching_metadata_fields_are_updated_idempotently(self) -> None:
        update = valid_update()
        update["timeline"] = None
        update["asks"] = {}
        update["fields"] = {
            "Category": "Planning",
            "Geo": "India",
            "EPD": "1037118",
            "Scope": "Red Hat Ascend India launch coordination.",
            "Exclude": "Paid course delivery and procurement.",
        }
        update["tags"] = {"add": ["Red Hat", "1037118"], "remove": ["Fixture", "Review"]}
        update["contacts"] = {
            "upsert": [{"name": "Prantar Deka", "email": "prantar@example.com", "role": "Requester"}],
            "remove": ["alex@example.com"],
        }
        update["raci"] = {
            "upsert": [{"name": "Prantar Deka", "email": "prantar@example.com", "role": "A"}],
            "remove": ["alex@example.com"],
        }
        update["notes"] = {"add": ["Matching metadata refreshed from the source message."]}
        update["matching_review"] = {key: "updated" for key in update["matching_review"]}

        once, report = update_task.plan_task_update(TASK_TEMPLATE, update)
        self.assertTrue(report["updated"])
        self.assertIn("**Category:** Planning", once)
        self.assertIn("**Geo:** India", once)
        self.assertIn("**EPD:** 1037118", once)
        self.assertIn("**Scope:** Red Hat Ascend India launch coordination.", once)
        self.assertIn("**Exclude:** Paid course delivery and procurement.", once)
        self.assertIn("`Red Hat`, `1037118`", once)
        self.assertNotIn("alex@example.com", once)
        self.assertIn("Prantar Deka <prantar@example.com>", once)
        self.assertIn("- Matching metadata refreshed from the source message.", once)

        twice, second_report = update_task.plan_task_update(once, update)
        self.assertEqual(once, twice)
        self.assertFalse(second_report["updated"])

    def test_tag_limit_and_contact_shapes_are_enforced(self) -> None:
        update = valid_update()
        update["tags"] = {"add": ["A", "B", "C"], "remove": []}
        update["matching_review"]["tags"] = "updated"
        with self.assertRaisesRegex(update_task.TaskUpdateError, "at most 4 tags"):
            update_task.plan_task_update(TASK_TEMPLATE, update)

        invalid_contact = valid_update()
        invalid_contact["contacts"] = {
            "upsert": [{"name": "Alex", "email": "not-an-email", "role": "Requester"}],
            "remove": [],
        }
        with self.assertRaises(update_task.TaskUpdateError):
            update_task.validate_task_update(invalid_contact)

    def test_scope_priority_and_minimum_tag_contract_are_enforced(self) -> None:
        invalid_scope = valid_update()
        invalid_scope["fields"] = {"Scope": "TBD"}
        invalid_scope["matching_review"]["scope"] = "updated"
        with self.assertRaisesRegex(update_task.TaskUpdateError, "positive, non-placeholder"):
            update_task.validate_task_update(invalid_scope)

        negative_scope = valid_update()
        negative_scope["fields"] = {"Scope": "Ascend launch, NOT course delivery."}
        negative_scope["matching_review"]["scope"] = "updated"
        with self.assertRaisesRegex(update_task.TaskUpdateError, "positive wording"):
            update_task.validate_task_update(negative_scope)

        invalid_priority = valid_update()
        invalid_priority["fields"] = {"Priority": "urgent"}
        with self.assertRaisesRegex(update_task.TaskUpdateError, "P1, P2, or P3"):
            update_task.validate_task_update(invalid_priority)

        no_tags = valid_update()
        no_tags["tags"] = {"add": [], "remove": ["Fixture", "Review"]}
        no_tags["matching_review"]["tags"] = "updated"
        with self.assertRaisesRegex(update_task.TaskUpdateError, "at least 1 tag"):
            update_task.plan_task_update(TASK_TEMPLATE, no_tags)

    def test_asks_and_current_state_can_be_completed(self) -> None:
        content = TASK_TEMPLATE.replace(
            "### My Actions\n",
            "### My Actions\n- [ ] {Due: TBD} 🎯 to Alex: Review fixture\n",
        ).replace(
            "### Waiting on Others\n",
            "### Waiting on Others\n- {Due: TBD} ⏳ Casey: Approve fixture\n",
        )
        update = valid_update()
        update["timeline"] = None
        update["asks"] = {
            "add_my_actions": [], "add_waiting": [],
            "complete_my_actions": ["Review fixture"], "remove_waiting": ["Approve fixture"],
        }
        update["current_state"] = {"add": [], "complete": ["Review request"]}
        updated, _ = update_task.plan_task_update(content, update)
        self.assertIn("[x] {Due: TBD} 🎯 to Alex: Review fixture", updated)
        self.assertNotIn("Approve fixture", updated)
        self.assertIn("- [x] Review request", updated)

        for key, section in (("complete_my_actions", "asks"), ("remove_waiting", "asks"), ("complete", "current_state")):
            miss = valid_update()
            miss["timeline"] = None
            miss["asks"] = {"add_my_actions": [], "add_waiting": [], "complete_my_actions": [], "remove_waiting": []}
            miss["current_state"] = {"add": [], "complete": []}
            miss[section][key] = ["No such item"]
            with self.assertRaisesRegex(update_task.TaskUpdateError, "matched no line"):
                update_task.plan_task_update(content, miss)


class IgnoreManagerTests(unittest.TestCase):
    def test_missing_snapshot_entry_fails_without_outlook_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot = Path(temp_dir) / "input.json"
            snapshot.write_text("[]", encoding="utf-8")
            pool = {"updated_at": None, "candidates": {}}
            self.assertEqual(1, manage_ignore_candidates.cmd_add(pool, "MISSING", "No action", snapshot))
            self.assertEqual({}, pool["candidates"])

    def test_strict_load_rejects_corrupt_pool(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pool_file = Path(temp_dir) / "ignore.json"
            pool_file.write_text("{not-json", encoding="utf-8")
            with self.assertRaises(ValueError):
                manage_ignore_candidates.load_pool(pool_file, strict=True)

    def test_cleanup_accepts_legacy_naive_timestamps(self) -> None:
        candidates = {
            "E1": {"last_seen_at": datetime.now().replace(microsecond=0).isoformat()},
        }
        self.assertIn("E1", manage_ignore_candidates.cleanup_candidates(candidates))

    def test_add_preserves_conversation_and_saves_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pool_file = Path(temp_dir) / "ignore.json"
            pool = {"updated_at": None, "candidates": {}}
            candidate = manage_ignore_candidates.add_candidate(pool, snapshot_email(), "Informational only")
            manage_ignore_candidates.save_pool(pool, pool_file)
            stored = json.loads(pool_file.read_text(encoding="utf-8"))
            self.assertEqual("C1", candidate["conversation_id"])
            self.assertEqual("semantic_classifier", stored["candidates"]["E1"]["source_section"])
            self.assertFalse(any(pool_file.parent.glob("*.tmp")))


class ApplyPlanTests(unittest.TestCase):
    def _fixture(self, root: Path, *, stale: bool = False, snapshot_id: str | None = None) -> dict[str, Path]:
        tasks = root / "tasks"
        tasks.mkdir()
        task = tasks / "T001-email-sync-test.md"
        task.write_text(TASK_TEMPLATE, encoding="utf-8")
        snapshot = root / "latest-input.json"
        snapshot_text = json.dumps([snapshot_email()])
        snapshot.write_text(snapshot_text, encoding="utf-8")
        effective_snapshot_id = snapshot_id or hashlib.sha256(snapshot_text.encode("utf-8")).hexdigest()[:16]
        metadata = root / "latest-meta.json"
        metadata.write_text(json.dumps({
            "schema_version": 1,
            "snapshot_id": effective_snapshot_id,
            "stale": stale,
            "stale_reason": "fixture",
        }), encoding="utf-8")
        plan = root / "latest-plan.json"
        plan.write_text(json.dumps({
            "schema_version": 1,
            "snapshot_id": effective_snapshot_id,
            "evaluated_tasks": ["T001"],
            "task_updates": [valid_update()],
            "ignore": [],
            "unresolved": [],
        }), encoding="utf-8")
        return {
            "tasks": tasks, "task": task, "snapshot": snapshot, "metadata": metadata,
            "plan": plan, "ignore": root / "ignore.json", "applied": root / "applied.json",
        }

    def test_rejects_stale_snapshot_and_snapshot_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._fixture(Path(temp_dir), stale=True)
            original = paths["task"].read_text(encoding="utf-8")
            with self.assertRaises(email_sync_apply.SyncPlanError):
                email_sync_apply.apply_plan(
                    paths["plan"], paths["snapshot"], paths["metadata"], paths["ignore"], paths["applied"],
                    tasks_dir=paths["tasks"],
                )
            self.assertEqual(original, paths["task"].read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._fixture(Path(temp_dir))
            plan = json.loads(paths["plan"].read_text(encoding="utf-8"))
            plan["snapshot_id"] = "WRONG"
            paths["plan"].write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaises(email_sync_apply.SyncPlanError):
                email_sync_apply.apply_plan(
                    paths["plan"], paths["snapshot"], paths["metadata"], paths["ignore"], paths["applied"],
                    tasks_dir=paths["tasks"],
                )

    def test_validates_all_updates_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._fixture(Path(temp_dir))
            original = paths["task"].read_text(encoding="utf-8")
            plan = json.loads(paths["plan"].read_text(encoding="utf-8"))
            invalid = valid_update()
            invalid["task"] = "T999"
            plan["task_updates"].append(invalid)
            paths["plan"].write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaises(email_sync_apply.SyncPlanError):
                email_sync_apply.apply_plan(
                    paths["plan"], paths["snapshot"], paths["metadata"], paths["ignore"], paths["applied"],
                    tasks_dir=paths["tasks"],
                )
            self.assertEqual(original, paths["task"].read_text(encoding="utf-8"))
            self.assertFalse(paths["applied"].exists())

    def test_success_applies_task_ignore_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._fixture(Path(temp_dir))
            second = snapshot_email("E2", "C2")
            snapshot_text = json.dumps([snapshot_email(), second])
            paths["snapshot"].write_text(snapshot_text, encoding="utf-8")
            snapshot_id = hashlib.sha256(snapshot_text.encode("utf-8")).hexdigest()[:16]
            metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
            metadata["snapshot_id"] = snapshot_id
            paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")
            plan = json.loads(paths["plan"].read_text(encoding="utf-8"))
            plan["snapshot_id"] = snapshot_id
            plan["ignore"] = [{"entry_id": "E2", "reason": "Informational notice; no task or action."}]
            paths["plan"].write_text(json.dumps(plan), encoding="utf-8")
            report = email_sync_apply.apply_plan(
                paths["plan"], paths["snapshot"], paths["metadata"], paths["ignore"], paths["applied"],
                tasks_dir=paths["tasks"],
            )
            self.assertIn("<!-- conversation:C1 -->", paths["task"].read_text(encoding="utf-8"))
            self.assertIn("E2", json.loads(paths["ignore"].read_text(encoding="utf-8"))["candidates"])
            self.assertEqual(json.loads(paths["metadata"].read_text(encoding="utf-8"))["snapshot_id"], report["snapshot_id"])
            self.assertEqual(1, report["audit"]["task_files_modified"])
            self.assertEqual(report, json.loads(paths["applied"].read_text(encoding="utf-8")))

    def test_atomic_apply_can_refresh_matching_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._fixture(Path(temp_dir))
            plan = json.loads(paths["plan"].read_text(encoding="utf-8"))
            update = plan["task_updates"][0]
            update["fields"] = {"EPD": "1037118", "Scope": "Updated fixture scope.", "Exclude": "Noise."}
            update["tags"] = {"add": ["1037118"], "remove": ["Review"]}
            update["contacts"] = {
                "upsert": [{"name": "Casey", "email": "casey@example.com", "role": "Approver"}],
                "remove": [],
            }
            update["raci"] = {
                "upsert": [{"name": "Casey", "email": "casey@example.com", "role": "C"}],
                "remove": [],
            }
            update["notes"] = {"add": ["Metadata refreshed atomically."]}
            update["matching_review"] = {key: "updated" for key in update["matching_review"]}
            paths["plan"].write_text(json.dumps(plan), encoding="utf-8")

            report = email_sync_apply.apply_plan(
                paths["plan"], paths["snapshot"], paths["metadata"], paths["ignore"], paths["applied"],
                tasks_dir=paths["tasks"],
            )
            content = paths["task"].read_text(encoding="utf-8")
            self.assertIn("**EPD:** 1037118", content)
            self.assertIn("Casey <casey@example.com>", content)
            self.assertIn("Metadata refreshed atomically.", content)
            self.assertEqual(1, report["audit"]["task_files_modified"])

    def test_snapshot_content_must_match_metadata_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._fixture(Path(temp_dir))
            changed = [snapshot_email(), snapshot_email("E2", "C2")]
            paths["snapshot"].write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaises(email_sync_apply.SyncPlanError):
                email_sync_apply.apply_plan(
                    paths["plan"], paths["snapshot"], paths["metadata"], paths["ignore"], paths["applied"],
                    tasks_dir=paths["tasks"],
                )

    def test_corrupt_ignore_pool_rejects_before_task_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._fixture(Path(temp_dir))
            original = paths["task"].read_text(encoding="utf-8")
            paths["ignore"].write_text("{not-json", encoding="utf-8")
            with self.assertRaises(email_sync_apply.SyncPlanError):
                email_sync_apply.apply_plan(
                    paths["plan"], paths["snapshot"], paths["metadata"], paths["ignore"], paths["applied"],
                    tasks_dir=paths["tasks"],
                )
            self.assertEqual(original, paths["task"].read_text(encoding="utf-8"))
            self.assertFalse(paths["applied"].exists())

    def test_archived_tasks_cannot_be_evaluated_or_mutated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            paths = self._fixture(root)
            paths["task"].unlink()
            archive = paths["tasks"] / "history" / "2026-Q3"
            archive.mkdir(parents=True)
            archived_task = archive / "T001-email-sync-test.md"
            archived_task.write_text(TASK_TEMPLATE, encoding="utf-8")

            plan = json.loads(paths["plan"].read_text(encoding="utf-8"))
            plan["task_updates"] = []
            paths["plan"].write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(email_sync_apply.SyncPlanError, "Invalid evaluated_tasks"):
                email_sync_apply.apply_plan(
                    paths["plan"], paths["snapshot"], paths["metadata"], paths["ignore"], paths["applied"],
                    tasks_dir=paths["tasks"],
                )
            self.assertFalse(paths["applied"].exists())

    def test_published_schema_is_executed_not_only_documented(self) -> None:
        schema = json.loads((ROOT / "assistant_brain/formats/email_sync_plan.schema.json").read_text(encoding="utf-8"))
        schema["properties"]["snapshot_id"]["minLength"] = 10
        with self.assertRaisesRegex(email_sync_apply.SyncPlanError, "Plan schema validation failed"):
            email_sync_apply.validate_plan_shape({
                "schema_version": 1,
                "snapshot_id": "short",
                "evaluated_tasks": [],
                "task_updates": [],
                "ignore": [],
            }, schema=schema)

    def test_apply_has_no_stale_override(self) -> None:
        email_sync_apply._parse_apply_args([])
        for removed in (["maintenance", "apply-stale"], ["--allow-stale"]):
            with self.assertRaises(SystemExit):
                email_sync_apply._parse_apply_args(removed)

    def test_every_review_email_needs_an_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._fixture(Path(temp_dir))
            snapshot_id = json.loads(paths["metadata"].read_text(encoding="utf-8"))["snapshot_id"]
            candidates = paths["snapshot"].parent / "latest-candidates.json"
            candidates.write_text(json.dumps({
                "snapshot_id": snapshot_id,
                "emails": [
                    {"entry_id": "E1", "review_status": "review"},
                    {"entry_id": "E9", "review_status": "review"},
                    {"entry_id": "E8", "review_status": "filtered"},
                ],
            }), encoding="utf-8")
            original = paths["task"].read_text(encoding="utf-8")
            with self.assertRaisesRegex(email_sync_apply.SyncPlanError, "1 review email"):
                email_sync_apply.apply_plan(
                    paths["plan"], paths["snapshot"], paths["metadata"], paths["ignore"], paths["applied"],
                    tasks_dir=paths["tasks"], candidates_file=candidates,
                )
            self.assertEqual(original, paths["task"].read_text(encoding="utf-8"))

            candidates.write_text(json.dumps({
                "snapshot_id": snapshot_id,
                "emails": [{"entry_id": "E1", "review_status": "review"}],
            }), encoding="utf-8")
            report = email_sync_apply.apply_plan(
                paths["plan"], paths["snapshot"], paths["metadata"], paths["ignore"], paths["applied"],
                tasks_dir=paths["tasks"], candidates_file=candidates,
            )
            self.assertEqual(1, report["audit"]["task_updates_requested"])

    def test_plan_schema_document_and_adapters_are_canonical(self) -> None:
        schema = json.loads((ROOT / "assistant_brain/formats/email_sync_plan.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(1, schema["properties"]["schema_version"]["const"])
        self.assertIn("evaluated_tasks", schema["required"])
        self.assertIn("task_updates", schema["required"])
        email_sync_apply.validate_plan_shape({
            "schema_version": 1,
            "snapshot_id": "S1",
            "evaluated_tasks": ["T001"],
            "task_updates": [],
            "ignore": [],
        })
        with self.assertRaises(email_sync_apply.SyncPlanError):
            email_sync_apply.validate_plan_shape({
                "schema_version": 1,
                "snapshot_id": "S1",
                "evaluated_tasks": [],
                "task_updates": [],
                "ignore": [],
                "unexpected": True,
            })
        invalid_nested = valid_update()
        invalid_nested["asks"]["add_my_actions"][0]["unexpected"] = True
        with self.assertRaises(email_sync_apply.SyncPlanError):
            email_sync_apply.validate_plan_shape({
                "schema_version": 1,
                "snapshot_id": "S1",
                "evaluated_tasks": ["T001"],
                "task_updates": [invalid_nested],
                "ignore": [],
            })
        canonical = (ROOT / "assistant_brain/agents/email-classifier.md").read_text(encoding="utf-8")
        self.assertIn("**Never run `run_email_sync.py`**", canonical)
        self.assertIn("Don't open anything under `assistant_brain/tasks/history/`", canonical)
        self.assertIn("get-email <EntryID>", canonical)
        self.assertIn("py -3 assistant_brain/scripts/email_sync_apply.py", canonical)
        workflow = (ROOT / "assistant_brain/workflows/EMAIL_WORKFLOW.md").read_text(encoding="utf-8")
        self.assertIn("**Fetch once.**", workflow)
        self.assertIn("exactly once", workflow)
        self.assertIn("Spawn exactly one `email-classifier`", workflow)
        prompt = (ROOT / "assistant_brain/prompts/SYSTEM_PROMPT.md").read_text(encoding="utf-8")
        self.assertIn("assistant_brain/workflows/EMAIL_WORKFLOW.md", prompt)
        self.assertLess(len(prompt.encode("utf-8")), 8 * 1024)
        for entrypoint in (".claude/agents/email-classifier.md", ".opencode/agents/email-classifier.md"):
            text = (ROOT / entrypoint).read_text(encoding="utf-8")
            self.assertIn("assistant_brain/agents/email-classifier.md", text)
            self.assertNotIn("update_task.py", text)
            self.assertNotIn("Step 1: Semantic Matching", text)

    def test_plan_rejects_duplicate_outcomes_for_one_email(self) -> None:
        base = {
            "schema_version": 1,
            "snapshot_id": "S1",
            "evaluated_tasks": ["T001"],
            "task_updates": [valid_update()],
            "ignore": [],
            "unresolved": [],
        }
        duplicate_task = json.loads(json.dumps(base))
        duplicate_task["task_updates"].append(valid_update())
        with self.assertRaises(email_sync_apply.SyncPlanError):
            email_sync_apply.validate_plan_shape(duplicate_task)

        duplicate_ignore = json.loads(json.dumps(base))
        duplicate_ignore["task_updates"] = []
        duplicate_ignore["ignore"] = [
            {"entry_id": "E1", "reason": "Informational"},
            {"entry_id": "E1", "reason": "Still informational"},
        ]
        with self.assertRaises(email_sync_apply.SyncPlanError):
            email_sync_apply.validate_plan_shape(duplicate_ignore)

        duplicate_unresolved = json.loads(json.dumps(base))
        duplicate_unresolved["task_updates"] = []
        duplicate_unresolved["unresolved"] = [
            {"entry_id": "E1", "reason": "Review", "task_candidates": []},
            {"entry_id": "E1", "reason": "Review again", "task_candidates": []},
        ]
        with self.assertRaises(email_sync_apply.SyncPlanError):
            email_sync_apply.validate_plan_shape(duplicate_unresolved)

    def test_one_email_can_update_multiple_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._fixture(Path(temp_dir))
            second_task = paths["tasks"] / "T002-second-task.md"
            second_task.write_text(TASK_TEMPLATE.replace("T001", "T002"), encoding="utf-8")
            plan = json.loads(paths["plan"].read_text(encoding="utf-8"))
            second_update = valid_update()
            second_update["task"] = "T002"
            second_update["timeline"]["summary"] = "Alex requested the same fixture review for the second task."
            plan["evaluated_tasks"].append("T002")
            plan["task_updates"].append(second_update)
            paths["plan"].write_text(json.dumps(plan), encoding="utf-8")

            report = email_sync_apply.apply_plan(
                paths["plan"], paths["snapshot"], paths["metadata"], paths["ignore"], paths["applied"],
                tasks_dir=paths["tasks"],
            )

            self.assertEqual(2, report["audit"]["task_updates_requested"])
            self.assertIn("<!-- email:E1 -->", paths["task"].read_text(encoding="utf-8"))
            self.assertIn("<!-- email:E1 -->", second_task.read_text(encoding="utf-8"))

    def test_task_ignore_overlap_rejects_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._fixture(Path(temp_dir))
            original = paths["task"].read_text(encoding="utf-8")
            plan = json.loads(paths["plan"].read_text(encoding="utf-8"))
            plan["ignore"] = [{"entry_id": "E1", "reason": "Incorrect duplicate outcome"}]
            paths["plan"].write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaises(email_sync_apply.SyncPlanError):
                email_sync_apply.apply_plan(
                    paths["plan"], paths["snapshot"], paths["metadata"], paths["ignore"], paths["applied"],
                    tasks_dir=paths["tasks"],
                )
            self.assertEqual(original, paths["task"].read_text(encoding="utf-8"))
            self.assertFalse(paths["ignore"].exists())
            self.assertFalse(paths["applied"].exists())


if __name__ == "__main__":
    unittest.main()
