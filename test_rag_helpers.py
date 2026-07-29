"""Unit tests for RAG framework and % complete helpers (no API required)."""

from datetime import date

from rag_framework import (
    burn_dimension,
    combine_rag,
    etc_dimension,
    project_pct_complete,
    schedule_dimension,
    velocity_dimension,
    wp_pct_from_epics,
)


def test_wp_pct_hours_weighted():
    epics = [
        {"loe": 100, "pct": 80},
        {"loe": 100, "pct": 20},
    ]
    assert wp_pct_from_epics(epics) == 50


def test_wp_pct_zero_hours_uses_simple_mean():
    epics = [
        {"loe": 0, "pct": 80},
        {"loe": 0, "pct": 20},
    ]
    assert wp_pct_from_epics(epics) == 50


def test_project_pct_excludes_not_started():
    inits = [
        {"pct": 60},
        {"pct": 40},
        {"pct": 0},
    ]
    assert project_pct_complete(inits) == 50


def test_burn_rag_matches_heather_examples():
    # OSC Jul 2026 example: Burn 70.4%, Complete 57.1% → +13.3pp → Amber
    assert burn_dimension(70.4, 57.1)[0] == "Amber"
    assert burn_dimension(44.5, 49.7)[0] == "Green"
    assert burn_dimension(90, 50)[0] == "Red"


def test_combine_rag():
    assert combine_rag(["Green", "Green", "Amber"]) == "Green"
    assert combine_rag(["Amber", "Amber", "Green"]) == "Amber"
    assert combine_rag(["Green", "Red", "Green"]) == "Red"
    assert combine_rag(["Green", None, "Green"]) == "Green"


def test_etc_dimension():
    assert etc_dimension(10000, 9000, 500) == "Green"
    assert etc_dimension(10000, 9000, 2000) == "Red"
    assert etc_dimension(10000, 9000, 900) == "Amber"


def test_velocity_none_skipped():
    assert velocity_dimension(None) is None
    assert velocity_dimension(85) == "Green"
    assert velocity_dimension(50) == "Red"


def test_schedule_on_track():
    today = date(2026, 7, 17)
    inits = [{"status": "In Progress", "end": "2026-07-24", "pct": 70}]
    assert schedule_dimension(inits, today=today) == "Green"


def test_schedule_far_behind():
    today = date(2026, 7, 17)
    inits = [{"status": "In Progress", "end": "2026-05-01", "pct": 40}]
    assert schedule_dimension(inits, today=today) == "Red"


if __name__ == "__main__":
    test_wp_pct_hours_weighted()
    test_wp_pct_zero_hours_uses_simple_mean()
    test_project_pct_excludes_not_started()
    test_burn_rag_matches_heather_examples()
    test_combine_rag()
    test_etc_dimension()
    test_velocity_none_skipped()
    test_schedule_on_track()
    test_schedule_far_behind()
    print("✅ All RAG helper tests passed")
