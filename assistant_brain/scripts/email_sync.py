"""BrainClaw Email Sync Pre-Processor.

Reads JSON email data from stdin (output of outlook_skill.py find-recent --json),
builds a task index, matches emails to tasks, filters noise, and outputs a compact
pre-matched summary for Claude to process with minimal context usage.

Usage:
    py -3 .../outlook_skill.py find-recent --days 1 --json | py -3 .../email_sync.py
    py -3 .../email_sync.py --input-file downloads/emails.json
"""

import sys
import io
import re
import json
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

# followup.py wraps stdout/stderr at import time; avoid double-wrap
from shared_config import BRAIN_DIR, scan_tasks, safe_read
from followup import parse_task_file

SYNC_RESULTS_DIR = BRAIN_DIR / "sync_results"


def save_sync_output(output: str) -> Path:
    """Save sync output to timestamped file for later reference."""
    SYNC_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_file = SYNC_RESULTS_DIR / f"{ts}.md"
    out_file.write_text(output, encoding="utf-8")
    return out_file


def cleanup_old_results(days: int = 14):
    """Remove sync result files older than N days."""
    if not SYNC_RESULTS_DIR.exists():
        return
    cutoff = datetime.now() - timedelta(days=days)
    for f in SYNC_RESULTS_DIR.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff.timestamp():
            f.unlink()


# --- Noise filter patterns ---

NOISE_SUBJECT_PREFIXES = [
    "Automatic reply:", "automatic reply:",
    "Out of office:", "Out of Office:",
    "Message Recall Report:",
    "One-time Passcode",
    "Undeliverable:",
]

NOISE_SUBJECT_CONTAINS = [
    "IBM IBV", "IBM Community", "IBM Consulting Advantage",
    "employee purchase", "IBM.Consulting.GCG",
    "Recall: ", "recall:",
    "员工内购",
]

NOISE_SENDER_CONTAINS = [
    "identity assurance", "office365reports",
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "mailer-daemon", "postmaster",
    "w3notifications", "ibmer news", "communications",
    "wellbeing@ibm", "events and classes", "your learning",
    "ibm ibv", "ibm community",
]

SYSTEM_SENDERS = [
    "learning request tool", "training request",
    "red hat training request", "red hat learning",
    "servicenow", "service-now", "jira", "confluence",
    "sharepoint", "microsoft flow", "power automate",
    "successfactors", "workday",
]

NOISE_MEETING_STATUSES = {"meeting_canceled"}
CALENDAR_MEETING_STATUSES = {"meeting_request", "meeting"}

GEO_DOMAIN_MAP = {
    "cn.ibm.com": "China",
    "ph.ibm.com": "Philippines",
    "in.ibm.com": "India",
}

GEO_FLAGS = {
    "China": "\U0001f1e8\U0001f1f3",
    "Philippines": "\U0001f1f5\U0001f1ed",
    "India": "\U0001f1ee\U0001f1f3",
    "Global": "\U0001f310",
    "ASEAN": "\U0001f30f",
}

# Chinese stopwords — high-frequency words with no discriminating power
ZH_STOPWORDS = {
    "答复", "转发", "回复", "请", "您好", "你好", "谢谢", "感谢",
    "关于", "通知", "提醒", "确认", "更新", "信息", "邮件", "附件",
    "需要", "问题", "情况", "工作", "时间", "申请", "进度", "安排",
    "完成", "已经", "可以", "如果", "是否", "希望", "麻烦", "帮忙",
    "收到", "发送", "联系", "处理", "参加", "了解", "看看", "知道",
    "好的", "没有", "这个", "那个", "我们", "他们", "大家", "公司",
    "团队", "部门", "同事", "老师", "经理", "主管", "领导",
}

# English stopwords for subject/preview matching
EN_STOPWORDS = {
    # Generic
    "the", "this", "that", "with", "from", "have", "has", "been",
    "will", "would", "could", "should", "can", "are", "was", "were",
    "for", "and", "not", "but", "all", "any", "our", "your", "their",
    "please", "thanks", "thank", "regards", "dear", "hello",
    "fwd", "ext", "msg", "subject", "sent", "date",
    "ibm", "ibmer",
    # Learning domain — appear in nearly every task, no discriminating power
    "course", "training", "exam", "learning", "skills", "certification",
    "voucher", "session", "workshop", "enroll", "enrollment",
    # Months — no discriminating power (many tasks share due dates)
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
}


def is_calendar_item(email: dict) -> bool:
    """Return True if this email is a meeting invite/calendar item (not noise, shown separately)."""
    meeting = email.get('meeting_status', '')
    if meeting in CALENDAR_MEETING_STATUSES:
        return True
    msg_class = email.get('message_class', '')
    if msg_class.startswith('IPM.Schedule.Meeting'):
        return True
    return False


def _meeting_type_label(email: dict) -> str:
    """Derive a short English label for the calendar item type from MessageClass."""
    msg_class = email.get('message_class', '')
    if 'Canceled' in msg_class:
        return "Canceled"
    if 'Resp.Pos' in msg_class:
        return "Accepted"
    if 'Resp.Neg' in msg_class:
        return "Declined"
    if 'Resp.Tent' in msg_class:
        return "Tentative"
    if 'Request' in msg_class:
        return "New Invite"
    if msg_class.startswith('IPM.Schedule.Meeting'):
        return "Update"
    meeting = email.get('meeting_status', '')
    if meeting == 'meeting_request':
        return "New Invite"
    if meeting == 'meeting_canceled':
        return "Canceled"
    return "Meeting"


