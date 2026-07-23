# GSTS Portfolio Report — GitLab CI handoff

Use Casey’s project (no new project needed):

**https://gitlab.com/gsts.ca/ociana/ociana-planning**

## Files in this folder to copy into that GitLab repo

| File | Purpose |
|------|---------|
| `.gitlab-ci.yml` | Weekly / manual pipeline |
| `GITLAB_SETUP.md` | Click-by-click setup |
| `requirements.txt` | Python deps (also installed in CI) |
| `inputs/.gitkeep` | Creates `inputs/` folder |
| `script_env_header.py` | Env var block to paste at top of your scripts |

You still upload from your laptop:

- `report_final_v3.py` (Excel + PPTX script)
- `report_html.py` (HTML dashboard — rename from `Report.py`)
- Excel inputs under `inputs/`

See **GITLAB_SETUP.md** for variables, schedule, and the one-line GitLab bug fix.
