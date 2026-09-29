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
# SE-01-029–037 merged 2026-09-28 (Cosmo QC).
LATE2_IDS = [f"SE-01-{n:03d}" for n in range(29, 38)]
# SE-01-038–046 merged 2026-09-28 (Cosmo QC).
LATE3_IDS = [f"SE-01-{n:03d}" for n in range(38, 47)]
# SE-01-047–055 merged 2026-09-28 (Cosmo QC).
LATE4_IDS = [f"SE-01-{n:03d}" for n in range(47, 56)]
# SE-01-056–064 merged 2026-09-28 (Cosmo QC).
LATE5_IDS = [f"SE-01-{n:03d}" for n in range(56, 65)]
# SE-01-065–073 merged 2026-09-28 (Cosmo QC).
LATE6_IDS = [f"SE-01-{n:03d}" for n in range(65, 74)]
# SE-01-074–082 merged 2026-09-28 (Cosmo QC).
BATCH_IDS = [f"SE-01-{n:03d}" for n in range(74, 83)]
# SE-01-110–118 are this checkout. SE-01-083–109 stay on open drafts #11, #12, and #13.
PARTA_IDS = [f"SE-01-{n:03d}" for n in range(110, 119)]
# Cosmo already flipped these notes and the published index. data.json stays Candidate.
COSMO_IDS = {f"SE-01-{n:03d}" for n in list(range(29, 74)) + list(range(74, 83))}
# Main's scene order is the merge order, not numeric order. Do not reorder 001–082.
EXPECTED_IDS = (
    ["SE-01-001", *NEW_IDS, *NIGHT_IDS, *LATE_IDS]
    + BATCH_IDS
    + LATE2_IDS
    + LATE3_IDS
    + LATE4_IDS
    + LATE5_IDS
    + LATE6_IDS
    + PARTA_IDS
)
# Hashes locked when SE-01-001 was approved. This batch must not touch them.
SE001_SHA = {
    "16x9": "1a175723bb5d4af5bff2ae470e58a59dcaa83953fd3261b5f3b5b030ad285db3",
    "4x5": "25810ce465b775fd5fad674cbeb5123eb55a5c76147893a6ed4d80f0d216944c",
    "9x16": "f155a695f8e90d56250cfeef2504e9152b7aa0776db05ebb65e8d0c055636a9a",
}
SE001_WEATHER_SHA = "b15db9903684cc310bdfa346251eb89d416e58916c7a1e317fca6dbfe0a54f6b"
SE001_RETRIEVAL = "2026-09-28T06:41:11+02:00"
# Masters on origin/main for SE-01-002–010. This batch must not touch them.
MAIN_MASTER_SHA = {
    "SE-01-002": {
        "16x9": "e4bb4f3d4f3825730cdd52ce5c2332d75683e2e49c2d7e64ff3ed2a853203d59",
        "4x5": "0fa79324d33a87ced491a6b1338734692be991d95ab733b4ed55f32ab4effb24",
        "9x16": "96d1fffb4b3c02b498003e5c81df735220bff28605a9fd177472235c418124e2",
    },
    "SE-01-003": {
        "16x9": "cd88ff6f31e5201490f2bf4486eeee84a877d6d5abdad7403b2b2cc08ac7b960",
        "4x5": "9329bbdc87d43a5f3024a4fd2a263dd50390e12f96167a95042584d472b6aee0",
        "9x16": "0b3c2098ef44e0a9a100aa5e229ada7203bb0fe40acddacdc8a348b0f5d341bd",
    },
    "SE-01-004": {
        "16x9": "55cd86a2de111ae3e39e36169796dec4b9e9493b740ab39fc7ceedc29518b7a6",
        "4x5": "df68b733476933266a7d1a11ad2254d3f8496ba02fbc9f0f5a6a20c87fb39ace",
        "9x16": "1731f84870a83eefcdddd67cff0795746dccfc37199f72a6c2229cedb81e9801",
    },
    "SE-01-005": {
        "16x9": "08702cb07898ec1ef6e368eea04130341f4f38345414d30390bc97098154ee59",
        "4x5": "121e88ab166a7ebfe3ca3352430a2d277a4868fabb3644d294b8af05b0b303da",
        "9x16": "025ded58810e98dc00b586a399fca3c2cf5a476c7cc578bfb0a25f1f601affd0",
    },
    "SE-01-006": {
        "16x9": "519ec77d3920c1277d9f5be54ced9806aa5838a607d730d34842815396398b6c",
        "4x5": "642e8ae5d79b7aa828dedd99ff662a480533e1f0fd3f8e3fd26aa106cecd741d",
        "9x16": "b3e33ee6b049aecdb91c903678a7ba45f3539cacce631541185ed7f215b24a69",
    },
    "SE-01-007": {
        "16x9": "3abcb61d26db8a15a650b239986a6fd068af001b37dff8550c94e2a94d899cbc",
        "4x5": "949c0ea3fa0333364ed4bfe85610f6144a7fa78143f608fc85162f69c1275bab",
        "9x16": "337e2176432c003eb0cc66c6a481c3b689745ce7f644cdf2b4549d5024d7a1cb",
    },
    "SE-01-008": {
        "16x9": "b6f5f0c06f046e16518995bc59bf5253c755712223ed6e5dbcd4eb77168ec649",
        "4x5": "443e596ce2506c7d99c6d13e5fde785d2d464b17ffb6aa15a8fde095ecb128db",
        "9x16": "4fe9800cf7608b9aeb372636c8050b94587553ca56c6801a0df47238f8924b68",
    },
    "SE-01-009": {
        "16x9": "93467088835352ee60685948850331c31a13899fb9b0779fe5fb9cafa5b56b20",
        "4x5": "f0b52c297e80a294fd03f0554083b12ef5a0bfdc09647e51ea45dd9d302a9aa2",
        "9x16": "7e181a57a0cf3a0476c55bfee5f0a2f826073e56cf2b6b0931cb4ed0a161dc9a",
    },
    "SE-01-010": {
        "16x9": "56dc778e7c100239b123411d1f178440d5874f3f26dc4b31c772f71923a65385",
        "4x5": "e641dfb00686c45514d2a8086aac8666e2a74fc59fba51f187228711f8895887",
        "9x16": "baadcb2e68e1f8967085f38bd88560ce0fd2f1cb4149aee90d0040775ed79c49",
    },
}


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
        cosmo = (
            entry_id in COSMO_IDS
            and "Approved by Cosmo QC" in text
            and re.search(r"(?m)^approval_status:\s*Approved\s*$", text) is not None
        )
        if not cosmo:
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
        for fmt, digest in MAIN_MASTER_SHA.get(entry_id, {}).items():
            path = ROOT / "assets" / "sweden" / "Stockholm" / f"{entry_id.lower()}-{fmt}.png"
            if not path.is_file() or sha256(path) != digest:
                errors.append(f"{entry_id} {fmt} master changed versus main")

    late_batch_path = ROOT / "approvals" / "BATCH-SE-01-029-037.txt"
    late_batch = late_batch_path.read_text() if late_batch_path.is_file() else ""
    if not late_batch_path.is_file():
        errors.append("missing approvals/BATCH-SE-01-029-037.txt")
    elif "night scenes do not get an aerial" not in late_batch.lower():
        errors.append("late batch file missing the no-aerial note")

    for entry_id in LATE2_IDS:
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
        if late_batch and entry_id not in late_batch:
            errors.append(f"late batch file missing {entry_id}")
        scene_line = ""
        if late_batch:
            for line in late_batch.splitlines():
                if line.startswith(entry_id + " "):
                    scene_line = line
                    break
            if not scene_line:
                errors.append(f"late batch file missing a scene line for {entry_id}")
            else:
                idx = late_batch.find(scene_line)
                nxt = late_batch.find("\nSE-01-", idx + len(scene_line))
                block = late_batch[idx:nxt if nxt > idx else None]
                if "aerial: no" not in block.lower():
                    errors.append(f"{entry_id} batch line is not aerial no")

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

    batch74_path = ROOT / "approvals" / "BATCH-SE-01-074-082.txt"
    batch74 = batch74_path.read_text() if batch74_path.is_file() else ""
    if not batch74_path.is_file():
        errors.append("missing approvals/BATCH-SE-01-074-082.txt")
    elif "night scenes do not get an aerial" not in batch74.lower():
        errors.append("074 batch file missing the no-aerial note")

    for entry_id in BATCH_IDS:
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
        if batch74 and entry_id not in batch74:
            errors.append(f"074 batch file missing {entry_id}")
        scene_line = ""
        if batch74:
            for line in batch74.splitlines():
                if line.startswith(entry_id + " "):
                    scene_line = line
                    break
            if not scene_line:
                errors.append(f"074 batch file missing a scene line for {entry_id}")
            else:
                idx = batch74.find(scene_line)
                nxt = batch74.find("\nSE-01-", idx + len(scene_line))
                block = batch74[idx:nxt if nxt > idx else None]
                if "aerial: no" not in block.lower():
                    errors.append(f"{entry_id} batch line is not aerial no")

    late_batch_path = ROOT / "approvals" / "BATCH-SE-01-038-046.txt"
    late_batch = late_batch_path.read_text() if late_batch_path.is_file() else ""
    if not late_batch_path.is_file():
        errors.append("missing approvals/BATCH-SE-01-038-046.txt")
    elif "night scenes do not get an aerial" not in late_batch.lower():
        errors.append("late batch file missing the no-aerial note")

    for entry_id in LATE3_IDS:
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
        if late_batch and entry_id not in late_batch:
            errors.append(f"late batch file missing {entry_id}")
        scene_line = ""
        if late_batch:
            for line in late_batch.splitlines():
                if line.startswith(entry_id + " "):
                    scene_line = line
                    break
            if not scene_line:
                errors.append(f"late batch file missing a scene line for {entry_id}")
            else:
                idx = late_batch.find(scene_line)
                nxt = late_batch.find("\nSE-01-", idx + len(scene_line))
                block = late_batch[idx:nxt if nxt > idx else None]
                if "aerial: no" not in block.lower():
                    errors.append(f"{entry_id} batch line is not aerial no")

    late_batch_path = ROOT / "approvals" / "BATCH-SE-01-047-055.txt"
    late_batch = late_batch_path.read_text() if late_batch_path.is_file() else ""
    if not late_batch_path.is_file():
        errors.append("missing approvals/BATCH-SE-01-047-055.txt")
    elif "night scenes do not get an aerial" not in late_batch.lower():
        errors.append("late batch file missing the no-aerial note")

    for entry_id in LATE4_IDS:
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
        if late_batch and entry_id not in late_batch:
            errors.append(f"late batch file missing {entry_id}")
        scene_line = ""
        if late_batch:
            for line in late_batch.splitlines():
                if line.startswith(entry_id + " "):
                    scene_line = line
                    break
            if not scene_line:
                errors.append(f"late batch file missing a scene line for {entry_id}")
            else:
                idx = late_batch.find(scene_line)
                nxt = late_batch.find("\nSE-01-", idx + len(scene_line))
                block = late_batch[idx:nxt if nxt > idx else None]
                if "aerial: no" not in block.lower():
                    errors.append(f"{entry_id} batch line is not aerial no")

    late_batch_path = ROOT / "approvals" / "BATCH-SE-01-056-064.txt"
    late_batch = late_batch_path.read_text() if late_batch_path.is_file() else ""
    if not late_batch_path.is_file():
        errors.append("missing approvals/BATCH-SE-01-056-064.txt")
    elif "night scenes do not get an aerial" not in late_batch.lower():
        errors.append("late batch file missing the no-aerial note")

    for entry_id in LATE5_IDS:
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
        if late_batch and entry_id not in late_batch:
            errors.append(f"late batch file missing {entry_id}")
        scene_line = ""
        if late_batch:
            for line in late_batch.splitlines():
                if line.startswith(entry_id + " "):
                    scene_line = line
                    break
            if not scene_line:
                errors.append(f"late batch file missing a scene line for {entry_id}")
            else:
                idx = late_batch.find(scene_line)
                nxt = late_batch.find("\nSE-01-", idx + len(scene_line))
                block = late_batch[idx:nxt if nxt > idx else None]
                if "aerial: no" not in block.lower():
                    errors.append(f"{entry_id} batch line is not aerial no")

    batch65_path = ROOT / "approvals" / "BATCH-SE-01-065-073.txt"
    batch65 = batch65_path.read_text() if batch65_path.is_file() else ""
    if not batch65_path.is_file():
        errors.append("missing approvals/BATCH-SE-01-065-073.txt")
    elif "night scenes do not get an aerial" not in batch65.lower():
        errors.append("065 batch file missing the no-aerial note")

    for entry_id in LATE6_IDS:
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
        if batch65 and entry_id not in batch65:
            errors.append(f"065 batch file missing {entry_id}")
        scene_line = ""
        if batch65:
            for line in batch65.splitlines():
                if line.startswith(entry_id + " "):
                    scene_line = line
                    break
            if not scene_line:
                errors.append(f"065 batch file missing a scene line for {entry_id}")
            else:
                idx = batch65.find(scene_line)
                nxt = batch65.find("\nSE-01-", idx + len(scene_line))
                block = batch65[idx:nxt if nxt > idx else None]
                if "aerial: no" not in block.lower():
                    errors.append(f"{entry_id} batch line is not aerial no")

    batch110_path = ROOT / "approvals" / "BATCH-SE-01-110-118.txt"
    batch110 = batch110_path.read_text() if batch110_path.is_file() else ""
    if not batch110_path.is_file():
        errors.append("missing approvals/BATCH-SE-01-110-118.txt")
    elif "night scenes do not get an aerial" not in batch110.lower():
        errors.append("110 batch file missing the no-aerial note")

    for entry_id in PARTA_IDS:
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
            minute = (weather.get("retrieval_timestamp") or "")[11:16]
            sunrise = (weather.get("sunrise") or "9999-99-99T99:99")[11:16]
            sunset = (weather.get("sunset") or "")[11:16]
            before_sunrise = minute < sunrise
            after_sunset = bool(sunset) and minute >= sunset
            if weather.get("is_day") != 0 or weather.get("daynight") != "night":
                errors.append(f"{entry_id} weather is not genuine night")
            if not (before_sunrise or after_sunset):
                errors.append(f"{entry_id} retrieval is inside the daylight window")
        check_masters(errors, entry_id, note)
        if batch110 and entry_id not in batch110:
            errors.append(f"110 batch file missing {entry_id}")
        scene_line = ""
        if batch110:
            for line in batch110.splitlines():
                if line.startswith(entry_id + " "):
                    scene_line = line
                    break
            if not scene_line:
                errors.append(f"110 batch file missing a scene line for {entry_id}")
            else:
                idx = batch110.find(scene_line)
                nxt = batch110.find("\nSE-01-", idx + len(scene_line))
                block = batch110[idx:nxt if nxt > idx else None]
                if "aerial: no" not in block.lower():
                    errors.append(f"{entry_id} batch line is not aerial no")

    html = (ROOT / "index.html").read_text()
    if "Download 9:16" in html.split("const SCENES")[0]:
        errors.append("static markup exposes a 9:16 download")
    if ">Sweden<" not in html or 'aria-current="page"' not in html:
        errors.append("Sweden is not marked current")
    if "G-PDJ4WSS725" not in html:
        errors.append("GA4 id missing")
    if "var INTERVAL=4000;" not in html:
        errors.append("lightbox interval is not the 4000ms value on main")
    template_html = (ROOT / "tools" / "gallery_template.html").read_text()
    if "var INTERVAL=4000;" not in template_html:
        errors.append("gallery template interval is not 4000")
    if "https://sweden.jdvision.org/" not in html:
        errors.append("Sweden canonical missing")
    for entry_id in [*NEW_IDS, *NIGHT_IDS, *LATE_IDS, *LATE2_IDS, *LATE3_IDS, *LATE4_IDS, *LATE5_IDS, *LATE6_IDS, *BATCH_IDS, *PARTA_IDS]:
        start = html.find(f'"entry_id": "{entry_id}"')
        if start < 0:
            errors.append(f"{entry_id} missing from index.html")
            continue
        end = html.find('"entry_id":', start + 10)
        chunk = html[start:end if end > start else start + 2500]
        if '"approval_status": "Approved"' in chunk and entry_id not in COSMO_IDS:
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
