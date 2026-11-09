# Shot Library

A local, PC-only tool that ingests a video, detects every shot/cut, and builds a
searchable personal library of shots — each tagged with color palette, motion,
on-screen text, and an AI-generated style/content/mood label. 

```
video.mp4 → scene detection → thumbnails → CV features → AI tagging → SQLite → browse in your browser
```

## 1. Setup

Requires Python 3.10+ and [FFmpeg](https://ffmpeg.org/download.html) installed and on your PATH
(EasyOCR and OpenCV also expect a working FFmpeg for some codecs).

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your Anthropic API key, then load it into
your shell before running anything, e.g.:

```bash
export GENAI_API_KEY=sk-ant-...     # Windows: set ANTHROPIC_API_KEY=sk-ant-...
```

(Or use a tool like `python-dotenv` / `direnv` if you prefer not to export it manually.)

## 2. Process a video

```bash
python process_video.py path/to/video.mp4
```

Options:
- `--threshold 22` — lower = more sensitive cut detection (catches subtle cuts,
  more false positives from fast motion). Default is 27.0.
- `--workers 4` — parallelize thumbnail extraction, feature extraction, and AI
  tagging across shots. Scene detection itself always runs single-threaded first.

This populates `shots.db` (SQLite) and writes one JPEG thumbnail per shot into
`thumbnails/`.

Run it again on more videos — everything accumulates into the same database,
so your library grows across your whole project.

## 3. Browse your library

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser. Filter by style, content,
mood, or presence of on-screen text (useful for finding shots with existing
lower-thirds/graphics vs. clean plates).

## Project structure

```
shotlibrary/
├── process_video.py       # CLI orchestrator — run this to ingest a video
├── app.py                 # Flask web UI — run this to browse
├── pipeline/
│   ├── db.py               # SQLite schema + queries
│   ├── scene_detect.py     # Stage 1: cut detection (PySceneDetect)
│   ├── frame_extract.py    # Stage 2: representative thumbnail per shot
│   ├── features.py         # Stage 3: palette, motion, OCR text regions
│   └── ai_tagging.py       # Stage 4: Claude API call for style/content/mood
├── templates/index.html   # Browser UI (contact-sheet layout)
├── thumbnails/             # Generated JPEGs, one per shot
├── shots.db                 # Generated SQLite database
└── requirements.txt
```

## Extending this later

Each pipeline stage writes its output to disk/DB before the next stage runs, so:
- If a Claude API call fails partway through a video, you don't lose scene
  detection or feature extraction — you'd just need to add a "retag" script
  that re-runs `ai_tagging.tag_shot` on shots with `style = 'unknown'`.
- Swapping the tagging model later (a different provider, a fine-tuned model,
  a local VLM) only touches `pipeline/ai_tagging.py`.
- The `--workers` flag already parallelizes steps 2-4 per shot; scene detection
  is inherently sequential since it needs the whole video.
- The web UI queries are centralized in `db.query_shots()` — new filters
  (e.g. by motion type, by shot duration) are a matter of adding SQL clauses
  there and a form field in `index.html`.
