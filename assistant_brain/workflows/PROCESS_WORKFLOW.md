# Process Workflow

> 流程推进引擎。关联 task → process template → next action。支持自动推进、流程学习、固化。

---

## Triggers

| User intent | Operation |
|-------------|-----------|
| "next step" / "下一步" / "推进" / "push" | Suggest next action for a task |
| "what process" / "什么流程" / "走哪个流程" | Show matched process for a task |
| "固化流程" / "记录流程" / "codify process" | Extract + create process file from task history |
| (automatic) email sync completes | Append process observations to summary |

---

## A. 流程匹配 + 自动推进

**When:** User asks "next step T###" or after email sync updates a task.

**Steps:**

1. Read task file → get **Category** + **Geo**
2. Match against [`process/README.md`](../process/README.md) index:

| Category keywords | Geo | Process File |
|-------------------|-----|-------------|
| Procurement, vendor, PO + offcycle/新增 | China | `china/offcycle-budget-approval.md` |
| Procurement, vendor, PO (quarterly) | Philippines | `philippines/vendor-procurement.md` |
| Voucher + AWS | Philippines | `philippines/aws-voucher-issuance.md` |
| Voucher + Azure | Philippines | `philippines/azure-voucher-issuance.md` |
| Retake, failed, 补考, reimbursement, 报销, no voucher | Philippines | `philippines/exam-reimbursement.md` |
| Reimbursement, 报销 | China | `china/futurenow-quarterly-reimbursement.md` |
| Snowflake | any | `global/snowflake-certification.md` |
| Google, GCP | any | `global/google-exam-voucher-discount.md` |

3. Read matched process file → get Steps list
4. Scan task `## Current State` → determine progress:
   - Consecutive checked `[x]` / `[✅]` from top = completed steps
   - First `[ ]` or `[⏳]` = current step
   - Map current step keywords back to process step number
5. Look up responsible contact from process file's Stakeholders table (or [`contacts.md`](../contacts.md) Process Roles)
6. Output suggestion

**Output format:**

```
🔄 T### | Process: {name} (step {N}/{total})
→ Next: {action from process step}
→ Contact: {name} <{email}> — {role}
→ Suggest: {draft email / follow up / wait / escalate}
```

**If no process matches** → use Generic Flows (below).

---

## Generic Flows

For tasks that don't match a specific process file.

### Generic Procurement

1. Requirements confirmed with requester
2. Vendor sourcing / quotation request
3. Quote received → budget approval (L&K leader)
4. Budget approved → EPD/PO processing
5. PO issued → vendor confirms
6. Delivery / fulfillment
7. Close task

**Contact lookup by geo:** See [`contacts.md` Process Roles Quick Reference](../contacts.md#process-roles-quick-reference)

### Generic Training Enrollment

1. Budget + vendor confirmed
2. Send nominations to vendor
3. Vendor confirms dates + logistics
4. Share joining details with participants
5. Training delivered
6. Collect completion results / certificates
7. Post-training admin (reimbursement if applicable)

### Generic Budget Approval

1. Draft budget plan / request
2. L&K leader approval (Janice / Beng / Alphonsa by geo)
3. EPD Plan Row created
4. George Varghese approves EPD
5. LDM assigned (Citra / Sneha / B Sowmya by geo)
6. Ready for procurement

---

## B. 流程学习（Email Sync 实时检测）

**When:** Every time email sync writes a new timeline entry to a task file.

**Logic:**

1. After writing timeline entry, check: does this task have a matched process file?
2. **If matched process exists:**
   - Compare new timeline entry against process steps (keyword match)
   - If entry maps to a known step → normal, note progress
   - If entry describes an action NOT in the process → flag as new step observation
3. **If no process matches:**
   - Check: are there ≥2 active/completed tasks with same Category+Geo?
   - If yes → flag as "untracked process pattern"

**Output (appended to email sync summary):**

```
📝 Process Observations:
- T053: "vendor confirms entity" — not in offcycle-budget-approval.md (seen in T042, T053)
- T044: No process file for Category="Training Procurement" + Geo="China" (3 tasks: T042, T044, T053)
  → Suggest: Codify this process? Say "固化流程" to proceed.
```

**Rules:**
- Only show observations when there's something new (don't repeat every sync)
- Track observation count mentally across the conversation (not persisted to file)
- Threshold for suggesting codification: same pattern seen in ≥2 tasks

---

## C. 流程固化

**Trigger:** User says "固化流程" / "记录流程" / "codify process", or system suggests after detecting repeated pattern.

**Steps:**

1. Identify target: which Category + Geo to codify
2. Find evidence tasks: active + completed tasks matching that Category+Geo
   - Active: `assistant_brain/tasks/T*.md`
   - Completed: `assistant_brain/tasks/history/*/T*.md`
3. Read their Timelines → extract action sequence (filter to `[milestone]`, `[action]`, `[decision]`, `[PO]`, `[Email Sent]` tags)
4. Normalize into ordered steps (merge duplicates, abstract specifics)
5. Identify stakeholders from task Contacts/RACI sections
6. Generate process file draft following existing format:

```markdown
# {Process Name}

**Effective:** {today}
**Geo:** {geo}

---

## When This Applies

{one-line description}

---

## Steps

1. **{Step name}** — {description}
2. ...

---

## Key Rules

- {extracted from task patterns — e.g., "sequence is mandatory", "never skip step X"}

---

## Stakeholders

| Role | Person | Email |
|------|--------|-------|
| ... | ... | ... |
```

7. Present draft to user for confirmation
8. On confirm → write to `process/{geo}/{name}.md` + update `process/README.md`
9. Update `scripts/shared_config.py` → add entry to `PROCESS_MATCH_RULES` with keywords, geo, and file path from the new process

---

## D. Stale Detection

**When:** During email sync, dashboard, or explicit "next step" query.

**Thresholds:**

| Priority | Stale if no activity for |
|----------|--------------------------|
| P1 | > 2 days |
| P2 | > 5 days |
| P3 | > 10 days |

**Logic:**
1. Read task timeline → find last entry date
2. Compare to today → if exceeds threshold, flag stale
3. Identify which process step is stuck (from Current State)
4. Look up contact responsible for that step

**Output:**

```
⚠️ Stale: T053 — 4d no activity
   Stuck at: step 5/6 "PO issued → vendor confirms"
   → Follow up: Padmashree K (vendor, order form)
   → Or escalate: WEN WEI ZHAO (Mandy) (procurement coordinator)
```

---

## Integration Points

| System | How process workflow integrates |
|--------|-------------------------------|
| Email Sync | After task updates → append process suggestion + observations |
| Dashboard | Stale tasks show process-aware follow-up |
| `before {person}` | Show which process step involves them |
| Task Creation | Match to process → pre-suggest Current State steps |
| Task Completion | Check if process was undocumented → offer codification |
