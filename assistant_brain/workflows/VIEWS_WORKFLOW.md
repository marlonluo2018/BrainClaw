# Views Workflow

> Cross-task and per-task views: surface what the user needs to know about their work, computed at read time.
>
> **Always** read [`views_config.md`](../views_config.md) BEFORE running any operation in this workflow. All thresholds, section orders, and display defaults live there.

---

## Intent Recognition (READ FIRST)

> User input is natural language, not commands. Map by **what the user wants to know**, not by exact keyword. The trigger lists below are examples, not an exhaustive whitelist — match by intent.

**Mapping table — when user asks…**

| User intent (in any phrasing) | Operation |
|------------------------------|-----------|
| "How is task T### going?" / "T### 怎么样" / "T### 啥情况" / "T### 状态" / bare `T###` | `status T###` |
| "What did I promise / owe people?" / "待我处理" / "我答应过啥" / "我有啥没回的" | `pending:out` |
| "Who haven't I heard back from?" / "等待" / "等谁回" / "啥事卡着" | `pending:in` |
| "Prep me before meeting X" / "见 X 之前" / "和 X 开会前" / "下午要见 X" | `before X` |
| "What did I accomplish this period?" / "述职" / "Q2 做了啥" / "总结这半年" | `review {period}` |
| "What's pending?" / "待办总览" / "all pending" / "所有待办" / "pending items" | `pending` |
| "Show all tasks" / "全部任务" / "taskboard" / "任务板" | `taskboard` (see CONFIG.md) |

**Disambiguation rules:**

1. **Match by question shape, not by keyword presence.** "我答应过 Beng 啥来着" should hit `owed` even though it has no "owed" word.
2. **Match by entity reference.** Any input that contains a `T###` reference is a strong signal for `status T###`. Bare `T###` (just the ID alone) → `status T###`. Any input that contains a person's name plus "之前" / "开会前" / "before" is `before {person}`.
3. **Time-period signals → review.** Phrases like "Q2", "半年", "annual", "这季度", "this quarter" combined with action words (做了啥, accomplished, summary, 总结) → `review`.
4. **Vague inputs without specific entity** ("看看", "what's up", "现在咋样") — point user to specific commands rather than guessing. There is no global view default.
5. **Ask one clarifying question if truly ambiguous.** E.g., user says only "Beng" — could mean `before Beng`, or pull all tasks with Beng as RACI, or look up Beng's contact info. Ask: "Want a meeting prep with Beng, or all open items involving Beng?" Don't guess wrong; one clarification is cheaper than re-running.
6. **Never silently fall back to no-op.** If you cannot match intent after one clarification, say so: "I'm not sure which view you want — try `status T###`, `pending`, `pending out`, `pending in`, `before {person}`, `taskboard`, or `review {period}`."

---

## Operations Index

| Operation | Scope | What it answers |
|-----------|-------|-----------------|
| `status T###` (or bare `T###`) | Single task | "How is this task going?" (also accepts legacy `digest T###` / `brief T###`) |
| `pending:out` (alias: `owed` / `待我处理`) | Cross-task (Grep-based) | "What do I owe other people?" |
| `pending:in` (alias: `waiting` / `等待`) | Cross-task (Grep-based) | "Who am I waiting on?" |
| `before {person}` | Person-scoped (Grep-based) | "What should I cover before meeting X?" |
| `review {period}` | Achievements | "What did I accomplish in this period?" |
| `pending` | Cross-task (Grep-based) | "All open asks in one view — both directions, with suggestions" |
| `taskboard` | Queue overview | "All my tasks at a glance" — see [`CONFIG.md`](../CONFIG.md) |

> **Startup brief is minimal and focus-driven** — only overdue tasks (queue `**Due:**` < today) are listed by ID at startup. There is no global dashboard; details come on-demand via `status T###` or the cross-task ops above.
>
> **Cross-task ops use Grep, not full-file reads.** The `pending` series (`pending`, `pending:out`, `pending:in`) and `before {person}` exploit the structured `Asks` format to extract just what they need — no need to read 18 task files.

---

## Common Setup (run before any operation)

1. Read [`views_config.md`](../views_config.md) — get all thresholds.
2. Get today's date via OS command (see [`OPERATIONAL_RULES.md`](../OPERATIONAL_RULES.md) → Date/Time Query).
3. Read [`tasks/queue.md`](../tasks/queue.md) — list of active tasks and metadata.
4. For operations needing per-task data, batch-read relevant `T###` files.

---

## status T###

**Triggers (any phrasing matching the intent — match by intent, not exact keyword):**

