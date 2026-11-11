"""SQLite database connection configuration.

The local development database remains inside the repository's database folder.
On Render, set MSME_DATABASE_PATH to a file on the service's persistent disk.
"""

import os
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "emi_planner.db"
DB_PATH = Path(os.getenv("MSME_DATABASE_PATH", str(DEFAULT_DB_PATH))).expanduser()


def get_connection():
    """Return a SQLite connection, creating the configured data directory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)
