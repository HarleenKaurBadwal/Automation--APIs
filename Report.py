#!/usr/bin/env python3
"""GSTS Portfolio LoE & Actuals Dashboard Generator.

Updates (Jul 2026 — Heather RAG framework v1.0):
  - OSC AI project LoE override: 26,750h (rebaseline 14 Jul 2026)
  - % complete: WP = hours-weighted epic mean; project = simple mean of started WPs
  - RAG: Budget/Burn, Schedule, ETC Confidence, Velocity (if available) + combining rule
  - Initiative/epic LoE rows stay live Aha; EAC uses live Aha LoE (not override)
"""

import os
import re
from collections import defaultdict
from datetime import datetime

import requests

from rag_framework import (
    burn_dimension,
    combine_rag,
    etc_dimension,
    project_pct_complete,
    review_from_rag,
    schedule_dimension,
    velocity_dimension,
    wp_pct_from_epics,
)

# ── CONFIG ────────────────────────────────────────────────────────────────────
AHA_API_KEY = os.environ.get("AHA_API_KEY", "")
AHA_SUBDOMAIN = os.environ.get("AHA_SUBDOMAIN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
QBO_FILE = os.environ.get("QBO_FILE", "QBO_Actuals.xlsx")
OUTPUT_HTML = os.environ.get("OUTPUT_HTML", "GSTS_LoE_Dashboard.html")

# Project-level LoE overrides (display / burn denominator only).
# Initiative & epic LoE rows stay live Aha. EAC uses live Aha LoE.
# OSC rebaseline 14 Jul 2026: 18,823h actuals + 7,927h Aha ETC = 26,750h
LOE_OVERRIDE = {
    "OSC AI": 26750,
}

QBO_MAP = {
    "2023 40 OSC AI": "OSC AI",
    "2025 57 OSPREY III": "OSPREY III",
    "2026 64 SLSMC PH II": "SLSMC",
    "SLSMC 4-Year Professional Support Services": "SLSMC",
    "2026 61 HHA Pilot": "HHA Pilot",
    "2026 59 IDP": "IDP",
    "2025 59 IDP": "IDP",
    "IDP 59": "IDP",
    "2026 00 ACOA": "ACOA",
}
PROJECT_CONFIG = {
    "OSC AI": {"code": "Proj 40", "color": "#027890"},
    "OSPREY III": {"code": "Proj 57", "color": "#D97706"},
    "SLSMC": {"code": "Proj 64", "color": "#15803D"},
    "IDP": {"code": "Proj 59", "color": "#7050C8"},
    "ACOA": {"code": "Proj 00", "color": "#EA580C"},
}
PROJ_ORDER = ["OSC AI", "OSPREY III", "SLSMC", "IDP", "ACOA"]


# ── AHA HELPERS ───────────────────────────────────────────────────────────────
def aha_get(endpoint, params=None):
    params = params or {}
    url = f"https://{AHA_SUBDOMAIN}.aha.io/api/v1/{endpoint}"
    h = {
        "Authorization": f"Bearer {AHA_API_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.get(url, headers=h, params=params, timeout=30)
    return r.json() if r.status_code == 200 else {}


def initiative_to_project(name):
    n = (name or "").upper()
    if n.startswith("OSC"):
        return "OSC AI"
    if n.startswith("IDP"):
        return "IDP"
    if n.startswith("ACOA"):
        return "ACOA"
    if n.startswith("OSPREY"):
        return "OSPREY III"
    if n.startswith("SLSMC"):
        return "SLSMC"
    return None


# Optional: GitLab velocity closure rates by project (0–100). Leave empty → dimension skipped.
VELOCITY_BY_PROJ = {}


def apportion(proj_name, initiatives, actuals_by_proj):
    """Distribute project-level QBO actuals to each initiative by LoE share."""
    total_loe = sum(i["loe"] for i in initiatives) or 1
    proj_act = actuals_by_proj.get(proj_name, 0)
    for i in initiatives:
        i["act"] = round(proj_act * (i["loe"] / total_loe))
        i["bgt"] = round(i["act"] / i["loe"] * 100) if i["loe"] > 0 else 0


def proj_date_range(inits):
    """Earliest start and latest end across initiatives (live from Aha)."""
    starts = [i["start"] for i in inits if i["start"] not in ("—", "None", "")]
    ends = [i["end"] for i in inits if i["end"] not in ("—", "None", "")]
    start = min(starts) if starts else "—"
    end = max(ends) if ends else "—"
    return start, end


def proj_summary(proj_name, inits, actuals_by_proj, contractor_by_proj):
    loe_live = sum(i["loe"] for i in inits)  # EAC / live Aha total
    loe = LOE_OVERRIDE.get(proj_name, loe_live)  # display + burn denominator
    act = round(actuals_by_proj.get(proj_name, 0))
    contractor = round(contractor_by_proj.get(proj_name, 0))
    total_act = act + contractor
    avg_pct = project_pct_complete(inits)
    burn_pct = round(total_act / loe * 100, 1) if loe > 0 else 0
    bgt = round(burn_pct)
    etc_remaining = round(loe_live * (1 - avg_pct / 100)) if loe_live > 0 else 0
    eac = total_act + etc_remaining

    burn_rag, burn_gap = burn_dimension(burn_pct, avg_pct)
    sched_rag = schedule_dimension(inits)
    etc_rag = etc_dimension(
        loe_baseline=loe,
        total_act=total_act,
        etc_remaining=etc_remaining,
        is_internal=(proj_name == "IDP"),
    )
    vel_rag = velocity_dimension(VELOCITY_BY_PROJ.get(proj_name))
    overall = combine_rag([burn_rag, sched_rag, etc_rag, vel_rag])

    return {
        "loe": loe,
        "loe_live": loe_live,
        "act": act,
        "contractor": contractor,
        "total_act": total_act,
        "avg_pct": avg_pct,
        "burn_pct": burn_pct,
        "burn_gap": burn_gap,
        "bgt": bgt,
        "etc_remaining": etc_remaining,
        "eac": eac,
        "rag_burn": burn_rag,
        "rag_schedule": sched_rag,
        "rag_etc": etc_rag,
        "rag_velocity": vel_rag,
        "rag": overall,
        "review": review_from_rag(overall),
    }


def call_claude(prompt):
    try:
        import anthropic

        c = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        m = c.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}],
        )
        return m.content[0].text.strip()
    except Exception as e:
        print(f"  Claude: {e}")
        return None


