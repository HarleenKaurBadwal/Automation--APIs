# GSTS HTML Reports — Beginner Runbook

**Who this is for:** Anyone who needs to regenerate and publish the live reports at  
**https://reports.gsts.ca** — no coding background required.

**What this covers:** The HTML reports on Azure (Portfolio dashboard, Scenario Planner, Roadmap Goals, Milestones, FTE Demand, etc.).

**What this does *not* cover:** The Excel / PowerPoint GitLab pipeline (that’s a separate process).

**Folder on the Mac:** `~/Documents/gsts_report_publish`

**Live site:** https://reports.gsts.ca (sign in with your `@gsts.ca` account)

---

## Regular workflow — generate everything and publish

### Step 1: Open Terminal

On a Mac: press **Cmd + Space**, type `Terminal`, press **Enter**.  
A window with a blinking cursor opens — that’s where you type commands.

---

### Step 2: Go to the project folder

```bash
cd ~/Documents/gsts_report_publish
```

Press **Enter**.  
(`cd` = “change directory” — same idea as opening a folder in Finder, but typed.)

---

### Step 3: Check you’re in the right place

```bash
ls
```

Press **Enter**.  
(`ls` = “list” — shows files in this folder.)

You should see files like:

- `Report.py`
- `ScenarioPlanner.py`
- `RoadmapGoals.py`
- `publish_reports.py`
- various `.html` files

If you see `No such file or directory`, you’re in the wrong place — confirm the folder exists, or ask Phil/IT where it lives on this machine.

---

### Step 4: Set API keys for this session

Paste these one line at a time (use the real keys from Phil/IT — never commit keys into files):

```bash
export AHA_API_KEY=your-real-aha-key
export AHA_SUBDOMAIN=global-spatial-technology-solutions-inc
export ANTHROPIC_API_KEY=your-real-anthropic-key
```

You need to do this **every time you open a new Terminal window**.  
It does not save automatically between sessions (a `.env` file is optional later).

Also restore Azure / Node tools if needed (common on this Mac):

```bash
export PATH="$(python3 -m site --user-base)/bin:$PATH"
export PATH="$HOME/nodejs/bin:$PATH"
```

And Azure publish env (if `publish_reports.py` uses Key Vault):

```bash
export KEY_VAULT_URL="https://kv-html-reports.vault.azure.net/"
export SECRET_NAME="swa-deployment-token"
```

Confirm Azure login if publish fails:

```bash
az account show
```

If that errors: `az login` → pick the GSTS subscription.

---

### Step 5: Update the Excel input files first

Before generating, put the latest files in the **same folder**:

| File | Source |
|------|--------|
| QBO actuals Excel | Emailed each cycle — save into this folder (overwrite old) |
| Contractor hours Excel | Emailed each cycle — save into this folder (overwrite old) |

There is **no automatic pull** for these yet. If you skip this step, actuals can be wrong or zero.

---

### Step 6: Generate everything and publish (one command)

Copy this **as one line** and press **Enter**:

```bash
python3 Report.py && python3 ScenarioPlanner.py && python3 RoadmapGoals.py && python3 publish_reports.py GSTS_LoE_Dashboard.html FTE_Demand_vs_Capacity.html GSTS_Squad_Scenario_Planner.html GSTS_Roadmap_Goals.html GSTS_Milestone_Report.html
```

**What this does, in order:**

1. `Report.py` — rebuilds the main Portfolio LoE & Actuals dashboard  
2. `ScenarioPlanner.py` — rebuilds the squad scenario planner  
3. `RoadmapGoals.py` — rebuilds the roadmap goals report  
4. `publish_reports.py …` — publishes the listed HTML files live to the website  

**Why `&&` matters:** each next step runs **only if** the previous one succeeded. If step 1 crashes, nothing gets published.

---

### Step 7: Confirm it worked

At the end of the Terminal output you should see something like:

```text
Deployed. Landing page: https://reports.gsts.ca
```

If you see `Traceback` or `Error`, copy the **full** error text and send it to support (or paste it to Claude).

---