- English: `status T###`, `T### status`, `summary T###`, `T### update`, `how is T###`, `what's the state of T###`
- Chinese: `T### 状态`, `查 T###`, `T### 怎么样了`, `T### 啥情况`, `T### 进展`, `看下 T###`
- Implicit: bare `T###` (just the ID, no other words) → treat as `status T###`. Any user input containing a `T###` reference and a question word is also a strong signal.
- Aliases: `digest T###`, `brief T###` — accepted for backward compat, route to `status T###`.

**Steps:**

1. **Common Setup** above.
2. Read the specified task file completely.
3. Read [`contacts.md`](../contacts.md) to resolve power levels for owed-overdue calculation.
4. Compute fields per [`views_config.md`](../views_config.md) → "Status Defaults":
   - **Now:** Oldest open item with tag `[blocker]` or `[waiting]` from Timeline. If none, current Status.
   - **Owed by me:** All unchecked `[ ]` items under `## Asks > Owed by me`. Compute overdue per stakeholder power.
   - **Owed to me:** All items under `## Asks > Owed to me`. Compute days waiting from item date.
   - **Stale flag:** True if max(latest Timeline date, latest Email Reference date) is older than the staleness threshold for the task's priority.
   - **Recent decisions:** Last 3 Timeline entries tagged `[decision]`, `[milestone]`, or `[delivery]`.
   - **Recent activity:** Last 5 Timeline entries (any tag).
5. Output format:

```
T### {Title} | {status_emoji} {priority} | Created {Nd} ago

📍 Now: {now_text}
{if Owed by me not empty:}
📤 Owed by me ({count}):
   • {date} → {person}: {what} {[overdue/due in Nd] from response_due or default}
{if Owed to me not empty:}
📥 Owed to me ({count}):
   • {date} ← {person}: {what} (waiting {Nd})
{if stale_flag:}
🤐 Stale: no activity in {Nd} (threshold: {threshold}d for P{x})
{if recent_decisions not empty:}
🏁 Recent decisions / milestones:
   • {date} [tag] {description}
📜 Recent activity:
   • {date} [tag] {description}
```

6. Sections with no content are omitted entirely (per config rule "Empty sections collapse").

---

## The `pending` Series

> Three commands sharing the same display format. `pending` = both directions; `pending:out` = only what I owe; `pending:in` = only what I'm waiting on.
> Old triggers (`owed`, `待我处理`, `waiting`, `等待`) still work as aliases routing to `pending:out` / `pending:in`.

---

### pending (unified)

**Triggers:**

- English: `pending`, `all pending`, `pending items`, `what's pending`, `show pending`, `open asks`
- Chinese: `待办总览`, `所有待办`, `待办汇总`, `所有待处理`

**Runs both Grep passes and outputs both sections.**

---

### pending:out (owed by me)

**Triggers:**

- English: `pending:out`, `owed`, `what do I owe`, `my open promises`, `what did I promise`, `outstanding asks from me`
- Chinese: `待我处理`, `我答应过啥`, `我有啥没回的`, `我还没做的`, `没办的事`
- Question shape: any "what / 啥 / 哪些" + "I / 我" + "owe / promise / 答应 / 待办 / 没回" pattern

**Runs only the owed-by-me Grep pass. Outputs the 📤 section only.**

---

### pending:in (waiting on others)

**Triggers:**

- English: `pending:in`, `waiting`, `who am I waiting on`, `who hasn't replied`, `who's blocking me`, `pending replies`
- Chinese: `等待`, `我在等谁`, `啥事卡着`, `谁还没回我`, `卡在谁身上`, `谁拖着我`, `谁压着`
- Question shape: any "who / 谁 / 啥事" + "waiting / 等 / 卡 / 没回 / 拖" pattern

**Runs only the owed-to-me Grep pass. Outputs the 📥 section only.**

---

### Shared Implementation (all three commands)

**Grep patterns:**

- Owed by me: `^- \[ \] .*→` across `tasks/T*.md`
- Owed to me: `^- \d{4}-\d{2}-\d{2} ←` across `tasks/T*.md`

**Steps:**

1. **Common Setup** (queue.md for task metadata: title, priority, due).
2. Run Grep pass(es) depending on command:
   - `pending` → both patterns
   - `pending:out` → owed-by-me pattern only
   - `pending:in` → owed-to-me pattern only
3. Parse each match:
   - Task ID from filename (e.g., `T033` from `T033-rhapsody-...md`)
   - Date, person (after `→` or `←`), action/what
4. Cross-reference queue.md for each task's **title**, **priority**, **due date**.
5. Cross-reference [`memory/things_to_avoid.md`](../memory/things_to_avoid.md) Patterns — flag any matching items.
6. Output in shared format below.

### Shared Output Format

