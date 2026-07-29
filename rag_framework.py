"""GSTS Portfolio RAG Framework v1.0 (July 2026) — pure helpers.

% Complete:
  WP  = hours-weighted epic progress (Aha); if no hours → simple mean of epic bars
  Project = simple mean of started WPs (exclude 0% so placeholders don't drag %)

RAG dimensions + combining rule applied at project level.
"""

from datetime import datetime


def wp_pct_from_epics(epics):
    """Step 1: Work package % = hours-weighted epic progress (Aha).

    If all epic hours are 0 → simple average of epic progress bars.
    """
    if not epics:
        return 0
    total_h = sum(e.get("loe", 0) or 0 for e in epics)
    if total_h > 0:
        return round(
            sum((e.get("loe", 0) or 0) * (e.get("pct", 0) or 0) for e in epics) / total_h
        )
    return round(sum(e.get("pct", 0) or 0 for e in epics) / len(epics))


def project_pct_complete(inits):
    """Step 2: Project % = simple mean of WP % values.

    Exclude WPs that have not started (0%) so they do not drag down claimed %.
    Falls back to all WPs if none have started.
    """
    if not inits:
        return 0
    started = [i for i in inits if (i.get("pct") or 0) > 0]
    pool = started if started else inits
    return round(sum(i.get("pct", 0) or 0 for i in pool) / len(pool))


def burn_dimension(burn_pct, scope_pct):
    """Budget / Burn Rate: Burn Gap = Burn % − Project % Complete."""
    gap = round(burn_pct - scope_pct, 1)
    if gap <= 10:
        return "Green", gap
    if gap <= 35:
        return "Amber", gap
    return "Red", gap


def schedule_dimension(inits, today=None):
    """Schedule vs planned milestone end dates (project-level)."""
    today = today or datetime.today().date()
    worst = "Green"
    for i in inits:
        if i.get("status") == "Complete ✓":
            continue
        end = i.get("end") or ""
        if end in ("—", "None", ""):
            continue
        try:
            end_d = datetime.strptime(str(end)[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        days_behind = (today - end_d).days
        days_until = (end_d - today).days
        if days_behind > 42:
            return "Red"
        if days_behind > 14:
            worst = "Amber"
            continue
        if 0 <= days_until <= 14 and (i.get("pct") or 0) < 50:
            worst = "Amber"
    return worst


def etc_dimension(loe_baseline, total_act, etc_remaining, is_internal=False):
    """ETC Confidence: remaining budget vs remaining ETC.

    Remaining budget = Baseline − Actuals.
    Headroom % = (Remaining budget − ETC) ÷ Remaining budget × 100.
    """
    _ = is_internal
    remaining_budget = loe_baseline - total_act
    if etc_remaining > remaining_budget:
        return "Red"
    if remaining_budget <= 0:
        return "Amber" if etc_remaining > 0 else "Green"
    headroom = (remaining_budget - etc_remaining) / remaining_budget * 100
    if headroom > 15:
        return "Green"
    return "Amber"


def velocity_dimension(closure_rate):
    """Delivery Velocity (GitLab). Returns None if no data."""
    if closure_rate is None:
        return None
    if closure_rate > 80:
        return "Green"
    if closure_rate >= 60:
        return "Amber"
    return "Red"


def combine_rag(dimensions):
    """Combining rule across dimensions (ignore None).

    Overall Red  — any dimension Red
    Overall Amber — two or more Amber
    Overall Green — all Green, or only one Amber
    """
    dims = [d for d in dimensions if d in ("Green", "Amber", "Red")]
    if not dims:
        return "No Data"
    if any(d == "Red" for d in dims):
        return "Red"
    if sum(1 for d in dims if d == "Amber") >= 2:
        return "Amber"
    return "Green"


def review_from_rag(rag):
    return {
        "Red": "HIGH",
        "Amber": "WATCH",
        "Green": "OK",
        "No Data": "—",
    }.get(rag, "—")
