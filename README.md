# python_to_sql

Simulates real-time sensor data and writes to MySQL (or dry-run mode).

## Enhanced Generator (generator_v2.py)

Major improvements have been implemented in `generator_v2.py` to provide more realistic traffic data:

### 1. Time-Based Traffic Distribution
- **Rush Hour Simulation**
  - Morning: 7-9 AM
  - Lunch: 11AM-1PM
  - Evening: 4-6PM
- **Smart Data Distribution**
  - 50% during rush hours (6 hours)
  - 30% during business hours (6 hours)
  - 15% during evening (4 hours)
  - 5% during overnight (8 hours)

### 2. Dynamic Traffic Patterns
- **Rush Hours**
  - Speeds reduced to 60-80% of normal
  - Vehicle counts increased by 150-200%
- **Late Night (11PM-5AM)**
  - Speeds increased to 110-120%
  - Vehicle counts reduced to 30-50%
- **Normal Hours**
  - Standard variations (90-110%)

### 3. Enhanced Sensor Network
- Expanded from single sensor to 10,000 unique sensors
- Each sensor generates 2-5 readings in bursts
- Maintains chronological order within batches

### 4. New Features
- Date-specific data generation (--date option)
- Synthetic timestamp generation
- Configurable time period weights

### Comparison with Original Generator
| Feature | generator.py | generator_v2.py |
|---------|-------------|-----------------|
| Sensors | Single fixed | 10,000 rotating |
| Timing | Real-time only | 24-hour distribution |
| Speed | Random normal | Time-based patterns |
| Vehicle Count | Fixed | Dynamic by time |
| Data Pattern | Random | Time-based realistic |

### Switching Between Generators

To change which generator is used:

1. In `runner.py`:
```python
# Comment/uncomment the desired import:
from generator_v2 import generate_records  # Enhanced version
# from generator import generate_records   # Original version
```

2. Data compatibility:
- Both generators produce identical field structures
- Database schema remains the same
- CSV format is unchanged
- Only the patterns and distributions differ

Setup

1. Create a virtualenv and install dependencies:

   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Copy `.env.example` to `.env` and edit credentials. Set `DB_WRITE=true` to enable actual DB writes.

Usage

### Using Enhanced Generator (Recommended)
```bash
# Generate 100 records with time-based patterns
python runner.py 100    # Uses generator_v2.py by default

# Generate data for specific date
python generator_v2.py 1000 --date 2025-10-27

# Run for duration with progress updates
python runner_runtime.py --duration 120 --progress 30
```

Example output (generator_v2):
```json
// Morning rush hour (8 AM) - higher vehicle count, lower speed
{"pgmid": "PMG02961", "vehicle_count": 8, "pepkspeed": 28.5, "timestamp": "08:15:37.919"}

// Late night (2 AM) - lower vehicle count, higher speed
{"pgmid": "PMG02961", "vehicle_count": 2, "pepkspeed": 45.2, "timestamp": "02:10:22.347"}
```

### Using Original Generator
```bash
# Basic generation (no time patterns)
python runner.py 100 --use-original    # Uses generator.py

# With DB writes enabled
export DB_WRITE=true
python runner.py 100 --use-original
```

Notes

- The generator uses a normal distribution for `pepeakspeed` around a configurable mean (default 40) with stddev 5.
- If you can't connect to the remote DB yet, the program will log the inserts it would perform.

CSV output

By default the project appends every generated record to `data/sensor_readings.csv` (controlled by `CSV_WRITE` and `CSV_PATH` in `.env`). This gives you an immediate, local copy of what would be written to the DB. To disable CSV output, set `CSV_WRITE=false` in `.env`.

Current behavior (what the programs do right now)

- `generator_v2.py` (recommended) produces realistic traffic data with time-based patterns, multiple sensors, and configurable distribution across 24 hours.
- `generator.py` (original) produces basic simulated sensor readings at the rate in `RECORDS_PER_SECOND`.
- `csv_writer.py` appends each generated record to the CSV at `CSV_PATH` for local inspection. A header row is written once when the file is created.
- `db_writer.py` will attempt to connect to the MySQL database only when `DB_WRITE=true` in `.env`. By default it is `false` so the program logs the write action instead of attempting a network connection (useful while your IP is being whitelisted).
- `runner.py` coordinates generation, CSV write, and DB write (CSV first, then DB). It accepts an optional integer argument (number of records) or reads `NUM_RECORDS` from `.env`.

Quick checklist to run locally

1. Create and activate a virtualenv, then install dependencies:

   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Copy the env template and inspect it (DO NOT commit `.env`):

   cp .env.example .env
   # edit .env if you want different rates/counts or to enable DB writes

3. Run a short dry-run to produce CSV and see logs:

   python runner.py 100

4. When your IP is whitelisted and you want to push to the remote DB:

   - set `DB_WRITE=true` in `.env`
   - confirm `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` are correct
   - run: python runner.py 100

Notes about GitHub push

The repository contains only code and `.env.example`. The `.env` file and `.venv/` are ignored via `.gitignore`. Below are the steps I attempted to run for you (and you can re-run locally if push requires credentials):

Create a new repo and push (replace URL with your repo):

   git init
   git add .
   git commit -m "Initial project: generator, CSV writer, DB writer, runner, README"
   git branch -M main
   git remote add origin https://github.com/johndutra1/python_to_sql.git
   git push -u origin main

If the remote already exists, set the URL then push:

   git remote set-url origin https://github.com/johndutra1/python_to_sql.git
   git push -u origin main

If push fails because of authentication, you'll need to: use an HTTPS PAT (personal access token) with `git push` or configure SSH keys and use an SSH remote URL. I tried to push from this environment; if it failed I included the error below in the run output so you can follow up locally.

That's it — the code is ready to be added to your GitHub repo. Let me know if you want me to also create a simple GitHub Actions workflow that runs a quick lint/test when you push.

CI (GitHub Actions)

[![CI](https://github.com/johndutra1/python_to_sql/actions/workflows/ci.yml/badge.svg)](https://github.com/johndutra1/python_to_sql/actions/workflows/ci.yml)

This repository includes a small GitHub Actions workflow (`.github/workflows/ci.yml`) that runs on push and pull requests to `main`. It:

- Tests on Python 3.11 and 3.12.
- Installs dependencies from `requirements.txt`.
- Executes a smoke run of the runner with writes disabled (it runs `python runner.py 1` with `DB_WRITE=false` and `CSV_WRITE=false`) to ensure imports and runtime start-up are OK.

This workflow is intentionally side-effect free (no DB connections, no CSV writes). It provides quick feedback that the code boots and basic dependencies are resolvable.

