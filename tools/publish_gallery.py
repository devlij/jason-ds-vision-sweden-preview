#!/usr/bin/env python3
"""Write index.html, robots.txt, sitemap.xml, and image-sitemap.xml."""

from __future__ import annotations

import json
import re
from pathlib import Path

from gallery_phase1 import ROOT, load_scenes, render_gallery

SITE = "https://sweden.jdvision.org/"


def write_robots() -> None:
    text = (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {SITE}sitemap.xml\n"
        f"Sitemap: {SITE}image-sitemap.xml\n"
    )
    (ROOT / "robots.txt").write_text(text)


def write_sitemap() -> None:
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE}</loc></url>\n"
        "</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(xml)


def write_image_sitemap(scenes: list[dict]) -> None:
    """Approved scenes only. 9:16 is never listed. Candidates contribute nothing."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    for scene in scenes:
        if scene.get("approval_status") != "Approved":
            continue
        images = []
        for key in ("file_16x9", "file_4x5"):
            rel = scene.get(key) or ""
            if not rel or "9x16" in rel:
                continue
            images.append(f"    <image:image><image:loc>{SITE}{rel}</image:loc></image:image>")
        if not images:
            continue
        lines.append(f"  <url><loc>{SITE}#{scene['entry_id']}</loc>")
        lines.extend(images)
        lines.append("  </url>")
    lines.append("</urlset>")
    (ROOT / "image-sitemap.xml").write_text("\n".join(lines) + "\n")


# Approvals this publisher accepts. SE-01-001 was approved on main before the
# QC zero-out. Everything else needs the current Jason-authorized credit,
# set by the approval PR in data.json (2026-10-05, relay
# wo-qc-zeroout-sweden-20261005T164050Z). The publisher never approves.
LEGACY_APPROVED = {"SE-01-001"}
APPROVED_QC_LABELS = {"Approved · Grok Bot QC 5/5"}
# An approval credit must never name Cosmo or Jason as the QC/approver
# ("Cosmo QC", "Jason approved", "approved by Cosmo"). "Jason-authorized" is fine.
FABRICATED_QC = re.compile(
    r"\b(cosmo|jason)\b(?:['’]s)?\s*(?:qc|approv)|approved\s+by\s+(?:cosmo|jason)\b",
    re.IGNORECASE,
)
QC_FIELDS = ("qc_label", "qc_status", "approval_basis")


def check_approvals(scenes: list[dict]) -> None:
    """Refuse a publish that carries an approval this pipeline did not grant."""
    for scene in scenes:
        entry_id = scene.get("entry_id")
        for field in QC_FIELDS:
            value = str(scene.get(field) or "")
            if FABRICATED_QC.search(value):
                raise SystemExit(f"refusing to publish {entry_id}: {field} claims a Cosmo/Jason QC credit")
        if scene.get("approval_status") != "Approved":
            continue
        if entry_id in LEGACY_APPROVED:
            continue
        if scene.get("qc_label") not in APPROVED_QC_LABELS:
            raise SystemExit(
                f"refusing to publish a self-approved scene: {entry_id} "
                f"(qc_label {scene.get('qc_label')!r} is not a recognized approval credit)"
            )


def main() -> None:
    scenes = load_scenes()
    html = render_gallery(scenes)
    check_approvals(scenes)
    (ROOT / "index.html").write_text(html)
    write_robots()
    write_sitemap()
    write_image_sitemap(scenes)
    print(f"wrote index.html ({len(html)} bytes), robots.txt, sitemap.xml, image-sitemap.xml")
    print(f"scenes {len(scenes)}")


if __name__ == "__main__":
    main()
