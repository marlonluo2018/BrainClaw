---
description: The review rulebook for outgoing BrainClaw email — screening table, deliberation classes, severity rules, and the locked output format. Applied by the root agent as a mandatory self-review before every draft presentation.
---

# Email Review Rulebook

This is the **rulebook** for reviewing every outgoing email draft before it is presented to the user. The root agent applies it as a self-review (see `EMAIL_WORKFLOW.md` Send Flow step 3). It is deliberately written as a checklist with a locked output format: working the table line by line is what removes the drafter's blind spot — a review that "reads the draft and feels it's fine" is not a review.

The review's findings are **advisory**: they ride along with the presented draft so the user approves with full information. The user's explicit decision overrides any finding.

## Review procedure

1. Read the body file completely, plus the task file when the email is task-related (it is the source of truth for what is established fact vs. internal reasoning).
2. Classify every recipient (To + CC): **L&K internal** (L&K / Delivery Shared Service / operations roles), **IBM non-L&K** (BU leaders, requesters, EMs, GM, finance, procurement), or **external** (any non-@ibm.com address or vendor). The strictest class on the thread sets the screening bar.
3. Run the scanner: `py -3 assistant_brain/scripts/screen_outgoing_body.py <body-file> --subject "..." --json` — treat its findings as input to this review, not the verdict; anything it flags that your semantic pass clears still appears as 🟡 "scanner flag, cleared for this audience".
4. Apply the screening table (below) to every sentence of the body and the subject — including the rows that end in "no finding": the output must show the table was worked, not skipped.
5. Produce the findings in the locked output format (below).

## Screening table

| Content | L&K internal | IBM non-L&K | External |
|---------|--------------|-------------|----------|
| EPD / Class ID / PO numbers | may keep | 🔴 high unless the workflow genuinely needs it (e.g. reimbursement process) | 🔴 high (remove) |
| BrainClaw task IDs (T###) | 🔴 high | 🔴 high | 🔴 high |
| AI-assistant deliberation / attribution — see class 1 below | 🔴 high | 🔴 high | 🔴 high |
| Task-handling deliberation — see class 2 below | 🟡 low | 🔴 high | 🔴 high |
| Internal approval-route disclosure ("via SVP exception", "offcycle approval", naming the exception/override mechanism a class went through) | 🟡 low | 🔴 high | 🔴 high |
| Unconfirmed info (numbers/dates/promises without a source in the task file or thread) | 🔴 high | 🔴 high | 🔴 high |
| Internal links (w3.ibm.com, lksprod.dst.ibm.com, ibm.box.com, ibm.sharepoint.com, wolf.yourlearning.ibm.com) | may keep | 🟡 low | 🔴 high |
| Vendor contact names when a business requester is on the thread | — | 🔴 high (use company/role) | — |
| Subject-line EPD numbers / Class IDs | 🟡 low | 🔴 high | 🔴 high |

### The two deliberation classes

A sentence is deliberation when it exposes **how a decision was reached** rather than the decision itself. Classify which kind first, then apply the tests:

**Class 1 — AI-assistant deliberation / attribution (🔴 for every audience).** Anything revealing that a personal AI assistant participated in analyzing, deciding, or drafting: "per the assistant's analysis", "my AI tool suggested", "the summary I generated", or references to task-management machinery the user alone would not write ("my task file notes...", "per my records, hold pending..."). Markers: language that treats the BrainClaw system (task files, Asks, timelines, the assistant) as a participant or source. Revealing a private AI workflow in business correspondence is never acceptable to any recipient.

**Class 2 — task-handling deliberation (🟡 for L&K internal, 🔴 otherwise).** Human-to-human internal discussion that shaped how the work is being handled: input from colleagues/managers/approvers, options weighed, sequencing logic. Apply these tests in order; the first hit decides:

1. **Does it name who influenced the outcome inside the approval/consultation chain?** — "per Hong Yang's suggestion", "George asked us to", "per Marlon's hold instruction" → deliberation. (Task-file Asks/Timeline language like "per Marlon:" is the strongest marker — that phrasing exists only in our internal records.)
2. **Does it narrate options or process before the conclusion?** — "we considered internal SMEs but they were unavailable", "we evaluated postponing to Q1", "first we'll X, then depending on Y" (internal sequencing logic) → deliberation.
3. **Does it attribute the request's origin or motive?** — "this training was requested because the AO team lacks...", "the vendor was chosen after we compared..." → deliberation when the motive/selection reasoning is ours, not the recipient's own.

**Rewrite direction for both classes**: keep the conclusion, drop the reasoning chain — "per Hong Yang's suggestion all spend goes through Andrew" → "all spend actions go through Andrew for approval"; "we considered SMEs but they were unavailable" → "internal SMEs are currently unavailable".

**Approval-route disclosure is its own row, not class 2.** Phrases like "approved via SVP exception", "through offcycle approval", "by GM exception" disclose the internal approval mechanism a class went through — an override route that exists only because normal governance didn't apply. Even when no influencer is named and no options are narrated (so the class-2 tests miss it), the route itself is internal information: it tells the recipient this spend was not normally approved, which can weaken the requester's position in vendor negotiations and invites questions about why. Rewrite: keep the outcome only — "was approved in EPD" — unless the recipient is inside that approval chain (L&K internal / the approver themselves / procurement already engaged in the exception workflow, where it stays 🟡).

Severity meaning: **🔴 high** = would leak internal information or commit the sender to something unverified if it reaches this audience; must be explicitly acknowledged by the user before sending. **🟡 low** = technically internal but low-risk for this audience; mention, don't insist.

## Output format

The review is only valid in this locked structure — it is the audit trail that the table was actually worked:

```
## 🔍 Review
**Audience:** L&K internal: <names> · IBM non-L&K: <names> · External: <names>
**Scanner:** <N> finding(s) — <covered below / all resolved>

**🔴 High findings** (must be explicitly accepted before sending)
- 🔴 <category> — "<exact quoted text from the body>" → <suggested fix: remove / rewrite as conclusion / confirm source>
(or "None")

**🟡 Low findings**
- 🟡 <category> — "<short quote>" → <note>
(or "None")

**Checked clean:** <list the screening-table rows worked with no finding, e.g. "EPD/Class/PO numbers; task IDs; AI-attribution; task-handling deliberation; approval-route; unconfirmed numbers; internal links; vendor names; subject identifiers">
```

Rules for the output:

- Quote the exact offending text — the user must be able to find it in the draft without hunting.
- One finding per item; no editorializing about the draft's quality, tone, or length — this screens for information leakage, not style.
- If the scanner flags something your semantic pass clears (e.g. an internal link to an L&K-internal recipient), still list it as 🟡 with "scanner flag, cleared for this audience" so nothing is silently dropped.
- Never soften a high finding because the content was intentional in the drafting conversation — the user decides at approval time, not during drafting.
- The "Checked clean" line is mandatory: it proves the rows without findings were examined, and it tells the user exactly which leakage shapes were covered on this round.
