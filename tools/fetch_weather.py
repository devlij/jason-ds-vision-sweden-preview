#!/usr/bin/env python3
"""One fresh Open-Meteo retrieval per scene. Never batch-share a timestamp.

Existing evidence files are kept. This script does not refresh SE-01-001.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "weather"
MONTHS = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# Later scenes append here. Do not re-list a scene that already has a file.
# Pins are the public viewpoint, not a surveyed tripod mark.
SCENES: list[tuple[str, str, str, float, float, str]] = [
    ("SE-01-001", "Royal Palace", "Stockholm", 59.32555, 18.07105, "Europe/Stockholm"),
    ("SE-01-002", "Vasa Museum", "Stockholm", 59.32830, 18.09140, "Europe/Stockholm"),
    ("SE-01-003", "City Hall", "Stockholm", 59.32690, 18.05620, "Europe/Stockholm"),
    ("SE-01-004", "Stortorget", "Stockholm", 59.32505, 18.07085, "Europe/Stockholm"),
    ("SE-01-005", "Nordic Museum", "Stockholm", 59.32860, 18.09370, "Europe/Stockholm"),
    ("SE-01-006", "Monteliusvägen", "Stockholm", 59.32155, 18.06105, "Europe/Stockholm"),
    ("SE-01-007", "Kungsträdgården", "Stockholm", 59.33055, 18.07175, "Europe/Stockholm"),
    ("SE-01-008", "Riddarholmen", "Stockholm", 59.32430, 18.06420, "Europe/Stockholm"),
    ("SE-01-009", "Skansen", "Stockholm", 59.32670, 18.10440, "Europe/Stockholm"),
    ("SE-01-010", "Strandvägen", "Stockholm", 59.33210, 18.08240, "Europe/Stockholm"),
    # SE-01-011–037 live on other drafts and are not in this checkout.
    # Pins below are public viewpoints, not surveyed tripod marks.
    ("SE-01-038", "Stureplan", "Stockholm", 59.33680, 18.07315, "Europe/Stockholm"),
    ("SE-01-039", "Central Station", "Stockholm", 59.33015, 18.05690, "Europe/Stockholm"),
    ("SE-01-040", "Sofia Church", "Stockholm", 59.31255, 18.08540, "Europe/Stockholm"),
    ("SE-01-041", "Gustaf Vasa Church", "Stockholm", 59.34240, 18.04820, "Europe/Stockholm"),
    ("SE-01-042", "Oscar's Church", "Stockholm", 59.33485, 18.09320, "Europe/Stockholm"),
    ("SE-01-043", "Medborgarplatsen", "Stockholm", 59.31455, 18.07205, "Europe/Stockholm"),
    ("SE-01-044", "Maritime Museum", "Stockholm", 59.33240, 18.11540, "Europe/Stockholm"),
    ("SE-01-045", "Mårten Trotzigs gränd", "Stockholm", 59.32295, 18.07270, "Europe/Stockholm"),
    ("SE-01-046", "Rosenbad", "Stockholm", 59.32890, 18.06490, "Europe/Stockholm"),
]


def existing_stamps() -> set[str]:
    stamps = set()
    if not OUT.exists():
        return stamps
    for path in OUT.glob("SE-*.json"):
        data = json.loads(path.read_text())
        stamps.add(data["retrieval_timestamp"])
    return stamps


def fetch_one(
    entry_id: str,
    site: str,
    city: str,
    lat: float,
    lon: float,
    tz_name: str,
    stamps: set[str],
) -> dict:
    tz = ZoneInfo(tz_name)
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code,cloud_cover,wind_speed_10m,is_day,precipitation",
        "daily": "sunrise,sunset",
        "timezone": tz_name,
        "forecast_days": 1,
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    time.sleep(2.0)
    request_started = datetime.now(tz)
    req = urllib.request.Request(url, headers={"User-Agent": "jasons-vision-sweden/1.0"})
    body = None
    last_err: Exception | None = None
    for _attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                body = resp.read()
            break
        except Exception as err:
            last_err = err
            time.sleep(2.0)
    if body is None:
        raise SystemExit(f"{entry_id} Open-Meteo failed: {last_err}")
    retrieval = datetime.now(tz)
    stamp = retrieval.isoformat(timespec="seconds")
    if stamp in stamps:
        raise SystemExit(f"{entry_id} retrieval second collided: {stamp}")
    payload = json.loads(body)
    current = payload["current"]
    daily = payload["daily"]
    sunrise = daily["sunrise"][0]
    is_day = current["is_day"]
    daynight = "night" if is_day == 0 or stamp[11:16] < sunrise[11:16] else "day"
    record = {
        "entry_id": entry_id,
        "site": site,
        "city": city,
        "latitude": lat,
        "longitude": lon,
        "model_latitude": payload.get("latitude"),
        "model_longitude": payload.get("longitude"),
        "provider": "Open-Meteo",
        "retrieval_timestamp": stamp,
        "retrieval_display": (
            f"{retrieval.day} {MONTHS[retrieval.month]} {retrieval.year} "
            f"{retrieval.strftime('%H:%M:%S')} {tz_name}"
        ),
        "request_started": request_started.isoformat(timespec="seconds"),
        "model_time": current["time"],
        "model_interval_seconds": current.get("interval", 900),
        "timezone": payload.get("timezone", tz_name),
        "temperature_2m": current["temperature_2m"],
        "weather_code": current["weather_code"],
        "cloud_cover": current["cloud_cover"],
        "wind_speed_10m": current["wind_speed_10m"],
        "is_day": is_day,
        "precipitation": current["precipitation"],
        "sunrise": sunrise,
        "sunset": daily["sunset"][0],
        "model_valid_hour_start": retrieval.strftime("%Y-%m-%dT%H:00"),
        "scenario_label": (
            f"{retrieval.day} {MONTHS[retrieval.month]} {retrieval.year} · "
            f"{retrieval.strftime('%H:%M')} {tz_name}"
        ),
        "daynight": daynight,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{entry_id}.json").write_text(json.dumps(record, indent=2) + "\n")
    stamps.add(stamp)
    print(entry_id, stamp, "daynight", daynight, "code", record["weather_code"])
    return record


def main() -> None:
    stamps = existing_stamps()
    for row in SCENES:
        if (OUT / f"{row[0]}.json").exists():
            print(f"keep {row[0]}")
            continue
        fetch_one(*row, stamps)


if __name__ == "__main__":
    main()