def status_chip(st):
    m = {
        "In Progress": "s-ip",
        "Complete ✓": "s-rd",
        "Complete": "s-rd",
        "Upcoming": "s-bl",
        "Backlog": "s-bl",
        "On Hold": "s-oh",
        "Planning": "s-pl",
        "Ready to Dev": "s-rd",
        "Ready to Develop": "s-rd",
    }
    cls = next((v for k, v in m.items() if k.lower() in (st or "").lower()), "s-bl")
    label = st[:18] if st else "—"
    return f'<span class="status {cls}">{label}</span>'


def pbar(pct, color="#14B8C8"):
    if pct is None:
        return "—"
    w = min(pct, 100)
    return (
        f'<div class="pbar"><div class="pbar-track">'
        f'<div class="pbar-fill" style="width:{w}%;background:{color}"></div>'
        f'</div><span class="pbar-pct">{pct}%</span></div>'
    )


def fh(v):
    return f"{int(v):,}h" if v else "—"


def rag_badge(label):
    colors = {
        "Red": ("#FEE2E2", "#DC2626"),
        "Amber": ("#FEF3C7", "#D97706"),
        "Green": ("#DCFCE7", "#00B050"),
        "No Data": ("#F1F5F9", "#94A3B8"),
        "—": ("#F1F5F9", "#94A3B8"),
        "HIGH": ("#FEE2E2", "#DC2626"),
        "WATCH": ("#FEF3C7", "#D97706"),
        "OK": ("#DCFCE7", "#00B050"),
    }
    bg, fg = colors.get(label, ("#F1F5F9", "#94A3B8"))
    return (
        f'<span style="background:{bg};color:{fg};padding:3px 12px;'
        f'border-radius:12px;font-size:11px;font-weight:700">{label}</span>'
    )


def initiative_rows(inits, proj_color):
    rows = []
    for it in inits:
        rows.append(
            f"""
      <tr class="initiative">
        <td title="{it['name']}">{it['name'][:62]+('…' if len(it['name'])>62 else '')}</td>
        <td class="ctr">{status_chip(it['status'])}</td>
        <td class="ctr dt">{it['start']}</td>
        <td class="ctr dt">{it['end']}</td>
        <td class="num">{fh(it['loe'])}</td>
        <td class="num">{fh(it['act'])}</td>
        <td style="min-width:90px">{pbar(it['pct'], proj_color)}</td>
      </tr>"""
        )
        for ep in it["epics"][:10]:
            rows.append(
                f"""
      <tr class="epic">
        <td style="padding-left:28px" title="{ep['name']}">↳ {ep['name'][:60]+('…' if len(ep['name'])>60 else '')}</td>
        <td class="ctr">{status_chip(ep['status'])}</td>
        <td class="ctr dt">{ep['start']}</td>
        <td class="ctr dt">{ep['end']}</td>
        <td class="num" style="color:#CBD5E1">{fh(ep['loe'])}</td>
        <td class="ctr" colspan="2" style="color:#CBD5E1;font-size:10px">apportioned above</td>
      </tr>"""
            )
    return "\n".join(rows)


