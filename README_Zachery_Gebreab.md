# Capstone Python → SQL Runtime Pipeline

This repository contains the runtime-based data ingestion system for our Capstone project. It generates simulated data streams and stores them in MySQL, designed for performance testing, scalability analysis, and eventual real-time dashboard integration.

---

## 🚀 New Feature — Runtime-Based Pipeline (`runner_runtime.py`)

**Author:** Zachery Gebreab

This new module introduces a **runtime-controlled data ingestion mode** that executes for a fixed duration rather than a fixed number of records.  
It is designed to simulate continuous real-world data streaming for performance testing and scalability evaluation.

### 🧠 Key Features
- **Runtime Parameterization:**  
  Script accepts a `--duration` argument (in seconds) to control total execution time.
- **Continuous Record Generation:**  
  Records are generated dynamically via the same data schema used in `generator.py`.
- **Performance Tracking:**  
  Logs total runtime, records written, and **average DB write time per record**.
- **CSV + MySQL Output:**  
  Each generated record is written both to a local CSV file and to the MySQL database for redundancy and verification.
- **Mac Sleep Protection:**  
  Verified stable long-duration runs (15–20 minutes) using `caffeinate` to prevent macOS sleep.
- **Scalability Validation:**  
  Demonstrated consistent insert performance across increasing durations (60s, 900s, 1200s), confirming system stability.

### ⚙️ Example Usage
Run for 15 minutes:
```bash
caffeinate python runner_runtime.py --duration 900
```

Run for 1 minute:
```bash
python runner_runtime.py --duration 60
```

### 📈 Next Steps
- Implement **batch insert mode** (`executemany()` in `db_writer.py`) for faster throughput.
- Add `--mode batch` CLI flag to toggle between normal and batch pipelines.
- Extend logging to include throughput (records/sec) trend graphs post-run.

---

## 🧩 Code Updates and Additions — Zachery Gebreab

## lines commented with double hashtags are where I made some changes

### 🗂️ Modified Files
The following existing files were updated to improve runtime diagnostics, logging clarity, and database performance tracking.

#### **runner.py**
- Added **execution timing** using the `time` module to measure database write durations per record.
- Implemented **aggregate performance metrics**, including:
  - Total database transfer time
  - Average DB write time per record
- Introduced new `##`-tagged comments to improve readability and indicate added performance-tracking sections.
- Adjusted loop logging to include cumulative timing summaries at the end of the run.

#### **db_writer.py**
- Added structured `logger` usage for consistent, centralized DB operation feedback.
- Enhanced reliability handling for failed inserts (with proper rollback logic).
- Improved readability with clear comment markers (`##`) identifying each functional block (connection, insert, close).
- Verified compatibility with both single-record inserts and upcoming batch-mode integration.

#### **generator.py**
- Added inline documentation (`##`) clarifying data structure creation and record composition.
- Standardized output record formatting to align with downstream JSON serialization used by the `runner` and `db_writer` modules.
- Confirmed consistent schema across both CSV and MySQL output paths.

---

### 🧠 Summary
These updates make the system easier to test, benchmark, and expand.  
Key impacts:
- Clearer insight into DB write performance.
- Better maintainability via consistent logging and comments.
- Seamless compatibility for the transition to the **runtime-based pipeline (`runner_runtime.py`)**.

Author: **Zachery Gebreab**

---

## 🧪 Update — October 2025 (A/B Testing & Data Realism)

**Author:** Zachery Gebreab  

This update introduces **`generator_v2.py`** and **enhanced runner integration** to support A/B testing between the original random data generator and a new, more realistic data simulation model.

### 🔄 New Files
- **`generator_v2.py`** – Generates more realistic traffic data:  
  - Each PMGID now produces 3–5 readings per cycle to simulate multiple cars per sensor.  
  - Locations are grouped to represent specific road segments rather than purely random coordinates.  
  - Framework ready for future modeling of time-dependent speed patterns (e.g., slower speeds during rush hours).  

### ⚙️ Runner Integration
- Both **`runner.py`** and **`runner_runtime.py`** now support toggling between data generators:
  ```python
  ## only have one of these active at a time
  ## from generator import generate_records
  from generator_v2 import generate_records

