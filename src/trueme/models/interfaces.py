"""The two model contracts used by the comparison pipeline."""

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class Face:
    bbox: tuple[float, float, float, float]
    landmarks: np.ndarray
    score: float


class Detector(Protocol):
    def detect(self, bgr: np.ndarray) -> list[Face]: ...


class Recognizer(Protocol):
    def embed(self, bgr: np.ndarray, face: Face) -> np.ndarray: ...