def _parse_dt(raw: str):
    """Parse a datetime string from the pipeline."""
    from datetime import datetime as _dt
    if not raw:
        return None
    try:
        return _dt.fromisoformat(raw.replace(" ", "T")) if "T" not in raw else _dt.fromisoformat(raw)
    except Exception:
        try:
            return _dt.strptime(raw[:16], "%Y-%m-%d %H:%M")
        except Exception:
            return None


def _format_start_time(email: dict) -> str:
    """Format start/end time like '2026-06-26 13:30-15:00'."""
    start_dt = _parse_dt(email.get('start_time', ''))
    if not start_dt:
        return ""
    end_dt = _parse_dt(email.get('end_time', ''))
    base = f"{start_dt.strftime('%Y-%m-%d')} {start_dt.strftime('%H:%M')}"
    if end_dt:
        return f"{base}-{end_dt.strftime('%H:%M')}"
    return base


def is_noise(email: dict) -> str | None:
    """Return noise category if email is noise, None if relevant."""
    subject = email.get('subject', '')
    sender = email.get('sender', '').lower()
    meeting = email.get('meeting_status', '')

    if meeting in NOISE_MEETING_STATUSES:
        return "calendar"

    for prefix in NOISE_SUBJECT_PREFIXES:
        if subject.startswith(prefix):
            if "One-time Passcode" in prefix:
                return "OTP"
            if "Recall" in prefix:
                return "recall"
            return "auto-reply"

    subj_lower = subject.lower()
    # Event heuristic (same as outlook_skill.py)
    event_subj_kw = ('webinar', 'join us', 'register now', 'you are invited',
                     "you're invited", 'invitation:', 'save the date',
                     'live event', 'virtual event')
    if any(kw in subj_lower for kw in event_subj_kw):
        return "calendar"

    for kw in NOISE_SUBJECT_CONTAINS:
        if kw.lower() in subj_lower:
            return "newsletter"

    for kw in NOISE_SENDER_CONTAINS:
        if kw in sender:
            if "identity assurance" in sender:
                return "OTP"
            return "auto-reply"

    return None


def is_system_sender(email: dict) -> bool:
    sender = email.get('sender', '').lower()
    for kw in SYSTEM_SENDERS:
        if kw in sender:
            return True
    return False


