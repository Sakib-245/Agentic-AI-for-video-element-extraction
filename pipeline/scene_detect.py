"""
Stage 1: Scene Detection

Wraps PySceneDetect's content-based detector. Returns a plain list of
(start_seconds, end_seconds) tuples so the rest of the pipeline doesn't
need to know anything about PySceneDetect's internal timecode objects.
"""
from scenedetect import detect, ContentDetector


def find_shots(video_path: str, threshold: float = 27.0):
    """
    threshold: lower = more sensitive (catches subtle cuts, more false
    positives from fast motion). Higher = misses soft dissolves/fades.
    27.0 is PySceneDetect's own default and a reasonable starting point.
    """
    scene_list = detect(video_path, ContentDetector(threshold=threshold))
    shots = []
    for start_tc, end_tc in scene_list:
        shots.append((start_tc.get_seconds(), end_tc.get_seconds()))
    return shots
