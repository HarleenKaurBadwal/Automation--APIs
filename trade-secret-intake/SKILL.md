---
name: trade-secret-intake
description: Use when a GSTS team member needs to complete the Trade Secret and IP intake interview for a reporting period. Conducts the full guided intake (metadata, period screening, codebase-up-front option, 16 standard questions per IP item), maintains a resumable YAML working file, generates CONFIDENTIAL .yaml + .md submission documents with deterministic Submission ID (TS-PERIOD-TEAM-YYYYMMDD), and instructs the user which files to upload. Use for trade secret intake, IP disclosure, GSTS IP submission, or /trade-secret-intake.
disable-model-invocation: true
---

# GSTS Trade Secret & IP Intake Skill v1.1

Follow `CLAUDE.md` in this skill folder if present; otherwise follow these instructions exactly.

## Security

- No source code in output. Links and high-level summaries only.
- **Public/unapproved AI** = not allowed for sensitive logic.
- **Approved GSTS AI** (this intake, private repo code-assist) = acceptable.
- Mark output CONFIDENTIAL. Not a legal determination.

## Working file (resumable)

- Maintain `TS-{PERIOD}-{TEAM}-{YYYYMMDD}.yaml` incrementally as answers are confirmed.
- On start: check for existing working file → resume if found.
- YAML = source of truth. Markdown generated from YAML at end.

## Flow

1. **Phase 1:** submitter name/role/email, team, reporting period, technical owner
2. **Phase 2:** any IP/trade secret this period? (yes/no/not sure)
3. **Phase 3 per item:**
   - **Up front:** offer codebase/repo path → review → draft answers → user approves
   - Q1–Q16 (confirm drafts or ask one at a time)
   - Q9: optional git contributor cross-check if repo provided
   - Write each answer to YAML immediately
   - More items? loop
4. **Phase 4:** quality checklist (all 16 per item)
5. **Phase 5:** generate files:
   - ID: `TS-{PERIOD}-{TEAM}-{YYYYMMDD}` (same-day collision: append `-02`, `-03`)
   - Output: `.yaml` + `.md` (and `.docx` if available)
6. **Phase 6:** tell user which files to upload where

## Submission ID

`TS-Q1-2026-DATASCIENCE-20260708` — no random chars. Date = generation date, not period.

## Q16 AI-use default

"No disclosure to public/unapproved AI tools. Approved, access-controlled AI use is acceptable; approved-tool use with sensitive material requires review."

## Phase 6 upload message

Tell user to upload **both**:
- `TS-...-.yaml` (required for aggregation)
- `TS-...-.md` (human review)
To: **[UPDATE: SharePoint path]**

## Start

User invokes `/trade-secret-intake`. Begin Phase 1, Question 1. Check for resumable YAML first.
