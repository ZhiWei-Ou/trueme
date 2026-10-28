"""Platform interfaces and entry-boundary selection."""

from .base import PlatformPaths
from .infrastructure import select_platform

__all__ = ["PlatformPaths", "select_platform"]
