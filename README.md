# Jason D’s Vision — Sweden

AI-generated artistic interpretations of Sweden. Free to use, no credit required.

Gallery: https://sweden.jdvision.org/ (CNAME is in the repo; GitHub Pages still has to be switched on for this project)

All scenes ship as **Candidate** until Cosmo QC. This seed does not approve anything.

## What is here

Phase-1 gallery shell, matching the Spain / Netherlands A7 page: GA4 `G-PDJ4WSS725`, canonical `https://sweden.jdvision.org/`, Open Graph, Twitter card, robots, sitemap, JSON-LD, Swedish flag band (`#006AA7` / `#FECC02`, 6px), country switcher (Home plus every live gallery, Sweden current and not a link), word-of-day band, search and region / day-night / mood filters, related scenes, copy-link, and a lightbox (16:9 and 4:5 tabs and download links, counter navigation, close, 4 second slideshow). The lightbox keeps both formats available and the chosen format persists across previous, next, and the slideshow.

`tools/sv.json` is an empty array, not a 365-item dictionary (`word`, `word_en`, `phrase`, `phrase_en`). **D026 is blocked-pending-Cosmo.** No Swedish words or phrases were invented. The template wires the band to that file and rotates by day-of-year only when the file is already that 365-item dictionary (local kicker `Dagens ord · Word of the day`, bold word, italic phrase, English glosses, `Day N of 365`). Until then the band stays hidden.

9:16 masters can sit on disk. The 9:16 tab and download stay hidden until `format_9x16_approval_status` is set to `Approved` by Jason. Narration controls appear only for Aria or Warm, model `avocado_v2:MAI_01`, status Approved, and an mp3 file. There is no day/night toggle on the card. A motion control is rendered only when a motion file exists.

## SE-01-001

Royal Palace, Stockholm, from Slottsbacken in Gamla Stan. One Open-Meteo retrieval at `2026-09-28T06:41:11+02:00` (Europe/Stockholm). Sunrise that morning was 06:45, so the scene is night. No 8 second aerial.

Masters:

- `assets/sweden/Stockholm/se-01-001-16x9.png` (1920×1270)
- `assets/sweden/Stockholm/se-01-001-4x5.png` (864×1270)
- `assets/sweden/Stockholm/se-01-001-9x16.png` (1080×2110)

Evidence: `approvals/SE-01-001.md` and `evidence/weather/SE-01-001.json`.

## Rebuild

```bash
python3 tools/publish_gallery.py
python3 tools/qc_preflight.py
```

`tools/fetch_weather.py` keeps an existing weather file. Do not re-fetch SE-01-001.

`tools/composite_masters.py` bakes the 190px label bar and the five Art. 50 PNG text chunks from a pure pre-text under `assets/pretext/sweden/<City>/`.
