"""
GSTS Trade Secret Intake — local server

Run:
    pip install -r requirements.txt
    python app.py

Open:
    http://localhost:8000
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
SUBMISSIONS_DIR = BASE_DIR / "submissions"
SUBMISSIONS_DIR.mkdir(exist_ok=True)

PORT = int(os.environ.get("PORT", "8000"))


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "interview.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/submit")
def submit():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body received"}), 400

    submission_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"trade_secret_{timestamp}_{submission_id}.json"
    filepath = SUBMISSIONS_DIR / filename

    record = {
        "_meta": {
            "submission_id": submission_id,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "review_status": "Drafted",
            "confidential": True,
        },
        **data,
    }

    filepath.write_text(json.dumps(record, indent=2), encoding="utf-8")

    return jsonify(
        {
            "ok": True,
            "message": "Submission saved successfully.",
            "submission_id": submission_id,
            "filename": filename,
        }
    )


@app.get("/api/submissions")
def list_submissions():
    files = sorted(SUBMISSIONS_DIR.glob("trade_secret_*.json"), reverse=True)
    items = []
    for f in files[:50]:
        items.append({"filename": f.name, "size_bytes": f.stat().st_size})
    return jsonify({"count": len(items), "submissions": items})


if __name__ == "__main__":
    print()
    print("=" * 50)
    print("  GSTS Trade Secret Intake")
    print("=" * 50)
    print(f"  Open in browser: http://localhost:{PORT}")
    print(f"  Submissions save to: {SUBMISSIONS_DIR}")
    print("  Press Ctrl+C to stop")
    print("=" * 50)
    print()
    app.run(host="0.0.0.0", port=PORT, debug=True)
