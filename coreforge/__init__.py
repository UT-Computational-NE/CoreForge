"""CoreForge — Python tools for setting up nuclear reactor models."""

from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version("coreforge")
except PackageNotFoundError:  # pragma: no cover - source tree without an install
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
