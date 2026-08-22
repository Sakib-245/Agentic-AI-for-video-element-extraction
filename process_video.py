#!/usr/bin/env python3
"""
Orchestrator: video.mp4 -> populated shots.db

Usage:
    python process_video.py path/to/video.mp4
    python process_video.py path/to/video.mp4 --threshold 22 --workers 4

Each shot's steps 2-4 (thumbnail, features, AI tag) run independently of
every other shot, so they're safe to parallelize with a thread pool once
scene detection (step 1) has produced the full shot list.
"""
import argparse
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from pipeline import db
from pipeline.scene_detect import find_shots
from pipeline.frame_extract import extract_thumbnail
from pipeline.features import get_palette, get_motion_vector, get_text_regions
from pipeline.ai_tagging import tag_shot


def process_one_shot(video_path, video_id, shot_index, start, end):
    shot_id = f"{video_id}_shot{shot_index:04d}"
    thumb = extract_thumbnail(video_path, start, end, shot_id)
    palette = get_palette(thumb)
    motion = get_motion_vector(video_path, start, end)
    text_regions = get_text_regions(thumb)
    tags = tag_shot(thumb, palette, motion, text_regions)
    return {
        "shot_id": shot_id,
        "shot_index": shot_index,
        "start": start,
        "end": end,
        "thumbnail": thumb,
        "palette": palette,
        "motion": motion,
        "text_regions": text_regions,
        "tags": tags,
    }


def process_video(video_path: str, threshold: float = 27.0, workers: int = 1):
    video_path = str(Path(video_path).resolve())
    if not Path(video_path).exists():
        print(f"File not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    conn = db.init_db()
    video_id = uuid.uuid4().hex[:12]
    filename = Path(video_path).name

    print(f"[1/5] Detecting shots in {filename} ...")
    shots = find_shots(video_path, threshold=threshold)
    print(f"      Found {len(shots)} shots.")

    db.save_video(conn, video_id, video_path, filename, datetime.now().isoformat())

    print(f"[2-4/5] Extracting thumbnails, features, and AI tags "
          f"({workers} worker{'s' if workers != 1 else ''}) ...")

    results = []
    if workers <= 1:
        for i, (start, end) in enumerate(shots):
            results.append(process_one_shot(video_path, video_id, i, start, end))
            print(f"      shot {i+1}/{len(shots)} done")
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(process_one_shot, video_path, video_id, i, start, end): i
                for i, (start, end) in enumerate(shots)
            }
            done = 0
            for fut in as_completed(futures):
                results.append(fut.result())
                done += 1
                print(f"      shot {done}/{len(shots)} done")

    print("[5/5] Writing to database ...")
    for r in results:
        db.save_shot(
            conn, r["shot_id"], video_id, r["shot_index"], r["start"], r["end"],
            r["thumbnail"], r["palette"], r["motion"], r["text_regions"], r["tags"],
        )

    print(f"Done. {len(results)} shots saved to {db.DB_PATH}")
    print("Run `python app.py` to browse your shot library in the browser.")


def main():
    parser = argparse.ArgumentParser(description="Process a video into a searchable shot library.")
    parser.add_argument("video", help="Path to the input video file")
    parser.add_argument("--threshold", type=float, default=27.0,
                         help="Scene-cut sensitivity (lower = more sensitive). Default 27.0")
    parser.add_argument("--workers", type=int, default=1,
                         help="Parallel workers for thumbnail/feature/AI stages. Default 1")
    args = parser.parse_args()
    process_video(args.video, threshold=args.threshold, workers=args.workers)


if __name__ == "__main__":
    main()
