# python_to_sql

Simulates real-time sensor data and writes to MySQL (or dry-run mode).

Setup

1. Create a virtualenv and install dependencies:

   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Copy `.env.example` to `.env` and edit credentials. Set `DB_WRITE=true` to enable actual DB writes.

Usage

- Dry run (no DB writes):

   python runner.py 100

- With DB writes enabled (after your IP is allowed in remote DB):

   Set DB_WRITE=true in `.env` and run:

   python runner.py 100

Notes

- The generator uses a normal distribution for `pepeakspeed` around a configurable mean (default 40) with stddev 5.
- If you can't connect to the remote DB yet, the program will log the inserts it would perform.

CSV output

By default the project appends every generated record to `data/sensor_readings.csv` (controlled by `CSV_WRITE` and `CSV_PATH` in `.env`). This gives you an immediate, local copy of what would be written to the DB. To disable CSV output, set `CSV_WRITE=false` in `.env`.

Current behavior (what the programs do right now)

- `generator.py` produces simulated sensor readings at the rate in `RECORDS_PER_SECOND`.
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