def build_task_index() -> tuple[dict, dict, dict]:
    """Build task index with contacts, entry_ids, and keywords.

    Returns:
        task_index: {task_id: {title, geo, priority, due, path, contacts, entry_ids, keywords}}
        email_to_tasks: {email_addr: [task_ids]}
        name_to_tasks: {lowercase_name: [task_ids]}
    """
    active_tasks, _, _ = scan_tasks()
    tasks_dir = BRAIN_DIR / 'tasks'

    task_index = {}
    email_to_tasks = {}
    name_to_tasks = {}

    for t in active_tasks:
        if t.status == "Completed":
            continue

        content = safe_read(tasks_dir / f"{t.id}-{_slug_from_path(t.path)}.md")
        if not content:
            # Try finding by ID prefix
            matches = list(tasks_dir.glob(f"{t.id}-*.md"))
            if matches:
                content = safe_read(matches[0])
        if not content:
            continue

        parsed = parse_task_file(content)

        # Extract entry_ids from timeline (<!-- email:XXXX -->)
        entry_ids = set(re.findall(r'<!-- email:(\S+?) -->', content))

        # Build keyword set from title + category + scope (English + Chinese)
        def extract_keywords(text: str) -> set:
            en = set(re.findall(r'[a-zA-Z]{3,}', text.lower())) - EN_STOPWORDS
            zh = set(re.findall(r'[一-鿿]{2,}', text)) - ZH_STOPWORDS
            # Alphanumeric codes: Q3, DO288, RH294, EX288, etc.
            codes = set(re.findall(r'[A-Za-z]+\d+[\w]*', text.upper()))
            codes |= set(re.findall(r'\b[Qq][1-4]\b', text.upper()))
            return en | zh | codes

        keywords = extract_keywords(t.title)
        keywords |= extract_keywords(parsed.get("category", ""))

        # Extract scope keywords (positive only — exclude text after "NOT")
        scope_text = ""
        scope_m = re.search(r'^\*\*Scope:\*\*\s*(.+)$', content, re.MULTILINE)
        if scope_m:
            scope_text = scope_m.group(1).strip()
            # Split on NOT clauses — only use text before first "NOT" for positive keywords
            scope_include = re.split(r'[.,;]\s*NOT\b', scope_text, flags=re.IGNORECASE)[0]
            keywords |= extract_keywords(scope_include)

        # Extract exclusion keywords from Exclude field or NOT clauses in Scope
        exclusion_keywords = set()
        exclude_m = re.search(r'^\*\*Exclude:\*\*\s*(.+)$', content, re.MULTILINE)
        if exclude_m:
            exclusion_keywords = extract_keywords(exclude_m.group(1).strip())
        elif scope_text:
            # Fallback: parse NOT clauses from Scope text
            not_parts = re.findall(r'(?:[.,;]\s*|^)NOT\s+(.+?)(?=[.,;]|$)', scope_text, re.IGNORECASE)
            for part in not_parts:
                exclusion_keywords |= extract_keywords(part)
        # Remove identity words (title+tags) from exclusion set — these are the task's
        # own brand words and would false-flag every legitimate email for this task.
        identity_words = extract_keywords(t.title)
        # Tags added below, but compute them here for exclusion filtering
        tags_m_pre = re.search(r'^## Tags\s*\n(.+)$', content, re.MULTILINE)
        if tags_m_pre:
            for tag in re.findall(r'`([^`]+)`', tags_m_pre.group(1)):
                identity_words |= extract_keywords(tag)
        exclusion_keywords -= identity_words

        # Remove exclusion keywords from positive set to avoid false boosting
        keywords -= exclusion_keywords

        # Extract Tags (backtick-delimited, curated high-quality discriminators)
        tags_m = re.search(r'^## Tags\s*\n(.+)$', content, re.MULTILINE)
        if tags_m:
            tags_line = tags_m.group(1)
            tags = re.findall(r'`([^`]+)`', tags_line)
            for tag in tags:
                keywords |= extract_keywords(tag)

        # Extract EPD (plan row IDs — unique numeric identifiers, weight 3.0)
        epd_ids = set()
        epd_m = re.search(r'^\*\*EPD:\*\*\s*(.+)$', content, re.MULTILINE)
        if epd_m:
            epd_val = epd_m.group(1).strip()
            if epd_val != '—' and epd_val != '-':
                epd_ids = set(re.findall(r'\d{6,}', epd_val))
                keywords |= epd_ids

        # Extract alphanumeric codes from header section only (above ## Timeline)
        # Timeline accumulates codes from all past emails — scanning it makes tasks
        # progressively broader keyword magnets, causing false matches.
        header_content = re.split(r'^## Timeline\b', content, maxsplit=1, flags=re.MULTILINE)[0]
        all_codes = set(re.findall(r'[A-Za-z]+\d+[\w]*', header_content.upper()))
        all_codes |= set(re.findall(r'\b[Qq][1-4]\b', header_content.upper()))
        # Filter out noise codes: years, generic IDs, hex strings
        all_codes = {c for c in all_codes if len(c) <= 10 and not re.match(r'^20\d\d$', c)}
        keywords |= all_codes

        task_index[t.id] = {
            "title": t.title,
            "geo": t.geo or parsed.get("geo", ""),
            "priority": t.priority,
            "due": t.due,
            "path": t.path,
            "scope": scope_text,
            "contacts": parsed.get("contacts", []),
            "entry_ids": entry_ids,
            "keywords": keywords,
            "exclusion_keywords": exclusion_keywords,
            "epd_ids": epd_ids,
        }

        # Build inverted indexes from Contacts section
        for contact in parsed.get("contacts", []):
            email_addr = contact.get("email", "").lower().strip()
            if email_addr:
                email_to_tasks.setdefault(email_addr, []).append(t.id)
            name = contact.get("name", "").lower().strip()
            if name:
                name_to_tasks.setdefault(name, []).append(t.id)

        # Also extract emails from RACI table (stakeholders not in Contacts)
        raci_emails = re.findall(r'<([^>]+@[^>]+)>', content)
        for addr in raci_emails:
            addr_lower = addr.lower().strip()
            if addr_lower and t.id not in email_to_tasks.get(addr_lower, []):
                email_to_tasks.setdefault(addr_lower, []).append(t.id)
        # Extract names from RACI table rows: | Name <email> | Role |
        raci_names = re.findall(r'\|\s*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*(?:<[^>]+>)?\s*\|', content)
        for rname in raci_names:
            rname_lower = rname.lower().strip()
            if rname_lower and rname_lower != "stakeholder" and t.id not in name_to_tasks.get(rname_lower, []):
                name_to_tasks.setdefault(rname_lower, []).append(t.id)

    # Scan closed/history tasks for entry_ids only — prevents false matching
    # when emails already recorded in a closed task fall through to contact signal
    history_dir = tasks_dir / 'history'
    if history_dir.exists():
        for hist_file in history_dir.rglob('T*.md'):
            content = safe_read(hist_file)
            if not content:
                continue
            entry_ids = set(re.findall(r'<!-- email:(\S+?) -->', content))
            if not entry_ids:
                continue
            tid_m = re.match(r'(T\d+)', hist_file.stem)
            if not tid_m:
                continue
            tid = tid_m.group(1)
            if tid in task_index:
                continue
            rel_path = str(hist_file.relative_to(BRAIN_DIR.parent)).replace('\\', '/')
            task_index[tid] = {
                "title": "(closed)",
                "geo": "",
                "priority": "",
                "due": "",
                "path": rel_path,
                "scope": "",
                "contacts": [],
                "entry_ids": entry_ids,
                "keywords": set(),
                "exclusion_keywords": set(),
                "epd_ids": set(),
            }

    return task_index, email_to_tasks, name_to_tasks


def _slug_from_path(path: str) -> str:
    """Extract filename slug from path like 'assistant_brain/tasks/T053-temenos-tlc.md'."""
    name = Path(path).stem
    # Remove the TXXX- prefix
    m = re.match(r'T\d+-(.+)', name)
    return m.group(1) if m else name


