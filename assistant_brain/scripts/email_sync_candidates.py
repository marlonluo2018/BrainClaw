"""Prepare structured evidence for semantic email-to-task classification."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from email_sync_catalog import TaskCatalog, extract_identifiers, extract_terms, public_task_catalog, scope_time_warning

STRICT_NOISE_PREFIXES = {
    "automatic reply:": "auto-reply",
    "out of office:": "auto-reply",
    "one-time passcode": "otp",
    "undeliverable:": "undeliverable",
    "delivery status notification": "undeliverable",
    "message recall report:": "recall",
    "recall:": "recall",
}
STRICT_NOISE_CONTAINS: dict[str, str] = {}
MAX_LEXICAL_CANDIDATES = 8


def extract_email_address(value: str) -> str:
    match = re.search(r"<([^<>]+@[^<>]+)>", value)
    if match:
        return match.group(1).strip().lower()
    return value.strip().lower() if "@" in value else ""


def extract_display_name(value: str) -> str:
    return value.split("<", 1)[0].strip() if "<" in value else value.strip()


def message_type(email: dict[str, Any]) -> str:
    message_class = str(email.get("message_class", ""))
    meeting_status = str(email.get("meeting_status", ""))
    if message_class.startswith("IPM.Schedule.Meeting") or meeting_status.startswith("meeting"):
        return "calendar"
    return "mail"


def direction(email: dict[str, Any]) -> str:
    if message_type(email) == "calendar":
        return "calendar"
    folder = str(email.get("folder", "")).lower()
    return "out" if "sent" in folder or "已发送" in folder else "in"


def strict_noise_reason(email: dict[str, Any]) -> str | None:
    """Filter only categories safe to classify without semantic ownership judgment."""
    subject = str(email.get("subject", "")).strip().lower()
    for prefix, reason in STRICT_NOISE_PREFIXES.items():
        if subject.startswith(prefix):
            return reason
    for fragment, reason in STRICT_NOISE_CONTAINS.items():
        if fragment in subject:
            return reason
    return None


def build_conversation_index(emails: list[dict[str, Any]], catalog: TaskCatalog) -> dict[str, set[str]]:
    """Combine persisted thread markers with EntryID-based migration evidence."""
    conversation_to_tasks: dict[str, set[str]] = {}
    entry_to_tasks: dict[str, set[str]] = {}
    for task_id, record in catalog.tasks.items():
        for conversation_id in record["conversation_ids"]:
            if conversation_id:
                conversation_to_tasks.setdefault(conversation_id, set()).add(task_id)
        for entry_id in record["entry_ids"]:
            if entry_id:
                entry_to_tasks.setdefault(entry_id, set()).add(task_id)

    for email in emails:
        entry_id = str(email.get("entry_id", "")).strip()
        conversation_id = str(email.get("conversation_id", "")).strip()
        if entry_id and conversation_id and entry_id in entry_to_tasks:
            conversation_to_tasks.setdefault(conversation_id, set()).update(entry_to_tasks[entry_id])
    return conversation_to_tasks


def _recipient_values(email: dict[str, Any]) -> tuple[set[str], set[str]]:
    emails = set()
    names = set()
    sender = str(email.get("sender", ""))
    sender_email = extract_email_address(sender)
    sender_name = extract_display_name(sender).lower()
    if sender_email:
        emails.add(sender_email)
    if sender_name:
        names.add(sender_name)
    for field in ("to_recipients", "cc_recipients"):
        for recipient in email.get(field, []) or []:
            address = str(recipient.get("address", "")).strip().lower()
            name = str(recipient.get("name", "")).strip().lower()
            if address:
                emails.add(address)
            if name:
                names.add(name)
    return emails, names


def _evidence_map_to_list(mapping: dict[str, set[str]]) -> list[dict[str, Any]]:
    return [
        {"task": task_id, "values": sorted(values)}
        for task_id, values in sorted(mapping.items())
    ]


def _candidate_evidence(
    email: dict[str, Any],
    catalog: TaskCatalog,
    conversation_to_tasks: dict[str, set[str]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    entry_id = str(email.get("entry_id", "")).strip()
    conversation_id = str(email.get("conversation_id", "")).strip()
    text = f"{email.get('subject', '')} {email.get('body_preview', '')}"
    email_terms = extract_terms(text)
    email_identifiers = extract_identifiers(text)
    participant_emails, participant_names = _recipient_values(email)

    all_entry_tasks = {
        task_id
        for task_id, record in catalog.tasks.items()
        if entry_id and entry_id in record["entry_ids"]
    }
    all_conversation_tasks = set(conversation_to_tasks.get(conversation_id, set())) if conversation_id else set()
    entry_tasks = {
        task_id for task_id in all_entry_tasks
        if catalog.tasks[task_id]["lifecycle"] == "active"
    }
    conversation_tasks = {
        task_id for task_id in all_conversation_tasks
        if catalog.tasks[task_id]["lifecycle"] == "active"
    }
    archived_entry_tasks = sorted(all_entry_tasks - entry_tasks)
    archived_conversation_tasks = sorted(all_conversation_tasks - conversation_tasks)

    identifier_hits: dict[str, set[str]] = {}
    contact_hits: dict[str, set[str]] = {}
    lexical_hits: dict[str, set[str]] = {}
    warning_hits: dict[str, set[str]] = {}

    for task_id, record in catalog.tasks.items():
        if record["lifecycle"] != "active":
            continue
        identifiers = email_identifiers & record["identifiers"]
        if identifiers:
            identifier_hits[task_id] = identifiers

        matched_contacts = set()
        for participant_email in participant_emails:
            if task_id in catalog.email_to_tasks.get(participant_email, set()):
                matched_contacts.add(participant_email)
        for participant_name in participant_names:
            if task_id in catalog.name_to_tasks.get(participant_name, set()):
                matched_contacts.add(participant_name)
        if matched_contacts:
            contact_hits[task_id] = matched_contacts

        overlap = email_terms & record["lexical_terms"]
        if overlap:
            lexical_hits[task_id] = overlap

        exclusion_overlap = email_terms & record["exclusion_terms"]
        warnings = {f"exclude term: {value}" for value in exclusion_overlap}
        time_warning = scope_time_warning(str(email.get("subject", "")), record["scope"])
        if time_warning:
            warnings.add(time_warning)
        if warnings:
            warning_hits[task_id] = warnings

    # Lexical evidence is retrieval-only. Keep the most informative candidates,
    # but never use it to assign ownership or suppress the email.
    lexical_order = sorted(
        lexical_hits,
        key=lambda task_id: (-len(lexical_hits[task_id]), task_id),
    )[:MAX_LEXICAL_CANDIDATES]
    lexical_hits = {task_id: lexical_hits[task_id] for task_id in lexical_order}

    candidate_ids = entry_tasks | conversation_tasks | set(identifier_hits) | set(contact_hits) | set(lexical_hits)
    candidates = []
    for task_id in sorted(candidate_ids):
        record = catalog.tasks[task_id]
        reasons = []
        if task_id in entry_tasks:
            reasons.append("EntryID already recorded in this task")
        if task_id in conversation_tasks:
            reasons.append("same Outlook ConversationID as a recorded task email")
        if task_id in identifier_hits:
            reasons.append("identifier overlap: " + ", ".join(sorted(identifier_hits[task_id])))
        if task_id in contact_hits:
            reasons.append("participant overlap: " + ", ".join(sorted(contact_hits[task_id])))
        if task_id in lexical_hits:
            reasons.append("lexical overlap: " + ", ".join(sorted(lexical_hits[task_id])))
        candidates.append({
            "task": task_id,
            "title": record["title"],
            "path": record["path"],
            "lifecycle": record["lifecycle"],
            "reasons": reasons,
            "warnings": sorted(warning_hits.get(task_id, set())),
        })

    evidence = {
        "entry_id_tasks": sorted(entry_tasks),
        "conversation_tasks": sorted(conversation_tasks),
        "archived_entry_tasks": archived_entry_tasks,
        "archived_conversation_tasks": archived_conversation_tasks,
        "identifier_hits": _evidence_map_to_list(identifier_hits),
        "contact_hits": _evidence_map_to_list(contact_hits),
        "lexical_hits": _evidence_map_to_list(lexical_hits),
    }
    return evidence, candidates


def _public_email(email: dict[str, Any], ordinal: int) -> dict[str, Any]:
    return {
        "number": ordinal,
        "entry_id": str(email.get("entry_id") or ""),
        "conversation_id": str(email.get("conversation_id") or ""),
        "direction": direction(email),
        "message_type": message_type(email),
        "folder": str(email.get("folder") or ""),
        "received_time": str(email.get("received_time") or email.get("start_time") or ""),
        "subject": str(email.get("subject") or ""),
        "sender": str(email.get("sender") or ""),
        "to_recipients": email.get("to_recipients", []) or [],
        "cc_recipients": email.get("cc_recipients", []) or [],
        "body_preview": str(email.get("body_preview") or ""),
        "message_class": str(email.get("message_class") or ""),
        "meeting_status": str(email.get("meeting_status") or ""),
        "start_time": str(email.get("start_time") or ""),
        "end_time": str(email.get("end_time") or ""),
    }


def prepare_candidate_payload(
    emails: list[dict[str, Any]],
    catalog: TaskCatalog,
    metadata: dict[str, Any],
    ignored_entry_ids: set[str],
) -> dict[str, Any]:
    conversation_to_tasks = build_conversation_index(emails, catalog)
    items = []
    for ordinal, email in enumerate(emails, 1):
        item = _public_email(email, ordinal)
        entry_id = item["entry_id"]
        if entry_id and entry_id in ignored_entry_ids:
            item.update({
                "review_status": "ignored",
                "deterministic_reason": "EntryID exists in the semantic ignore pool",
                "evidence": {
                    "entry_id_tasks": [], "conversation_tasks": [],
                    "archived_entry_tasks": [], "archived_conversation_tasks": [],
                    "identifier_hits": [], "contact_hits": [], "lexical_hits": [],
                },
                "candidate_tasks": [],
            })
        else:
            noise_reason = strict_noise_reason(email)
            if noise_reason:
                item.update({
                    "review_status": "filtered",
                    "deterministic_reason": noise_reason,
                    "evidence": {
                        "entry_id_tasks": [], "conversation_tasks": [],
                        "archived_entry_tasks": [], "archived_conversation_tasks": [],
                        "identifier_hits": [], "contact_hits": [], "lexical_hits": [],
                    },
                    "candidate_tasks": [],
                })
            else:
                evidence, candidates = _candidate_evidence(email, catalog, conversation_to_tasks)
                if evidence["archived_entry_tasks"] and not evidence["entry_id_tasks"]:
                    archived = ", ".join(evidence["archived_entry_tasks"])
                    item.update({
                        "review_status": "filtered",
                        "deterministic_reason": f"EntryID already recorded in archived task(s): {archived}",
                        "evidence": evidence,
                        "candidate_tasks": [],
                    })
                else:
                    item.update({
                        "review_status": "review",
                        "deterministic_reason": "",
                        "evidence": evidence,
                        "candidate_tasks": candidates,
                    })
        items.append(item)

    return {
        "schema_version": 1,
        "snapshot_id": str(metadata.get("snapshot_id") or ""),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "snapshot": {
            "fetched_at": str(metadata.get("fetched_at") or ""),
            "source": str(metadata.get("source") or ""),
            "stale": bool(metadata.get("stale", False)),
            "stale_reason": str(metadata.get("stale_reason") or ""),
            "email_count": len(emails),
        },
        "task_catalog": public_task_catalog(catalog),
        "emails": items,
    }


def render_diagnostic(payload: dict[str, Any]) -> str:
    """Render a human-readable view without asserting semantic ownership."""
    snapshot = payload["snapshot"]
    review = [item for item in payload["emails"] if item["review_status"] == "review"]
    filtered = [item for item in payload["emails"] if item["review_status"] == "filtered"]
    ignored = [item for item in payload["emails"] if item["review_status"] == "ignored"]
    lines = [
        f"## Email Sync Evidence | {payload['generated_at'][:10]} | {len(review)} for semantic review",
        "",
        f"Snapshot: `{payload['snapshot_id']}` | fetched: {snapshot['fetched_at'] or 'unknown'} | "
        f"stale: {'YES - READ ONLY' if snapshot['stale'] else 'no'} | source: {snapshot['source'] or 'unknown'}",
        "",
        "Deterministic code prepared evidence only. Candidate tasks below are not ownership decisions.",
        "",
        f"### Semantic Review Queue ({len(review)})",
        "",
    ]
    for item in review:
        arrow = "←" if item["direction"] == "out" else "→"
        type_label = " [calendar]" if item["message_type"] == "calendar" else ""
        lines.append(
            f"{arrow} #{item['number']}{type_label} {item['received_time'][:16]} "
            f"{extract_display_name(item['sender'])}: \"{item['subject']}\""
        )
        lines.append(f"  EntryID: {item['entry_id']}")
        if item["conversation_id"]:
            lines.append(f"  ConversationID: {item['conversation_id']}")
        preview = item["body_preview"].replace("\r", " ").replace("\n", " ").strip()
        if preview:
            lines.append(f"  Preview: {preview[:300]}")
        archived_context = sorted(set(
            item["evidence"]["archived_entry_tasks"]
            + item["evidence"]["archived_conversation_tasks"]
        ))
        if archived_context:
            lines.append(
                "  Archived context markers (read-only; do not open/evaluate): "
                + ", ".join(archived_context)
            )
        if not item["candidate_tasks"]:
            lines.append("  Active candidate tasks: none; classifier must still decide actionable / ignore / unresolved")
        else:
            lines.append("  Candidate tasks (evidence only):")
            for candidate in item["candidate_tasks"]:
                reasons = "; ".join(candidate["reasons"])
                lines.append(f"  - {candidate['task']} {candidate['title']}: {reasons}")
                for warning in candidate["warnings"]:
                    lines.append(f"    Warning: {warning}")
        lines.append("")

    if filtered:
        lines.extend([f"### Deterministic Filters ({len(filtered)})", ""])
        for item in filtered:
            lines.append(
                f"- #{item['number']} {item['sender']}: \"{item['subject']}\" "
                f"({item['deterministic_reason']})"
            )
        lines.append("")
    if ignored:
        lines.extend([f"### Existing Semantic Ignore Pool ({len(ignored)})", ""])
        for item in ignored:
            lines.append(f"- #{item['number']} {item['sender']}: \"{item['subject']}\" | {item['entry_id']}")
        lines.append("")

    lines.extend([
        f"### Active Task Catalog ({len(payload['task_catalog'])})",
        "",
    ])
    for task in payload["task_catalog"]:
        scope = f" | Scope: {task['scope']}" if task["scope"] else ""
        lines.append(
            f"- **{task['task']}** {task['title']} | {task['priority']} | {task['geo']} | "
            f"Due: {task['due']}{scope}"
        )
    lines.extend([
        "",
        "### Evidence Stats",
        f"Snapshot emails: {len(payload['emails'])} | Review: {len(review)} | "
        f"Strict noise: {len(filtered)} | Existing ignores: {len(ignored)}",
    ])
    return "\n".join(lines)

