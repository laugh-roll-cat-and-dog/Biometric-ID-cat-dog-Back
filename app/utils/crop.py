from pathlib import Path
from typing import Any

import cv2
from ultralytics import YOLO


def crop_image(
    image_path: str | Path,
    conf: float = 0.75,
) -> Any | None:
    """Load YOLO model, run detection, and return the best cropped image.

    Returns the highest-confidence cropped image array, or None if no detection.
    """

    if conf < 0.75 or conf > 1:
        raise ValueError("Confidence must be between 0.75 and 1")

    image_file = Path(image_path)
    if not image_file.is_file():
        raise FileNotFoundError(f"Image file not found: {image_file}")

    # Load YOLO model
    model_file = Path("/var/jenkins_home/workspace/whatTheDog-backend/app/ai/yolo.pt")
    if not model_file.is_file():
        raise FileNotFoundError(f"Invalid model path: {model_file}")
    model = YOLO(str(model_file))

    image = cv2.imread(str(image_file))
    if image is None:
        raise ValueError("Could not read image. Unsupported or corrupted file")

    results = model.predict(source=str(image_file), conf=conf, verbose=False)
    result = results[0]
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        return None

    best_crop: Any | None = None
    best_conf = -1.0

    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0].int().tolist()
        conf_score = float(box.conf[0].item())

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(image.shape[1], x2)
        y2 = min(image.shape[0], y2)
        if x2 <= x1 or y2 <= y1:
            continue

        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        if conf_score > best_conf:
            best_conf = conf_score
            best_crop = crop

    return best_crop
