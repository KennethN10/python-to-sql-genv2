"""Runner that ties generator and DB writer together.

Usage:
  python runner.py [num_records]

It will generate records and attempt to write them into DB (or dry-run if DB_WRITE=false).
"""
from __future__ import annotations
import json
import logging
import sys
from generator import generate_records
from db_writer import write_record_to_db
from csv_writer import write_record_to_csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("runner")


def main(num_records: int = -1):
    i = 0
    for rec in generate_records(num_records):
        j = json.loads(rec.to_json())
        # Always write to CSV for local inspection first
        csv_ok = write_record_to_csv(j)
        if not csv_ok:
            logger.error("CSV write failed; stopping")
            break

        # Then attempt DB write (may be dry-run)
        success = write_record_to_db(j)
        if not success:
            logger.error("Stopping due to DB write failure")
            break
        i += 1


if __name__ == "__main__":
    n = -1
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except Exception:
            pass
    main(n)
