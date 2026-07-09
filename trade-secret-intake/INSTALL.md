# Installing the GSTS Trade Secret Intake Skill

## CLAUDE.md vs Skill — what's the difference?

| | `CLAUDE.md` | **Claude Skill** (`SKILL.md`) |
|---|-------------|-------------------------------|
| What it is | Full interview guide (reference doc) | Packaged instructions Claude loads as a capability |
| How users run it | Attach file every session + prompt | Type `/trade-secret-intake` once installed |
| Upload to Claude | Attach to chat or add to Project | Upload **skill folder** (zip) to Skills settings |
| Best for | Editing the full guide, fallback | **Org-wide rollout on GSTS Claude server** |

**You do NOT upload `CLAUDE.md` as the Skill.**  
You upload the **`trade-secret-intake/` folder** (which contains `SKILL.md` + `CLAUDE.md` as reference).

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

## Option C — GSTS Claude server (org-wide — preferred)

Ask IT / Claude admin to deploy `trade-secret-intake.zip` to the **organization workspace**.

After deployment, every licensed user can type in chat:

```
/trade-secret-intake
```

No need to attach `CLAUDE.md` each time.

**To update the skill:** edit `CLAUDE.md` / `SKILL.md` → re-zip → IT re-uploads new version.

---

## Option D — Claude API (workspace skill)

IT uploads via Anthropic Skills API (`POST /v1/skills`) with the zip bundle.  
All API users in the workspace reference `skill_id` in requests.

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