def proj_section(proj, inits, s):
    cfg = PROJECT_CONFIG.get(proj, {"code": "", "color": "#64748B"})
    color = cfg["color"]
    start, end = proj_date_range(inits)

    return f"""
  <div class="proj-section" data-proj="{proj}">
    <div class="proj-header" style="background:{color}" onclick="toggleSection(this)">
      <h2>{proj}&nbsp;<span style="font-weight:400;font-size:12px;opacity:.8">{cfg['code']} · {start} – {end}</span></h2>
      <div class="proj-stats">
        <span>LoE <strong>{s['loe']:,}h</strong></span>
        <span>Actuals <strong>{s['act']:,}h</strong></span>
        <span>Burn <strong>{s['bgt']}%</strong></span>
        <span>% Complete <strong>{s['avg_pct']}%</strong></span>
        <span>EAC <strong>{s['eac']:,}h</strong></span>
        <span>RAG <strong>{s['rag']}</strong></span>
      </div>
      <span class="chevron">▼</span>
    </div>

    <table class="init-table">
      <thead><tr>
        <th style="width:36%;text-align:left">Initiative / Epic</th>
        <th>Status</th><th>Start</th><th>End</th>
        <th class="num">LoE</th>
        <th class="num">Actuals (apportioned)</th>
        <th>WP % Complete</th>
      </tr></thead>
      <tbody>{initiative_rows(inits, color)}</tbody>
    </table>
  </div>"""


