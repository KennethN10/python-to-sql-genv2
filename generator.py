"""Data generator for simulating real-time sensor data.

Outputs JSON lines to stdout and optionally writes to MySQL.
"""
from __future__ import annotations
import os
import time
import json
import random
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Iterator, Dict

import numpy as np
from dotenv import load_dotenv

load_dotenv()

DB_WRITE = os.getenv("DB_WRITE", "false").lower() == "true"
RECORDS_PER_SECOND = float(os.getenv("RECORDS_PER_SECOND", "10"))
NUM_RECORDS = int(os.getenv("NUM_RECORDS", "100"))
PGMID = os.getenv("PGMID", "88")
VEHICLE_COUNT = int(os.getenv("VEHICLE_COUNT", "1"))
LOCATION_LAT = float(os.getenv("LOCATION_LAT", "32.8945"))
LOCATION_LONG = float(os.getenv("LOCATION_LONG", "-96.57679"))
PEAKSPEED_MEAN = float(os.getenv("PEAKSPEED_MEAN", "40"))
PEAKSPEED_STD = float(os.getenv("PEAKSPEED_STD", "5"))

@dataclass
class SensorRecord:
    pgmid: str
    vehicle_count: int
    pepkspeed: float
    timestamp: str  # ISO-formatted with milliseconds
    location: str  # "lat,long"

    def to_json(self) -> str:
        return json.dumps(asdict(self))


def sample_peakspeed() -> float:
    # Use normal distribution and clip to realistic bounds 0..120
    val = float(np.random.normal(PEAKSPEED_MEAN, PEAKSPEED_STD))
    return max(0.0, min(val, 120.0))


def generate_records(num_records: int = -1) -> Iterator[SensorRecord]:
    i = 0
    interval = 1.0 / RECORDS_PER_SECOND if RECORDS_PER_SECOND > 0 else 0.1
    while num_records == -1 or i < num_records:
        now = datetime.utcnow()
        ts = now.strftime("%H:%M:%S.%f")[:-3]  # HH:MM:SS.milliseconds
        rec = SensorRecord(
            pgmid=str(PGMID),
            vehicle_count=VEHICLE_COUNT,
            pepkspeed=round(sample_peakspeed(), 2),
            timestamp=ts,
            location=f"{LOCATION_LAT},{LOCATION_LONG}",
        )
        yield rec
        i += 1
        time.sleep(interval)


if __name__ == "__main__":
    # Simple CLI runner
    import sys

    n = NUM_RECORDS
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except Exception:
            pass

    for r in generate_records(n):
        print(r.to_json())
