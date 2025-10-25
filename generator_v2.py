"""
Enhanced Data Generator (generator_v2.py)
-----------------------------------------
Simulates realistic multi-sensor traffic data for the runtime pipeline.

Key Features:
- 10,000 persistent PMGIDs (sensors)
- Fixed street assignments per sensor
- Generates 2–5 samples per sensor cycle
- Random vehicle counts and realistic speeds

Author: Zachery Gebreab
"""

from __future__ import annotations
import os
import time
import json
import random
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Iterator
import numpy as np
from dotenv import load_dotenv

load_dotenv()

DB_WRITE = os.getenv("DB_WRITE", "false").lower() == "true"
RECORDS_PER_SECOND = float(os.getenv("RECORDS_PER_SECOND", "10"))
NUM_RECORDS = int(os.getenv("NUM_RECORDS", "100"))
PEAKSPEED_MEAN = float(os.getenv("PEAKSPEED_MEAN", "40"))
PEAKSPEED_STD = float(os.getenv("PEAKSPEED_STD", "5"))

# Persistent sensors and locations
SENSOR_IDS = [f"PMG{i:05d}" for i in range(1, 10001)]
STREETS = [
    "Main St", "Elm Ave", "Broadway", "Preston Rd",
    "Belt Line Rd", "Central Expwy", "Coit Rd", "Plano Pkwy",
    "Legacy Dr", "Campbell Rd"
]

# Assign each sensor a fixed street
SENSOR_LOC_MAP = {sensor: random.choice(STREETS) for sensor in SENSOR_IDS}


@dataclass
class SensorRecord:
    pgmid: str
    vehicle_count: int
    peakspeed: float
    timestamp: str  # ISO-formatted with milliseconds
    location: str  # street name

    def to_json(self) -> str:
        return json.dumps(asdict(self))


def sample_peakspeed() -> float:
    """Sample speed from normal distribution, clipped to 0–120 mph."""
    val = float(np.random.normal(PEAKSPEED_MEAN, PEAKSPEED_STD))
    return max(0.0, min(val, 120.0))


def generate_records(num_records: int = -1) -> Iterator[SensorRecord]:
    """
    Generator that simulates real sensors sending data bursts.
    Each sensor emits 2–5 readings per cycle.
    """
    i = 0
    interval = 1.0 / RECORDS_PER_SECOND if RECORDS_PER_SECOND > 0 else 0.1

    while num_records == -1 or i < num_records:
        sensor_id = random.choice(SENSOR_IDS)
        location = SENSOR_LOC_MAP[sensor_id]
        batch_size = random.randint(2, 5)

        for _ in range(batch_size):
            now = datetime.utcnow()
            ts = now.strftime("%H:%M:%S.%f")[:-3]
            rec = SensorRecord(
                pgmid=sensor_id,
                vehicle_count=random.randint(1, 5),
                peakspeed=round(sample_peakspeed(), 2),
                timestamp=ts,
                location=location,
            )
            yield rec
            i += 1
            if num_records != -1 and i >= num_records:
                break
            time.sleep(interval)


if __name__ == "__main__":
    import sys
    n = NUM_RECORDS
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except Exception:
            pass

    for r in generate_records(n):
        print(r.to_json())
