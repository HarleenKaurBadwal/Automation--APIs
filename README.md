# GSTS Trade Secret Intake

## Recommended approach (per Harry Singh)

**No hosting required.** Use the self-contained markdown interview guide:

| File | What it is |
|------|------------|
| **`CLAUDE.md`** | Email this to teams — they run their own Claude session against it |

### Workflow

1. Email `CLAUDE.md` to technical staff
2. Each person opens an **approved Claude session** and attaches this file
3. They say: *"Please run the GSTS Trade Secret and IP intake interview from the attached CLAUDE.md guide."*
4. Claude asks metadata → period screening → iterative IP collection
5. User saves the generated document (unique Submission ID)
6. User uploads to the designated SharePoint / Document Control location
7. Coordinator aggregates all team docs into one period register

### Before sending

Update the upload path in **Phase 6** of `CLAUDE.md` once Document Control confirms the folder.

---

## Legacy prototype (optional — hosted web app)

| File | What it is |
|------|------------|
| `interview.html` | Chat-style interview page |
| `app.py` | Python Flask server (requires hosting + auth) |

```bash
pip install -r requirements.txt
python app.py
# open http://localhost:8000
```

Not the preferred approach — kept for reference only.
