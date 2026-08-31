# Red Hat Training Workflow

> Red Hat Training operations domain: **audience targeting & shortlisting** + **Training Unit (TU) ledger sync**.
>
> **Script execution** (extract/select CLI args) lives in `skills/redhat-audience-processor/SKILL.md` — load it before running any script.

---

## Part A: Audience Targeting & Enrollment Shortlist

> **Lifecycle** applies to Red Hat training classes in FNC India.

### 📅 Timeline & Operational Phases

| Timeline Stage | Action Phase | Purpose |
|----------------|--------------|---------|
| 2 Weeks Ahead (Mon) | Phase 1: Event Promotion | Dispatch course announcement eCards to Sector/Practice SPOCs |
| 2 Weeks Ahead (Thu/Fri) | Phase 2: Target Audience Extraction | If class waitlist < 30, run multi-source extraction (5 data sources) → Top 1,000–1,500 targets → batch-forward eCards |
| 1 Week Ahead (Mon) | Phase 3: Final Shortlist & Roster | Score waitlisted candidates, filter exclusions, select Top 12 Confirmed (Green) + Backups (Yellow), export styled Excel for LDM |
| Delivery Week (Mon–Fri) | Phase 4: Class Delivery | Track attendance, resolve access issues, collect feedback |

### Phase 2: Target Audience Extraction

**When:** 2 weeks before course start, OR class registration < 30, OR full employee-base promo needed.

5 data sources evaluated (CLI args in skill — parameters default gracefully if a report is unavailable or omitted):

| # | Data Report | Purpose |
|---|-------------|---------|
| 1 | Certifications & Badges | Excludes active target cert holders; +100 pts for prereq certs |
| 2 | Past 1-Year Class Attendance | Excludes learners who attended target class in last 12 months |
| 3 | Target Course Self-Paced Transcripts | +60 pts for target self-paced completers |
| 4 | Prerequisite Transcripts | +80 pts for prereq course completers (bypassed for foundational courses with no prereqs like DO188) |
| 5 | Headcount Database (GDMIS PIR) | Base pool; +15~35 pts for skill/role match |

### 📥 5-File Report Input Process (MANDATORY USER PROMPT)

> **⛔ DO NOT AUTO-SCAN FOLDERS:** The agent MUST NOT automatically scan `Downloads/` or workspace folders for report files without asking the user first, as local files may be stale or outdated.

When executing Phase 2 (Target Audience Extraction) or Phase 3 (Participant Shortlist):

1. **Always Prompt the User First:**
   * Identify the course code for the target class and run `py -3 "assistant_brain/skills/redhat-audience-processor/scripts/course_rules.py" <COURSE_CODE>` (or check the table below) to fetch its exact prerequisite rules.
   * Prompt the user to provide or confirm the exact paths for the 5 report files (or reply `none` for any unavailable/unneeded report). **In the prompt, explicitly state the target course code and list the exact Tier 1 Certifications and Tier 2 Prerequisite Course Codes for File #4 (`--prereq`) and File #1 (`--cert`)**:
     - **1. Certificate Data (`--cert`):** T2G / Credly certificate report (filters Tier 1 certs: `{TIER_1_CERTS}`)
     - **2. Past Attendance (`--past`):** Past 1-Year class attendance report
     - **3. Target Self-Paced (`--selfpaced`):** Target course self-paced completion report
     - **4. Prerequisite Transcripts (`--prereq`):** Prerequisite course completion report — **for `{COURSE_CODE}`, filter for Tier 2 courses: `{TIER_2_COURSES}`** *(optional for DO188)*
     - **5. Headcount Database (`--hc`):** GDMIS PIR headcount database report
   * Only run the script once the user has provided or confirmed the file paths. Any omitted file (`none`) defaults gracefully.

### ✉️ Standard Batch Promotional Email Template

Use this standardized template when dispatching batch-forward eCard campaigns to target audiences in Phase 2:

```html
<p>Dear Team,</p>
<p>We encourage you to enroll in this {COURSE_CODE} {COURSE_NAME} class ({START_DATE}–{END_DATE}). This skills-focused course is highly recommended to boost your {TOPIC_SKILLS} capabilities.</p>
<p>Please note:<br>
- Your enrollment will be 'wait-listed' by default.<br>
- Confirmation is on a first-come, first-served basis, subject to L&K eligibility checks.<br>
- Confirmed learners will receive a final confirmation email next Monday ({CONFIRMATION_DATE}).</p>
<p>Enrollment links and details are in the eCard below.</p>
```

### Red Hat Course Reference Rules

> **Single Source of Truth:** Course prerequisite rules and Tier 1 / Tier 2 mappings are maintained in:  
> 👉 **[`assistant_brain/skills/redhat-audience-processor/references/course_rules.md`](../skills/redhat-audience-processor/references/course_rules.md)**

### Phase 3: Final Shortlist & Roster Selection

Executed exactly 1 week prior to course start.

1. **Download live roster** → `enrollment-downloader` skill: `download_roster.py <class_id>`
2. **Select participant** → `redhat-audience-processor` skill: `select_participant.py <class_id>` with the 5 data source CLI args (see skill).
   - If the roster was already downloaded in the same workflow/session, **reuse it** with `--skip-download --input "downloads/class_<class_id>_enrollments.csv"` instead of downloading again.
   - Only omit `--skip-download` when a fresh live roster refresh is explicitly needed.
   - **Filter 1 (Exclusions):** non-India (Country Code != 744 / email != @in.ibm.com), non-Regular (Type != P), prior completions.
   - **Filter 2 (Scoring):** role fit +30, target band +10, prereq credentials +100. Waitlist position = baseline tiebreaker.
   - **Output:** 🟩 Green (Top 12 Confirmed) · 🟨 Yellow (Backup) · 🟥 Red (Excluded).
3. **Handoff to LDM** → share color-coded Excel with LDM B Sowmya for LMS confirmation + RHID/registration dispatch.

---

## Part B: Training Unit (TU) Ledger Sync

> On-demand sync of Red Hat TU consumption from email notifications into the reference ledger.

**Reference file:** `assistant_brain/references/redhat-tu-tracking.md`

### TU Sync

**Triggers:** "tu sync", "sync tu", "同步TU", "TU更新", "update tu"

1. **Read reference file** → get "Next sync" boundary + processed order numbers list.
2. **Load email skill** → search emails from `no-reply@training.redhat.com` dated after the boundary date.
3. **Filter new orders** → for each email: extract order number (subject `Your Red Hat Training order {ORDER_NUM} is confirmed`), skip if already processed; extract Order #, Line #, Learner, Course, Start, End, TUs, TUA account.
4. **Update reference file** → append rows to correct TUA section, update TUA subtotal (Used/Left) + Balance Summary, add order number to processed list.
5. **Update sync metadata** → "Last Updated", Sync Log row, advance "Next sync" boundary.
6. **Report:**
   ```
   TU Sync Complete
   Emails checked: {count} | New orders found: {count} | TUs consumed: {total}
   Balance changes: - {TUA}: {old_left} → {new_left}
   Alerts: - {any TUA with Left < 50}
   ```

### Smartsheet Balance Update

**Triggers:** "tu balance", "TU余额", "smartsheet balance"

1. Read reference file → current balances.
2. Search latest email from `automation@app.smartsheet.com` containing "Training Unit".
3. Extract TUA balances from Smartsheet notification.
4. **Cross-reference** vs calculated balances — Smartsheet is authoritative for total Used/Left.
5. Update Balance Summary if divergent; report discrepancies + corrections.

### TU Notes

- Each email may contain multiple line items (same order, different lines).
- TUA assignment in body: `Training Unit Account: {TUA_ID}`.
- "Total Training Units used to Date" = batch snapshot — use to cross-check Left.
- Near-depletion threshold: Left < 50 TUs → flag alert.