def load_global_contacts(contacts_path: Path) -> dict:
    """Parse contacts.md into {email: {name, role, section}}."""
    content = safe_read(contacts_path)
    if not content:
        return {}

    contacts = {}
    current_section = ""
    for line in content.split('\n'):
        if line.startswith('## '):
            current_section = line.lstrip('#').strip()
            continue
        m = re.match(r'^- \*\*(.+?)\*\*\s+<(.+?)>', line)
        if m:
            name = m.group(1).strip()
            email = m.group(2).strip().lower()
            contacts[email] = {"name": name, "section": current_section}

    return contacts


def extract_sender_email(sender_str: str) -> str:
    """Extract email address from sender string like 'Name <email@domain.com>'."""
    m = re.search(r'<(.+?@.+?)>', sender_str)
    if m:
        return m.group(1).lower()
    if '@' in sender_str:
        return sender_str.strip().lower()
    return ""


def extract_sender_name(sender_str: str) -> str:
    """Extract display name from sender string."""
    if '<' in sender_str:
        return sender_str.split('<')[0].strip()
    return sender_str.strip()


GEO_SUBJECT_KEYWORDS = {
    "americas": "Americas",
    "america": "Americas",
    "emea": "EMEA",
    "europe": "EMEA",
    "apac": "APAC",
    "asia pacific": "APAC",
    "india": "India",
    "china": "China",
    "philippines": "Philippines",
}


def extract_geo_from_email(email: dict) -> str | None:
    """Infer geo from sender/recipient email domains, then subject keywords."""
    sender = email.get('sender', '')
    sender_email = extract_sender_email(sender)
    for domain, geo in GEO_DOMAIN_MAP.items():
        if sender_email.endswith(domain):
            return geo
    # Check recipients
    for recip in email.get('to_recipients', []):
        addr = (recip.get('address', '') or '').lower()
        for domain, geo in GEO_DOMAIN_MAP.items():
            if addr.endswith(domain):
                return geo
    # Fallback: subject keyword geo detection
    subject_lower = email.get('subject', '').lower()
    for kw, geo in GEO_SUBJECT_KEYWORDS.items():
        if kw in subject_lower:
            return geo
    return None


QUARTER_MONTHS = {
    "Q1": (1, 3), "Q2": (4, 6), "Q3": (7, 9), "Q4": (10, 12),
}

