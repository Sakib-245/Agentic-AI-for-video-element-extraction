from pathlib import Path

# Use a raw string OR forward slashes — Windows accepts both, but pathlib is safest
BASE_DIR = Path(r"E:\Projects and trials\AIML\shotlibrary")

THUMBNAIL_DIR = BASE_DIR / "thumbnails"
DB_PATH = BASE_DIR / "shotlibrary.db"
VIDEO_INPUT_DIR = BASE_DIR / "videos"

# Ensure folders exist on first run
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_INPUT_DIR.mkdir(parents=True, exist_ok=True)