"""
SQLite layer for the shot library.

One row per shot. Palette is stored as a JSON string (list of [r,g,b] triples).
Text regions are stored as a JSON string too, since they're a variable-length
list of (bbox, text, confidence) tuples.
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "shots.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
    video_id    TEXT PRIMARY KEY,
    path        TEXT NOT NULL,
    filename    TEXT NOT NULL,
    processed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shots (
    shot_id      TEXT PRIMARY KEY,
    video_id     TEXT NOT NULL,
    shot_index   INTEGER NOT NULL,
    start_time   REAL NOT NULL,
    end_time     REAL NOT NULL,
    thumbnail    TEXT NOT NULL,
    palette      TEXT,              -- JSON list of [r,g,b]
    motion_x     REAL,
    motion_y     REAL,
    text_regions TEXT,              -- JSON list of [bbox, text, confidence]
    style        TEXT,
    content      TEXT,
    mood         TEXT,
    FOREIGN KEY (video_id) REFERENCES videos (video_id)
);

CREATE INDEX IF NOT EXISTS idx_shots_style   ON shots (style);
CREATE INDEX IF NOT EXISTS idx_shots_content ON shots (content);
CREATE INDEX IF NOT EXISTS idx_shots_mood    ON shots (mood);
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def save_video(conn, video_id, path, filename, processed_at):
    conn.execute(
        """INSERT OR REPLACE INTO videos (video_id, path, filename, processed_at)
           VALUES (?, ?, ?, ?)""",
        (video_id, path, filename, processed_at),
    )
    conn.commit()


def save_shot(conn, shot_id, video_id, shot_index, start, end, thumbnail_path,
              palette, motion, text_regions, tags):
    conn.execute(
        """INSERT OR REPLACE INTO shots
           (shot_id, video_id, shot_index, start_time, end_time, thumbnail,
            palette, motion_x, motion_y, text_regions, style, content, mood)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            shot_id, video_id, shot_index, start, end, thumbnail_path,
            json.dumps(palette), motion[0], motion[1], json.dumps(text_regions),
            tags.get("style"), tags.get("content"), tags.get("mood"),
        ),
    )
    conn.commit()


def query_shots(conn, style=None, content=None, mood=None, has_text=None, limit=200):
    """Flexible search used by the web UI. Any filter left as None is ignored."""
    clauses, params = [], []
    if style:
        clauses.append("style LIKE ?")
        params.append(f"%{style}%")
    if content:
        clauses.append("content LIKE ?")
        params.append(f"%{content}%")
    if mood:
        clauses.append("mood LIKE ?")
        params.append(f"%{mood}%")
    if has_text is True:
        clauses.append("text_regions != '[]'")
    elif has_text is False:
        clauses.append("text_regions = '[]'")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""SELECT shots.*, videos.filename AS video_filename
              FROM shots JOIN videos ON shots.video_id = videos.video_id
              {where}
              ORDER BY shots.video_id, shots.shot_index
              LIMIT ?"""
    params.append(limit)
    return conn.execute(sql, params).fetchall()


def distinct_values(conn, column):
    rows = conn.execute(f"SELECT DISTINCT {column} FROM shots WHERE {column} IS NOT NULL ORDER BY {column}")
    return [r[0] for r in rows.fetchall()]
