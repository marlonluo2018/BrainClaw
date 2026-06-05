# Views Workflow

> On-demand views not covered by `dashboard.py`. Script handles: `pending`, `pending-out`, `pending-in`, `taskboard`.

---

## Intent Recognition

| User intent | Operation |
|-------------|-----------|
| `T###` or "T### status/怎么样/啥情况" | `status T###` |
| "pending/待办/owed/waiting" | Run `py -3 assistant_brain/scripts/dashboard.py` with appropriate arg |
| "before {person}" / "见X之前" / "和X开会前" | `before {person}` |
| "review Q2" / "述职" / "总结这半年" | `review {period}` |

**Rules:** Match by intent, not keyword. Bare `T###` → `status T###`. Person + "前/before" → `before {person}`. Period + action word → `review`. Vague input → show command hints.

---

## status T###

1. Read task file completely.
2. Compute:
   - **Now:** Current blocker or status
   - **Owed by me:** Unchecked `[ ]` items under `Asks > Owed by me`
   - **Owed to me:** Items under `Asks > Owed to me` + days waiting
   - **Stale flag:** No activity beyond threshold for priority
   - **Recent activity:** Last 5 Timeline entries

Output:
```
T### {Title} | {emoji} {priority} | Created {Nd} ago

📍 Now: {text}
📤 Owed by me ({count}):
   • {date} → {person}: {what} {[overdue/due]}
📥 Owed to me ({count}):
   • {date} ← {person}: {what} (waiting {Nd})
🤐 Stale: no activity in {Nd}
📜 Recent activity:
   • {date} [tag] {description}
```
Empty sections omitted.

---

## before {person}

1. Grep person's name across `tasks/T*.md` → get matching files (usually 2-5).
2. Read only those files. For each, gather:
   - RACI role, last touch date
   - Open asks owed by me to them
   - Open asks owed to me from them
   - **Process context:** match task to process file (see [PROCESS_WORKFLOW](PROCESS_WORKFLOW.md)), determine which step involves this person
3. Output:

```
🤝 Pre-meeting brief: {person}

▸ {task_link} {title} — {status} | role: {RACI}
   📤 Owed by me: {what} ({age})
   📥 Waiting on them: {what} ({age})
   🔄 Process step {N}/{total}: "{step description}"

Suggested agenda:
1. {oldest owed by me} — close it
2. {oldest owed to me} — chase it
3. {process-stuck task} — unblock (step {N})
```

---

## review {period}

1. Resolve period (Q1-Q4, H1/H2, annual). Ask if ambiguous.
2. Glob `tasks/history/{YYYY}-Q{n}/T*.md` → aggregate completed tasks by Category, Geo, Tags.
3. Output three formats sequentially:
   - **Workload stats** — tasks completed, geos, categories, top tags
   - **Bullet summary** — key achievements grouped by category
   - **Narrative draft** — paragraph form for performance review
