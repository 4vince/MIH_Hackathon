"""Dual-output logging: console (INFO+) and output/transcript.log (DEBUG+)."""

import logging
import pathlib

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "output"


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("confluence_iq")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(OUTPUT_DIR / "transcript.log", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(name)s] %(levelname)s %(message)s")
    )
    logger.addHandler(file_handler)

    return logger
