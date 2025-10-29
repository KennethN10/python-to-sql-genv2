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
from datetime import datetime, timedelta, UTC
from typing import Iterator, Tuple, List, Optional
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# Define rush hour periods (24-hour format)
RUSH_HOURS: List[Tuple[int, int]] = [
    (7, 9),    # Morning rush: 7-9 AM
    (11, 13),  # Lunch rush: 11AM-1PM
    (16, 18)   # Evening rush: 4-6 PM
]

# Time distribution weights (higher numbers = more data in that period)
TIME_WEIGHTS = {
    'rush_hour': 0.5,     # 50% of data during rush hours (6 hours total)
    'business': 0.3,      # 30% during business hours (non-rush, 6 hours)
    'evening': 0.15,      # 15% during evening (4 hours)
    'overnight': 0.05     # 5% during overnight (8 hours)
}

DB_WRITE = os.getenv("DB_WRITE", "false").lower() == "true"
RECORDS_PER_SECOND = float(os.getenv("RECORDS_PER_SECOND", "10"))
NUM_RECORDS = int(os.getenv("NUM_RECORDS", "100"))
PEAKSPEED_MEAN = float(os.getenv("PEAKSPEED_MEAN", "40"))
PEAKSPEED_STD = float(os.getenv("PEAKSPEED_STD", "5"))

# Load location from environment (matching generator.py)
LOCATION_LAT = float(os.getenv("LOCATION_LAT", "32.8945"))
LOCATION_LONG = float(os.getenv("LOCATION_LONG", "-96.57679"))

# Persistent sensors (10,000 PMGIDs)
SENSOR_IDS = [f"PMG{i:05d}" for i in range(1, 10001)]


@dataclass
class SensorRecord:
    pgmid: str
    vehicle_count: int
    pepkspeed: float  # matches generator.py field name
    timestamp: str  # ISO-formatted with milliseconds
    location: str  # lat,long format to match generator.py

    def to_json(self) -> str:
        return json.dumps(asdict(self))


def get_time_period(hour: int) -> str:
    """Determine which time period a given hour belongs to."""
    if any(start <= hour < end for start, end in RUSH_HOURS):
        return 'rush_hour'
    elif 9 <= hour < 17:  # 9 AM - 5 PM (excluding rush hours)
        return 'business'
    elif 18 <= hour < 22:  # 6 PM - 10 PM
        return 'evening'
    else:  # 10 PM - 7 AM
        return 'overnight'

def is_rush_hour(hour: int) -> bool:
    """Check if given hour is during rush hour periods."""
    return any(start <= hour < end for start, end in RUSH_HOURS)

def generate_timestamp(base_time: Optional[datetime] = None) -> Tuple[datetime, str]:
    """
    Generate a synthetic timestamp based on time distribution weights.
    Returns both the datetime object and formatted string.
    """
    if base_time is None:
        base_time = datetime.now(UTC)
    
    # Randomly select time period based on weights
    period = random.choices(
        list(TIME_WEIGHTS.keys()),
        weights=list(TIME_WEIGHTS.values())
    )[0]
    
    # Generate hour based on selected period
    if period == 'rush_hour':
        # Randomly select one of the rush hour periods
        rush_period = random.choice(RUSH_HOURS)
        hour = random.randint(rush_period[0], rush_period[1] - 1)
    elif period == 'business':
        # Business hours excluding rush hours
        non_rush_hours = [h for h in range(9, 17) 
                         if not any(start <= h < end for start, end in RUSH_HOURS)]
        hour = random.choice(non_rush_hours)
    elif period == 'evening':
        hour = random.randint(18, 21)
    else:  # overnight
        hour = random.choice(list(range(22, 24)) + list(range(0, 7)))
    
    # Generate random minute and second
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    microsecond = random.randint(0, 999) * 1000  # millisecond precision
    
    # Create new datetime with generated time
    new_time = base_time.replace(
        hour=hour,
        minute=minute,
        second=second,
        microsecond=microsecond
    )
    
    # Format for output
    ts = new_time.strftime("%H:%M:%S.%f")[:-3]
    
    return new_time, ts

