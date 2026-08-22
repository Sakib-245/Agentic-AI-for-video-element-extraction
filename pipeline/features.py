"""
Stage 3: Feature Extraction (classic CV, no neural nets)

Three independent sub-analyses per shot:
  - get_palette:       dominant colors via k-means on pixel values
  - get_motion_vector: optical flow between a shot's first/last frame
  - get_text_regions:  OCR bounding boxes (lower-thirds, on-screen text)

EasyOCR's reader is expensive to initialize, so it's created once at
module import time and reused across every shot.
"""
import cv2
import numpy as np
from sklearn.cluster import KMeans

_ocr_reader = None


def _get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        _ocr_reader = easyocr.Reader(["en"], gpu=False)
    return _ocr_reader


def get_palette(image_path: str, k: int = 5):
    img = cv2.imread(image_path)
    if img is None:
        return []
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pixels = img.reshape(-1, 3).astype(np.float32)

    # Downsample for speed on large frames -- palette doesn't need every pixel
    if len(pixels) > 20000:
        idx = np.random.choice(len(pixels), 20000, replace=False)
        pixels = pixels[idx]

    kmeans = KMeans(n_clusters=k, n_init=10, random_state=0).fit(pixels)
    return kmeans.cluster_centers_.astype(int).tolist()


def _frame_at(video_path: str, timestamp: float):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
    ok, frame = cap.read()
    cap.release()
    return frame if ok else None


def get_motion_vector(video_path: str, start: float, end: float):
    """Optical flow between the shot's first and last frame.
    Returns (avg_dx, avg_dy). Near-zero = static shot; large uniform dx = pan."""
    frame1 = _frame_at(video_path, start + 0.05)
    frame2 = _frame_at(video_path, max(end - 0.05, start + 0.05))
    if frame1 is None or frame2 is None:
        return (0.0, 0.0)

    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    if gray1.shape != gray2.shape:
        gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))

    flow = cv2.calcOpticalFlowFarneback(
        gray1, gray2, None, 0.5, 3, 15, 3, 5, 1.2, 0
    )
    return float(flow[..., 0].mean()), float(flow[..., 1].mean())


def get_text_regions(thumbnail_path: str):
    """Returns [[bbox, text, confidence], ...]. bbox is 4 corner points."""
    reader = _get_ocr_reader()
    results = reader.readtext(thumbnail_path)
    return [
        [np.array(bbox).tolist(), text, float(conf)]
        for bbox, text, conf in results
    ]
