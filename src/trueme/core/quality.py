"""Uncalibrated image-quality hints, never identity decisions."""

import cv2
import numpy as np


def quality_warnings(image: np.ndarray, bbox: tuple[float, float, float, float]) -> list[str]:
    x, y, width, height = bbox
    warnings = []
    if min(width, height) < 80:
        warnings.append("Heuristic: small face region (under 80 pixels on one side).")
    rows, columns = image.shape[:2]
    left, top = max(0, int(x)), max(0, int(y))
    right, bottom = min(columns, int(np.ceil(x + width))), min(rows, int(np.ceil(y + height)))
    crop = image[top:bottom, left:right]
    if crop.size == 0:
        return warnings + ["Heuristic: face region lies outside the image."]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    if cv2.Laplacian(gray, cv2.CV_64F).var() < 50:
        warnings.append("Heuristic: possible blur (face Laplacian variance below 50).")
    brightness = float(gray.mean())
    if brightness < 40:
        warnings.append(
            "Heuristic: possible severe underexposure (face mean brightness below 40/255)."
        )
    elif brightness > 220:
        warnings.append(
            "Heuristic: possible severe overexposure (face mean brightness above 220/255)."
        )
    return warnings
