#!/usr/bin/env python3
"""Sweden 360 pack 1 — static-ambient Ken Burns clips (ffmpeg).

Jason re-authorized static-ambient (Ken Burns / ffmpeg) for this round, the
same contingency class as 2026-10-02. Image-to-video is not called. Night
masters are never opened. Approval stays Candidate. Cosmo QC is not claimed.

Each genuine daylight 4:5 master is cropped with ffmpeg ``crop=864:1080:0:0``
so the 190px label bar is gone, then a centered Ken Burns zoom
(1.00 → 1.07 over 240 frames) is encoded to
``assets/<id-lower>-motion-10s-4x5.mp4``: 10.0s, 864×1080, 24 fps, h264,
yuv420p, +faststart, no audio.

Self-QC runs once. One failure holds that scene and the partial file is
deleted. Three holds in a row stop the pack. There is no second attempt.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FPS = 24
FRAMES = 240
PHOTO_W = 864
PHOTO_H = 1080
LABEL_H = 190
SOURCE_H = PHOTO_H + LABEL_H  # 1270
ZOOM_END = 1.07
MIN_TOP_V = 90.0
# Decoded frame 0 versus the cropped plate. Encode noise on the test plate was ~1.6.
MAX_FRAME0_MAD = 4.0
# Last frame versus first. A frozen encode sits near encode noise; 7% zoom is ~12.
MIN_MOTION_MAD = 3.0
MAX_MOTION_MAD = 40.0
# Plate bottom versus the label strip. The real label differs by ~60.
MIN_LABEL_MAD = 25.0
PACK_LIMIT = 12
WORK_ORDER = "wo-sweden-360-2026-10-05"
DIRECTIVE = "wo-360-technical-directive-2026-10-02"
DATE = "2026-10-05"

ZOOM_FILTER = (
    "zoompan="
    f"z='1+{(ZOOM_END - 1):.2f}*on/{FRAMES - 1}':"
    "x='iw/2-(iw/zoom/2)':"
    "y='ih/2-(ih/zoom/2)':"
    f"d={FRAMES}:s={PHOTO_W}x{PHOTO_H}:fps={FPS}"
)


def catalog() -> list[dict]:
    data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
    rows = data["scenes"] if isinstance(data, dict) else data
    return sorted(rows, key=lambda row: row.get("entry_id") or "")


def weather_record(entry_id: str) -> dict | None:
    path = ROOT / "evidence" / "weather" / f"{entry_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def is_genuine_daylight(weather: dict | None) -> bool:
    if not weather:
        return False
    if weather.get("is_day") != 1 or weather.get("daynight") != "day":
        return False
    sunrise = (weather.get("sunrise") or "")[11:16]
    sunset = (weather.get("sunset") or "")[11:16]
    minute = (weather.get("retrieval_timestamp") or "")[11:16]
    return bool(sunrise and sunset and minute and sunrise <= minute < sunset)


def clip_path(entry_id: str) -> Path:
    return ROOT / "assets" / f"{entry_id.lower()}-motion-10s-4x5.mp4"


def poster_path(entry_id: str) -> Path:
    return ROOT / "assets" / f"{entry_id.lower()}-motion-10s-4x5-poster.jpg"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_ffmpeg(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr or "")[-1800:]
        raise RuntimeError(f"ffmpeg failed ({cmd[0]})\n{tail}")


def ffprobe(path: Path) -> dict:
    raw = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_type,codec_name,width,height,pix_fmt,nb_frames,avg_frame_rate,duration",
            "-show_entries", "format=duration",
            "-of", "json", str(path),
        ],
        text=True,
    )
    return json.loads(raw)


def raw_rgb(path: Path) -> bytes:
    return subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
    )


def mean_abs(a: bytes, b: bytes) -> float:
    n = min(len(a), len(b))
    if n == 0:
        raise RuntimeError("empty frame")
    left = np.frombuffer(a, dtype=np.uint8, count=n).astype(np.int16)
    right = np.frombuffer(b, dtype=np.uint8, count=n).astype(np.int16)
    return float(np.abs(left - right).mean())


def mean_v(raw: bytes, width: int, height: int, rows: int | None = None) -> float:
    """OpenCV-style HSV V: max(R, G, B), averaged over the top ``rows``."""
    use_rows = height if rows is None else rows
    count = width * use_rows
    if len(raw) < count * 3:
        raise RuntimeError("frame shorter than the requested window")
    pixels = np.frombuffer(raw, dtype=np.uint8, count=count * 3).reshape(-1, 3)
    return float(pixels.max(axis=1).mean())


def select_pack() -> tuple[list[dict], list[dict]]:
    """Daylight scenes missing a clip, capped at 12. Night is recorded, not opened."""
    chosen: list[dict] = []
    skips: list[dict] = []
    for scene in catalog():
        entry_id = scene.get("entry_id") or ""
        weather = weather_record(entry_id)
        if not is_genuine_daylight(weather):
            skips.append({
                "entry_id": entry_id,
                "reason": "night" if (weather or {}).get("is_day") == 0 or scene.get("daynight") == "night" or not weather else "not genuine daylight",
                "opened_master": False,
            })
            continue
        if clip_path(entry_id).is_file():
            skips.append({
                "entry_id": entry_id,
                "reason": "daylight clip already on disk",
                "opened_master": False,
            })
            continue
        if len(chosen) >= PACK_LIMIT:
            skips.append({
                "entry_id": entry_id,
                "reason": f"past the {PACK_LIMIT}-scene cap",
                "opened_master": False,
            })
            continue
        chosen.append(scene)
    return chosen, skips


def prepare_plate(scene: dict, work: Path) -> dict:
    entry_id = scene["entry_id"]
    weather = weather_record(entry_id)
    if not is_genuine_daylight(weather):
        raise RuntimeError(f"{entry_id} is not genuine daylight; refusing to open a master")
    rel = scene.get("file_4x5") or ""
    src = ROOT / rel
    if not rel.endswith("-4x5.png") or not src.is_file():
        raise RuntimeError(f"{entry_id} has no 4:5 master")
    probe = ffprobe(src)
    streams = [row for row in probe.get("streams") or [] if row.get("codec_type") == "video"]
    if not streams:
        raise RuntimeError(f"{entry_id} 4:5 master has no video stream")
    width = int(streams[0]["width"])
    height = int(streams[0]["height"])
    if width != PHOTO_W or height != SOURCE_H:
        raise RuntimeError(f"{entry_id} 4:5 master is {width}x{height}, expected {PHOTO_W}x{SOURCE_H}")
    plate = work / f"{entry_id.lower()}-plate.png"
    run_ffmpeg([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", f"crop={PHOTO_W}:{PHOTO_H}:0:0",
        "-frames:v", "1", str(plate),
    ])
    plate_raw = raw_rgb(plate)
    master_raw = raw_rgb(src)
    row_bytes = PHOTO_W * 3
    if len(plate_raw) != PHOTO_W * PHOTO_H * 3:
        raise RuntimeError(f"{entry_id} cropped plate is not {PHOTO_W}x{PHOTO_H}")
    top_mad = mean_abs(plate_raw, master_raw[: len(plate_raw)])
    if top_mad > 0.01:
        raise RuntimeError(f"{entry_id} crop does not match the top {PHOTO_H}px (mad {top_mad:.3f})")
    label = master_raw[-LABEL_H * row_bytes:]
    plate_bottom = plate_raw[-40 * row_bytes:]
    label_bottom = label[-40 * row_bytes:]
    label_mad = mean_abs(plate_bottom, label_bottom)
    if label_mad < MIN_LABEL_MAD:
        raise RuntimeError(f"{entry_id} label bar still in frame (bottom mad {label_mad:.2f})")
    top_rows = PHOTO_H // 5
    top_v = mean_v(plate_raw, PHOTO_W, PHOTO_H, top_rows)
    if top_v < MIN_TOP_V:
        raise RuntimeError(f"{entry_id} top-fifth V {top_v:.1f} is below {MIN_TOP_V}")
    return {
        "plate": plate,
        "plate_raw": plate_raw,
        "top_v": round(top_v, 2),
        "mean_v": round(mean_v(plate_raw, PHOTO_W, PHOTO_H), 2),
        "label_mad": round(label_mad, 3),
        "anchor": {
            "repo_path": rel,
            "sha256": sha256(src),
            "bytes": src.stat().st_size,
            "dimensions_before_crop": f"{width}x{height}",
            "crop": f"{PHOTO_W}:{PHOTO_H}:0:0",
            "caption": scene.get("caption") or "",
            "weather": {
                "is_day": weather.get("is_day"),
                "daynight": weather.get("daynight"),
                "retrieval_timestamp": weather.get("retrieval_timestamp"),
                "sunrise": weather.get("sunrise"),
                "sunset": weather.get("sunset"),
            },
        },
    }


def encode_ken_burns(plate: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg([
        "ffmpeg", "-y", "-loop", "1", "-i", str(plate),
        "-vf", ZOOM_FILTER,
        "-frames:v", str(FRAMES), "-r", str(FPS),
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "18", "-preset", "medium", "-movflags", "+faststart",
        str(dest),
    ])


def extract_frame(clip: Path, index: int, dest: Path) -> None:
    run_ffmpeg([
        "ffmpeg", "-y", "-i", str(clip),
        "-vf", f"select=eq(n\\,{index})",
        "-frames:v", "1", str(dest),
    ])


def probe_clip(path: Path) -> dict:
    data = ffprobe(path)
    video = [row for row in data.get("streams") or [] if row.get("codec_type") == "video"]
    audio = [row for row in data.get("streams") or [] if row.get("codec_type") == "audio"]
    if len(video) != 1 or audio:
        raise RuntimeError(f"expected one video stream and no audio, got {data.get('streams')}")
    stream = video[0]
    duration = float(stream.get("duration") or data["format"]["duration"])
    head = path.read_bytes()[:262144]
    moov = head.find(b"moov")
    mdat = head.find(b"mdat")
    fast = moov > 0 and (mdat < 0 or moov < mdat)
    info = {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "codec": stream["codec_name"],
        "pix_fmt": stream["pix_fmt"],
        "nb_frames": int(stream.get("nb_frames") or 0),
        "avg_frame_rate": stream.get("avg_frame_rate"),
        "duration": round(duration, 3),
        "faststart": fast,
        "audio": False,
    }
    if info["width"] != PHOTO_W or info["height"] != PHOTO_H:
        raise RuntimeError(f"dims {info['width']}x{info['height']}")
    if info["codec"] != "h264" or info["pix_fmt"] != "yuv420p":
        raise RuntimeError(f"codec {info['codec']} {info['pix_fmt']}")
    if info["nb_frames"] != FRAMES:
        raise RuntimeError(f"frames {info['nb_frames']}")
    if abs(info["duration"] - 10.0) > 0.05:
        raise RuntimeError(f"duration {info['duration']}")
    if info["avg_frame_rate"] not in ("24/1", "24/1.0"):
        rate = info["avg_frame_rate"] or ""
        if not re.fullmatch(r"24/1", rate):
            raise RuntimeError(f"frame rate {rate}")
    if not info["faststart"]:
        raise RuntimeError("moov is not before mdat")
    return info


def qc_motion(clip: Path, plate_raw: bytes, work: Path, entry_id: str) -> dict:
    first = work / f"{entry_id.lower()}-f0.png"
    last = work / f"{entry_id.lower()}-f239.png"
    extract_frame(clip, 0, first)
    extract_frame(clip, FRAMES - 1, last)
    frame0 = raw_rgb(first)
    frame_last = raw_rgb(last)
    if len(frame0) != len(plate_raw) or len(frame_last) != len(plate_raw):
        raise RuntimeError("decoded frame size does not match the cropped plate")
    frame0_mad = mean_abs(frame0, plate_raw)
    motion_mad = mean_abs(frame0, frame_last)
    if frame0_mad > MAX_FRAME0_MAD:
        raise RuntimeError(f"frame 0 mad {frame0_mad:.2f} exceeds {MAX_FRAME0_MAD} (crop or zoom start)")
    if motion_mad < MIN_MOTION_MAD:
        raise RuntimeError(f"motion mad {motion_mad:.2f} below {MIN_MOTION_MAD} (clip is still)")
    if motion_mad > MAX_MOTION_MAD:
        raise RuntimeError(f"motion mad {motion_mad:.2f} exceeds {MAX_MOTION_MAD} (zoom left the subject)")
    return {
        "frame0_mad": round(frame0_mad, 3),
        "motion_mad": round(motion_mad, 3),
    }


def write_poster(plate: Path, dest: Path) -> None:
    run_ffmpeg(["ffmpeg", "-y", "-i", str(plate), "-q:v", "3", str(dest)])


def discard(entry_id: str, partial: Path) -> None:
    partial.unlink(missing_ok=True)
    clip_path(entry_id).unlink(missing_ok=True)
    poster_path(entry_id).unlink(missing_ok=True)


def bake_scene(scene: dict, work: Path) -> dict:
    entry_id = scene["entry_id"]
    row = {
        "entry_id": entry_id,
        "caption": scene.get("caption") or "",
        "method": "static-ambient",
        "technique": "ken-burns",
        "tool": "ffmpeg",
        "crop": f"{PHOTO_W}:{PHOTO_H}:0:0",
        "zoom": f"centered 1.00 → {ZOOM_END:.2f}",
        "approval_status": "Candidate",
        "cosmo_qc": None,
        "attempts": 1,
        "status": "HOLD",
        "camera": "ken-burns",
        "daytime": True,
    }
    partial = clip_path(entry_id).with_suffix(".partial.mp4")
    try:
        prepared = prepare_plate(scene, work)
        row["caption"] = prepared["anchor"]["caption"] or row["caption"]
        row["anchor"] = prepared["anchor"]
        row["top_v"] = prepared["top_v"]
        row["mean_v"] = prepared["mean_v"]
        row["label_mad"] = prepared["label_mad"]
        encode_ken_burns(prepared["plate"], partial)
        info = probe_clip(partial)
        motion = qc_motion(partial, prepared["plate_raw"], work, entry_id)
        dest = clip_path(entry_id)
        partial.replace(dest)
        write_poster(prepared["plate"], poster_path(entry_id))
        info["sha256"] = sha256(dest)
        info["bytes"] = dest.stat().st_size
        info.update(motion)
        row["probe"] = info
        row["frame0_mad"] = motion["frame0_mad"]
        row["motion_mad"] = motion["motion_mad"]
        row["status"] = "shipped"
        row["variant"] = "ken-burns"
        row["file"] = str(dest.relative_to(ROOT))
        row["poster"] = str(poster_path(entry_id).relative_to(ROOT))
    except Exception as exc:
        discard(entry_id, partial)
        row["error"] = str(exc)
        row["hold_reason"] = str(exc)
        row["status"] = "HOLD"
    return row


def scene_evidence(row: dict) -> dict:
    shipped = row.get("status") == "shipped"
    return {
        "work_order": WORK_ORDER,
        "directive": DIRECTIVE,
        "pack": 1,
        "date": DATE,
        "entry_id": row["entry_id"],
        "caption": row.get("caption"),
        "disposition": row.get("status"),
        "method": "static-ambient" if shipped else "HOLD",
        "technique": "ken-burns" if shipped else None,
        "tool": "ffmpeg",
        "attempted_method": "static-ambient",
        "attempts": row.get("attempts"),
        "retry": False,
        "approval_status": "Candidate",
        "cosmo_qc": None,
        "daytime": True,
        "weather": (row.get("anchor") or {}).get("weather"),
        "source": row.get("anchor"),
        "zoom": row.get("zoom"),
        "crop": row.get("crop"),
        "top_v": row.get("top_v"),
        "mean_v": row.get("mean_v"),
        "label_mad": row.get("label_mad"),
        "frame0_mad": row.get("frame0_mad"),
        "motion_mad": row.get("motion_mad"),
        "output": {
            "file": row.get("file"),
            "poster": row.get("poster"),
            "probe": row.get("probe"),
        } if shipped else None,
        "gallery_button": "wired ▶ 360° via SE_MOTION" if shipped else "not wired",
        "hold_reason": row.get("hold_reason"),
        "escalation": row.get("escalation"),
    }


def write_scene_evidence(row: dict) -> None:
    dest = ROOT / "evidence" / "motion" / f"{row['entry_id']}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(scene_evidence(row), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_proof(evidence: dict) -> None:
    lines = [
        "# Sweden 360 pack 1 proof (Candidate)",
        "",
        f"Work order `{WORK_ORDER}` pack 1. Directive `{DIRECTIVE}`. Date {DATE}.",
        "",
        "Method is **static-ambient**. Jason re-authorized static-ambient (Ken Burns / ffmpeg) for this round, the same contingency class as 2026-10-02. Image-to-video was not called. No orbit was encoded. Night masters were not opened. Approval status stays Candidate. Cosmo QC was not recorded.",
        "",
        "Each genuine daylight 4:5 master on `main` was cropped with `ffmpeg crop=864:1080:0:0`, which drops the 190px label bar. A centered Ken Burns zoom (1.00 → 1.07 over 240 frames, no lateral pan) was encoded with ffmpeg `zoompan` to `assets/<scene-id-lower>-motion-10s-4x5.mp4`.",
        "",
        "Self-QC is one attempt. A failed check holds that scene and deletes the partial. Three holds in a row stop the pack. This run did not get a second try.",
        "",
        "| Scene | Caption | Status | Duration | Dims | frame0 mad | motion mad |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in evidence["scenes"]:
        probe = row.get("probe") or {}
        dims = f"{probe.get('width')}×{probe.get('height')}" if probe else "—"
        duration = f"{probe.get('duration')}s" if probe else "—"
        lines.append(
            f"| {row['entry_id']} | {row.get('caption') or ''} | {row.get('status')} | "
            f"{duration} | {dims} | {row.get('frame0_mad', '—')} | {row.get('motion_mad', '—')} |"
        )
    lines.extend([
        "",
        f"Clip count: **{len(evidence['shipped'])}**. HOLD: {len(evidence['hold'])}. Stopped early: {'yes' if evidence['stopped_early'] else 'no'}.",
        "",
        "Each shipped file is 24 fps, 240 frames, h264, yuv420p, +faststart, no audio, 864×1080, 10.0s.",
        "",
        "`▶ 360°` is rendered only for a scene whose mp4 is on disk. It switches to `✕ Close`. The clip is autoplay, muted, loop, playsinline, and controls is false. Format clicks stop the clip. `data.json` `motion` stays null because that field is the aerial slot. Approval status stays Candidate.",
        "",
        f"Evidence: `evidence/motion/{WORK_ORDER}-pack1.json`.",
        "",
        "Do not merge.",
        "",
    ])
    dest = ROOT / "evidence" / "motion" / f"PROOF-{WORK_ORDER}-pack1.md"
    dest.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    chosen, skips = select_pack()
    work = Path("/tmp/se360-pack1")
    work.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    consecutive = 0
    stopped = False
    for scene in chosen:
        entry_id = scene["entry_id"]
        if stopped:
            row = {
                "entry_id": entry_id,
                "caption": scene.get("caption") or "",
                "method": "static-ambient",
                "status": "not-attempted",
                "attempts": 0,
                "hold_reason": "stopped after 3 consecutive QC holds",
                "approval_status": "Candidate",
                "cosmo_qc": None,
                "daytime": True,
            }
            rows.append(row)
            write_scene_evidence(row)
            print(json.dumps({"entry_id": entry_id, "status": "not-attempted"}), flush=True)
            continue
        print(f"bake {entry_id}", flush=True)
        row = bake_scene(scene, work)
        if row["status"] == "HOLD":
            consecutive += 1
            if consecutive >= 3:
                stopped = True
                row["escalation"] = "3 consecutive QC failures; pack stopped"
        else:
            consecutive = 0
        rows.append(row)
        write_scene_evidence(row)
        brief = {
            k: row.get(k)
            for k in ("entry_id", "status", "attempts", "top_v", "frame0_mad", "motion_mad", "hold_reason")
        }
        print(json.dumps(brief, ensure_ascii=False), flush=True)

    night_ids = [row["entry_id"] for row in skips if row["reason"] == "night"]
    evidence = {
        "work_order": WORK_ORDER,
        "directive": DIRECTIVE,
        "pack": 1,
        "date": DATE,
        "status": "Candidate",
        "merge": False,
        "method": "static-ambient",
        "technique": "ken-burns",
        "tool": "ffmpeg",
        "authorization": "Jason re-authorized static-ambient (Ken Burns / ffmpeg) for this round, same as 2026-10-02",
        "i2v": {"called": False, "note": "this round uses the re-authorized ffmpeg Ken Burns path"},
        "zoom": {
            "filter": ZOOM_FILTER,
            "start": 1.0,
            "end": ZOOM_END,
            "pan": "none; subject stays centered",
        },
        "qc": {
            "policy": "fail once → HOLD; 3 holds in a row → STOP",
            "retry": False,
            "max_frame0_mad": MAX_FRAME0_MAD,
            "min_motion_mad": MIN_MOTION_MAD,
            "max_motion_mad": MAX_MOTION_MAD,
            "min_top_v": MIN_TOP_V,
            "min_label_mad": MIN_LABEL_MAD,
        },
        "spec": {
            "duration_s": 10.0,
            "fps": FPS,
            "frames": FRAMES,
            "width": PHOTO_W,
            "height": PHOTO_H,
            "codec": "h264",
            "pix_fmt": "yuv420p",
            "faststart": True,
            "audio": False,
            "crop": f"{PHOTO_W}:{PHOTO_H}:0:0",
            "source": "genuine daylight 4:5 master on main",
        },
        "approval_status": "Candidate",
        "cosmo_qc": None,
        "stopped_early": stopped,
        "scenes": rows,
        "shipped": [row["entry_id"] for row in rows if row["status"] == "shipped"],
        "hold": [
            {"entry_id": row["entry_id"], "reason": row.get("hold_reason")}
            for row in rows if row["status"] == "HOLD"
        ],
        "not_attempted": [row["entry_id"] for row in rows if row["status"] == "not-attempted"],
        "skips": {
            "night_count": len(night_ids),
            "night_ids_head": night_ids[:3],
            "night_ids_tail": night_ids[-3:],
            "note": "Night scenes were not opened and did not get a clip.",
            "other": [row for row in skips if row["reason"] != "night"],
        },
        "gallery_buttons_wired": [row["entry_id"] for row in rows if row["status"] == "shipped"],
        "counts": {
            "shipped": sum(1 for row in rows if row["status"] == "shipped"),
            "hold": sum(1 for row in rows if row["status"] == "HOLD"),
            "not_attempted": sum(1 for row in rows if row["status"] == "not-attempted"),
            "skipped_night": len(night_ids),
        },
    }
    dest = ROOT / "evidence" / "motion" / f"{WORK_ORDER}-pack1.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_proof(evidence)
    print(f"wrote {dest}", flush=True)
    print(
        f"shipped {evidence['counts']['shipped']} hold {evidence['counts']['hold']} "
        f"stopped {stopped}",
        flush=True,
    )
    if stopped:
        sys.exit(2)


if __name__ == "__main__":
    main()
