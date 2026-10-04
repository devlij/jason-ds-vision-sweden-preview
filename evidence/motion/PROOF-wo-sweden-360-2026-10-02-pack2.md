# Sweden 360 pack 2 proof (Candidate)

Work order `wo-sweden-360-2026-10-02`. Directive `wo-360-technical-directive-2026-10-02`. Orbit was not used.

Pack 1 is already Candidate on draft PR #20 at tip `9b6b4c12e9b8a3e64bcd831ca2b998175e8b3d17`: SE-01-002 through SE-01-010, nine static-ambient clips. Those clips were not regenerated.

Pack 2 looked for the next daytime scenes from SE-01-011 upward that lack `motion-10s-4x5.mp4`. On `main`, and on every other branch in this repo, the only `is_day` 1 scenes are SE-01-002 through SE-01-010. SE-01-011 through SE-01-091 are night (`is_day` 0, `daynight` night). Each of those 81 masters is night-only. None was opened, cropped, or encoded. No pan, zoom, or orbit was baked.

Image-to-video was probed and is unavailable (`POST https://api.x.ai/v1/videos/generations` returns 401 unauthenticated:no-credentials; no `XAI_API_KEY`; `media.generate_video` is not in this runtime). The lateral-sweep prompt was not sent. The static-ambient contingency (`ffmpeg crop=864:1080:0:0` on a daytime 4:5 master, locked camera, 864×1080, 10.0s, h264, yuv420p, +faststart) was not run, because no eligible daytime plate remains.

The next nine IDs, SE-01-011 through SE-01-019, are the pack window. All nine are night-only and were skipped.

| Scene | Caption | is_day | Retrieval | Disposition |
| --- | --- | --- | --- | --- |
| SE-01-011 | Skeppsbron, Stockholm | 0 | 2026-09-28T20:00:22+02:00 | skipped, night-only |
| SE-01-012 | Fjällgatan, Stockholm | 0 | 2026-09-28T20:00:25+02:00 | skipped, night-only |
| SE-01-013 | Nationalmuseum, Stockholm | 0 | 2026-09-28T20:00:28+02:00 | skipped, night-only |
| SE-01-014 | Royal Opera, Stockholm | 0 | 2026-09-28T20:00:30+02:00 | skipped, night-only |
| SE-01-015 | Riksdagshuset, Stockholm | 0 | 2026-09-28T20:00:32+02:00 | skipped, night-only |
| SE-01-016 | af Chapman, Stockholm | 0 | 2026-09-28T20:00:35+02:00 | skipped, night-only |
| SE-01-017 | Norr Mälarstrand, Stockholm | 0 | 2026-09-28T20:00:37+02:00 | skipped, night-only |
| SE-01-018 | Stockholm Public Library, Stockholm | 0 | 2026-09-28T20:00:40+02:00 | skipped, night-only |
| SE-01-019 | Östermalms Saluhall, Stockholm | 0 | 2026-09-28T20:00:42+02:00 | skipped, night-only |

SE-01-020 through SE-01-091 are the same: night-only, not clipped. Unmerged drafts SE-01-092 through SE-01-127 are not on `main`; their weather is also night, and they were not used.

Clip count: **0**. Method: **none** (no lateral-sweep i2v clip, no static-ambient clip).

No `▶ 360°` button was wired, because no new mp4 is on disk. `data.json` `motion` stays null. Approval status stays Candidate. Cosmo QC was not recorded.

Evidence: `evidence/motion/wo-sweden-360-2026-10-02-pack2.json` and `evidence/motion/SE-01-011.json` through `evidence/motion/SE-01-019.json`.

Do not merge.