def get_time_multipliers(hour: int) -> Tuple[float, float]:
    """
    Get speed and vehicle count multipliers based on time of day.
    Returns: (speed_multiplier, vehicle_count_multiplier)
    
    Time periods:
    - Rush hours: Slower speeds (0.6-0.8x), More vehicles (1.5-2.0x)
    - Late night (11PM-5AM): Faster speeds (1.1-1.2x), Fewer vehicles (0.3-0.5x)
    - Normal hours: Normal variation (0.9-1.1x for both)
    """
    if is_rush_hour(hour):
        return (
            random.uniform(0.6, 0.8),    # Slower during rush hour
            random.uniform(1.5, 2.0)     # More vehicles during rush hour
        )
    elif 23 <= hour or hour < 5:
        return (
            random.uniform(1.1, 1.2),    # Faster at night
            random.uniform(0.3, 0.5)     # Fewer vehicles at night
        )
    else:
        return (
            random.uniform(0.9, 1.1),    # Normal speed variation
            random.uniform(0.8, 1.2)     # Normal vehicle count variation
        )

def sample_peakspeed(hour: int) -> float:
    """
    Sample speed from normal distribution, adjusted for time of day.
    Speed is clipped to 0–120 mph after time-based adjustment.
    """
    base_speed = float(np.random.normal(PEAKSPEED_MEAN, PEAKSPEED_STD))
    speed_mult, _ = get_time_multipliers(hour)
    adjusted_speed = base_speed * speed_mult
    return max(0.0, min(adjusted_speed, 120.0))


def generate_records(num_records: int = -1, base_time: Optional[datetime] = None) -> Iterator[SensorRecord]:
    """
    Generator that simulates real sensors sending data bursts.
    Each sensor emits 2–5 readings per cycle.
    
    Args:
        num_records: Number of records to generate (-1 for infinite)
        base_time: Optional base time to generate records around (defaults to now)
    """
    i = 0
    interval = 1.0 / RECORDS_PER_SECOND if RECORDS_PER_SECOND > 0 else 0.1

    while num_records == -1 or i < num_records:
        sensor_id = random.choice(SENSOR_IDS)
        batch_size = random.randint(2, 5)
        
        # Generate base timestamp for this batch
        batch_time, _ = generate_timestamp(base_time)
        
        # Generate slightly increasing timestamps within the batch
        for j in range(batch_size):
            # Add small random increment within the batch (0-500ms between readings)
            batch_offset = timedelta(milliseconds=random.randint(0, 500) * j)
            current_time = batch_time + batch_offset
            current_hour = current_time.hour
            ts = current_time.strftime("%H:%M:%S.%f")[:-3]

            # Get time-based multipliers for speed and vehicle count
            speed_mult, vehicle_mult = get_time_multipliers(current_hour)
            
            # Calculate adjusted vehicle count
            base_vehicle_count = random.randint(1, 5)
            adjusted_count = max(1, round(base_vehicle_count * vehicle_mult))

            rec = SensorRecord(
                pgmid=sensor_id,
                vehicle_count=adjusted_count,
                pepkspeed=round(sample_peakspeed(current_hour), 2),
                timestamp=ts,
                location=f"{LOCATION_LAT},{LOCATION_LONG}",
            )
            yield rec
            i += 1
            if num_records != -1 and i >= num_records:
                break
            time.sleep(interval)


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic traffic sensor data")
    parser.add_argument("num_records", nargs="?", type=int, default=NUM_RECORDS,
                      help="Number of records to generate")
    parser.add_argument("--date", type=str,
                      help="Optional date to generate data for (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    base_time = None
    if args.date:
        try:
            base_time = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            print("Error: Date must be in YYYY-MM-DD format")
            sys.exit(1)
    
    for r in generate_records(args.num_records, base_time):
        print(r.to_json())
