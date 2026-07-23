# COMPLETE STEPS — Schedule GSTS report in GitLab
# Project: https://gitlab.com/gsts.ca/ociana/ociana-planning
# Do NOT create a new project. Use Casey's repo only.

---

## PART A — Files you must put in the repo

| # | Filename | Where it comes from |
|---|----------|---------------------|
| 1 | `.gitlab-ci.yml` | Copy from this handoff (full text below / in repo) |
| 2 | `report_html.py` | Your HTML dashboard script (Report.py renamed) |
| 3 | `rag_framework.py` | Required helper for report_html.py |
| 4 | `report_final_v3.py` | Your Excel + PowerPoint script from your laptop |
| 5 | `requirements.txt` | Optional (CI also pip-installs inline) |
| 6 | `inputs/qbo_actuals.xlsx` | Your latest QBO Excel (rename to this) |
| 7 | `inputs/prism_allocation.xlsx` | Prism allocation file |
| 8 | `inputs/GSTS_Contractor_Hours_by_Project.xlsx` | Contractor hours file |

**Never commit API keys in any file.**

---

## PART B — Open the correct project

1. Open: https://gitlab.com/gsts.ca/ociana/ociana-planning
2. Confirm you see **OCIANA Planning** and `README.md`
3. Stay on branch **main**

---

## PART C — Create `.gitlab-ci.yml`

1. On the project page, find the **small +** next to `main` / `ociana-planning` (NOT the top-bar +)
2. Click **New file**
3. File name: `.gitlab-ci.yml`
4. Paste the full contents of `.gitlab-ci.yml` from this handoff
5. Scroll down → **Commit message:** `Add CI pipeline for portfolio reports`
6. Target branch: **main**
7. Click **Commit changes**

---

## PART D — Create `rag_framework.py`

1. Small **+** → **New file**
2. Name: `rag_framework.py`
3. Paste full contents of `rag_framework.py`
4. Commit to **main**

---

## PART E — Create `report_html.py`

1. Small **+** → **New file** (or Upload file)
2. Name: `report_html.py`
3. Paste / upload your HTML script
4. At the top, make sure it uses env vars (not hardcoded keys):

```python
import os
AHA_API_KEY = os.environ.get("AHA_API_KEY", "")
AHA_SUBDOMAIN = os.environ.get("AHA_SUBDOMAIN", "ociana")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
QBO_FILE = os.environ.get("QBO_FILE", "inputs/qbo_actuals.xlsx")
CONTRACTOR_FILE = os.environ.get("CONTRACTOR_FILE", "inputs/GSTS_Contractor_Hours_by_Project.xlsx")
OUTPUT_HTML = os.environ.get("OUTPUT_HTML", "GSTS_LoE_Dashboard.html")
```

5. Commit to **main**

---

## PART F — Upload `report_final_v3.py`

1. Small **+** → **Upload file**
2. Choose your Excel/PPTX script from your Mac
3. Target filename must be exactly: `report_final_v3.py`
4. Commit to **main**

### Required fixes in that script (edit in GitLab after upload)

**Fix 1 — env vars at top** (replace hardcoded keys):

```python
import os
from datetime import datetime, timedelta

AHA_API_KEY = os.environ["AHA_API_KEY"]
AHA_SUBDOMAIN = os.environ.get("AHA_SUBDOMAIN", "ociana")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN") or os.environ.get("GL_API_TOKEN", "")

QBO_FILE = os.environ.get("QBO_FILE", "inputs/qbo_actuals.xlsx")
ALLOC_FILE = os.environ.get("ALLOC_FILE", "inputs/prism_allocation.xlsx")
CONTRACTOR_FILE = os.environ.get("CONTRACTOR_FILE", "inputs/GSTS_Contractor_Hours_by_Project.xlsx")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "GSTS_Portfolio_Report.xlsx")
```

**Fix 2 — bug in `get_gitlab_issues_by_labels`:**

Find:
```python
issue["portfolio_project"] = proj_name
```

Change to:
```python
issue["portfolio_project"] = project_name
```

---

## PART G — Create `inputs` folder + upload Excels

1. Small **+** → **New directory**
2. Directory name: `inputs`
3. You can add a dummy file `inputs/.gitkeep` first, commit
4. Then small **+** → **Upload file**
5. Upload and set paths:
   - `inputs/qbo_actuals.xlsx`
   - `inputs/prism_allocation.xlsx`
   - `inputs/GSTS_Contractor_Hours_by_Project.xlsx`
6. Commit each upload to **main**

---

## PART H — Add CI/CD Variables (secrets)

1. Left sidebar → **Settings** (gear)
2. **CI/CD**
3. Expand **Variables**
4. Click **Add variable** for each:

| Key | Value | Masked | Protected |
|-----|--------|--------|-----------|
| `AHA_API_KEY` | your Aha key | Yes | No (unless only protected branches) |
| `AHA_SUBDOMAIN` | `ociana` | No | No |
| `ANTHROPIC_API_KEY` | your Claude key | Yes | No |
| `GITLAB_TOKEN` | token that can read ociana issues | Yes | No |

5. Save each one

---

## PART I — Run once manually (test)

1. Left sidebar → **Build** (rocket)
2. **Pipelines**
3. **Run pipeline**
4. Branch: **main**
5. Click **Run pipeline**
6. Open the pipeline → click job **generate_reports**
7. Wait for green check
8. On the job page → **Browse** / **Download** artifacts:
   - `GSTS_LoE_Dashboard.html`
   - `GSTS_Portfolio_Report.xlsx`
   - `GSTS_Portfolio_Slides.pptx`

If it fails, open the job log (red X) and fix the error shown (usually missing input file or API key).

---

## PART J — Schedule every Monday

1. **Build** → **Pipeline schedules**
2. **New schedule**
3. Fill in:
   - Description: `Weekly GSTS Portfolio Report`
   - Interval pattern: `30 11 * * 1`
   - Cron timezone: UTC (11:30 UTC ≈ morning Atlantic/Eastern)
   - Target branch: `main`
   - Active: **checked**
4. **Save pipeline schedule**

---

## PART K — What this does NOT do

- Does **not** auto-publish to https://reports.gsts.ca
- Artifacts stay in GitLab for download (8 weeks)
- Azure site still needs Phil’s publish path (or a later deploy job with SWA token)

---

## Checklist

- [ ] Using ociana-planning (no new project)
- [ ] `.gitlab-ci.yml` committed
- [ ] `report_html.py` + `rag_framework.py` committed
- [ ] `report_final_v3.py` uploaded + 2 fixes applied
- [ ] `inputs/*.xlsx` uploaded
- [ ] CI variables set
- [ ] Manual pipeline succeeded
- [ ] Monday schedule saved
