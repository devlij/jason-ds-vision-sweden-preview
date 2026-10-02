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


_WOTD_FIELDS = ("word", "word_en", "phrase", "phrase_en")


def usable_wotd(data: object) -> list:
    """Pass through a Cosmo 365-item dictionary. Anything else is a no-op.

    D026 stays blocked-pending-Cosmo until tools/sv.json is that dictionary.
    Never invent Swedish words or phrases.
    """
    if not isinstance(data, list) or len(data) != 365:
        return []
    for entry in data:
        if not isinstance(entry, dict):
            return []
        for field in _WOTD_FIELDS:
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                return []
    return data


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
    return usable_wotd(data)


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
        "lb-formats",
        "Download 16:9",
        "Download 4:5",
        "lb-close",
        "https://jdvision.org/",
    )
    missing = [token for token in required if token not in html]
    if missing:
        raise SystemExit("gallery page is missing Phase-1 or chrome: " + ", ".join(missing))
    if "__SCENES__" in html or "__SE_META__" in html or "__WOTD_JSON__" in html or "__NARR_JSON__" in html:
        raise SystemExit("gallery template placeholders were not filled")
    nav_start = html.find('<nav class="country-switch"')
    nav_end = html.find("</nav>", nav_start)
    nav = html[nav_start:nav_end] if nav_start >= 0 else ""
    if nav.count(">Sweden<") != 1 or nav.count('aria-current="page"') != 1:
        raise SystemExit("country switcher must mark Sweden once as the current page")
    if "jason-ds-vision-sweden-preview" in nav or 'href="https://sweden.jdvision.org/"' in nav:
        raise SystemExit("country switcher must not link this page to itself")
    if "Home</a>" not in nav or 'href="https://jdvision.org/"' not in nav:
        raise SystemExit("country switcher must include Home")
    if "Belgium" in nav or "Austria" in nav:
        raise SystemExit("country switcher must not list Belgium or Austria")
    order = [
        "Home",
        "Germany",
        "Italy",
        "France",
        "Spain",
        "Greece",
        "Norway",
        "Denmark",
        "Netherlands",
        "Finland",
        "Sweden",
        "Ireland",
        "United Kingdom",
        "Switzerland",
    ]
    positions = [nav.find(name) for name in order]
    if any(pos < 0 for pos in positions) or positions != sorted(positions):
        raise SystemExit(f"switcher order is not Home→Switzerland: {list(zip(order, positions))}")
    live = {
        "Germany": "https://germany.jdvision.org/",
        "Italy": "https://italy.jdvision.org/",
        "France": "https://france.jdvision.org/",
        "Spain": "https://spain.jdvision.org/",
        "Greece": "https://greece.jdvision.org/",
        "Norway": "https://norway.jdvision.org/",
        "Denmark": "https://denmark.jdvision.org/",
        "Netherlands": "https://netherlands.jdvision.org/",
        "Finland": "https://devlij.github.io/jason-ds-vision-finland-preview/",
        "Ireland": "https://ireland.jdvision.org/",
        "United Kingdom": "https://uk.jdvision.org/",
        "Switzerland": "https://devlij.github.io/jason-ds-vision-switzerland-preview/",
    }
    for name, url in live.items():
        if url not in nav:
            raise SystemExit(f"switcher missing {name} at {url}")
    if "jason-ds-vision-norway-preview" in nav or "jason-ds-vision-denmark-preview" in nav:
        raise SystemExit("Norway and Denmark must use jdvision.org hosts")
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


def render_gallery(scenes: list[dict] | None = None) -> str:
    page_scenes = scenes if scenes is not None else load_scenes()
    meta = build_meta(page_scenes)
    _check_meta(meta)
    template = TEMPLATE.read_text()
    wotd = load_wotd()
    narr = narr_manifest(page_scenes)
    # Compact separators match the gallery already published on main.
    compact = (",", ":")
    payload = json.dumps(page_scenes, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    meta_payload = json.dumps(meta, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    wotd_payload = json.dumps(wotd, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    narr_payload = json.dumps(narr, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    html = (
        template.replace("__SCENES__", payload)
        .replace("__SE_META__", meta_payload)
        .replace("__WOTD_JSON__", wotd_payload)
        .replace("__NARR_JSON__", narr_payload)
    )
    assert_phase1(html, meta)
    return html
