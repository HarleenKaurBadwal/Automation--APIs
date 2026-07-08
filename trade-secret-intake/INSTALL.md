# Installing the GSTS Trade Secret Intake Skill

## What changes from CLAUDE.md?

| CLAUDE.md | Claude Skill |
|-----------|--------------|
| Email file each period | Install once per user (or org-wide) |
| Attach file every session | Type `/trade-secret-intake` |
| Same interview logic | Same interview logic |
| SharePoint upload still required | SharePoint upload still required |

---

## Option A — Claude.ai (each user, ~2 min)

1. Open **Claude.ai** → **Settings** → **Capabilities** → **Skills**
2. Click **Add custom skill** / **Upload**
3. Upload the `trade-secret-intake` folder (zip it first)
4. Start any session → type `/trade-secret-intake`

---

## Option B — Claude Code (developers)

```bash
# Personal (all your sessions)
cp -r trade-secret-intake ~/.claude/skills/

# Or project-level (this repo only)
mkdir -p .claude/skills
cp -r trade-secret-intake .claude/skills/
```

Then run `/trade-secret-intake` in Claude Code.

---

## Option C — Organization-wide (ask IT / Claude admin)

For **Claude Team or Enterprise**:

1. IT/admin uploads skill to the **organization workspace** (if available)
2. Or distribute zip via SharePoint + one-page install instructions
3. Kickoff email links to install guide instead of attaching CLAUDE.md

**Claude API (workspace skill):** IT uploads via Skills API — all API users in workspace can use it.

---

## Zip for distribution

```bash
cd /path/to/repo
zip -r trade-secret-intake.zip trade-secret-intake/
```

Email `trade-secret-intake.zip` + link to this INSTALL.md.

---

## Kickoff email (once skill is org-wide)

> Install the GSTS Trade Secret Intake skill (see attached zip / IT portal).
> Each quarter, open Claude and run `/trade-secret-intake`.
> Upload your completed document to [SharePoint link] by [deadline].

Power Automate can still send this email on a schedule.
