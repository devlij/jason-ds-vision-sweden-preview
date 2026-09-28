#!/usr/bin/env python3
"""QC pre-flight for the Sweden gallery. Exits non-zero on any failure."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from composite_masters import CANVAS, assert_art50

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = (
    "real-time conditions",
    "photograph of",
    "captured on",
)
NEW_IDS = [f"SE-01-{n:03d}" for n in range(2, 11)]
NIGHT_IDS = [f"SE-01-{n:03d}" for n in range(11, 20)]
LATE_IDS = [f"SE-01-{n:03d}" for n in range(20, 29)]
EXPECTED_IDS = ["SE-01-001", *NEW_IDS, *NIGHT_IDS, *LATE_IDS]
# Hashes locked when SE-01-001 was approved. This batch must not touch them.
SE001_SHA = {
    "16x9": "1a175723bb5d4af5bff2ae470e58a59dcaa83953fd3261b5f3b5b030ad285db3",
    "4x5": "25810ce465b775fd5fad674cbeb5123eb55a5c76147893a6ed4d80f0d216944c",
    "9x16": "f155a695f8e90d56250cfeef2504e9152b7aa0776db05ebb65e8d0c055636a9a",
}
SE001_WEATHER_SHA = "b15db9903684cc310bdfa346251eb89d416e58916c7a1e317fca6dbfe0a54f6b"
SE001_RETRIEVAL = "2026-09-28T06:41:11+02:00"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def check_note(errors: list[str], entry_id: str, candidate: bool) -> str:
    note_path = ROOT / "approvals" / f"{entry_id}.md"
    if not note_path.is_file():
        errors.append(f"missing approvals/{entry_id}.md")
        return ""
    text = note_path.read_text()
    if candidate:
        if "approval_status: Candidate" not in text:
            errors.append(f"{entry_id} approval note is not Candidate")
        if re.search(r"approval_status:\s*Approved", text):
            errors.append(f"{entry_id} approval note self-approved")
    low = text.lower()
    for phrase in FORBIDDEN:
        if phrase in low:
            errors.append(f"{entry_id} approval note contains {phrase!r}")
    if "not a verified on-site observation" not in text:
        errors.append(f"{entry_id} approval note missing model-data wording")
    if "Model data from Open-Meteo, retrieved" not in text:
        errors.append(f"{entry_id} approval note missing retrieval wording")
    return text


def check_weather(errors: list[str], entry_id: str, stamps: set[str]) -> dict | None:
    path = ROOT / "evidence" / "weather" / f"{entry_id}.json"
    if not path.is_file():
        errors.append(f"missing weather {entry_id}")
        return None
    weather = json.loads(path.read_text())
    if weather.get("timezone") != "Europe/Stockholm":
        errors.append(f"{entry_id} weather timezone is not Europe/Stockholm")
    stamp = weather.get("retrieval_timestamp") or ""
    if stamp in stamps:
        errors.append(f"{entry_id} retrieval second collided: {stamp}")
    stamps.add(stamp)
    hour = stamp[11:13]
    scenario = weather.get("scenario_label") or ""
    if "·" not in scenario or not scenario.split("·", 1)[1].strip().startswith(hour):
        errors.append(f"{entry_id} scenario hour is outside the retrieval hour")
    if (weather.get("model_valid_hour_start") or "")[11:13] != hour:
        errors.append(f"{entry_id} model-valid hour does not contain the scenario hour")
    return weather


def check_masters(errors: list[str], entry_id: str, note: str) -> None:
    for fmt, size in CANVAS.items():
        path = ROOT / "assets" / "sweden" / "Stockholm" / f"{entry_id.lower()}-{fmt}.png"
        if not path.is_file():
            errors.append(f"missing master {path}")
            continue
        with Image.open(path) as im:
            if im.size != size:
                errors.append(f"bad size {path.name} {im.size}")
        try:
            assert_art50(path)
        except SystemExit as err:
            errors.append(str(err))
        if note and sha256(path) not in note:
            errors.append(f"{entry_id} approval note missing sha256 for {fmt}")


def main() -> None:
    errors: list[str] = []
    data = json.loads((ROOT / "data.json").read_text())
    scenes = data["scenes"]
    ids = [scene.get("entry_id") for scene in scenes]
    if ids != EXPECTED_IDS:
        errors.append(f"data.json scene order is {ids}")
    by_id = {scene.get("entry_id"): scene for scene in scenes}

    sv = json.loads((ROOT / "tools" / "sv.json").read_text())
    if sv != []:
        errors.append("tools/sv.json must stay an empty array until Cosmo delivers entries")

    note_001 = check_note(errors, "SE-01-001", candidate=False)
    if note_001 and "approval_status: Approved" not in note_001:
        errors.append("SE-01-001 approval note lost its Approved status")
    weather_001_path = ROOT / "evidence" / "weather" / "SE-01-001.json"
    if sha256(weather_001_path) != SE001_WEATHER_SHA:
        errors.append("SE-01-001 weather file changed; do not re-fetch it")
    stamps: set[str] = set()
    weather_001 = check_weather(errors, "SE-01-001", stamps)
    if weather_001:
        if weather_001.get("retrieval_timestamp") != SE001_RETRIEVAL:
            errors.append("SE-01-001 retrieval timestamp changed")
        if weather_001.get("is_day") != 0:
            errors.append("SE-01-001 retrieval is_day is not 0")
        if weather_001["retrieval_timestamp"][11:16] >= weather_001["sunrise"][11:16]:
            errors.append("SE-01-001 retrieval is not before sunrise")
        if weather_001.get("daynight") != "night":
            errors.append("SE-01-001 daynight is not night")
    scene_001 = by_id.get("SE-01-001") or {}
    if scene_001.get("approval_status") != "Approved":
        errors.append("SE-01-001 approval_status must stay Approved")
    if scene_001.get("format_9x16_approval_status") == "Approved":
        errors.append("SE-01-001 9:16 must stay hidden until Jason clears it")
    for fmt, digest in SE001_SHA.items():
        path = ROOT / "assets" / "sweden" / "Stockholm" / f"se-01-001-{fmt}.png"
        if not path.is_file() or sha256(path) != digest:
            errors.append(f"SE-01-001 {fmt} master changed")
    if note_001:
        check_masters(errors, "SE-01-001", note_001)

    batch_path = ROOT / "approvals" / "BATCH-SE-01-002-010.txt"
    batch = batch_path.read_text() if batch_path.is_file() else ""
    if not batch_path.is_file():
        errors.append("missing approvals/BATCH-SE-01-002-010.txt")
    elif "backfill" not in batch.lower():
        errors.append("batch file missing the aerial backfill note")

    for entry_id in NEW_IDS:
        scene = by_id.get(entry_id) or {}
        if scene.get("approval_status") != "Candidate":
            errors.append(f"{entry_id} approval_status is not Candidate")
        if scene.get("format_9x16_approval_status") != "Candidate":
            errors.append(f"{entry_id} 9:16 approval is not Candidate")
        if scene.get("format_16x9_approval_status") == "Approved":
            errors.append(f"{entry_id} 16:9 was self-approved")
        if scene.get("format_4x5_approval_status") == "Approved":
            errors.append(f"{entry_id} 4:5 was self-approved")
        if scene.get("motion"):
            errors.append(f"{entry_id} motion is set without an aerial file")
        note = check_note(errors, entry_id, candidate=True)
        weather = check_weather(errors, entry_id, stamps)
        if weather:
            if weather.get("is_day") != 1 or weather.get("daynight") != "day":
                errors.append(f"{entry_id} weather is not genuine daylight")
            sunrise = weather.get("sunrise") or ""
            sunset = weather.get("sunset") or ""
            minute = (weather.get("retrieval_timestamp") or "")[11:16]
            if not (sunrise[11:16] <= minute < sunset[11:16]):
                errors.append(f"{entry_id} retrieval is outside the daylight window")
        check_masters(errors, entry_id, note)
        if batch and entry_id not in batch:
            errors.append(f"batch file missing {entry_id}")

    night_batch_path = ROOT / "approvals" / "BATCH-SE-01-011-019.txt"
    night_batch = night_batch_path.read_text() if night_batch_path.is_file() else ""
    if not night_batch_path.is_file():
        errors.append("missing approvals/BATCH-SE-01-011-019.txt")
    elif "night scenes do not get an aerial" not in night_batch.lower():
        errors.append("night batch file missing the no-aerial note")

    late_batch_path = ROOT / "approvals" / "BATCH-SE-01-020-028.txt"
    late_batch = late_batch_path.read_text() if late_batch_path.is_file() else ""
    if not late_batch_path.is_file():
        errors.append("missing approvals/BATCH-SE-01-020-028.txt")
    elif "night scenes do not get an aerial" not in late_batch.lower():
        errors.append("late batch file missing the no-aerial note")

    for entry_id in [*NIGHT_IDS, *LATE_IDS]:
        scene = by_id.get(entry_id) or {}
        if scene.get("approval_status") != "Candidate":
            errors.append(f"{entry_id} approval_status is not Candidate")
        if scene.get("format_9x16_approval_status") != "Candidate":
            errors.append(f"{entry_id} 9:16 approval is not Candidate")
        if scene.get("format_16x9_approval_status") == "Approved":
            errors.append(f"{entry_id} 16:9 was self-approved")
        if scene.get("format_4x5_approval_status") == "Approved":
            errors.append(f"{entry_id} 4:5 was self-approved")
        if scene.get("motion"):
            errors.append(f"{entry_id} motion is set without an aerial file")
        note = check_note(errors, entry_id, candidate=True)
        if note and "night scenes do not get an aerial" not in note.lower():
            errors.append(f"{entry_id} approval note missing the night aerial refusal")
        weather = check_weather(errors, entry_id, stamps)
        if weather:
            if weather.get("is_day") != 0 or weather.get("daynight") != "night":
                errors.append(f"{entry_id} weather is not genuine night")
            sunset = weather.get("sunset") or ""
            minute = (weather.get("retrieval_timestamp") or "")[11:16]
            if minute < sunset[11:16]:
                errors.append(f"{entry_id} retrieval is not after sunset")
        check_masters(errors, entry_id, note)
        batch = night_batch if entry_id in NIGHT_IDS else late_batch
        batch_name = "night" if entry_id in NIGHT_IDS else "late"
        if batch and entry_id not in batch:
            errors.append(f"{batch_name} batch file missing {entry_id}")
        scene_line = ""
        if batch:
            for line in batch.splitlines():
                if line.startswith(entry_id + " "):
                    scene_line = line
                    break
            if not scene_line:
                errors.append(f"{batch_name} batch file missing a scene line for {entry_id}")
            else:
                idx = batch.find(scene_line)
                nxt = batch.find("\nSE-01-", idx + len(scene_line))
                block = batch[idx:nxt if nxt > idx else None]
                if "aerial: no" not in block.lower():
                    errors.append(f"{entry_id} batch line is not aerial no")

    html = (ROOT / "index.html").read_text()
    if "Download 9:16" in html.split("const SCENES")[0]:
        errors.append("static markup exposes a 9:16 download")
    if ">Sweden<" not in html or 'aria-current="page"' not in html:
        errors.append("Sweden is not marked current")
    if "G-PDJ4WSS725" not in html:
        errors.append("GA4 id missing")
    if "https://sweden.jdvision.org/" not in html:
        errors.append("Sweden canonical missing")
    for entry_id in [*NEW_IDS, *NIGHT_IDS, *LATE_IDS]:
        start = html.find(f'"entry_id": "{entry_id}"')
        if start < 0:
            errors.append(f"{entry_id} missing from index.html")
            continue
        end = html.find('"entry_id":', start + 10)
        chunk = html[start:end if end > start else start + 2500]
        if '"approval_status": "Approved"' in chunk:
            errors.append(f"{entry_id} is Approved in index.html")
        if '"format_9x16_approval_status": "Approved"' in chunk:
            errors.append(f"{entry_id} 9:16 is Approved in index.html")

    cname = (ROOT / "CNAME").read_text().strip()
    if cname != "sweden.jdvision.org":
        errors.append(f"CNAME is {cname!r}")
    if errors:
        print("\n".join(errors))
        raise SystemExit(f"{len(errors)} qc failures")
    print("qc preflight ok")


if __name__ == "__main__":
    main()
