# 01_ingest_traffic.py
# Ingest Brussels Realtime Traffic Counts (1m, t1)
#
# Fetches the latest traverse-level vehicle counts from the Brussels traffic API
# and stores normalized rows in SQLite.
#
# Run from inside cron/ directory:
#   python 01_ingest_traffic.py

import os
import sys
import sqlite3
import requests
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# 1. CONFIG ##########################################

BASE_URL = "https://data.mobility.brussels/traffic/api/counts/"
BRUSSELS_METRO_ID = 948

SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR / "data"
DB_PATH = DATA_DIR / "traffic.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)

print("\n====================================================")
print("01_ingest_traffic.py")
print("====================================================")
print(f"   metro_id: {BRUSSELS_METRO_ID}")
print(f"   url:      {BASE_URL}")

# 2. FETCH DATA ######################################

resp = requests.get(BASE_URL, params={"request": "live", "includeLanes": "false", "interval": "1"})
if resp.status_code != 200:
    print(f"   ERROR: Brussels traffic API failed with status {resp.status_code}", file=sys.stderr)
    sys.exit(1)

body = resp.json()
if not body.get("data"):
    print("   ERROR: Brussels traffic API returned empty data payload", file=sys.stderr)
    sys.exit(1)

monitors = body["data"]
print(f"   monitors in payload: {len(monitors)}")

# 3. CLEAN DATA ######################################

BXL_TZ = ZoneInfo("Europe/Brussels")

def parse_bxl_time(raw: str) -> str | None:
    if not raw:
        return None
    try:
        # API returns "YYYY-MM-DDTHH:MM" or "YYYY-MM-DD HH:MM"
        for fmt in ("%Y/%m/%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
            try:
                naive = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue
        else:
            return None
        local = naive.replace(tzinfo=BXL_TZ)
        utc = local.astimezone(timezone.utc)
        return utc.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

rows = []
for monitor_id, payload in monitors.items():
    try:
        one_min = payload.get("results", {}).get("1m", {})
        t1 = one_min.get("t1", {}) if one_min else {}
        vehicles = t1.get("count")
        speed = t1.get("speed")
        occupancy = t1.get("occupancy")
        end_time_raw = str(t1.get("end_time", ""))

        if vehicles is None:
            continue

        observed_at = parse_bxl_time(end_time_raw)
        if observed_at is None:
            continue

        try:
            vehicles = int(vehicles)
        except (ValueError, TypeError):
            continue

        try:
            speed = float(speed) if speed is not None else None
            if speed is not None and speed < 0:
                speed = 0.0
        except (ValueError, TypeError):
            speed = None

        try:
            occupancy = float(occupancy) if occupancy is not None else None
        except (ValueError, TypeError):
            occupancy = None

        rows.append({
            "metro_id": BRUSSELS_METRO_ID,
            "monitor_id": monitor_id,
            "observed_at": observed_at,
            "vehicles": vehicles,
            "speed": speed,
            "occupancy": occupancy,
        })
    except Exception:
        continue

if not rows:
    print("   ERROR: No valid 1m/t1 monitor rows parsed from Brussels API payload", file=sys.stderr)
    sys.exit(1)

print(f"   parsed rows: {len(rows)}")
for r in rows[:3]:
    print(f"      {r}")

# 4. WRITE TO SQLITE ##################################

db = sqlite3.connect(DB_PATH)
db.execute("""
    CREATE TABLE IF NOT EXISTS traffic (
        metro_id    INTEGER,
        monitor_id  TEXT,
        observed_at TEXT,
        vehicles    INTEGER,
        speed       REAL,
        occupancy   REAL,
        PRIMARY KEY (metro_id, monitor_id, observed_at)
    )
""")
db.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_traffic_metro_monitor_observed
    ON traffic (metro_id, monitor_id, observed_at)
""")
db.commit()

before_count = db.execute(
    "SELECT COUNT(*) FROM traffic WHERE metro_id = ?", (BRUSSELS_METRO_ID,)
).fetchone()[0]

db.executemany("""
    INSERT INTO traffic (metro_id, monitor_id, observed_at, vehicles, speed, occupancy)
    VALUES (:metro_id, :monitor_id, :observed_at, :vehicles, :speed, :occupancy)
    ON CONFLICT(metro_id, monitor_id, observed_at) DO NOTHING
""", rows)
db.commit()

total_rows = db.execute(
    "SELECT COUNT(*) FROM traffic WHERE metro_id = ?", (BRUSSELS_METRO_ID,)
).fetchone()[0]
db.close()

inserted_rows = max(total_rows - before_count, 0)

# 5. VERIFY ##########################################
print(f"   candidate rows this run: {len(rows)}")
print(f"   new rows appended:       {inserted_rows}")
print(f"   total rows (metro):      {total_rows}")
