# Paste these near the TOP of report_final_v3.py and report_html.py
# (replace any hardcoded API keys)

import os
from datetime import datetime, timedelta

AHA_API_KEY = os.environ["AHA_API_KEY"]
AHA_SUBDOMAIN = os.environ.get("AHA_SUBDOMAIN", "ociana")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN") or os.environ.get("GL_API_TOKEN", "")

QBO_FILE = os.environ.get("QBO_FILE", "inputs/qbo_actuals.xlsx")
ALLOC_FILE = os.environ.get("ALLOC_FILE", "inputs/prism_allocation.xlsx")
CONTRACTOR_FILE = os.environ.get(
    "CONTRACTOR_FILE", "inputs/GSTS_Contractor_Hours_by_Project.xlsx"
)
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "GSTS_Portfolio_Report.xlsx")
OUTPUT_HTML = os.environ.get("OUTPUT_HTML", "GSTS_LoE_Dashboard.html")
