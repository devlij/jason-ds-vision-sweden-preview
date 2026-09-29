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
    ("SE-01-011", "Skeppsbron", "Stockholm", 59.32455, 18.07515, "Europe/Stockholm"),
    ("SE-01-012", "Fjällgatan", "Stockholm", 59.31720, 18.08440, "Europe/Stockholm"),
    ("SE-01-013", "Nationalmuseum", "Stockholm", 59.32800, 18.07820, "Europe/Stockholm"),
    ("SE-01-014", "Royal Opera", "Stockholm", 59.32920, 18.06940, "Europe/Stockholm"),
    ("SE-01-015", "Riksdagshuset", "Stockholm", 59.32745, 18.06630, "Europe/Stockholm"),
    ("SE-01-016", "af Chapman", "Stockholm", 59.32705, 18.08055, "Europe/Stockholm"),
    ("SE-01-017", "Norr Mälarstrand", "Stockholm", 59.32855, 18.04280, "Europe/Stockholm"),
    ("SE-01-018", "Stockholm Public Library", "Stockholm", 59.34340, 18.05480, "Europe/Stockholm"),
    ("SE-01-019", "Östermalms Saluhall", "Stockholm", 59.33660, 18.07790, "Europe/Stockholm"),
    ("SE-01-020", "Concert Hall", "Stockholm", 59.33490, 18.06280, "Europe/Stockholm"),
    ("SE-01-021", "Katarina Church", "Stockholm", 59.31690, 18.07740, "Europe/Stockholm"),
    ("SE-01-022", "Moderna Museet", "Stockholm", 59.32610, 18.08320, "Europe/Stockholm"),
    ("SE-01-023", "Olympic Stadium", "Stockholm", 59.34455, 18.07910, "Europe/Stockholm"),
    ("SE-01-024", "German Church", "Stockholm", 59.32410, 18.07205, "Europe/Stockholm"),
    ("SE-01-025", "House of Nobility", "Stockholm", 59.32570, 18.06620, "Europe/Stockholm"),
    ("SE-01-026", "Sergels Torg", "Stockholm", 59.33230, 18.06450, "Europe/Stockholm"),
    ("SE-01-027", "Waldemarsudde", "Stockholm", 59.31945, 18.11370, "Europe/Stockholm"),
    ("SE-01-028", "Kaknäs Tower", "Stockholm", 59.33440, 18.12640, "Europe/Stockholm"),
    # SE-01-029–037 merged 2026-09-28 (Cosmo QC).
    # Pins below are public viewpoints, not surveyed tripod marks.
    ("SE-01-029", "Högalid Church", "Stockholm", 59.31750, 18.03920, "Europe/Stockholm"),
    ("SE-01-030", "Royal Dramatic Theatre", "Stockholm", 59.33323, 18.07708, "Europe/Stockholm"),
    ("SE-01-031", "Köpmantorget", "Stockholm", 59.32572, 18.07355, "Europe/Stockholm"),
    ("SE-01-032", "Kastellet", "Stockholm", 59.32240, 18.08960, "Europe/Stockholm"),
    ("SE-01-033", "Royal Library", "Stockholm", 59.33820, 18.07240, "Europe/Stockholm"),
    ("SE-01-034", "Västerbron", "Stockholm", 59.32840, 18.02680, "Europe/Stockholm"),
    ("SE-01-035", "Woodland Cemetery", "Stockholm", 59.27550, 18.09820, "Europe/Stockholm"),
    ("SE-01-036", "Koppartälten", "Stockholm", 59.36420, 18.03220, "Europe/Stockholm"),
    ("SE-01-037", "Engelbrekt Church", "Stockholm", 59.34390, 18.06680, "Europe/Stockholm"),
    # Pins below are public viewpoints, not surveyed tripod marks.
    # SE-01-038–046 merged 2026-09-28 (Cosmo QC).
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
    # Pins below are public viewpoints, not surveyed tripod marks.
    # SE-01-047–055 merged 2026-09-28 (Cosmo QC).
    # Pins below are public viewpoints, not surveyed tripod marks.
    ("SE-01-047", "Katarinahissen", "Stockholm", 59.31990, 18.07255, "Europe/Stockholm"),
    ("SE-01-048", "Fotografiska", "Stockholm", 59.31785, 18.08515, "Europe/Stockholm"),
    ("SE-01-049", "Gröna Lund", "Stockholm", 59.32335, 18.09570, "Europe/Stockholm"),
    ("SE-01-050", "Storkyrkan", "Stockholm", 59.32540, 18.07055, "Europe/Stockholm"),
    ("SE-01-051", "Nordiska Kompaniet", "Stockholm", 59.33290, 18.06935, "Europe/Stockholm"),
    ("SE-01-052", "Södra Teatern", "Stockholm", 59.31845, 18.07385, "Europe/Stockholm"),
    ("SE-01-053", "Liljevalchs", "Stockholm", 59.32510, 18.09645, "Europe/Stockholm"),
    ("SE-01-054", "Stockholm Observatory", "Stockholm", 59.34155, 18.05475, "Europe/Stockholm"),
    ("SE-01-055", "Djurgårdsbron", "Stockholm", 59.33265, 18.09355, "Europe/Stockholm"),
    # SE-01-056–073 live on open drafts and are not in this checkout.
    # Pins below are public viewpoints, not surveyed tripod marks.
    ("SE-01-074", "Karlberg Palace", "Stockholm", 59.34111, 18.02194, "Europe/Stockholm"),
    ("SE-01-075", "Västerlånggatan", "Stockholm", 59.32440, 18.06915, "Europe/Stockholm"),
    ("SE-01-076", "Söder Mälarstrand", "Stockholm", 59.32040, 18.05800, "Europe/Stockholm"),
    ("SE-01-077", "Vanadis Reservoir", "Stockholm", 59.34887, 18.05491, "Europe/Stockholm"),
    ("SE-01-078", "Beckholmen", "Stockholm", 59.32073, 18.10095, "Europe/Stockholm"),
    ("SE-01-079", "Långholmen", "Stockholm", 59.32083, 18.02611, "Europe/Stockholm"),
    ("SE-01-080", "St. John's Church", "Stockholm", 59.33944, 18.06472, "Europe/Stockholm"),
    ("SE-01-081", "Kornhamnstorg", "Stockholm", 59.32286, 18.07101, "Europe/Stockholm"),
    ("SE-01-082", "Natural History Museum", "Stockholm", 59.36889, 18.05361, "Europe/Stockholm"),
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
