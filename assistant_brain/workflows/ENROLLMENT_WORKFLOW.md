# Enrollment Workflow

> **ALWAYS load the enrollment workflow before executing any enrollment check, eCard dispatch, or roster processing.**

---

## Triggers and Timeline

This workflow manages the pre-training enrollment, promotion, and shortlisting schedule for high-capacity courses (such as Red Hat training sessions in FNC India). These are handled as two independent and separate business procedures.

| Timeline | Action | Purpose / Rules |
|----------|--------|-----------------|
| **2 Weeks Ahead (Monday)** | **Dispatch eCard to SPOCs** | **Workflow: Promote Event** — Send course announcement and nomination links to geo/sector SPOCs. |
| **2 Weeks Ahead (Thursday)** | **First Enrollment Check** | Check registrations; if < 30, deploy promotion to the large audience. |
| **2 Weeks Ahead (Friday)** | **Second Enrollment Check** | Check registrations; if still < 30, send out reminder promotion. |
| **1 Week Ahead (Monday)** | **Shortlist & Roster Finalization** | **Workflow: Select Nominations** — Run check-enrollment to match headcount, select 12 confirmed and backups, and share workbook with LDM. |

---

## Workflow: Select Nominations (1 Week Ahead Monday)

This procedure is executed exactly **1 week prior** to the course start date to evaluate waitlists and select the final participants.

### Step 1: Run Enrollment Downloader
Execute the Playwright-backed enrollment downloader skill for the target Class ID to get the raw CSV:
```bash
py -3 "assistant_brain/skills/enrollment-downloader/scripts/download_roster.py" <class_id>
```
*Note: Headless mode is disabled (`headless=False`) by default. If SSO is required, complete the PIN/passkey manually in the browser window. Subsequent runs will use the cached state in `.auth_state.json`.*

### Step 2: Roster Evaluation and Selection
Run the standard enrollment evaluator script to automatically cross-reference with the headcount database, exclude non-India or non-regular employees, score candidates, and generate the final color-coded shortlist workbook:
```bash
py -3 "assistant_brain/skills/enrollment-downloader/scripts/check_enrollment.py" <class_id> [--hc <headcount_csv_path>] [--history <historical_enrollment_csv_path>] [--export <output_excel_path>]
```
- **Inputs & Parameters:**
  - `class_id` — Positional parameter (e.g., `10580795`).
  - `--hc` — Headcount database file containing bands and roles. (Defaults to `C:\Users\MengNingLuo\Downloads\GDMIS_PIR_withBand_07-Jul-2026.csv\extracted_columns_20260715_181852.csv`).
  - `--history` — Historical enrollment file to exclude past completions. (Defaults to `downloads/class_10580795_enrollments.csv`).
  - `--export` — Output path for the styled Excel shortlist. (Defaults to `downloads/<COURSE_CODE>_<day_num>_<Month>.xlsx` — e.g., `downloads/DO288_3_Aug.xlsx`).
- **Filters & Logic Evaluated:**
  - **Exclusion 1:** Exclude non-India candidates (Country Code must be `744` or email ends with `@in.ibm.com`).
  - **Exclusion 2:** Exclude non-regular employees (Type must be `P`).
  - **Exclusion 3:** Exclude duplicate learners who have already completed the course previously in the history file (status = completed/complete).
  - **Scoring & Selection (to select top 12):** Valid learners are scored based on job roles (Developers/Architects get `+30`, DevOps/SRE/Platform get `+20`) and target bands (6A, 6B, 6G, 7A, 7B get `+10`, while bands 8/9 get `-10`). Waitlist position order is kept as the baseline tiebreaker.
- **Roster Export:** Generates a beautifully styled Excel workbook with explicit gridlines enabled and row-wide color highlights applied:
  - **Green (Confirmed):** Top 12 scored, qualified learners.
  - **Yellow (Backup):** Next eligible runners-up in waitlist order.
  - **Red (Excluded):** Candidates who failed geographic, employment, or historical duplicate checks.

Share the final color-coded Excel workbook with LDM B Sowmya.

---

## Workflow: Promote Event (2 Weeks Ahead Monday)

This procedure is executed exactly **2 weeks prior** to the course start date to invite registrations.

### Step 1: Locate Previous eCard Template
Search the `Sent Items` folder to find the EntryID of the previous session's sent eCard (e.g., search for "RH294" or other course keywords):
```bash
py -3 "assistant_brain/skills/outlook-com-skill/scripts/outlook_skill.py" find --subject "<course_code>" --folders "Sent Items" --days 60
```

### Step 2: Create the New Draft using `edit-html`
Take the template's `EntryID`, override the subject line, perform in-place replacements (class IDs, registration links, date strings), and save it as a new draft in your Outlook `Drafts` folder:
```bash
py -3 "assistant_brain/skills/outlook-com-skill/scripts/outlook_skill.py" edit-html <original_email_id> --subject "<new_subject_line>" --replace "old_date::new_date" --replace "old_class_id::new_class_id"
```
*Note: The `--replace` argument is repeatable for multiple substitutions.*

### Step 3: Review and Send
Open Outlook to review the draft, or send it out automatically after obtaining explicit user approval:
```bash
py -3 "assistant_brain/skills/outlook-com-skill/scripts/outlook_skill.py" send-draft <draft_email_id>
```

---

## Common Procedures: Timeline and Task State Updates

After completing any step in either workflow, immediately read the corresponding task file and update the `## Timeline` (including the exact email thread or action references) and check off completed items in `## Current State` or `## Asks`.

---

## Large Audience Detail
*Note: The exact target segment criteria and distribution list details for the broad/large audience promotion will be finalized next time.*
