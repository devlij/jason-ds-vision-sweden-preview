"""Phase-1 gallery metadata for the Sweden page.

Spain stores each scene as a five-field client tuple:

    [region, "day"|"night", "coastal,mountain,urban,historic", thumbPath, caption]

Filters and related-scene thumbnails read that tuple. Related order is:
same region first, then most shared mood tags, then entry id.

Day or night comes from the scene's own Open-Meteo ``is_day`` flag.
A thumbnail is emitted only when that master file exists.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "tools" / "gallery_template.html"
WOTD = ROOT / "tools" / "sv.json"
DATA = ROOT / "data.json"

MOOD_ORDER = ("coastal", "mountain", "urban", "historic")


def master_exists(rel: str | None) -> bool:
    if not rel or not isinstance(rel, str):
        return False
    if rel.startswith("/") or ".." in Path(rel).parts:
        return False
    path = ROOT / rel
    try:
        path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return False
    return path.is_file()


def recorded_night(entry_id: str, scene: dict) -> bool:
    """True only when a genuine night master is recorded for this scene.

    A weather retrieval is the record when one exists: ``is_day`` 0 and
    ``daynight`` night. Scenes with no retrieval qualify only when data.json
    itself says ``daynight`` is night (the SE-01-128–139 plates). Scenario
    hour is not used, so a late-afternoon daylight plate stays out.
    """
    path = ROOT / "evidence" / "weather" / f"{entry_id}.json"
    if path.is_file():
        weather = json.loads(path.read_text())
        return weather.get("is_day") == 0 and weather.get("daynight") == "night"
    return scene.get("daynight") == "night"


def load_night_masters(scenes: list[dict]) -> dict[str, list[str]]:
    """Night-master URLs keyed by entry id: [16:9, 4:5, 9:16].

    Each slot is the scene's own master, and only when that file is on disk.
    An empty slot means that format has no night master. Another format is
    never copied in, so a missing 9:16 stays missing.
    """
    found: dict[str, list[str]] = {}
    keys = ("file_16x9", "file_4x5", "file_9x16")
    for scene in scenes:
        entry_id = scene.get("entry_id")
        if not entry_id or not recorded_night(entry_id, scene):
            continue
        urls = ["", "", ""]
        for index, key in enumerate(keys):
            rel = scene.get(key) or ""
            if isinstance(rel, str) and rel and master_exists(rel):
                urls[index] = rel
        if any(urls):
            found[entry_id] = urls
    return found


def time_of_day(entry_id: str, scene: dict) -> str:
    path = ROOT / "evidence" / "weather" / f"{entry_id}.json"
    if path.is_file():
        weather = json.loads(path.read_text())
        is_day = weather.get("is_day")
        if is_day == 1:
            return "day"
        if is_day == 0:
            return "night"
        sunrise = weather.get("sunrise") or ""
        stamp = weather.get("retrieval_timestamp") or ""
        if sunrise and stamp and stamp[11:16] < sunrise[11:16]:
            return "night"
    return "night" if scene.get("daynight") == "night" else "day"


def prepare_scene(scene: dict) -> dict | None:
    out = dict(scene)
    if out.get("motion") and not master_exists(out.get("motion")):
        out["motion"] = None
    if out.get("file_9x16") and not master_exists(out.get("file_9x16")):
        out.pop("file_9x16", None)
    if out.get("file_4x5") and not master_exists(out.get("file_4x5")):
        out.pop("file_4x5", None)
    if not master_exists(out.get("file_16x9")):
        return None
    # 9:16 stays on disk. The tab and download render only after Jason clears it.
    if out.get("format_9x16_approval_status") != "Approved":
        out["format_9x16_approval_status"] = out.get("format_9x16_approval_status") or "Candidate"
    return out


def derive_moods(scene: dict) -> list[str]:
    explicit = scene.get("moods")
    if isinstance(explicit, list):
        allowed = set(MOOD_ORDER)
        return [mood for mood in MOOD_ORDER if mood in explicit and mood in allowed]
    return []


def build_meta(scenes: list[dict]) -> dict[str, list]:
    meta: dict[str, list] = {}
    for scene in scenes:
        entry_id = scene.get("entry_id")
        if not entry_id:
            continue
        thumb = scene["file_16x9"]
        if not master_exists(thumb):
            continue
        meta[entry_id] = [
            scene.get("region") or "",
            time_of_day(entry_id, scene),
            ",".join(derive_moods(scene)),
            thumb,
            scene.get("caption") or entry_id,
        ]
    return meta


def load_scenes() -> list[dict]:
    payload = json.loads(DATA.read_text())
    rows = payload["scenes"] if isinstance(payload, dict) else payload
    prepared = []
    for scene in rows:
        item = prepare_scene(scene)
        if item is None:
            print("skip gallery card, missing 16:9 master", scene.get("entry_id"))
            continue
        prepared.append(item)
    return prepared


def load_wotd() -> list:
    if not WOTD.is_file():
        return []
    data = json.loads(WOTD.read_text())
    if not isinstance(data, list):
        raise SystemExit("tools/sv.json must be a JSON array. Do not invent entries.")
    return data


def narr_manifest(scenes: list[dict]) -> dict:
    """Only Aria/Warm, avocado_v2:MAI_01, Approved, and a real mp3 are listed."""
    out = {}
    for scene in scenes:
        rec = scene.get("narration")
        if not isinstance(rec, dict):
            continue
        src = rec.get("src") or ""
        if rec.get("status") != "Approved":
            continue
        if rec.get("voice") not in ("Aria", "Warm"):
            continue
        if rec.get("model") != "avocado_v2:MAI_01":
            continue
        if not src.lower().endswith(".mp3") or not master_exists(src):
            continue
        out[scene["entry_id"]] = {
            "src": src,
            "voice": rec["voice"],
            "model": rec["model"],
            "status": "Approved",
        }
    return out


def _check_meta(meta: dict[str, list]) -> None:
    for entry_id, row in meta.items():
        if len(row) != 5:
            raise SystemExit(f"phase-1 meta for {entry_id} is not a 5-field tuple")
        if row[1] not in ("day", "night"):
            raise SystemExit(f"phase-1 time of day for {entry_id} is {row[1]!r}")
        moods = [part for part in row[2].split(",") if part]
        if any(mood not in MOOD_ORDER for mood in moods):
            raise SystemExit(f"phase-1 mood outside Spain's set for {entry_id}: {row[2]!r}")
        if not master_exists(row[3]):
            raise SystemExit(f"phase-1 thumbnail missing on disk for {entry_id}: {row[3]}")


def assert_phase1(html: str, meta: dict[str, list]) -> None:
    required = (
        'id="f-daynight"',
        'id="f-mood"',
        "Coastal",
        "Mountain",
        "Urban",
        "Historic",
        'id="result-count"',
        'id="clear"',
        "f-daynight').value = ''",
        "f-mood').value = ''",
        "card.id = s.entry_id",
        "function relatedFor",
        "Copy link",
        "Copied",
        "G-PDJ4WSS725",
        "https://spain.jdvision.org/",
        "https://sweden.jdvision.org/",
        'id="wotd"',
        "lb-play",
        "Play slideshow",
        "approval_status",
        "flag-band",
        "#006AA7",
        "#FECC02",
        "format_9x16_approval_status",
        "phase1Enhance",
        "getAttribute",
        "avocado_v2:MAI_01",
        "lbFormat",
        "https://jdvision.org/transparency.html",
    )
    missing = [token for token in required if token not in html]
    if missing:
        raise SystemExit("gallery page is missing Phase-1 or chrome: " + ", ".join(missing))
    if "__SCENES__" in html or "__SE_META__" in html or "__WOTD_JSON__" in html or "__NARR_JSON__" in html or "__SE_NIGHT__" in html:
        raise SystemExit("gallery template placeholders were not filled")
    if html.count("const SE_NIGHT=") != 1:
        raise SystemExit("SE_NIGHT was duplicated or dropped")
    if html.count('class="night-tab"') != 1:
        raise SystemExit("night-tab markup was duplicated or dropped")
    if "closest('.night-tab')" not in html:
        raise SystemExit("night click handler missing")
    nav_start = html.find('<nav class="country-switch"')
    nav_end = html.find("</nav>", nav_start)
    nav = html[nav_start:nav_end] if nav_start >= 0 else ""
    if nav.count(">Sweden<") != 1 or nav.count('aria-current="page"') != 1:
        raise SystemExit("country switcher must mark Sweden once as the current page")
    if "jason-ds-vision-sweden-preview" in nav:
        raise SystemExit("country switcher must not link this page to itself")
    if nav.find(">Sweden<") < nav.find("Switzerland"):
        raise SystemExit("Sweden must be last in the switcher")
    order = ["Germany", "Italy", "France", "Greece", "Spain", "Norway", "Denmark", "Switzerland", "Sweden"]
    positions = [nav.find(name) for name in order]
    if any(pos < 0 for pos in positions) or positions != sorted(positions):
        raise SystemExit(f"switcher order is not Germany→Sweden: {positions}")
    if "linear-gradient(#fff,#fff) center/45% 22%" not in html:
        raise SystemExit("Swiss flag chip is missing the white cross")
    if 'class="day-tab"' in html.split("const SCENES")[0] and "day-tab" in html.split("<script>")[0]:
        pass
    if not meta:
        raise SystemExit("phase-1 meta is empty")
    for entry_id, row in meta.items():
        if entry_id not in html:
            raise SystemExit(f"{entry_id} missing from generated page")
        if row[3] not in html:
            raise SystemExit(f"thumbnail for {entry_id} missing from generated page")
        if row[1] != "night" and entry_id == "SE-01-001":
            raise SystemExit("SE-01-001 must stay night while the retrieval is before sunrise")


def assert_night(scenes: list[dict], night: dict[str, list[str]]) -> None:
    """Refuse a publish that invents a night plate or puts Night on a daylight card."""
    keys = ("file_16x9", "file_4x5", "file_9x16")
    formats = ("16x9", "4x5", "9x16")
    for scene in scenes:
        entry_id = scene.get("entry_id")
        if not entry_id:
            continue
        if not recorded_night(entry_id, scene):
            if entry_id in night:
                raise SystemExit(f"{entry_id} is not a recorded night scene and must not get Night")
            continue
        urls = night.get(entry_id)
        if not urls or len(urls) != 3:
            raise SystemExit(f"{entry_id} night record must be [16:9, 4:5, 9:16]")
        if not any(urls):
            raise SystemExit(f"{entry_id} has no night master on disk")
        for fmt, key, url in zip(formats, keys, urls):
            own = scene.get(key) or ""
            if url and url != own:
                raise SystemExit(f"{entry_id} {fmt} night URL is not the scene master")
            if fmt == "9x16" and url and "9x16" not in url:
                raise SystemExit(f"{entry_id} invented a 9:16 night plate")
            if url and not master_exists(url):
                raise SystemExit(f"{entry_id} {fmt} night master missing on disk")
    if "SE-01-002" in night:
        raise SystemExit("SE-01-002 is daylight and must not get a Night button")
    if "SE-01-001" not in night or not night["SE-01-001"][0]:
        raise SystemExit("SE-01-001 night master missing")


def render_gallery(scenes: list[dict] | None = None) -> str:
    page_scenes = scenes if scenes is not None else load_scenes()
    meta = build_meta(page_scenes)
    _check_meta(meta)
    night = load_night_masters(page_scenes)
    assert_night(page_scenes, night)
    template = TEMPLATE.read_text()
    wotd = load_wotd()
    narr = narr_manifest(page_scenes)
    # Compact separators match the gallery already published on main.
    compact = (",", ":")
    payload = json.dumps(page_scenes, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    meta_payload = json.dumps(meta, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    wotd_payload = json.dumps(wotd, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    narr_payload = json.dumps(narr, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    night_payload = json.dumps(night, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    html = (
        template.replace("__SCENES__", payload)
        .replace("__SE_META__", meta_payload)
        .replace("__WOTD_JSON__", wotd_payload)
        .replace("__NARR_JSON__", narr_payload)
        .replace("__SE_NIGHT__", night_payload)
    )
    assert_phase1(html, meta)
    return html