```
📋 Pending ({total} items across {N} tasks)

📤 Owed by me ({count}):

- [T033](path) · Rhapsody Cert... · P1 · Due: TBD
  → Jian Hui Liang: Contact learner to use "external education" · Since: 2026-05-19

- [T024](path) · Cert Voucher Quotation... · P2 · Due: TBD
  → LearnQuest: Request voucher codes (after PO completed) · Since: 2026-05-18

📥 Owed to me ({count}):

- [T041](path) · Red Hat Procurement... · P1 · Due: 2026-05-15
  ← B Sowmya: Complete PO for Red Hat Learning Subscription · Since: 2026-05-18

- [T042](path) · Veeva Course... · P2 · Due: 2026-06-30
  ← Citra Ganeshty: PO# issuance · Since: 2026-05-19

{if any pattern flagged from things_to_avoid.md, append notes here}
```

**Format rules:**

- Each item is a **2-line block**: line 1 = task context, line 2 = action (with `→`/`←` + person + what + `· Since: YYYY-MM-DD`).
- `Since:` date = the date from the Asks line (for out: when the ask was logged; for in: when the waiting item was logged).
- Items separated by a blank line for scan-ability.
- Sort: P1 first → then by wait duration (longest first).
- Title truncated to ~30 chars with `...` if needed.
- `pending:out` renders only the 📤 section; `pending:in` renders only the 📥 section; `pending` renders both.
- Empty sections omitted entirely.
- Header line (`📋 Pending...`) always appears with correct counts for whichever sections are shown.

---

## Legacy aliases (digest / brief)

**`digest T###`** and **`brief T###`** are accepted as aliases for `status T###` (backward compat). Route them to `status T###` directly.

**Standalone `brief` is not a view operation.** The startup brief is minimal (just overdue tasks from queue.md). For task detail, the user must focus on a specific task with `status T###` or use a cross-task op (`owed` / `waiting` / `before`).

**Vague inputs without specific entity** (`看看`, `what's up`, `现在咋样`, `今天该干啥`, `啥要紧`, `今天重点`) — do not guess. Reply with command hints: `Try 'status T###', 'pending', 'pending out', 'pending in', 'before {person}', 'taskboard', or 'review {period}'.`

---

## before {person/meeting}

**Triggers (any phrasing matching the intent — must include a person name OR meeting reference):**

- English: `before {name}`, `prep for meeting with {name}`, `prep for {time/event}`, `meeting prep {name}`, `briefing on {name}`, `getting ready to meet {name}`
- Chinese: `见 {人} 前`, `见 {人} 之前`, `和 {人} 开会前`, `下午要见 {人}`, `明天和 {人} 谈之前`, `跟 {人} meeting 前`, `备会 {人}`
- Pattern: input contains a contact name (in contacts.md) AND a "before / 前 / 之前 / 之前" / meeting reference word
- If only a person name is given without "before / 前", **ASK** ("Want a meeting prep, or all open items with this person?") — don't guess.

**Implementation: Grep first, then read only matching task files.** Do NOT read all 18 task files. Grep for the person's name across `assistant_brain/tasks/T*.md` to identify the (usually 2-5) relevant files, then read only those.

**Steps:**

1. **Common Setup**.
2. Identify the target:
   - If a person name → match against [`contacts.md`](../contacts.md) by name, alias, or email. Collect all known aliases for the next step.
   - If a time/event → ask user which contacts are involved (default: read context from recent calendar mentions if available).
3. **Grep for matching files**: Run Grep with the person's name (and aliases) across `assistant_brain/tasks/T*.md`, `output_mode: files_with_matches`. Returns the small subset of task files involving this person.
4. **Read only those task files** (typically 2-5, not 18).
5. For each such task, gather:
   - Task ID, title, status, priority
   - Their RACI role on this task
   - Last Timeline entry mentioning them OR last Email Reference from/to them (whichever is newer)
   - Open `Asks > Owed by me` items where this person is the recipient
   - Open `Asks > Owed to me` items where this person is who-we-await
6. Output format:

```
🤝 Pre-meeting brief: {person}
{if contact has tone/role annotation in contacts.md, brief context: power, geo, typical tone}

Active tasks involving {person} ({n}):

▸ {task_link} {title} — {status} {priority} | their role: {RACI}
   Last touch: {date} ({source: Timeline/email})
   {if open asks owed by me to this person:}
   📤 Owed by me:
      • {what} ({age} since asked)
   {if open asks owed to me from this person:}
   📥 Waiting on them:
      • {what} ({age} waiting)

▸ {next task...}

Suggested agenda:
1. {open ask owed by me, oldest} — close it
2. {open ask owed to me, oldest} — chase it
3. {long-untouched task} — heads-up sync
4. {anything new since last touch} — FYI
```

7. Agenda items use real data — no template fillers.

---

## review {period} / 述职

**Triggers (any phrasing matching the intent — must include a time-period signal):**

