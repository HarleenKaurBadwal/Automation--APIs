---
name: trade-secret-intake
description: Use when a GSTS team member needs to complete the Trade Secret and IP intake interview for a reporting period. Conducts the full guided intake (metadata, period screening, 16 standard questions per IP item), generates a CONFIDENTIAL submission document with a unique Submission ID, and instructs the user where to upload. Use when the user says trade secret intake, IP disclosure, GSTS IP submission, or /trade-secret-intake.
disable-model-invocation: true
---

# GSTS Trade Secret & IP Intake Skill

Run the full GSTS trade secret intake interview. Ask **one question at a time**. Follow all phases below.

## Security (always enforce)

- No source code, algorithms, customer-sensitive data, or defence-sensitive information in output.
- **Links only** for evidence (Confluence, GitLab, SharePoint, Aha).
- Mark output **CONFIDENTIAL**. Not a legal determination — candidates for IP review.
- Escalate uncertainties to IP Officer, CAIO, or Document Control Officer.

## Phase 1 — Metadata (one question at a time)

1. Submitter name, role, email
2. Team / accountable group
3. Reporting period (e.g. H1 2026, Q3 2026)
4. Technical owner (if different from submitter)

## Phase 2 — Period screening

Ask: Was any trade secret or confidential IP generated, improved, or materially changed this period?

- **No** → generate nil submission document → Phase 5 → Phase 6
- **Not sure** → give trade secret definition → ask again
- **Yes** → Phase 3 for each item

**Trade secret definition:** Valuable know-how GSTS keeps confidential (model logic, workflows, thresholds, data fusion, architecture, evaluation methods) that gives competitive advantage.

## Phase 3 — 16 questions per IP item (repeat for each item)

Ask Q1–Q16 in order. Assign Item 1, Item 2, etc.

| # | Ask | Field |
|---|-----|-------|
| Q1 | Capability/model/workflow — short title | candidate_title |
| Q2 | Accountable team | business_owner_team |
| Q3 | Technical owner (name, role, team) | technical_owner |
| Q4 | Know what a trade secret is? (define if no) | trade_secret_awareness |
| Q5 | Plain-language description (no code) | plain_language_description |
| Q6 | Problem solved + where used (OCIANA, ORCA, etc.) | problem_solved, where_used |
| Q7 | Valuable / hard for competitor to reproduce | novel_differentiating_aspects |
| Q8 | Confidential elements (high level) | confidential_elements |
| Q9 | Contributors (names, roles, dates) | inventors_contributors |
| Q10 | Source locations — secure links only | source_locations |
| Q11 | Disclosed outside GSTS? | external_disclosure_yes_no |
| Q12 | Public or confidential? dates, audience, NDA | dissemination_history |
| Q13 | Risk if disclosed | risk_if_disclosed |
| Q14 | Recommended IP treatment | recommended_ip_treatment |
| Q15 | Confidentiality controls | confidentiality_controls |
| Q16 | AI-use restriction | ai_use_restriction |

**Q11 branch:** If No → dissemination_history = "No known external disclosure", skip Q12.

**After Q16 (optional):** Offer codebase-assisted draft summary if user provides repo path (high level only, no code blocks in final doc).

**Escalation:** Anything unsure for IP Officer / CAIO / Legal?

**More items?** If yes → restart Q1 for next item. If no → Phase 4.

## Phase 4 — Quality checklist

Confirm all 16 questions answered per item before generating document.

## Phase 5 — Generate submission document

**Submission ID format:** `TS-{PERIOD}-{TEAM}-{RANDOM}`  
Example: `TS-H1-2026-DATASCIENCE-A7F3`

Generate CONFIDENTIAL markdown document with:
- Header: Submission ID, team, period, submitter, technical owner, date, status Drafted
- Summary table (item count, nil return if applicable)
- Per item: all Q1–Q16 responses in structured sections
- Certification block

Offer to export as Word/docx if user has document generation available.

## Phase 6 — Submission instructions

Tell the user:

1. Save document with Submission ID in filename
2. Upload to: **[UPDATE: SharePoint folder path — confirm with Document Control]**
3. Mark CONFIDENTIAL
4. Notify technical owner for accuracy review
5. Review path: Drafted → Technical review → IP review → Approved

## How users start this skill

User invokes: `/trade-secret-intake` or says "Start the GSTS trade secret intake interview."

Begin immediately with Phase 1, Question 1.
