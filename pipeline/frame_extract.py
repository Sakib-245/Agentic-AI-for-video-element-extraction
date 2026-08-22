"""
Stage 2: Frame Extraction

Pulls one representative thumbnail per shot, sampled 20-30% into the shot
(rather than frame 0) to avoid motion-blur right at the cut point.
"""
from pathlib import Path
import ffmpeg

THUMB_DIR = Path(__file__).resolve().parent.parent / "thumbnails"
THUMB_DIR.mkdir(exist_ok=True)


def extract_thumbnail(video_path: str, start: float, end: float, shot_id: str) -> str:
    duration = max(end - start, 0.01)
    sample_point = start + duration * 0.25  # 25% into the shot

    output = str(THUMB_DIR / f"{shot_id}.jpg")
    (
        ffmpeg
        .input(video_path, ss=sample_point)
        .output(output, vframes=1, qscale=2)
        .overwrite_output()
        .run(quiet=True)
    )
    return output