- English: `review Q1 2026`, `review 2026`, `annual review 2026`, `semi-annual review`, `H1 review`, `what did I accomplish in Q2`, `summary of this quarter`, `performance review prep`
- Chinese: `述职`, `半年述职`, `年度总结`, `年度述职`, `Q2 做了啥`, `Q2 总结`, `这季度做了啥`, `这半年做了啥`, `总结一下这半年`, `工作汇报材料`
- Pattern: input contains a period reference (`Q1-Q4`, `半年`, `annual`, `年度`, `这季度`, `H1/H2`) AND an action word (`做了啥`, `accomplished`, `总结`, `summary`, `review`, `述职`)
- If period is ambiguous (e.g., user just says "述职"), ask which period: current quarter / last quarter / H1 of current year / annual.

**Steps:**

1. **Common Setup**.
2. Resolve period:
   - `review Q2 2026` → Q2 2026
   - `半年述职` / `review semi-annual` → ask user H1 (Q1+Q2) or H2 (Q3+Q4) of current year, or both halves of prior year if late in current year
   - `review 2026` / `annual review 2026` → all four quarters of 2026
3. **Big events:** Read [`memory/achievements.md`](../memory/achievements.md). Filter entries to the resolved period.
4. **Workload aggregation (small tasks):**
   - Glob `tasks/history/{YYYY}-Q{n}/T*.md` for quarters within the resolved period → read header fields (Category, Geo, Tags, Timeline completion date) from each file
   - Filter to tasks completed within the resolved period
   - Exclude tasks already in achievements.md (avoid double-counting)
   - Aggregate by: Category (count), Geo (count), and Tag clusters (top keywords by frequency)
   - Compute totals: tasks completed, geos served, unique stakeholders touched
5. Read [`memory/preferences.md`](../memory/preferences.md) → tone, language.
6. Group achievement entries by category (taxonomy already in achievements.md).
7. Output **three sequential formats**:

   **Format 1: Workload stats** (quantitative overview)
   ```
   📊 Workload: {period}

   Tasks completed: {N} (Big events: {n_achievements} · Routine: {n_routine})
   Geos served: {geo_list with counts}

   By category:
   - Training coordination: {n} tasks
   - Vendor procurement: {n} tasks
   - Reporting: {n} tasks
   - {other categories...}

   Top tags: `{tag1}` ({n}) · `{tag2}` ({n}) · `{tag3}` ({n}) · ...
   ```

   **Format 2: Bullet summary** (big events, dense)
   ```
   📋 Key achievements: {period}

   🎓 Training Delivery ({n})
   - {Title} (T###, {date}) — {Outcome shortened to 1 line}
   - ...

   💼 Process / Strategy ({n})
   - ...

   {repeat for each non-empty category}
   ```

   **Format 3: Narrative draft** (述职 paragraph form, in user's preferred tone)
   ```
   ✍️ Narrative draft (in {tone} tone, {language})

   ## {Period} Performance Summary

   {Opening paragraph with workload stats — tasks completed, geos served, scope}

   {Category 1 narrative paragraph — 3-5 sentences synthesizing big events + volume context}

   {Category 2 narrative paragraph}

   {...}

   ---
   Notes:
   - All {N} achievements have task ID linkbacks above for verification
   - Workload stats derived from {N_total} completed tasks in history
   - Empty categories ({list}) intentionally omitted — add manual entries if relevant
   ```

8. Don't invent achievements not in `achievements.md`. Workload stats come from actual history files only.
9. Always include task ID linkbacks `[T###](../tasks/history/{YYYY}-Q{n}/T###-xxx.md)` so the user can verify any claim.
10. Offer follow-up: `Want me to expand a specific category, adjust tone, or pull supporting evidence?`

---

## Pattern Matching for Cognitive Blind Spots

Used by `owed` (and any future view op that wants to flag matched patterns).

**Source:** [`memory/things_to_avoid.md`](../memory/things_to_avoid.md) → `Patterns` section.

**Matching:**

1. Parse each Pattern's `Trigger` field. Triggers are written in natural language but should be machine-checkable predicates over current state (tasks, Asks, emails).
2. Evaluate each Trigger against current state.
3. For each Pattern that matches, emit its `Brief action` text in the appropriate Brief section (or as a top-level note if Brief action specifies).
4. **Conservative evaluation:** if a Trigger is ambiguous, do NOT fire. Patterns should be cleaned up to be unambiguous; firing falsely trains the user to ignore them.

---

## Notes

- **Stateless.** View commands never write derived data anywhere. All output is recomputed from task files + Asks + Email References + config.
- **Read order matters for cache locality.** Common Setup reads queue.md first to know which T### files to load.
- **Section ordering and thresholds** all live in [`views_config.md`](../views_config.md). Edits to behavior happen there, not in this file.
- **No silent skips.** If a task file is malformed (missing Asks section), surface a one-line warning at the bottom of the view output, but still produce results from the rest.