### Step 8: Check the live site

1. Open https://reports.gsts.ca  
2. Sign in with `@gsts.ca` if asked  
3. If numbers look old, hard refresh: **Cmd + Shift + R** (Mac) or **Ctrl + Shift + R** (Windows)

---

## Adding a new report later

There are two kinds of reports.

### Type A — Live report (pulls current data from Aha)

Needs a **new Python script**. If you don’t code, ask a developer or use an AI assistant (see “Using AI” below).

### Type B — Fixed snapshot HTML (no auto-update)

Anyone can do this:

1. Get the `.html` file (e.g. from Heather)  
2. Copy it into `gsts_report_publish` (Finder drag-and-drop is fine)  
3. Open `publish_reports.py` in a text editor  
4. Find `REPORT_META` near the top and **add one line** in the same pattern:

```python
REPORT_META = {
    "GSTS_LoE_Dashboard.html": ("Portfolio LoE & Actuals", "Level of effort, budget burn, and RAG status across active projects"),
    "FTE_Demand_vs_Capacity.html": ("Pipeline · FTE Demand vs Capacity", "Scenario planner for pipeline hiring and capacity through Jun 2027"),
    "GSTS_Squad_Scenario_Planner.html": ("Squad Scenario Planner", "Work-package hours by squad across OSC, OSPREY III, and SLSMC, with planning scenarios"),
    "GSTS_Roadmap_Goals.html": ("Roadmap Goals", "Progress by initiative goal, rolled up hours and ETC across projects"),
    "GSTS_Milestone_Report.html": ("Upcoming Milestones", "Active and upcoming milestones by project, with budget and status"),
    "NewReport.html": ("My New Report Title", "A short one-sentence description of what this shows"),
}
```

5. Save the file  
6. Publish, including the new filename at the end:

```bash
python3 publish_reports.py GSTS_LoE_Dashboard.html FTE_Demand_vs_Capacity.html GSTS_Squad_Scenario_Planner.html GSTS_Roadmap_Goals.html GSTS_Milestone_Report.html NewReport.html
```

The landing page will show the new title instead of a raw filename.

---

## Using AI to add a live report (Type A)

1. **Give context** — share this document plus a similar working script (`Report.py`, `ScenarioPlanner.py`, or `RoadmapGoals.py`).  
2. **Describe in plain English** what the report should show; attach a screenshot/example if you have one.  
3. **Ask the AI to verify with real data** before trusting output (debug prints / a small test). Silent “0 hours everywhere” bugs have happened before when assumptions didn’t match Aha.  
4. **Save → run locally → check HTML → then add to `REPORT_META` and publish.**  
5. When something breaks, paste the **exact** Terminal error — don’t paraphrase.

---

## Current reports on the site (typical set)

| File | Purpose |
|------|---------|
| `GSTS_LoE_Dashboard.html` | Portfolio LoE, actuals, burn, RAG |
| `FTE_Demand_vs_Capacity.html` | Pipeline FTE demand vs capacity |
| `GSTS_Squad_Scenario_Planner.html` | Squad scenario planner |
| `GSTS_Roadmap_Goals.html` | Roadmap goals / initiative progress |
| `GSTS_Milestone_Report.html` | Upcoming milestones |

---

## Who to ask when stuck

| Problem | Who |
|---------|-----|
| API keys / Azure Key Vault / site access | Phil / IT |
| Wrong LoE, RAG rules, report content | Heather |
| QBO / contractor Excel each cycle | Whoever emails the files (finance/manager) |
| Script errors | Paste full Terminal error to support or Claude |

---

## Quick checklist (each cycle)

- [ ] Latest QBO + contractor Excels saved into `gsts_report_publish`  
- [ ] Terminal opened; `cd ~/Documents/gsts_report_publish`  
- [ ] API keys exported for this session  
- [ ] Generate + publish command finished with “Deployed…”  
- [ ] https://reports.gsts.ca checked (hard refresh if needed)  

---

*Last updated: July 2026 · Maintainer handoff document for HTML reports on reports.gsts.ca*
