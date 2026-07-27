---
name: trade-secret-intake
description: FINAL deployment release (July 2026). Use when a GSTS team member needs to complete the Trade Secret and IP intake interview for a reporting period. Conducts the full guided intake (metadata, period screening, codebase-up-front option, 16 standard questions per IP item plus category), maintains a resumable YAML working file, generates CONFIDENTIAL .yaml + .md submission documents with deterministic Submission ID (TS-PERIOD-TEAM-YYYYMMDD). Use for trade secret intake, IP disclosure, GSTS IP submission, or /trade-secret-intake.
disable-model-invocation: true
---

# GSTS Trade Secret & IP Intake Skill v1.0 — FINAL deployment release

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

## Interview conduct

- **One item at a time, one question at a time** — say this upfront; never dump all drafts at once
- **Warm-up:** 20–40 min per item; bi-monthly deadline; explain technical owner + handover
- **Draft-then-confirm:** if codebase/diagrams provided → draft Q1–Q16 internally → show **one draft at a time** for confirm/adjust
- **Edits:** user can always edit answers; update YAML only during interview; generate `.md` **once at end** — do not keep rewriting doc mid-interview
- **Inputs:** codebase, links, images, draw.io diagrams (links in output; no sensitive embeds unless user requests)

## Technical owner

Person who explains the asset and reviews draft for accuracy. Support **handover**: someone completing on behalf of owner → record `completion_mode: handover`.

## Trade secret examples (when user is unsure)

Model logic, feature engineering, data fusion pipelines, architecture/deployment, evaluation methods, operational workflows, technical diagrams.

## Flow

1. **Opening:** warm-up + timeline + conduct rules
2. **Phase 1:** submitter, team, period, completion mode, technical owner
2. **Phase 2:** any IP/trade secret this period? (yes/no/not sure)
3. **Phase 3 per item:**
   - **Up front:** codebase/docs/diagrams → draft answers → **one question at a time** confirm/adjust
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

## Q1b Category (ask after title)

> "Which category best describes this trade secret?"

Options: Risk (defence and security) | Supply chain and logistics | Predictive maintenance | Data engineering | Something else

Record: `trade_secret_category` (+ `trade_secret_category_other` if Other)

## Q16 AI-use default

"No disclosure to public/unapproved AI tools. Approved, access-controlled AI use is acceptable; approved-tool use with sensitive material requires review."

## Phase 6 upload message

Tell user to upload **both**:
- `TS-...-.yaml` (required for aggregation)
- `TS-...-.md` (human review)
To: **[UPDATE: SharePoint path]**

## Start

User invokes `/trade-secret-intake`. Begin Phase 1, Question 1. Check for resumable YAML first.
