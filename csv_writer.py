"""Append sensor records to a CSV file continuously.

This writer will create the parent directory if necessary, write a header if the
file does not exist, and append rows for each record. It is safe to call for
every generated record and is intended for local inspection while DB access is
not available.
"""
from __future__ import annotations
import csv
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CSV_WRITE = os.getenv("CSV_WRITE", "true").lower() == "true"
CSV_PATH = os.getenv("CSV_PATH", "data/sensor_readings.csv")


def _ensure_parent(path: Path) -> None:
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


def write_record_to_csv(rec: dict) -> bool:
    """Append a record dict to the CSV at CSV_PATH.

    Returns True on success (or when CSV_WRITE is false and dry-run).
    """
    if not CSV_WRITE:
        # If CSV writing disabled, behave like a dry-run success
        return True

    path = Path(CSV_PATH)
    _ensure_parent(path)

    # Field order
    fields = ["pgmid", "vehicle_count", "pepkspeed", "timestamp", "location", "created_at"]

    write_header = not path.exists()
    try:
        with path.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            if write_header:
                writer.writeheader()
            row = {
                "pgmid": rec.get("pgmid"),
                "vehicle_count": rec.get("vehicle_count"),
                "pepkspeed": rec.get("pepkspeed"),
                "timestamp": rec.get("timestamp"),
                "location": rec.get("location"),
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            writer.writerow(row)
        return True
    except Exception:
        return False
