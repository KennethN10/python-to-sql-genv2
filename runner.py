"""Runner that ties generator and DB writer together.

Usage:
  python runner.py [num_records]

It will generate records and attempt to write them into DB (or dry-run if DB_WRITE=false).
"""
from __future__ import annotations
import json
import logging
import sys
import time ## added to measure time
from db_writer import write_record_to_db
from csv_writer import write_record_to_csv

## only have one of these active at a time
## from generator import generate_records
from generator_v2 import generate_records


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("runner")


def main(num_records: int = -1):
    total_db_time = 0  ## added to track db transfer time
    i = 0
    for rec in generate_records(num_records):
        j = json.loads(rec.to_json())

        # Always write to CSV for local inspection first
        csv_ok = write_record_to_csv(j)
        if not csv_ok:
            logger.error("CSV write failed; stopping")
            break

        ## Measure only DB write duration
        start_db = time.time()  ## added to start timing
        success = write_record_to_db(j)
        db_elapsed = time.time() - start_db  ## added to end timing
        total_db_time += db_elapsed  ## accumulate DB transfer time

        if not success:
            logger.error("Stopping due to DB write failure")
            break
        i += 1

    # ## After loop, show total and average DB write times
    if i > 0:
        avg_db_time = total_db_time / i
      ##  logger.info(f"✅ Wrote {i} records.")  
        logger.info(f"⏱️ Total DB transfer time: {total_db_time:.4f} sec")
        logger.info(f"⚙️ Average DB write time per record: {avg_db_time:.4f} sec")


if __name__ == "__main__":
    n = -1
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except Exception:
            pass
    main(n)
