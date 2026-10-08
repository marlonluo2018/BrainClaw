"""Build a structured task catalog for the email-sync classifier.

This module extracts deterministic evidence only. It never decides that an email
belongs to a task; semantic ownership remains the classifier's responsibility.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from followup import parse_task_file
from shared_config import BRAIN_DIR, PROJECT_ROOT, safe_read, scan_tasks

EN_STOPWORDS = {
    "the", "this", "that", "with", "from", "have", "has", "been", "will", "would", "could",
    "should", "can", "are", "was", "were", "for", "and", "not", "but", "all", "any", "our",
    "your", "their", "please", "thanks", "thank", "regards", "dear", "hello", "fwd", "re",
    "ext", "msg", "subject", "sent", "date", "january", "february", "march", "april", "may",
    "june", "july", "august", "september", "october", "november", "december", "jan", "feb",
    "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
}

ZH_STOPWORDS = {
    "答复", "转发", "回复", "请", "您好", "你好", "谢谢", "感谢", "关于", "通知", "提醒",
    "确认", "更新", "信息", "邮件", "附件", "需要", "问题", "情况", "工作", "时间", "申请",
    "进度", "安排", "完成", "已经", "可以", "如果", "是否", "希望", "麻烦", "帮忙", "收到",
    "发送", "联系", "处理", "参加", "了解", "看看", "知道", "好的", "没有", "这个", "那个",
    "我们", "他们", "大家", "公司", "团队", "部门", "同事", "老师", "经理", "主管", "领导",
}

MONTH_NAMES = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}
QUARTER_MONTHS = {"Q1": (1, 3), "Q2": (4, 6), "Q3": (7, 9), "Q4": (10, 12)}


def extract_terms(text: str) -> set[str]:
    """Extract normalized lexical terms and business identifiers."""
    english = set(re.findall(r"[a-zA-Z]{3,}", text.lower())) - EN_STOPWORDS
    chinese = set(re.findall(r"[\u4e00-\u9fff]{2,}", text)) - ZH_STOPWORDS
    codes = {value.upper() for value in re.findall(r"\b[A-Za-z]+\d+[A-Za-z0-9_-]*\b", text)}
    quarters = {value.upper() for value in re.findall(r"\bQ[1-4]\b", text, re.IGNORECASE)}
    return english | chinese | codes | quarters


def extract_identifiers(text: str) -> set[str]:
    """Extract stable-looking identifiers without treating ordinary words as IDs."""
    values = {value.upper() for value in re.findall(r"\b[A-Za-z]+\d+[A-Za-z0-9_-]*\b", text)}
    values |= set(re.findall(r"\b\d{6,}\b", text))
    return {value for value in values if len(value) <= 32 and not re.fullmatch(r"20\d{2}", value)}


def _field(content: str, name: str) -> str:
    match = re.search(rf"^\*\*{re.escape(name)}:\*\*\s*(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _section_tags(content: str) -> list[str]:
    match = re.search(r"^## Tags\s*\n(.+)$", content, re.MULTILINE)
    return re.findall(r"`([^`]+)`", match.group(1)) if match else []


def _scope_parts(content: str) -> tuple[str, str]:
    scope = _field(content, "Scope")
    explicit_exclude = _field(content, "Exclude")
    exclusions: list[str] = []
    if explicit_exclude and explicit_exclude not in {"-", "—"}:
        exclusions.append(explicit_exclude)
    if scope:
        exclusions.extend(
            part.strip()
            for part in re.findall(r"(?:[.,;]\s*|^)NOT\s+(.+?)(?=[.,;]|$)", scope, re.IGNORECASE)
            if part.strip()
        )
    return scope, "; ".join(exclusions)


def parse_scope_time_window(scope: str) -> tuple[int, int] | None:
    if not scope:
        return None
    match = re.search(
        r"[\(（]?\b([A-Za-z]{3,9})\s*(?:[–\-−]|to)+\s*([A-Za-z]{3,9})\b[\)）]?",
        scope,
        re.IGNORECASE,
    )
    if match:
        start = MONTH_NAMES.get(match.group(1).lower())
        end = MONTH_NAMES.get(match.group(2).lower())
        if start and end:
            return start, end
    quarter = re.search(r"\b(Q[1-4])\b", scope, re.IGNORECASE)
    return QUARTER_MONTHS.get(quarter.group(1).upper()) if quarter else None


def scope_time_warning(subject: str, scope: str) -> str | None:
    """Return a factual date-scope warning; never reject a candidate."""
    window = parse_scope_time_window(scope)
    if not window:
        return None
    months = {
        MONTH_NAMES[token.lower()]
        for token in re.findall(r"\b[A-Za-z]{3,9}\b", subject)
        if token.lower() in MONTH_NAMES
    }
    outside = sorted(month for month in months if not (window[0] <= month <= window[1]))
    if not outside:
        return None
    short_names = {value: key.title() for key, value in MONTH_NAMES.items() if len(key) == 3}
    referenced = ", ".join(short_names.get(month, str(month)) for month in outside)
    expected = f"{short_names.get(window[0], window[0])}-{short_names.get(window[1], window[1])}"
    return f"subject references {referenced}; task scope window is {expected}"


@dataclass(frozen=True)
class TaskCatalog:
    tasks: dict[str, dict[str, Any]]
    email_to_tasks: dict[str, set[str]]
    name_to_tasks: dict[str, set[str]]


def _register_contact(
    mapping: dict[str, set[str]],
    value: str,
    task_id: str,
) -> None:
    normalized = value.strip().lower()
    if normalized:
        mapping.setdefault(normalized, set()).add(task_id)


def _active_task_record(task: Any, content: str) -> dict[str, Any]:
    parsed = parse_task_file(content)
    scope, exclude = _scope_parts(content)
    tags = _section_tags(content)
    header = re.split(r"^## Timeline\b", content, maxsplit=1, flags=re.MULTILINE)[0]
    category = parsed.get("category", "")
    positive_scope = re.split(r"(?:[.,;]\s*|^)NOT\b", scope, maxsplit=1, flags=re.IGNORECASE)[0]
    evidence_text = " ".join([task.title, category, positive_scope, *tags, header])
    identifiers = extract_identifiers(evidence_text)
    epd = _field(content, "EPD")
    if epd not in {"", "-", "—"}:
        identifiers |= set(re.findall(r"\b\d{6,}\b", epd))
    lexical_terms = extract_terms(" ".join([task.title, category, positive_scope, *tags]))
    exclusion_terms = extract_terms(exclude)
    lexical_terms -= exclusion_terms

    contacts = []
    for contact in parsed.get("contacts", []):
        contacts.append({
            "name": str(contact.get("name", "")).strip(),
            "email": str(contact.get("email", "")).strip().lower(),
            "role": str(contact.get("role", "")).strip(),
        })

    raci_match = re.search(
        r"^### RACI Matrix\s*$\n(.*?)(?=^###?\s|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    raci_content = raci_match.group(1) if raci_match else ""
    for name, email, role in re.findall(
        r"^\|\s*([^|<>]+?)\s*(?:<([^>]+@[^>]+)>)?\s*\|\s*([^|]+?)\s*\|",
        raci_content,
        re.MULTILINE,
    ):
        clean_name = name.strip()
        clean_email = email.strip().lower()
        clean_role = role.strip()
        if clean_name.lower() in {"stakeholder", "name", "contact"}:
            continue
        if set(clean_name) <= {"-", ":"} or set(clean_role) <= {"-", ":"}:
            continue
        candidate = {"name": clean_name, "email": clean_email, "role": clean_role or "RACI"}
        if candidate not in contacts:
            contacts.append(candidate)

    return {
        "task": task.id,
        "title": task.title,
        "path": task.path,
        "lifecycle": "active",
        "status": task.status,
        "priority": task.priority,
        "geo": task.geo or parsed.get("geo", ""),
        "due": task.due,
        "scope": scope,
        "exclude": exclude,
        "contacts": contacts,
        "identifiers": identifiers,
        "lexical_terms": lexical_terms,
        "exclusion_terms": exclusion_terms,
        "entry_ids": set(re.findall(r"<!-- email:(\S+?) -->", content)),
        "conversation_ids": set(re.findall(r"<!-- conversation:(\S+?) -->", content)),
    }


def build_task_catalog() -> TaskCatalog:
    """Build active task evidence plus archived message/thread markers."""
    active_tasks, _, _ = scan_tasks()
    tasks: dict[str, dict[str, Any]] = {}
    email_to_tasks: dict[str, set[str]] = {}
    name_to_tasks: dict[str, set[str]] = {}

    for task in active_tasks:
        if task.status == "Completed":
            continue
        task_path = PROJECT_ROOT / task.path
        content = safe_read(task_path)
        if not content:
            matches = sorted((BRAIN_DIR / "tasks").glob(f"{task.id}-*.md"))
            content = safe_read(matches[0]) if matches else ""
        if not content:
            continue
        record = _active_task_record(task, content)
        tasks[task.id] = record
        for contact in record["contacts"]:
            _register_contact(email_to_tasks, contact["email"], task.id)
            _register_contact(name_to_tasks, contact["name"], task.id)

    history_dir = BRAIN_DIR / "tasks" / "history"
    if history_dir.exists():
        for path in sorted(history_dir.rglob("T*.md")):
            content = safe_read(path)
            task_match = re.match(r"(T\d+)", path.stem)
            if not content or not task_match or task_match.group(1) in tasks:
                continue
            entry_ids = set(re.findall(r"<!-- email:(\S+?) -->", content))
            conversation_ids = set(re.findall(r"<!-- conversation:(\S+?) -->", content))
            if not entry_ids and not conversation_ids:
                continue
            task_id = task_match.group(1)
            title_match = re.match(r"^#\s+T\d+:\s*(.+)$", content, re.MULTILINE)
            tasks[task_id] = {
                "task": task_id,
                "title": title_match.group(1).strip() if title_match else "Archived task",
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
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
                "entry_ids": entry_ids,
                "conversation_ids": conversation_ids,
            }

    return TaskCatalog(tasks=tasks, email_to_tasks=email_to_tasks, name_to_tasks=name_to_tasks)


def public_task_catalog(catalog: TaskCatalog) -> list[dict[str, Any]]:
    """Return the JSON-safe task catalog consumed by the semantic classifier."""
    result = []
    for task_id in sorted(catalog.tasks):
        record = catalog.tasks[task_id]
        if record["lifecycle"] != "active":
            continue
        result.append({
            "task": task_id,
            "title": record["title"],
            "path": record["path"],
            "status": record["status"],
            "priority": record["priority"],
            "geo": record["geo"],
            "due": record["due"],
            "scope": record["scope"],
            "exclude": record["exclude"],
            "contacts": record["contacts"],
            "identifiers": sorted(record["identifiers"]),
        })
    return result
