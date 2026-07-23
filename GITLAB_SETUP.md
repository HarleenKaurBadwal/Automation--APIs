# GitLab setup — ociana-planning (Casey)

Use this project (do **not** create a new GitLab project unless Casey says so):

https://gitlab.com/gsts.ca/ociana/ociana-planning

Casey gave you **Developer** access. That is enough to add files, run pipelines, and create schedules.

---

## What to click in GitLab

| Goal | Where |
|------|--------|
| Add / edit files | **Code** → repository → **+** → Upload file / New file / Web IDE |
| CI/CD variables (API keys) | **Settings** (gear) → **CI/CD** → **Variables** → Expand → Add |
| Run pipeline manually | **Build** (rocket) → **Pipelines** → **Run pipeline** |
| Schedule weekly run | **Build** → **Pipeline schedules** → **New schedule** |

---

## Files to create / upload (repo root)

| File | Action |
|------|--------|
| `.gitlab-ci.yml` | **Create** — use the file from this handoff |
| `report_final_v3.py` | **Upload** — your Excel + PowerPoint script (paste from your laptop) |
| `report_html.py` | **Upload** — your HTML dashboard script (`Report.py` renamed) |
| `requirements.txt` | **Create** — optional; CI installs packages in `before_script` |
| `inputs/qbo_actuals.xlsx` | **Upload** — latest QBO export (rename to this name) |
| `inputs/prism_allocation.xlsx` | **Upload** — Prism allocation (if used) |
| `inputs/GSTS_Contractor_Hours_by_Project.xlsx` | **Upload** — contractor hours |
| `inputs/.gitkeep` | **Create** — empty file so `inputs/` exists if Excels are not committed yet |
| `GITLAB_SETUP.md` | Optional — this guide |

Do **not** commit real API keys in any file. Use CI/CD Variables only.

---

## CI/CD Variables (Settings → CI/CD → Variables)

Add these (Mask = Yes, Protect = only if you use protected branches):

| Key | Example / notes |
|-----|-----------------|
| `AHA_API_KEY` | Your Aha token |
| `AHA_SUBDOMAIN` | `ociana` |
| `ANTHROPIC_API_KEY` | Claude key |
| `GITLAB_TOKEN` | Personal/project token that can read `gsts.ca/ociana` issues |

In `report_final_v3.py`, the top must read:

```python
AHA_API_KEY = os.environ["AHA_API_KEY"]
AHA_SUBDOMAIN = os.environ.get("AHA_SUBDOMAIN", "ociana")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN") or os.environ.get("GL_API_TOKEN", "")
```

---

## Schedule (Build → Pipeline schedules → New schedule)

- **Description:** Weekly GSTS Portfolio Report  
- **Interval pattern (cron):** `30 11 * * 1`  
  (Monday 11:30 UTC ≈ 7:30am Atlantic/Eastern depending on DST)  
- **Target branch:** `main`  
- **Active:** checked  
- Save  

Also allow **manual** runs: Build → Pipelines → Run pipeline.

---

## After a successful pipeline

1. Open the pipeline → **generate_reports** job → **Browse** / **Download** artifacts  
2. You get:
   - `GSTS_LoE_Dashboard.html`
   - `GSTS_Portfolio_Report.xlsx`
   - `GSTS_Portfolio_Slides.pptx`

**Website:** Artifacts are **not** automatically on https://reports.gsts.ca.  
To publish HTML to the Azure site, either:

- Keep publishing manually / via Phil’s Azure path, or  
- Later add a deploy job with `SWA_DEPLOYMENT_TOKEN` (ask Phil — don’t bypass IT)

---

## Input Excels every month

Someone must refresh files under `inputs/` before the schedule (or the job will fail / show 0 actuals):

1. Download latest QBO + contractor (+ Prism) files  
2. Upload/replace under `inputs/` with the exact names above  
3. Commit to `main`  

Longer term: Phil can point the job at Blob/SharePoint so nobody emails files to you.

---

## Fix one bug in report_final_v3.py before first run

In `get_gitlab_issues_by_labels`, change:

```python
issue["portfolio_project"] = proj_name
```

to:

```python
issue["portfolio_project"] = project_name
```

(`project_name` is the function argument; `proj_name` is wrong and will crash.)

---

## Reply to Casey (optional)

> Thanks! I’ll use ociana-planning as you suggested (no new project). I’ll add the report scripts + `.gitlab-ci.yml` and set a Monday schedule. Outputs will be pipeline artifacts; Azure reports.gsts.ca stays the public host unless Phil adds an automated publish step.
