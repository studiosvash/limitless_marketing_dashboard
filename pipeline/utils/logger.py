"""
utils/logger.py — Centralized logging setup for all connectors and workers.
"""
import logging
import os
import sys
from pathlib import Path

# Where the pipeline's own log file lives.
#
# This defaults INSIDE the project, and on a dev box that is actively harmful: a sync writes
# to this file continuously at INFO level, and `manage.py runserver`'s auto-reloader watches
# the project tree. The reloader restarts the server mid-sync, which kills the daemon sync
# thread outright -- the terminal simply returns to the prompt with no traceback, and the
# RefreshRun row is left stuck at "running" forever. (Proven 2026-07-27: the identical audit
# sync that killed `runserver` ran for 90+ seconds without incident under `--noreload`.
# It is also where the orphaned "running since 16 Jun" RefreshRun rows came from.)
#
# Set FUSEHEALTH_LOG_DIR to a path OUTSIDE the project to stop that happening. The default is
# unchanged so nothing about production logging moves unless an operator asks for it.
LOG_DIR = Path(os.environ.get("FUSEHEALTH_LOG_DIR") or (Path(__file__).parent.parent.parent / "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"fusehealth.{name}")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(_FORMATTER)
    logger.addHandler(console)
    log_file = LOG_DIR / "fusehealth.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(_FORMATTER)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger
