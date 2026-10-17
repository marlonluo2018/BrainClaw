"""Deterministic scanner for outgoing email bodies (L&K-internal content).

Usage: py -3 assistant_brain/scripts/screen_outgoing_body.py <body-file> [--subject "..."] [--json]

A detector, not a gate: it always exits 0 (missing file exits 1) and reports
findings for the EMAIL_REVIEW_RULEBOOK.md review to confirm or override.
Detected categories — EPD numbers, Class IDs, PO numbers, BrainClaw task IDs
(T###), internal-only link hosts, and identifiers leaking into subjects.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from shared_config import configure_utf8_stdio

configure_utf8_stdio()

TAG_RE = re.compile(r"<[^>]+>")
EPD_RE = re.compile(r"\bEPD[ \t]*(?:No\.?|number|:|-|=)?[ \t]*(\d{6,8})\b", re.IGNORECASE)
EPD_LABELLED_RE = re.compile(r"\b(\d{7})\b")
TASK_ID_RE = re.compile(r"\bT\d{3}\b")
PO_RE = re.compile(r"\bP\.?O\.?[ \t]*(?:No\.?|number|:|-|=)?[ \t]*([A-Z0-9]{5,})\b", re.IGNORECASE)
CLASS_ID_RE = re.compile(r"\bClass[ \t]*(?:ID|No\.?|number)?[ \t]*[:#=]?[ \t]*([A-Z0-9]{4,})\b", re.IGNORECASE)
INTERNAL_HOSTS = ("w3.ibm.com", "lksprod.dst.ibm.com", "ibm.box.com", "ibm.sharepoint.com")
HOST_RE = re.compile(r"https?://([a-z0-9.-]+)|([a-z0-9.-]+\.(?:com|net|org))", re.IGNORECASE)

# Wording that usually signals internal deliberation rather than a conclusion.
# Advisory only — the drafter decides; the scanner just flags it for review.
DELIBERATION_RE = re.compile(
    r"\b(?:per|according to|as suggested by|as advised by)\s+[A-Z][a-z]+"
    r"|\binternal(?:ly)?\s+(?:discussion|alignment|process)\b"
    r"|\bwe\s+(?:considered|debated|weighed|hesitated)\b",
    re.IGNORECASE,
)


def strip_html(raw: str) -> str:
    """Strip tags, comments, and style/script blocks; unescape entities."""
    text = re.sub(r"<!--.*?-->", " ", raw, flags=re.DOTALL)
    text = re.sub(r"<(style|script)\b[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = TAG_RE.sub(" ", text)
    return html.unescape(text)


def _hosts(text: str) -> list[str]:
    hosts = []
    for match in HOST_RE.finditer(text):
        host = match.group(1) or match.group(2)
        if host:
            hosts.append(host.lower())
    return hosts


def findings(body_text: str, subject: str = "") -> list[dict]:
    """Return findings for one outgoing body (already HTML-stripped) and subject.

    Each finding: {"category", "severity", "match", "context"}.
    "severity" is a scanning-level default ("high"/"low"); the drafter may
    downgrade a finding with recipient-context (e.g. EPD kept for an L&K
    internal reimbursement thread) and must say so in the Draft Review.
    """
    text = strip_html(body_text)
    subject_text = strip_html(subject) if subject else ""
    found: list[dict] = []

    def add(category: str, severity: str, match: str, context: str) -> None:
        snippet = " ".join(context.split())[:120]
        found.append({"category": category, "severity": severity, "match": match, "context": snippet})

    for match in EPD_RE.finditer(text):
        add("epd-number", "high", f"EPD {match.group(1)}", text[max(0, match.start() - 40):match.end() + 40])
    for match in EPD_LABELLED_RE.finditer(text):
        if EPD_RE.search(text[max(0, match.start() - 8):match.end()]) or re.search(
            r"(?i)\bepd\b", text[max(0, match.start() - 60):match.start()]
        ):
            continue  # already captured with its label
        add("epd-number", "low", match.group(1), text[max(0, match.start() - 40):match.end() + 40])
    for match in TASK_ID_RE.finditer(text):
        add("task-id", "high", match.group(0), text[max(0, match.start() - 40):match.end() + 40])
    for match in PO_RE.finditer(text):
        add("po-number", "high", f"PO {match.group(1)}", text[max(0, match.start() - 40):match.end() + 40])
    for match in CLASS_ID_RE.finditer(text):
        add("class-id", "high", f"Class {match.group(1)}", text[max(0, match.start() - 40):match.end() + 40])
    for host in _hosts(text):
        if host in INTERNAL_HOSTS or host.endswith(".box.com") or host.endswith(".sharepoint.com"):
            add("internal-link", "high", host, text[:0] or host)
    for match in DELIBERATION_RE.finditer(text):
        add("deliberation-wording", "low", match.group(0), text[max(0, match.start() - 40):match.end() + 40])

    # Subject rules from EMAIL_WORKFLOW.md: never EPD numbers or Class IDs.
    if subject_text:
        for match in EPD_RE.finditer(subject_text) or EPD_LABELLED_RE.finditer(subject_text):
            add("subject-identifier", "high", match.group(0), f"subject: {subject_text}")
        for match in CLASS_ID_RE.finditer(subject_text):
            add("subject-identifier", "high", match.group(0), f"subject: {subject_text}")
    return found


def render(findings_list: list[dict]) -> str:
    if not findings_list:
        return "Screen: clean — no L&K-internal content patterns detected."
    lines = [f"Screen: {len(findings_list)} finding(s)"]
    for index, item in enumerate(findings_list, start=1):
        lines.append(
            f"  {index}. [{item['severity']}] {item['category']} — {item['match']} — \"{item['context']}\""
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan an outgoing email body for L&K-internal content")
    parser.add_argument("body_file", type=Path)
    parser.add_argument("--subject", default="")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        raw = args.body_file.read_text(encoding="utf-8-sig")
    except OSError as exc:
        print(f"ERROR: could not read body file: {exc}")
        return 1
    result = findings(raw, args.subject)
    if args.as_json:
        print(json.dumps({"body_file": str(args.body_file), "findings": result}, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
