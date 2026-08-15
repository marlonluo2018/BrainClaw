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

5 mandatory data sources (CLI args in skill):

| # | Data Report | Purpose |
|---|-------------|---------|
| 1 | Certifications & Badges | Excludes active target cert holders; +100 pts for prereq certs |
| 2 | Past 1-Year Class Attendance | Excludes learners who attended target class in last 12 months |
| 3 | Target Course Self-Paced Transcripts | +60 pts for target self-paced completers |
| 4 | Prerequisite Transcripts | +80 pts for prereq course completers |
| 5 | Headcount Database (GDMIS PIR) | Base pool; +15~35 pts for skill/role match |

### Red Hat Course Reference Rules

| Course | Prerequisite Credentials (Tier 1, +100) | Prerequisite Courses (Tier 2, +80) | Target Cert Exclusions (Pass 1) |
|--------|------------------------------------------|------------------------------------|---------------------------------|
| DO316 OpenShift Virtualization | EX200, EX280 | DO180, DO280, RH124, RH134, DO188 | EX316 |
| DO374 Ansible Automation Platform | EX294 / RHCE | RH294, AU294, RH124, RH134 | EX374 |
| RH294 Linux Automation w/ Ansible | EX200 | RH124, RH134 | EX294 / RHCE / any active Ansible cert |
| DO288 OpenShift Developer II | EX188, EX180, EX280 | DO188, DO180, DO280 | EX288 |
| DO280 OpenShift Administration II | EX200 | DO180, RH124, RH134 | EX280 |
| DO188 Intro to Containers w/ Podman | None (Linux/Unix role priority) | RH124, RH134 | EX188, EX180, EX280, EX288, EX380 |
| AI267 AI/ML on OpenShift AI | EX280, EX188 | DO280, DO188, DO288 | EX267 |

### Phase 3: Final Shortlist & Roster Selection

Executed exactly 1 week prior to course start.

1. **Download live roster** → `enrollment-downloader` skill: `download_roster.py <class_id>`
2. **Select participant** → `redhat-audience-processor` skill: `select_participant.py <class_id>` with the 5 data source CLI args (see skill).
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
