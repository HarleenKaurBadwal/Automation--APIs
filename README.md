# GSTS Trade Secret Intake

## Files

| File | What it is |
|------|------------|
| `interview.html` | Chat-style interview page (questions + UI) |
| `app.py` | Python server — hosts the page and saves submissions |
| `requirements.txt` | Python dependencies |
| `submissions/` | Saved JSON records (created automatically) |

---

## Run with Python (recommended)

```bash
pip install -r requirements.txt
python app.py
```

Open in your browser:

**http://localhost:8000**

When someone completes the interview, the record is saved to the `submissions/` folder as a JSON file.

---

## HTML only (no Python)

Double-click `interview.html` or:

```bash
python -m http.server 8080
```

Open `http://localhost:8080/interview.html`

Note: submissions won't save to server in this mode — use Download JSON at the end.

---

## Next step

Add Claude API to `app.py` for smarter follow-up questions (optional).
