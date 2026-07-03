# TU Sync Workflow

> On-demand sync of Red Hat Training Unit consumption from email notifications into the reference ledger.

---

## TU Sync

**Triggers:** "tu sync", "sync tu", "同步TU", "TU更新", "update tu"

**Reference file:** `assistant_brain/references/redhat-tu-tracking.md`

**Steps:**

1. **Read reference file** — load `redhat-tu-tracking.md` to get:
   - The "Next sync" date boundary
   - The processed order numbers list
2. **Load email skill** — glob for `assistant_brain/skills/*/SKILL.md`, load the outlook skill
3. **Search emails** — find emails from `no-reply@training.redhat.com` dated after the boundary date
   ```
   search-emails "from:no-reply@training.redhat.com" --after {boundary_date} --limit 50
   ```
4. **Filter new orders** — for each email found:
   - Read full email content
   - Extract order number from subject/body
   - Skip if order number is already in processed list
   - Extract: Order #, Line #, Learner, Course, Start, End, TUs, TUA account
5. **Update reference file** — for each new order:
   - Append row to correct TUA section table
   - Update TUA subtotal (Used/Left)
   - Update Balance Summary table
   - Add order number to processed list
6. **Update sync metadata:**
   - Update "Last Updated" date
   - Add row to Sync Log table
   - Update "Next sync" boundary to latest email date
7. **Report** — present summary to user:
   ```
   TU Sync Complete
   ─────────────────
   Emails checked: {count}
   New orders found: {count}
   TUs consumed: {total_new_tus}
   
   Balance changes:
   - {TUA}: {old_left} → {new_left}
   
   Alerts:
   - {any TUA with Left < 50}
   ```

---

## Smartsheet Balance Update

**Triggers:** "tu balance", "TU余额", "smartsheet balance"

**Steps:**

1. **Read reference file** — load current balances
2. **Load email skill**
3. **Search emails** — find latest email from `automation@app.smartsheet.com` containing "Training Unit"
4. **Extract snapshot** — parse TUA balances from Smartsheet notification
5. **Cross-reference** — compare Smartsheet balances against calculated balances in reference file
6. **Update if divergent** — Smartsheet is authoritative for total Used/Left; update Balance Summary table
7. **Report** — show any discrepancies found and corrections made

---

## Notes

- Order emails have subject pattern: `Your Red Hat Training order {ORDER_NUM} is confirmed`
- Each email may contain multiple line items (same order, different lines)
- TUA assignment is in email body: "Training Unit Account: {TUA_ID}"
- "Total Training Units used to Date" in emails is a batch-level snapshot — use it to cross-check Left values
- Near-depletion threshold: Left < 50 TUs → flag alert