def main():
    # ── PULL DATA ─────────────────────────────────────────────────────────────
    print("Fetching Aha initiatives...")
    all_inits, page = [], 1
    while True:
        d = aha_get("initiatives", {"per_page": 100, "page": page})
        batch = d.get("initiatives", [])
        if not batch:
            break
        all_inits.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    print(f"  {len(all_inits)} initiatives")

    print("Fetching Aha epics...")
    all_epics, page = [], 1
    while True:
        d = aha_get(
            "epics",
            {
                "per_page": 200,
                "page": page,
                "fields": "name,workflow_status,progress,original_estimate,initiative,release,start_date,end_date",
            },
        )
        batch = d.get("epics", [])
        if not batch:
            break
        all_epics.extend(batch)
        print(f"  Page {page}: {len(batch)}")
        if len(batch) < 200:
            break
        page += 1
    print(f"  {len(all_epics)} epics")

    print("Loading QBO actuals...")
    actuals_by_proj = {}
    try:
        import pandas as pd

        qbo = pd.read_excel(QBO_FILE)
        if "hours" not in qbo.columns:
            qbo = pd.read_excel(QBO_FILE, header=1)
        for col in ["tasks", "employee", "billable", "notes"]:
            if col not in qbo.columns:
                qbo[col] = ""
        qbo["hours"] = pd.to_numeric(qbo["hours"], errors="coerce").fillna(0)
        qbo["project_clean"] = qbo["jobcode_2"].map(QBO_MAP).fillna("Other")
        actuals_by_proj = qbo.groupby("project_clean")["hours"].sum().to_dict()
        print(
            f"  {len(qbo)} rows | projects: {[k for k, v in actuals_by_proj.items() if v > 0]}"
        )
        for proj in ["OSC AI", "OSPREY III", "SLSMC", "IDP"]:
            if actuals_by_proj.get(proj, 0) == 0:
                print(f"  ⚠️  {proj} has 0 actuals — check job code mapping")
    except Exception as e:
        print(f"  QBO load failed ({e}) — actuals will be 0")

    print("Loading contractor hours...")
    contractor_by_proj = {}
    try:
        import pandas as pd

        ct = pd.read_excel(
            "GSTS_Contractor_Hours_by_Project.xlsx",
            sheet_name="Monthly Detail",
            header=2,
        )
        ct.columns = [str(c).strip() for c in ct.columns]
        ct["PROJECT"] = ct["PROJECT"].ffill()
        proj_map = {
            "OSC AI": "OSC AI",
            "OSPREY": "OSPREY III",
            "OSPREY III": "OSPREY III",
            "IDP": "IDP",
            "SLSMC": "SLSMC",
            "ACOA": "ACOA",
        }
        ct["proj_clean"] = ct["PROJECT"].map(proj_map)
        month_cols = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        for col in month_cols:
            if col in ct.columns:
                ct[col] = pd.to_numeric(ct[col], errors="coerce").fillna(0)
        ct["total"] = ct[[c for c in month_cols if c in ct.columns]].sum(axis=1)
        contractor_by_proj = ct.groupby("proj_clean")["total"].sum().to_dict()
        print(f"  Contractor hours: {contractor_by_proj}")
    except Exception as e:
        print(f"  Contractor load failed ({e})")
        contractor_by_proj = {}

    # ── BUILD INITIATIVE TREE ─────────────────────────────────────────────────
    epics_by_init = defaultdict(list)
    for e in all_epics:
        ref = (e.get("initiative") or {}).get("reference_num", "")
        if ref:
            epics_by_init[ref].append(e)

    projects_data = defaultdict(list)
    for it in all_inits:
        proj = initiative_to_project(it.get("name", ""))
        if not proj:
            continue
        loe = round((it.get("initial_estimate") or 0) / 60)
        start = str(it.get("start_date") or "—")[:10]
        end = str(it.get("end_date") or "—")[:10]
        ref = it.get("reference_num", "")

        epics = []
        for e in epics_by_init.get(ref, []):
            epics.append(
                {
                    "name": (e.get("name", "")[:70]),
                    "status": (e.get("workflow_status") or {}).get("name", "—"),
                    "start": str(e.get("start_date") or "—")[:10],
                    "end": str(e.get("end_date") or "—")[:10],
                    "loe": round((e.get("original_estimate") or {}).get("value", 0) or 0),
                    "pct": round(e.get("progress") or 0),
                }
            )
        epics.sort(key=lambda x: (-x["pct"], x["name"]))

        pct = wp_pct_from_epics(epics)
        if not epics:
            pct = round(it.get("progress") or 0)

        status = (
            "Complete ✓"
            if pct >= 100
            else ("In Progress" if pct > 0 else "Upcoming")
        )

        projects_data[proj].append(
            {
                "name": it.get("name", "")[:70],
                "status": status,
                "start": start,
                "end": end,
                "loe": loe,
                "pct": pct,
                "epics": epics,
            }
        )

    print("\n--- OSC AI initiative dates (debug) ---")
    for it in projects_data.get("OSC AI", []):
        print(
            f"{it['end']}  |  {it['start']}  |  {it['loe']}h  |  {it['pct']}%  |  {it['name']}"
        )

    print("\n--- All initiatives NOT mapped to a project (debug) ---")
    for it in all_inits:
        if initiative_to_project(it.get("name", "")) is None:
            loe_h = round((it.get("initial_estimate") or 0) / 60)
            print(f"{loe_h}h  |  {it.get('name')}")

    for proj, inits in projects_data.items():
        apportion(proj, inits, actuals_by_proj)

    summaries = {
        p: proj_summary(p, projects_data.get(p, []), actuals_by_proj, contractor_by_proj)
        for p in PROJ_ORDER
        if p in projects_data
    }
    port_loe = sum(s["loe"] for s in summaries.values())
    port_act = sum(s["act"] for s in summaries.values())
    port_bgt = round(port_act / port_loe * 100) if port_loe > 0 else 0
    all_pcts = [s["avg_pct"] for s in summaries.values() if s["avg_pct"] > 0]
    port_pct = round(sum(all_pcts) / len(all_pcts)) if all_pcts else 0
    total_inits = sum(len(v) for v in projects_data.values())
    total_epics = sum(sum(len(i["epics"]) for i in v) for v in projects_data.values())

    print("Calling Claude...")
    proj_lines = "\n".join(
        [
            f"- {p}: LoE {s['loe']:,}h | Actuals {s['act']:,}h | Burn {s['burn_pct']}% | "
            f"Aha/WP {s['avg_pct']}% | Burn gap {s['burn_gap']:+.1f}pp | RAG {s['rag']}"
            for p, s in summaries.items()
        ]
    )
    narrative = call_claude(
        f"Write exactly 2 sentences summarising GSTS portfolio health for a stakeholder dashboard. "
        f"Plain English only — no markdown, no asterisks, no bullet points. "
        f"Be specific: name projects and numbers. First sentence: overall status. "
        f"Second sentence: the biggest risk.\n\nData:\n{proj_lines}\n"
        f"Total LoE: {port_loe:,}h | Actuals: {port_act:,}h | Budget spent: {port_bgt}%"
    ) or (
        f"The portfolio has consumed {port_bgt}% of total budget ({port_act:,}h of {port_loe:,}h). "
        f"Review projects with high burn rates for scope alignment."
    )
    narrative = re.sub(r"\*+([^*]+)\*+", r"\1", narrative).strip()

    all_sections = "\n".join(
        [
            proj_section(p, projects_data[p], summaries[p])
            for p in PROJ_ORDER
            if p in projects_data
        ]
    )

    rag_rows = ""
    for p in PROJ_ORDER:
        if p not in summaries:
            continue
        s = summaries[p]
        cfg = PROJECT_CONFIG[p]
        inits_p = projects_data.get(p, [])
        backlog_count = sum(1 for i in inits_p if i["pct"] == 0)
        backlog_pct = round(backlog_count / len(inits_p) * 100) if inits_p else 0
        bl_color = (
            "#6B3939"
            if backlog_pct > 60
            else ("#D97706" if backlog_pct > 30 else "#64748B")
        )

        today_str = datetime.today().strftime("%Y-%m-%d")
        candidates = sorted(
            [
                i
                for i in inits_p
                if i["status"] != "Complete ✓"
                and i["end"] not in ("—", "None", "")
                and i["end"] >= today_str
            ],
            key=lambda x: x["end"],
        )
        next_ms = (
            (candidates[0]["end"] + " · " + candidates[0]["name"][:28])
            if candidates
            else "—"
        )

        vel_label = s["rag_velocity"] if s["rag_velocity"] else "—"
        gap_str = f"{s['burn_gap']:+.1f}pp"

        rag_rows += f"""
      <tr>
        <td><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:{cfg['color']};margin-right:8px;vertical-align:middle"></span><strong>{p}</strong></td>
        <td class="ctr">{cfg['code']}</td>
        <td class="ctr">{proj_date_range(projects_data.get(p, []))[1]}</td>
        <td class="num">{fh(s['loe'])}</td>
        <td class="num">{fh(s['total_act'])}<br><small style="color:#94A3B8;font-size:10px">QBO {fh(s['act'])} · Contractor {fh(s['contractor'])}</small></td>
        <td class="ctr">{s['avg_pct']}%</td>
        <td class="ctr" title="Burn {s['burn_pct']}% − Complete {s['avg_pct']}%">{s['burn_pct']}%<br><small style="color:#94A3B8">{gap_str}</small></td>
        <td class="ctr" style="font-weight:700;color:{bl_color}">{backlog_pct}%</td>
        <td class="ctr" style="font-size:11px;color:#64748B">{next_ms}</td>
        <td class="ctr" style="font-size:10px;line-height:1.6">
          B {rag_badge(s['rag_burn'])}<br>
          S {rag_badge(s['rag_schedule'])}<br>
          E {rag_badge(s['rag_etc'])}<br>
          V {rag_badge(vel_label)}
        </td>
        <td class="ctr">{rag_badge(s['rag'])}</td>
        <td class="ctr">{rag_badge(s['review'])}</td>
      </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>GSTS Portfolio · LoE &amp; Actuals · {datetime.today().strftime('%B %Y')}</title>
<style>
  :root{{--navy:#0F1F3D;--teal:#14B8C8;--white:#fff;--lgray:#F1F5F9;--mgray:#64748B;--dgray:#1E293B}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:Arial,sans-serif;background:var(--lgray);color:var(--dgray);font-size:13px}}

  .page-header{{background:var(--navy);color:var(--white);padding:28px 40px 24px}}
  .page-header h1{{font-size:24px;font-weight:700;margin-bottom:12px}}
  .rag-table tr:last-child td{{border-bottom:none}}
  .rag-table tr:hover td{{background:#F8FAFC}}
  .rag-legend{{width:280px;flex-shrink:0;background:var(--white);border-radius:8px;
    padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,.06);font-size:11px;color:var(--mgray)}}
  .rag-legend-title{{font-size:11px;font-weight:700;color:var(--dgray);margin-bottom:10px;
    text-transform:uppercase;letter-spacing:.4px}}
  .rag-legend-row{{display:flex;align-items:flex-start;gap:8px;margin-bottom:10px;line-height:1.4}}
  .rag-legend-row:last-child{{margin-bottom:0}}
  .rag-dot{{width:9px;height:9px;border-radius:50%;flex-shrink:0;margin-top:3px}}
  .meta-row{{display:flex;gap:28px;flex-wrap:wrap;margin-bottom:16px}}
  .meta-item .lbl{{font-size:10px;color:#94A3B8;text-transform:uppercase;letter-spacing:.5px}}
  .meta-item .val{{font-size:14px;font-weight:600;color:#E2E8F0;margin-top:2px}}
  .narrative-box{{background:rgba(20,184,200,.12);border-left:3px solid var(--teal);
    padding:12px 16px;border-radius:0 6px 6px 0;max-width:900px;
    font-size:12px;color:#CBD5E1;line-height:1.6}}
  .teal{{color:var(--teal)}}

  .content{{max-width:1400px;margin:0 auto;padding:24px 32px}}
  .summary-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:20px}}
  .card{{background:var(--white);border-radius:10px;padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
  .card .clbl{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}}
  .card .cbig{{font-size:26px;font-weight:700;line-height:1}}
  .card .csub{{font-size:11px;color:var(--mgray);margin-top:4px}}
  .card .cbar{{background:#E2E8F0;border-radius:4px;height:5px;margin-top:10px;overflow:hidden}}
  .card .cbar-fill{{height:100%;border-radius:4px}}

  .section-title{{font-size:14px;font-weight:700;color:var(--dgray);margin:24px 0 10px;
    padding-bottom:6px;border-bottom:2px solid #E2E8F0}}
  .rag-table{{width:100%;border-collapse:collapse;background:var(--white);
    border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:28px}}
  .rag-table th{{background:var(--dgray);color:var(--white);padding:9px 12px;
    font-size:10px;font-weight:700;text-align:center;white-space:nowrap}}
  .rag-table th:first-child{{text-align:left}}
  .rag-table td{{padding:10px 12px;border-bottom:1px solid #F1F5F9;vertical-align:middle}}

  .filter-bar{{display:flex;gap:10px;margin-bottom:20px;align-items:center;flex-wrap:wrap}}
  .filter-bar select,.filter-bar input{{padding:7px 12px;border:1px solid #CBD5E1;
    border-radius:6px;font-size:12px;background:var(--white);color:var(--dgray)}}
  .filter-bar label{{font-size:11px;color:var(--mgray);font-weight:600}}
  .btn{{padding:7px 14px;background:var(--navy);color:var(--white);
    border:none;border-radius:6px;font-size:11px;cursor:pointer;font-weight:600}}
  .btn:hover{{background:#1C3566}}
  .btn-gray{{background:#374151}}.btn-gray:hover{{background:#1F2937}}

  .proj-section{{margin-bottom:18px}}
  .proj-header{{display:flex;align-items:center;gap:12px;padding:12px 18px;
    border-radius:8px 8px 0 0;color:var(--white);cursor:pointer;user-select:none}}
  .proj-header h2{{font-size:14px;font-weight:700;flex:1}}
  .proj-header .proj-stats{{display:flex;gap:18px;font-size:11px;opacity:.9}}
  .proj-header .chevron{{font-size:12px;transition:transform .2s}}
  .proj-header.collapsed .chevron{{transform:rotate(-90deg)}}

  .init-table{{width:100%;border-collapse:collapse;background:var(--white);
    border-radius:0 0 8px 8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
  .init-table th{{background:var(--dgray);color:var(--white);padding:8px 12px;
    font-size:10px;font-weight:700;text-align:center;white-space:nowrap}}
  .init-table th:first-child{{text-align:left}}
  .init-table td{{padding:7px 12px;border-bottom:1px solid #F1F5F9;vertical-align:middle}}
  .init-table tr.initiative td{{font-weight:600;background:#FAFBFC}}
  .init-table tr.epic td{{font-size:11px;color:var(--mgray)}}
  .init-table tr:hover td{{background:#F8FAFC}}
  .num{{text-align:right;font-variant-numeric:tabular-nums}}
  .ctr{{text-align:center}}
  .dt{{font-size:10px;color:var(--mgray)}}

  .status{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;white-space:nowrap}}
  .s-ip{{background:#DBEAFE;color:#1D4ED8}}.s-pl{{background:#F3E8FF;color:#7C3AED}}
  .s-bl{{background:var(--lgray);color:var(--mgray)}}.s-rd{{background:#DCFCE7;color:#00B050}}
  .s-oh{{background:#FEE2E2;color:#DC2626}}

  .pbar{{display:flex;align-items:center;gap:6px}}
  .pbar-track{{flex:1;background:#E2E8F0;border-radius:3px;height:6px;overflow:hidden;min-width:60px}}
  .pbar-fill{{height:100%;border-radius:3px}}
  .pbar-pct{{font-size:10px;color:var(--mgray);width:30px;text-align:right}}

  .footer{{background:var(--navy);color:#64748B;font-size:10px;padding:14px 40px;margin-top:32px}}
  @media(max-width:900px){{.summary-grid{{grid-template-columns:repeat(2,1fr)}}.content{{padding:16px}}.proj-header .proj-stats{{display:none}}}}
  @media print{{.filter-bar,.btn{{display:none}}}}
</style>
</head>
<body>

<div class="page-header">
  <h1>GSTS Portfolio <span class="teal">·</span> Squad LoE &amp; Actuals</h1>
  <div class="meta-row">
    <div class="meta-item"><div class="lbl">Report Date</div><div class="val">{datetime.today().strftime('%B %d, %Y')}</div></div>
    <div class="meta-item"><div class="lbl">LoE Source</div><div class="val">Aha! (live) · OSC rebaselined</div></div>
    <div class="meta-item"><div class="lbl">Actuals Period</div><div class="val">Jan – Jun 2026 · QBO</div></div>
    <div class="meta-item"><div class="lbl">Initiatives</div><div class="val">{total_inits}</div></div>
    <div class="meta-item"><div class="lbl">Epics</div><div class="val">{total_epics}</div></div>
    <div class="meta-item"><div class="lbl">Generated</div><div class="val">{datetime.today().strftime('%H:%M')}</div></div>
  </div>
  <div class="narrative-box">💡 {narrative}</div>
  <p style="margin-top:10px;font-size:10px;color:#475569">
    WP % = hours-weighted epic progress in Aha · Project % = simple mean of started work packages ·
    Burn % = Actuals ÷ Project LoE (OSC uses rebaselined 26,750h) · Burn Gap = Burn % − Project % ·
    RAG = Budget/Burn + Schedule + ETC Confidence (+ Velocity when available) ·
    EAC = Actuals + remaining live Aha scope · CONFIDENTIAL — internal use only
  </p>
</div>

<div class="content">

  <div class="summary-grid">
    <div class="card"><div class="clbl teal">Portfolio LoE</div>
      <div class="cbig">{port_loe:,}h</div><div class="csub">Total planned effort</div>
      <div class="cbar"><div class="cbar-fill" style="width:100%;background:var(--teal)"></div></div></div>
    <div class="card"><div class="clbl" style="color:#00B050">Actuals YTD</div>
      <div class="cbig">{port_act:,}h</div><div class="csub">Jan–Jun 2026 (QBO)</div>
      <div class="cbar"><div class="cbar-fill" style="width:{min(port_bgt,100)}%;background:#00B050"></div></div></div>
    <div class="card"><div class="clbl" style="color:#1D4ED8">% Complete</div>
      <div class="cbig">{port_pct}%</div><div class="csub">Simple mean of project WP %</div>
      <div class="cbar"><div class="cbar-fill" style="width:{port_pct}%;background:#1D4ED8"></div></div></div>
    <div class="card"><div class="clbl" style="color:var(--mgray)">Active Projects</div>
      <div class="cbig">{len(summaries)}</div>
      <div class="csub">{' · '.join(p for p in PROJ_ORDER if p in summaries)}</div></div>
    <div class="card" style="border-left:3px solid #7C3AED">
      <div class="clbl" style="color:#7C3AED">Trade Secret Pipeline</div>
      <div class="cbig" style="font-size:16px;margin-top:4px">🔒 In Progress</div>
      <div class="csub" style="margin-top:6px;line-height:1.5">
        Automated IP collection pipeline using Claude AI skills + n8n.
      </div>
    </div>
  </div>

  <div class="section-title">Portfolio RAG Status — Framework v1.0 (Aha &amp; QBO)</div>
  <div style="display:flex;gap:16px;align-items:flex-start;margin-bottom:28px">
    <table class="rag-table" style="flex:1;margin-bottom:0">
      <thead><tr>
        <th style="text-align:left">Project</th>
        <th>Code</th><th>End</th>
        <th class="num">LoE (h)</th>
        <th class="num">Total Actuals (h)</th>
        <th>% Complete</th>
        <th>Burn % / Gap</th>
        <th>Backlog %</th>
        <th>Next Milestone</th>
        <th>Dimensions<br><small>B Burn · S Schedule · E ETC · V Velocity</small></th>
        <th>RAG</th>
        <th>Review</th>
      </tr></thead>
      <tbody>{rag_rows}</tbody>
    </table>
    <div class="rag-legend">
      <div class="rag-legend-title">Combining rule</div>
      <div class="rag-legend-row"><span class="rag-dot" style="background:#DC2626"></span><span><strong>Red</strong> — any dimension Red</span></div>
      <div class="rag-legend-row"><span class="rag-dot" style="background:#D97706"></span><span><strong>Amber</strong> — two or more Amber</span></div>
      <div class="rag-legend-row"><span class="rag-dot" style="background:#00B050"></span><span><strong>Green</strong> — all Green, or only one Amber</span></div>
      <div class="rag-legend-title" style="margin-top:14px">Burn gap (Burn − % Complete)</div>
      <div class="rag-legend-row"><span class="rag-dot" style="background:#00B050"></span><span><strong>Green</strong> — gap ≤ +10pp</span></div>
      <div class="rag-legend-row"><span class="rag-dot" style="background:#D97706"></span><span><strong>Amber</strong> — +11 to +35pp</span></div>
      <div class="rag-legend-row"><span class="rag-dot" style="background:#DC2626"></span><span><strong>Red</strong> — gap &gt; +35pp</span></div>
      <div class="rag-legend-title" style="margin-top:14px">Notes</div>
      <div class="rag-legend-row"><span class="rag-dot" style="background:#64748B"></span><span>OSC LoE = 26,750h rebaseline. Velocity omitted until GitLab rates are wired.</span></div>
    </div>
  </div>

  <div class="section-title">Initiative &amp; Epic Detail</div>
  <div class="filter-bar">
    <label>Project:</label>
    <select id="pf" onchange="filterRows()">
      <option value="">All</option>
      {''.join(f'<option>{p}</option>' for p in PROJ_ORDER if p in projects_data)}
    </select>
    <label>Status:</label>
    <select id="sf" onchange="filterRows()">
      <option value="">All</option>
      <option>In Progress</option>
      <option>Upcoming</option>
      <option>Backlog</option>
      <option>Complete</option>
      <option>On Hold</option>
    </select>
    <label>Search:</label>
    <input id="qf" placeholder="Initiative or epic…" oninput="filterRows()" style="width:200px">
    <button class="btn" onclick="toggleAll()">Expand / Collapse All</button>
    <button class="btn btn-gray" onclick="window.print()">🖨 Print</button>
  </div>

  {all_sections}

</div>

<div class="footer">
  GSTS Portfolio · LoE &amp; Actuals Dashboard ·
  Generated {datetime.today().strftime('%B %d, %Y at %H:%M')} ·
  RAG Framework v1.0 · Source: Aha! (live) + QBO (YTD) · CONFIDENTIAL
</div>

<script>
function toggleSection(h){{
  h.classList.toggle('collapsed');
  const t=h.parentElement.querySelector('table');
  if(t) t.style.display=h.classList.contains('collapsed')?'none':'';
}}
let expanded=true;
function toggleAll(){{
  expanded=!expanded;
  document.querySelectorAll('.proj-header').forEach(h=>{{
    const t=h.parentElement.querySelector('table');
    h.classList.toggle('collapsed',!expanded);
    if(t) t.style.display=expanded?'':'none';
  }});
}}
function filterRows(){{
  const p=document.getElementById('pf').value.toLowerCase();
  const s=document.getElementById('sf').value.toLowerCase();
  const q=document.getElementById('qf').value.toLowerCase();
  document.querySelectorAll('.proj-section').forEach(sec=>{{
    const pm=!p||sec.dataset.proj.toLowerCase().includes(p);
    sec.style.display=pm?'':'none';
    if(!pm) return;
    sec.querySelectorAll('tbody tr').forEach(r=>{{
      const txt=r.textContent.toLowerCase();
      r.style.display=(!s||txt.includes(s))&&(!q||txt.includes(q))?'':'none';
    }});
  }});
}}
</script>
</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    kb = round(os.path.getsize(OUTPUT_HTML) / 1024)
    print(f"\n✅ HTML saved: {OUTPUT_HTML} ({kb} KB)")
    print(
        f"   {total_inits} initiatives · {total_epics} epics · "
        f"LoE {port_loe:,}h · Budget {port_bgt}%"
    )
    print("\n--- Project RAG summary ---")
    for p, s in summaries.items():
        print(
            f"  {p}: LoE {s['loe']:,}h | Burn {s['burn_pct']}% | "
            f"%C {s['avg_pct']}% | Gap {s['burn_gap']:+.1f}pp | "
            f"B={s['rag_burn']} S={s['rag_schedule']} E={s['rag_etc']} "
            f"V={s['rag_velocity'] or '—'} → {s['rag']}/{s['review']}"
        )


if __name__ == "__main__":
    main()
