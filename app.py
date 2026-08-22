#!/usr/bin/env python3
"""
Local web UI for browsing/searching your shot library.

Run with: python app.py
Then open: http://127.0.0.1:5000
"""
import json
from pathlib import Path

from flask import Flask, render_template, request, send_from_directory

from pipeline import db

app = Flask(__name__)
THUMB_DIR = Path(__file__).resolve().parent / "thumbnails"


@app.route("/")
def index():
    conn = db.get_connection()
    style = request.args.get("style") or None
    content = request.args.get("content") or None
    mood = request.args.get("mood") or None
    has_text_raw = request.args.get("has_text")
    has_text = {"yes": True, "no": False}.get(has_text_raw)

    rows = db.query_shots(conn, style=style, content=content, mood=mood, has_text=has_text)
    shots = []
    for r in rows:
        d = dict(r)
        d["palette"] = json.loads(d["palette"] or "[]")
        d["thumbnail_name"] = Path(d["thumbnail"]).name
        shots.append(d)

    styles = db.distinct_values(conn, "style")
    contents = db.distinct_values(conn, "content")
    moods = db.distinct_values(conn, "mood")
    conn.close()

    return render_template(
        "index.html",
        shots=shots,
        styles=styles,
        contents=contents,
        moods=moods,
        filters={"style": style or "", "content": content or "", "mood": mood or "",
                 "has_text": has_text_raw or ""},
    )


@app.route("/thumbnails/<path:filename>")
def thumbnail(filename):
    return send_from_directory(THUMB_DIR, filename)


if __name__ == "__main__":
    db.init_db()  # ensure tables exist even if no video processed yet
    app.run(debug=True, port=5000)
