# GSTS Portfolio Report (LoE & Actuals)

Generates `GSTS_LoE_Dashboard.html` from Aha + QBO (+ contractor hours).

## RAG Framework v1.0 (July 2026)

| Change | Detail |
|--------|--------|
| OSC LoE | Overridden to **26,750h** (rebaseline 14 Jul 2026) for burn / display display |
| Initiative LoE rows | Stay live Aha |
| EAC | Uses live Aha LoE (not the override) |
| WP % complete | Hours-weighted epic progress; if no hours → simple mean of epic bars |
| Project % complete | Simple mean of **started** work packages (excludes 0%) |
| Burn RAG | Gap = Burn% − Project%; Green ≤+10pp, Amber +11–35pp, Red >+35pp |
| Overall RAG | Any Red → Red; ≥2 Amber → Amber; else Green |
| Velocity | Optional via `VELOCITY_BY_PROJ`; skipped until GitLab rates are wired |

## Run

```bash
export AHA_API_KEY=...
export AHA_SUBDOMAIN=...
export ANTHROPIC_API_KEY=...   # optional
python3 -m pip install -r requirements.txt
python3 Report.py
```

## Tests (no API)

```bash
python3 test_rag_helpers.py
```
