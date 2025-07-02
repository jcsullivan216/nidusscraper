from __future__ import annotations

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data_raw"
DATA_DIR.mkdir(exist_ok=True)
MANIFEST = DATA_DIR / "sources.csv"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
