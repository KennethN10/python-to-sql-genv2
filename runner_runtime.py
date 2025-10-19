"""
Runtime-based runner that ties generator and DB writer together.

Usage:
  python runner_runtime.py --duration 120
  (Runs for 120 seconds, generating and writing records continuously)

Optional arguments:
  --rate <records_per_sec>   Throttle record generation (default: 0 = unlimited)
  --progress <seconds>       How often to log progress (default: 5s)
"""

from __future__ import annotations
import json
import logging
import argparse
import signal
import sys
import time
from generator import generate_records
from db_writer import write_record_to_db
from csv_writer import write_record_to_csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("runner_runtime")

# Graceful shutdown flag (so Ctrl+C stops cleanly)
_stop = False
def handle_exit(signum, frame):
    global _stop
    _stop = True

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

def main(duration: float, rate: float = 0.0, progress_interval: float = 5.0):
    """Run generator for a fixed duration instead of fixed record count."""
    total_db_time = 0.0
    i = 0

    start_time = time.perf_counter()
    next_log = start_time + progress_interval
    next_tick = start_time  # for rate control
    interval = 1.0 / rate if rate > 0 else 0.0

    logger.info(f"Starting runtime mode for {duration:.1f} seconds")
    logger.info(f"Target rate: {'unlimited' if rate <= 0 else f'{rate} rec/s'}")

    for rec in generate_records(-1):  # generator keeps yielding until we stop
        if _stop:
            logger.info("Stop signal received, exiting loop.")
            break

        now = time.perf_counter()
        if now - start_time >= duration:
            logger.info("Reached duration limit.")
            break

        # Rate control (optional pacing)
        if rate > 0 and now < next_tick:
            time.sleep(next_tick - now)
        next_tick += interval

        j = json.loads(rec.to_json())

        # Always write to CSV
        csv_ok = write_record_to_csv(j)
        if not csv_ok:
            logger.error("CSV write failed; stopping.")
            break

        # Time DB write
        start_db = time.time()
        success = write_record_to_db(j)
        db_elapsed = time.time() - start_db
        total_db_time += db_elapsed

        if not success:
            logger.error("Stopping due to DB write failure.")
            break

        i += 1

        # Periodic progress logging
        if time.perf_counter() >= next_log:
            elapsed = time.perf_counter() - start_time
            rate_now = i / elapsed if elapsed > 0 else 0
            logger.info(f"[progress] Records={i}, Elapsed={elapsed:.1f}s, Rate≈{rate_now:.1f} rec/s")
            next_log = time.perf_counter() + progress_interval

    # Final summary
    if i > 0:
        avg_db_time = total_db_time / i
        total_elapsed = time.perf_counter() - start_time
        logger.info("Run complete.")
        logger.info(f"Records written: {i}")
        logger.info(f"Total elapsed time: {total_elapsed:.2f} sec")
        logger.info(f"Average DB write time per record: {avg_db_time:.4f} sec")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run generator for fixed duration.")
    parser.add_argument("--duration", type=float, required=True,
                        help="Runtime in seconds (e.g. 120 for 2 minutes)")
    parser.add_argument("--rate", type=float, default=0.0,
                        help="Optional target rate in records/sec (0 = unlimited)")
    parser.add_argument("--progress", type=float, default=5.0,
                        help="How often to print progress (seconds)")
    args = parser.parse_args()

    try:
        main(duration=args.duration, rate=args.rate, progress_interval=args.progress)
    except KeyboardInterrupt:
        logger.warning("Interrupted by user.")
