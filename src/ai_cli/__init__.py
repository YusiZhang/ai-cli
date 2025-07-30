"""AI CLI - Multi-model AI command line interface."""

try:
    from ._version import __version__
except ImportError:
    # Fallback for development mode
    __version__ = "unknown"

__all__ = ["__version__"]