MONTH_NAMES = {
    "jan": 1, "january": 1, "feb": 2, "february": 2,
    "mar": 3, "march": 3, "apr": 4, "april": 4,
    "may": 5, "jun": 6, "june": 6,
    "jul": 7, "july": 7, "aug": 8, "august": 8,
    "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def parse_scope_time_window(scope_text: str) -> tuple[int, int] | None:
    """Parse a time window from scope text. Returns (start_month, end_month) or None."""
    if not scope_text:
        return None
    # Try explicit month range: (Jul–Sep), (Apr–Jun), Jan-Mar
    m = re.search(r'[\(（]?\b([A-Za-z]{3,9})\s*[–\-−to]+\s*([A-Za-z]{3,9})\b[\)）]?', scope_text)
    if m:
        start = MONTH_NAMES.get(m.group(1).lower())
        end = MONTH_NAMES.get(m.group(2).lower())
        if start and end:
            return (start, end)
    # Try quarter: Q3, Q2
    m = re.search(r'\b(Q[1-4])\b', scope_text, re.IGNORECASE)
    if m:
        q = m.group(1).upper()
        return QUARTER_MONTHS.get(q)
    return None


def extract_email_months(subject: str) -> set[int]:
    """Extract referenced months from email subject. Returns set of month numbers."""
    months = set()
    # Pattern: "22nd June", "June 22", "Jun 2026", month names standalone
    for m in re.finditer(r'\b([A-Za-z]{3,9})\b', subject):
        month_num = MONTH_NAMES.get(m.group(1).lower())
        if month_num:
            months.add(month_num)
    return months


def check_temporal_scope(email: dict, task_scope: str) -> str | None:
    """Check if email dates conflict with task scope. Returns conflict description or None."""
    window = parse_scope_time_window(task_scope)
    if not window:
        return None
    start_month, end_month = window
    subject = email.get("subject", "")
    email_months = extract_email_months(subject)
    if not email_months:
        return None
    # Check if ANY referenced month falls outside the window
    outside = {m for m in email_months if not (start_month <= m <= end_month)}
    if not outside:
        return None
    month_names = {v: k for k, v in MONTH_NAMES.items() if len(k) == 3}
    outside_str = ", ".join(sorted(month_names.get(m, str(m)).capitalize() for m in outside))
    window_str = f"{month_names.get(start_month, '?').capitalize()}–{month_names.get(end_month, '?').capitalize()}"
    return f"email refs {outside_str}, task scope={window_str}"


def match_email_to_tasks(email: dict, task_index: dict,
                         email_to_tasks: dict, name_to_tasks: dict) -> list[dict]:
    """Match an email to tasks using 3-signal priority matching.

    Returns list of {task_id, confidence, signal, already_known} sorted by confidence desc.
    """
    entry_id = email.get('entry_id', '')
    sender = email.get('sender', '')
    sender_email = extract_sender_email(sender)
    sender_name = extract_sender_name(sender).lower()
    subject = email.get('subject', '').lower()

    matches = []

    # Signal 1: Thread/entry_id match (confidence 1.0)
    for tid, info in task_index.items():
        if entry_id and entry_id in info["entry_ids"]:
            matches.append({
                "task_id": tid,
                "confidence": 1.0,
                "signal": "entry_id",
                "already_known": True,
            })
            return matches  # Definitive match

    # Signal 1.5: EPD match (confidence 0.95) — runs unconditionally
    subject_raw_epd = email.get('subject', '')
    preview_epd = email.get('body_preview', '')
    epd_codes = set(re.findall(r'\b\d{6,8}\b', subject_raw_epd))
    epd_codes |= set(re.findall(r'\b\d{6,8}\b', preview_epd))
    if epd_codes:
        for tid, info in task_index.items():
            if epd_codes & info["epd_ids"]:
                matches.append({
                    "task_id": tid,
                    "confidence": 0.95,
                    "signal": "epd",
                    "already_known": False,
                })
        if matches:
            matches.sort(key=lambda x: x["confidence"], reverse=True)
            return matches  # EPD is definitive — skip lower signals

    # Signal 2: Contact match (confidence 0.8)
    contact_matches = set()
    if sender_email:
        for tid in email_to_tasks.get(sender_email, []):
            contact_matches.add(tid)
    if sender_name:
        for tid in name_to_tasks.get(sender_name, []):
            contact_matches.add(tid)
    # Also check recipients for sent emails
    for recip in email.get('to_recipients', []):
        addr = (recip.get('address', '') or '').lower()
        if addr:
            for tid in email_to_tasks.get(addr, []):
                contact_matches.add(tid)
        rname = (recip.get('name', '') or '').lower()
        if rname:
            for tid in name_to_tasks.get(rname, []):
                contact_matches.add(tid)

    # Corroborate contact matches with keyword overlap + geo + master-task check
    if contact_matches:
        subject_raw = email.get('subject', '')
        preview = email.get('body_preview', '')
        corr_en = set(re.findall(r'[a-zA-Z]{3,}', f"{subject_raw} {preview}".lower())) - EN_STOPWORDS
        corr_zh = set(re.findall(r'[一-鿿]{2,}', f"{subject_raw} {preview}")) - ZH_STOPWORDS
        corr_codes = set(re.findall(r'[A-Za-z]+\d+[\w]*', f"{subject_raw} {preview}".upper()))
        corr_words = corr_en | corr_zh | corr_codes
        email_geo = extract_geo_from_email(email)

        for tid in contact_matches:
            info = task_index.get(tid, {})
            conf = 0.8

            # Keyword corroboration: demote if zero overlap with task keywords
            overlap = corr_words & info.get("keywords", set())
            if not overlap:
                conf -= 0.3  # 0.8 → 0.5 (ambiguous level)

            # Geo mismatch penalty: task has specific geo, email geo differs
            task_geo = info.get("geo", "")
            if email_geo and task_geo and email_geo.lower() != task_geo.lower():
                conf -= 0.25

            # Master task penalty: umbrella tasks should not capture operational emails
            title = info.get("title", "")
            scope = info.get("scope", "")
            if re.search(r'\bmaster\b', f"{title} {scope}", re.IGNORECASE):
                conf -= 0.2

            matches.append({
                "task_id": tid,
                "confidence": round(conf, 2),
                "signal": "contact",
                "already_known": False,
            })

    # Signal 3: Keyword + geo match (confidence 0.5)
    if not matches:
        subject_raw = email.get('subject', '')
        subject_en = set(re.findall(r'[a-zA-Z]{3,}', subject_raw.lower())) - EN_STOPWORDS
        subject_zh = set(re.findall(r'[一-鿿]{2,}', subject_raw)) - ZH_STOPWORDS
        subject_codes = set(re.findall(r'[A-Za-z]+\d+[\w]*', subject_raw.upper()))
        subject_codes |= set(re.findall(r'\b[Qq][1-4]\b', subject_raw.upper()))
        # Extract numeric IDs (EPD plan row IDs like 1032769)
        subject_codes |= set(re.findall(r'\b\d{6,8}\b', subject_raw))
        # Also extract from body_preview for richer signal
        preview = email.get('body_preview', '')
        if preview:
            subject_en |= set(re.findall(r'[a-zA-Z]{3,}', preview.lower())) - EN_STOPWORDS
            subject_zh |= set(re.findall(r'[一-鿿]{2,}', preview)) - ZH_STOPWORDS
            subject_codes |= set(re.findall(r'[A-Za-z]+\d+[\w]*', preview.upper()))
            subject_codes |= set(re.findall(r'\b[Qq][1-4]\b', preview.upper()))
            subject_codes |= set(re.findall(r'\b\d{6,8}\b', preview))
        email_words = subject_en | subject_zh | subject_codes
        email_geo = extract_geo_from_email(email)

        scored_matches = []
        for tid, info in task_index.items():
            overlap = email_words & info["keywords"]
            en_overlap = overlap & subject_en
            zh_overlap = overlap & subject_zh
            code_overlap = overlap & subject_codes
            # EPD IDs (pure numeric, unique per task) get weight 3.0; other codes 1.5
            epd_overlap = code_overlap & info["epd_ids"]
            regular_code_overlap = code_overlap - epd_overlap
            score = len(en_overlap) + len(regular_code_overlap) * 1.5 + len(epd_overlap) * 3.0
            for w in zh_overlap:
                score += 1.0 if len(w) >= 3 else 0.5
            if score >= 2.0:
                geo_match = (email_geo and info["geo"] and
                             email_geo.lower() == info["geo"].lower())
                geo_mismatch = (email_geo and info["geo"] and
                                email_geo.lower() != info["geo"].lower())
                conf = 0.5 + (0.15 if geo_match else 0) - (0.25 if geo_mismatch else 0)
                # Master task penalty
                t_title = info.get("title", "")
                t_scope = info.get("scope", "")
                if re.search(r'\bmaster\b', f"{t_title} {t_scope}", re.IGNORECASE):
                    conf -= 0.2
                scored_matches.append({
                    "task_id": tid,
                    "confidence": round(conf, 2),
                    "signal": "keyword",
                    "already_known": False,
                    "_score": score,
                })

        # Dominance rule: if top scorer leads by >= 2.0 points, it wins outright
        if scored_matches:
            scored_matches.sort(key=lambda x: x["_score"], reverse=True)
            best = scored_matches[0]["_score"]
            second = scored_matches[1]["_score"] if len(scored_matches) > 1 else 0
            if best - second >= 2.0:
                matches = [scored_matches[0]]
            else:
                matches = scored_matches

    # Check scope exclusions — flag matches where email content hits exclusion keywords
    subject_raw = email.get('subject', '')
    preview = email.get('body_preview', '')
    email_text_for_exclusion = f"{subject_raw} {preview}".upper()
    email_excl_words = set(re.findall(r'[A-Za-z]{3,}', email_text_for_exclusion.lower())) - EN_STOPWORDS
    email_excl_words |= set(re.findall(r'[A-Za-z]+\d+[\w]*', email_text_for_exclusion))

    for m in matches:
        tid = m["task_id"]
        excl_kw = task_index.get(tid, {}).get("exclusion_keywords", set())
        if excl_kw:
            hit = email_excl_words & excl_kw
            if len(hit) >= 2:
                m["exclusion_flag"] = sorted(hit)
                m["confidence"] = round(m["confidence"] - 0.3, 2)
            elif len(hit) == 1:
                m["exclusion_flag"] = sorted(hit)
                m["confidence"] = round(m["confidence"] - 0.15, 2)

    # Sort by confidence descending
    matches.sort(key=lambda x: x["confidence"], reverse=True)
    return matches


def format_output(matched: dict, ambiguous: list, unmatched: list,
                  noise_stats: dict, task_index: dict, global_contacts: dict,
                  total_count: int, emails_by_num: dict,
                  calendar_items: list | None = None) -> str:
    """Format compact pre-matched summary for Claude."""
    today = date.today().strftime('%Y-%m-%d')
    calendar_items = calendar_items or []
    noise_total = sum(len(v) for v in noise_stats.values())
    relevant_count = total_count - noise_total - len(calendar_items)

    lines = []
    cal_note = f", {len(calendar_items)} calendar" if calendar_items else ""
    lines.append(f"## Email Sync Pre-Match | {today} | "
                 f"{relevant_count} relevant / {total_count} total "
                 f"({noise_total} noise filtered{cal_note})")
    lines.append("")

    # --- Task-Matched ---
    # Count only tasks with new (unrecorded) emails
    tasks_with_new = sum(
        1 for emails in matched.values()
        if any(not e["_match"]["already_known"] for e in emails)
    )
    new_email_count = sum(
        sum(1 for e in emails if not e["_match"]["already_known"])
        for emails in matched.values()
    )
    known_only_count = len(matched) - tasks_with_new
    known_note = f", {known_only_count} known-only hidden" if known_only_count else ""
    lines.append(f"### Task-Matched ({new_email_count} new emails → {tasks_with_new} tasks{known_note})")
    lines.append("")

    for tid in sorted(matched.keys(), key=lambda t: task_index.get(t, {}).get("priority", "P9")):
        info = task_index.get(tid, {})

        new_emails = [e for e in matched[tid] if not e["_match"]["already_known"]]
        known_emails = [e for e in matched[tid] if e["_match"]["already_known"]]

        # Skip tasks with only known emails — nothing new to act on
        if not new_emails:
            continue

        geo = info.get("geo", "")
        flag = GEO_FLAGS.get(geo, "")
        priority = info.get("priority", "")
        due = info.get("due", "")
        path = info.get("path", "")

        lines.append(f"**[{tid}]({path}) {info.get('title', '')}** | "
                     f"{priority} {flag} | Due: {due}")
        scope = info.get("scope", "")
        if scope:
            lines.append(f"  Scope: {scope}")

        for em_info in new_emails:
            num = em_info["_num"]
            received = em_info.get("received_time", "")[:16]
            sender_name = extract_sender_name(em_info.get("sender", ""))
            subject = em_info.get("subject", "")
            signal = em_info["_match"]["signal"]

            excl_flag = ""
            if em_info["_match"].get("exclusion_flag"):
                excl_words = ", ".join(em_info["_match"]["exclusion_flag"][:4])
                excl_flag = f" ⚠️EXCLUDED?[{excl_words}]"
            generic_flag = " ⚠️GENERIC" if em_info.get("_system_sender") else ""

            is_sent = "sent" in em_info.get("folder", "").lower()
            if is_sent:
                to_names = []
                for r in em_info.get("to_recipients", []):
                    n = r.get("name", r.get("address", ""))
                    if n:
                        to_names.append(n.split('<')[0].strip() if '<' in n else n)
                to_str = ", ".join(to_names[:2])
                label = f"← #{num} [{signal}] {received} to {to_str}: \"{subject}\""
            else:
                label = f"→ #{num} [{signal}] {received} {sender_name}: \"{subject}\""

            lines.append(f"  {label} ⚡NEW{excl_flag}{generic_flag}")
            eid = em_info.get("entry_id", "")
            if eid:
                lines.append(f"    ID: {eid}")
            preview = em_info.get("body_preview", "").replace("\r\n", " ").replace("\n", " ").strip()
            if is_sent:
                if preview:
                    lines.append(f"    Preview: {preview[:300]}")
                lines.append("    ⚠️READ_BODY: Must get-email before summarizing outbound")
            elif preview:
                lines.append(f"    Preview: {preview[:150]}")

        if known_emails:
            latest_time = max(e.get("received_time", "")[:16] for e in known_emails)
            lines.append(f"  ✅ {len(known_emails)} known emails (latest: {latest_time})")

        lines.append("")

    # --- Ambiguous ---
    if ambiguous:
        lines.append(f"### Ambiguous — Needs Scope Check ({len(ambiguous)})")
        lines.append("")
        for em_info in ambiguous:
            num = em_info["_num"]
            received = em_info.get("received_time", "")[:16]
            sender_name = extract_sender_name(em_info.get("sender", ""))
            subject = em_info.get("subject", "")
            candidates = em_info["_candidates"]

            lines.append(f"→ #{num} {received} {sender_name}: \"{subject}\"")
            eid = em_info.get("entry_id", "")
            if eid:
                lines.append(f"  ID: {eid}")
            preview = em_info.get("body_preview", "").replace("\r\n", " ").replace("\n", " ").strip()
            if preview:
                lines.append(f"  Preview: {preview[:150]}")
            if em_info.get("_system_sender"):
                lines.append(f"  ⚠️GENERIC: System sender — must read body before attribution")
            for c in candidates[:3]:
                tid = c["task_id"]
                info = task_index.get(tid, {})
                scope = info.get("scope", "")
                scope_str = f" | Scope: {scope}" if scope else ""
                lines.append(
                    f"  → {tid} ({info.get('title', '')[:30]}, "
                    f"{info.get('geo', '')}, {c['confidence']:.1f}){scope_str}")
            geo = extract_geo_from_email(em_info)
            if geo:
                lines.append(f"  Geo signal: {geo}")
            lines.append("")

    # --- Non-Task ---
    if unmatched:
        lines.append(f"### Non-Task — No Match ({len(unmatched)})")
        lines.append("")

        for em_info in unmatched:
            num = em_info["_num"]
            received = em_info.get("received_time", "")[:16]
            sender_name = extract_sender_name(em_info.get("sender", ""))
            sender_email = extract_sender_email(em_info.get("sender", ""))
            subject = em_info.get("subject", "")

            known_str = ""
            if sender_email in global_contacts:
                gc = global_contacts[sender_email]
                known_str = f" [Known: {gc['section']}]"

            lines.append(f"→ #{num} {received} {sender_name}: \"{subject}\"{known_str}")
            eid = em_info.get("entry_id", "")
            if eid:
                lines.append(f"  ID: {eid}")
        lines.append("")

    # --- Calendar ---
    if calendar_items:
        lines.append(f"### 📅 Calendar ({len(calendar_items)})")
        for em in calendar_items:
            num = em.get("_num", "?")
            sender_name = em.get("sender_name") or em.get("sender", "").split("@")[0]
            subj = em.get("subject", "")
            short_subj = (subj[:50] + "…") if len(subj) > 52 else subj
            label = _meeting_type_label(em)
            time_str = _format_start_time(em)
            meta_parts = []
            if label:
                meta_parts.append(label)
            if time_str:
                meta_parts.append(time_str)
            meta = " ".join(meta_parts)
            match_info = em.get("_match")
            if match_info:
                tid = match_info["task_id"]
                t_title = task_index.get(tid, {}).get("title", "")
                short_title = (t_title[:30] + "…") if len(t_title) > 32 else t_title
                lines.append(f"  #{num} [{meta}] {sender_name}: \"{short_subj}\" → {tid} ({short_title})")
            else:
                lines.append(f"  #{num} [{meta}] {sender_name}: \"{short_subj}\"")
            entry_id = em.get("entry_id", "")
            if entry_id:
                lines.append(f"    ID: {entry_id}")
        lines.append("")

    # --- Noise ---
    if noise_stats:
        total_noise = sum(len(v) for v in noise_stats.values())
        lines.append(f"### Noise Filtered ({total_noise})")
        for cat, cat_emails in sorted(noise_stats.items(), key=lambda x: -len(x[1])):
            count = len(cat_emails)
            examples = []
            for em in cat_emails[:2]:
                sender_name = em.get("sender_name") or em.get("sender", "").split("@")[0]
                subj = em.get("subject", "")
                short_subj = (subj[:28] + "…") if len(subj) > 30 else subj
                examples.append(f'{sender_name} "{short_subj}"')
            detail = " | ".join(examples)
            if count > 2:
                detail += f" +{count - 2} more"
            lines.append(f"{cat} ({count}): {detail}")
        lines.append("")

    # --- Active Task Reference (for AI semantic matching in Pass B) ---
    unmatched_tasks = {tid: info for tid, info in task_index.items()
                       if tid not in matched and info.get("title") != "(closed)"}
    if unmatched_tasks:
        lines.append("### 📋 Active Tasks Not Matched (reference for AI Pass B)")
        lines.append("")
        for tid in sorted(unmatched_tasks.keys()):
            info = unmatched_tasks[tid]
            title = info.get("title", "")
            scope = info.get("scope", "")
            contacts = info.get("contacts", [])
            geo = info.get("geo", "")
            flag = GEO_FLAGS.get(geo, "")
            contact_str = ", ".join(
                c.get("name", c.get("email", "")) if isinstance(c, dict) else str(c)
                for c in contacts[:5]
            ) if contacts else ""
            line = f"- **{tid}** {title} {flag}"
            if scope:
                line += f" | Scope: {scope[:80]}"
            if contact_str:
                line += f" | Contacts: {contact_str}"
            lines.append(line)
        lines.append("")

    # --- Stats ---
    lines.append(f"### Index Stats")
    lines.append(f"Tasks indexed: {len(task_index)} | "
                 f"Matched: {new_email_count} new + {sum(len(v) for v in matched.values()) - new_email_count} known | "
                 f"Ambiguous: {len(ambiguous)} | "
                 f"Non-task: {len(unmatched)} | "
                 f"Calendar: {len(calendar_items)} | "
                 f"Noise: {sum(len(v) for v in noise_stats.values())}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='BrainClaw email sync pre-processor')
    parser.add_argument('--input-file', type=str, help='Read JSON from file instead of stdin')
    args = parser.parse_args()

    # Read input
    if args.input_file:
        raw = safe_read(Path(args.input_file))
    else:
        raw = sys.stdin.buffer.read().decode('utf-8')

    if not raw.strip():
        print(f"## Email Sync Pre-Match | {date.today()} | 0 emails found")
        print("\nNo email data received. Check outlook_skill.py output.")
        return

    # Parse JSON
    try:
        emails = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse email JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not emails:
        print(f"## Email Sync Pre-Match | {date.today()} | 0 emails")
        return

    # Build task index
    task_index, email_to_tasks, name_to_tasks = build_task_index()

    # Load global contacts
    global_contacts = load_global_contacts(BRAIN_DIR / 'contacts.md')

    # Process emails: filter noise, then match
    noise_stats = {}    # category -> [email dicts]
    calendar_items = []  # meeting invites (shown separately, not noise)
    matched = {}        # task_id -> [email dicts with match info]
    ambiguous = []      # emails with multiple weak candidates
    unmatched = []      # no match at all
    emails_by_num = {}  # email_num -> email dict

    for idx, email in enumerate(emails, 1):
        email["_num"] = idx
        email["_system_sender"] = is_system_sender(email)
        emails_by_num[idx] = email

        # Calendar items — task-linked ones go into matched section; unlinked ones shown separately
        if is_calendar_item(email):
            cal_matches = match_email_to_tasks(email, task_index, email_to_tasks, name_to_tasks)
            cal_matches = [m for m in cal_matches if m["confidence"] >= 0.5]
            if cal_matches:
                # Task-linked calendar item → treat as regular task-matched email
                email["_match"] = cal_matches[0]
                email["_is_calendar"] = True
                tid = cal_matches[0]["task_id"]
                matched.setdefault(tid, []).append(email)
            else:
                # Unlinked calendar item → separate section for AI semantic review
                calendar_items.append(email)
            continue

        # Noise filter
        noise_cat = is_noise(email)
        if noise_cat:
            noise_stats.setdefault(noise_cat, []).append(email)
            continue

        # Match to tasks
        matches = match_email_to_tasks(email, task_index, email_to_tasks, name_to_tasks)

        # Filter out matches below minimum confidence threshold
        matches = [m for m in matches if m["confidence"] >= 0.4]

        if not matches:
            unmatched.append(email)
        elif len(matches) == 1 and matches[0]["confidence"] >= 0.6:
            tid = matches[0]["task_id"]
            scope = task_index.get(tid, {}).get("scope", "")
            if not matches[0]["already_known"] and check_temporal_scope(email, scope):
                unmatched.append(email)
            else:
                email["_match"] = matches[0]
                matched.setdefault(tid, []).append(email)
        elif len(matches) >= 1 and matches[0]["confidence"] >= 0.8:
            # Multiple matches at same confidence → ambiguous (contact in multiple tasks)
            top_conf = matches[0]["confidence"]
            same_conf_count = sum(1 for m in matches if m["confidence"] == top_conf)
            if same_conf_count > 1:
                email["_candidates"] = matches
                ambiguous.append(email)
            else:
                tid = matches[0]["task_id"]
                scope = task_index.get(tid, {}).get("scope", "")
                if not matches[0]["already_known"] and check_temporal_scope(email, scope):
                    unmatched.append(email)
                else:
                    email["_match"] = matches[0]
                    matched.setdefault(tid, []).append(email)
        else:
            email["_candidates"] = matches
            ambiguous.append(email)

    # Clean up old results
    cleanup_old_results()

    # Format output
    output = format_output(
        matched, ambiguous, unmatched, noise_stats,
        task_index, global_contacts, len(emails), emails_by_num,
        calendar_items=calendar_items
    )
    print(output)

    # Save output to file for later reference
    out_file = save_sync_output(output)
    print(f"\n📁 Saved: {out_file.relative_to(BRAIN_DIR.parent)}")


if __name__ == '__main__':
    main()
