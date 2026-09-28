#!/usr/bin/env python3
"""QC pre-flight for the Sweden starter. Exits non-zero on any failure."""

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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    errors: list[str] = []
    note = ROOT / "approvals" / "SE-01-001.md"
    weather_path = ROOT / "evidence" / "weather" / "SE-01-001.json"
    data = json.loads((ROOT / "data.json").read_text())
    scenes = data["scenes"]
    if len(scenes) != 1 or scenes[0]["entry_id"] != "SE-01-001":
        errors.append("data.json must contain only SE-01-001 at this seed")
    scene = scenes[0]
    if scene.get("approval_status") != "Candidate":
        errors.append("scene approval_status is not Candidate")
    if scene.get("format_9x16_approval_status") == "Approved":
        errors.append("9:16 must stay hidden until Jason clears it")
    sv = json.loads((ROOT / "tools" / "sv.json").read_text())
    if sv != []:
        errors.append("tools/sv.json must stay an empty array until Cosmo delivers entries")
    if not note.is_file():
        errors.append("missing approvals/SE-01-001.md")
    else:
        text = note.read_text()
        if "approval_status: Candidate" not in text:
            errors.append("approval note is not Candidate")
        if re.search(r"approval_status:\s*Approved", text):
            errors.append("approval note self-approved")
        low = text.lower()
        for phrase in FORBIDDEN:
            if phrase in low:
                errors.append(f"approval note contains {phrase!r}")
        if "not a verified on-site observation" not in text:
            errors.append("approval note missing model-data wording")
        if "Model data from Open-Meteo, retrieved" not in text:
            errors.append("approval note missing retrieval wording")
    weather = json.loads(weather_path.read_text())
    if weather["timezone"] != "Europe/Stockholm":
        errors.append("weather timezone is not Europe/Stockholm")
    if weather["is_day"] != 0:
        errors.append("SE-01-001 retrieval is_day is not 0")
    if weather["retrieval_timestamp"][11:16] >= weather["sunrise"][11:16]:
        errors.append("retrieval is not before sunrise")
    hour = weather["retrieval_timestamp"][11:13]
    if not weather["scenario_label"].split("·")[1].strip().startswith(hour):
        errors.append("scenario hour is outside the retrieval hour")
    if weather["model_valid_hour_start"][11:13] != hour:
        errors.append("model-valid hour does not contain the scenario hour")
    html = (ROOT / "index.html").read_text()
    if "Download 9:16" in html.split("const SCENES")[0]:
        errors.append("static markup exposes a 9:16 download")
    if ">Sweden<" not in html or 'aria-current="page"' not in html:
        errors.append("Sweden is not marked current")
    if "day-tab" in html and 'class="day-tab"' in html.split("function render")[1].split("grid.addEventListener")[0]:
        errors.append("day/night toggle button is rendered")
    for fmt, size in CANVAS.items():
        path = ROOT / "assets" / "sweden" / "Stockholm" / f"se-01-001-{fmt}.png"
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
        if note.is_file() and sha256(path) not in note.read_text():
            errors.append(f"approval note missing sha256 for {fmt}")
    cname = (ROOT / "CNAME").read_text().strip()
    if cname != "sweden.jdvision.org":
        errors.append(f"CNAME is {cname!r}")
    if errors:
        print("\n".join(errors))
        raise SystemExit(f"{len(errors)} qc failures")
    print("qc preflight ok")


if __name__ == "__main__":
    main()
