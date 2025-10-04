"""MySQL writer for sensor records.

This file exposes a simple function `write_record_to_db(record)` which attempts to connect
and insert a row into a `sensor_readings` table. It reads DB credentials from env vars.

If `DB_WRITE` in the env is false, the writer will operate in dry-run mode and only log what it would do.
"""
from __future__ import annotations
import os
import logging
from typing import Optional

import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv

load_dotenv()

DB_WRITE = os.getenv("DB_WRITE", "false").lower() == "true"
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "capstone_db")

logger = logging.getLogger("db_writer")
logging.basicConfig(level=logging.INFO)

create_table_sql = """
CREATE TABLE IF NOT EXISTS sensor_readings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    pgmid VARCHAR(32),
    vehicle_count INT,
    pepkspeed DOUBLE,
    timestamp VARCHAR(64),
    location POINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
"""

insert_sql = "INSERT INTO sensor_readings (pgmid, vehicle_count, pepkspeed, timestamp, location) VALUES (%s,%s,%s,%s,POINT(%s,%s))"


def get_connection():
    if not DB_WRITE:
        logger.info("DB_WRITE is false; not creating a DB connection (dry-run).")
        return None
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            ssl_disabled=False,
        )
        return conn
    except mysql.connector.Error as err:
        logger.error(f"DB connection error: {err}")
        return None


def ensure_table(conn) -> None:
    if conn is None:
        logger.info("No DB connection; skipping table creation (dry-run).")
        return
    cur = conn.cursor()
    cur.execute(create_table_sql)
    conn.commit()
    cur.close()


def write_record_to_db(rec: dict) -> bool:
    """Attempt to write record (dict) to DB. Returns True on success or dry-run logging."""
    conn = get_connection()
    if conn is None:
        logger.info(f"Dry-run: would write record: {rec}")
        return True

    try:
        ensure_table(conn)
        cur = conn.cursor()
        lat, lon = map(float, rec["location"].split(","))
        cur.execute(insert_sql, (rec["pgmid"], rec["vehicle_count"], rec["pepkspeed"], rec["timestamp"], lat, lon))
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Wrote record to DB")
        return True
    except mysql.connector.Error as err:
        logger.error(f"Error writing to DB: {err}")
        return False
