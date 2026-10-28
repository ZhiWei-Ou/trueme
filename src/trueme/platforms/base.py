"""The platform contract used by model-directory resolution."""

from abc import ABC, abstractmethod
from pathlib import Path


class PlatformPaths(ABC):
    @abstractmethod
    def model_dir(self) -> Path:
        """Return the per-user model location without creating it."""
