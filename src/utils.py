"""Shared logging and validation utilities."""
import logging
from pathlib import Path

def configure_logging(log_dir: Path) -> None:
    """Configure console and file logging."""
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "application.log", encoding="utf-8"),
        ],
        force=True,
    )
