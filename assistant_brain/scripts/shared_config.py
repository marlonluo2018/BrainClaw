"""Shared configuration for BrainClaw scripts.

Source of truth for thresholds: ../views_config.md
If views_config.md changes, update this file to match.
"""

from pathlib import Path

BRAIN_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BRAIN_DIR.parent

# Staleness thresholds (days) — aligned with views_config.md
STALE_THRESHOLDS = {"P1": 3, "P2": 7, "P3": 14}

# Process matching rules — used by followup.py and dashboard.py
PROCESS_MATCH_RULES = [
    {"keywords": ["procurement", "vendor", "po", "offcycle", "新增"], "geo": "China", "file": "china/offcycle-budget-approval.md"},
    {"keywords": ["procurement", "vendor", "po"], "geo": "Philippines", "file": "philippines/vendor-procurement.md"},
    {"keywords": ["voucher", "aws"], "geo": "Philippines", "file": "philippines/aws-voucher-issuance.md"},
    {"keywords": ["voucher", "azure"], "geo": "Philippines", "file": "philippines/azure-voucher-issuance.md"},
    {"keywords": ["retake", "failed", "补考", "reimbursement", "报销", "no voucher", "out of pocket"], "geo": "Philippines", "file": "philippines/exam-reimbursement.md"},
    {"keywords": ["reimbursement", "报销"], "geo": "China", "file": "china/futurenow-quarterly-reimbursement.md"},
    {"keywords": ["snowflake"], "geo": None, "file": "global/snowflake-certification.md"},
    {"keywords": ["google", "gcp"], "geo": None, "file": "global/google-exam-voucher-discount.md"},
]


# Timeline tag alias mapping — normalises legacy tags to canonical form
TAG_ALIASES = {
    "Email Sent": "email-out",
    "Email Forwarded": "email-out",
    "email sent": "email-out",
    "Email-out": "email-out",
    "Email Received": "email-in",
    "Email-in": "email-in",
    "email received": "email-in",
    "Email": "email-in",
    "Slack": "slack",
    "Slack-in": "slack",
    "slack-in": "slack",
    "Slack-out": "slack",
    "Slack from Tao Han": "slack",
    "Call/Meeting": "meeting",
    "Meeting": "meeting",
    "Meeting Scheduled": "meeting",
    "Update": "update",
    "Action": "update",
    "Task Created": "created",
    "Created": "created",
    "Decision": "decision",
    "Decision Received": "decision",
    "Completed": "milestone",
    "Completion": "milestone",
}


def normalize_tag(raw_tag: str) -> str:
    """Return canonical lowercase-kebab tag, resolving legacy aliases."""
    return TAG_ALIASES.get(raw_tag, raw_tag.lower())


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except (FileNotFoundError, UnicodeDecodeError):
        return ""
