# Views Config

> Thresholds and display preferences for view commands (`status`, `owed`, `waiting`, `before`, `review`). The view workflow MUST read this file before computing — never hardcode thresholds elsewhere.

**Last Updated:** 2026-05-16

---

## Staleness Thresholds (no activity warnings)

| Task category | "Going stale" threshold |
|---------------|-------------------------|
| P1 (active) | 3 days no Timeline activity |
| P2 (active) | 7 days no Timeline activity |
| P3 (active) | 14 days no Timeline activity |
| Any status: 🔴 Blocked | 14 days no follow-up on blocker |
| Any task waiting on a stakeholder | 14 days no inbound from them |

> "Activity" = any Timeline entry OR any Email Reference dated after threshold.

---

## Owed-by-me Overdue Thresholds

| Recipient power | Overdue trigger |
|-----------------|-----------------|
| High Power stakeholder | 1 day past `response_due` |
| Medium Power | 2 days past `response_due` |
| Low Power / unknown | 3 days past `response_due` |
| No `response_due` set | Use [Follow-up Timing](memory/preferences.md) standard: 3-5 business days from ask date |

---

## Status Defaults (single-task `status T###` view)

When the user runs `status T###`, show:

- **Header line:** ID, Title, Status, Priority, Created Nd ago
- **Now:** Current blocking item (oldest open `[blocker]` or `[waiting]`)
- **Owed by me:** Open items from `Asks > Owed by me`, sorted by overdue first
- **Owed to me:** Open items from `Asks > Owed to me`, sorted by waiting duration
- **Stale flag:** if no activity past staleness threshold
- **Recent decisions:** Last 3 Timeline entries tagged `[decision]`, `[milestone]`, or `[delivery]`
- **Recent activity:** Last 5 Timeline entries (any tag), most recent first

If a section has no content, omit it (don't print "(none)").

---

## Owed / Waiting Cross-Task Defaults

> **Implementation:** Both commands use Grep, not full-file reads. `Owed by me` items are unchecked checkboxes (`^- \[ \] .*→`); `Owed to me` items use `^- \d{4}-\d{2}-\d{2} ←`. Grep extracts these directly across all `tasks/T*.md`.

`owed` / `待我处理`:
- Grep pattern across `tasks/T*.md`: `^- \[ \] .*→`
- Group by recipient (person)
- Within each group, sort by overdue severity (most overdue first)
- Show: `→ {person}: {what} (T###, Nd overdue or Nd until due)`

`waiting` / `等待`:
- Grep pattern across `tasks/T*.md`: `^- \d{4}-\d{2}-\d{2} ←`
- Group by who-we're-waiting-on
- Within each group, sort by wait duration (longest first)
- Show: `← {person}: {what} (T###, waiting Nd)`

---

## "Before [person/meeting]" Defaults

> **Implementation:** Grep first, then read only matching files. Grep the person's name (and aliases from registry) across `tasks/T*.md` with `output_mode: files_with_matches`, then Read only the (typically small) subset of matching task files.

`before {person}` or `before {meeting context}`:
- Grep for the person's name across `tasks/T*.md` → small subset of files
- Read only those files
- For each task, show:
  - Task ID, title, status
  - Their RACI role
  - Last Timeline entry mentioning them (or last Email Reference from/to them)
  - Open Asks owed by/to them on this task
- Suggest a draft agenda: open asks first, then long-untouched items, then heads-up items

---

## Review / 述职 Defaults

`review {period}` (e.g., `review Q2 2026`, `半年述职`, `annual review 2026`):
- Read [achievements.md](memory/achievements.md) entries in period
- Group by category (already in achievements format)
- Read tone preference from [preferences.md](memory/preferences.md)
- Output two formats sequentially:
  1. **Bullet summary** (for self-review tracking)
  2. **Narrative draft** (述职 paragraph form, in user's preferred tone)
- Always show task ID linkbacks `[T###]` so user can verify details

---

## Notes for AI

- **Startup is minimal.** Only overdue tasks (queue `**Due:**` < today) are listed by ID at startup. No global dashboard, no per-task status lines.
- **All operations are read-time and focus-driven.** `status T###` reads one task file. `owed` / `waiting` use a single Grep across `tasks/T*.md`. `before {person}` greps for the person's name then reads only the matching subset. `review` reads `achievements.md`.
- **Never store view results.** Always recompute from task files + grep + this config.
- **Empty sections collapse.** Don't print headings for sections with zero items.
- **All thresholds are user-tunable.** If user says "make P1 staleness 5 days", update this file, not workflow files.
- **When config is silent on a case, default to conservative** (longer threshold, more items shown). Better to surface than to hide.
