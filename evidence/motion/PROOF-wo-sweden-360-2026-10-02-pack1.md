# Sweden 360 pack 1 proof (Candidate)

Work order `wo-sweden-360-2026-10-02`. Directive `wo-360-technical-directive-2026-10-02`. Orbit was not used.

Image-to-video is unavailable (`POST https://api.x.ai/v1/videos/generations` returns 401 unauthenticated:no-credentials; no `XAI_API_KEY`; `media.generate_video` is not in this runtime). The lateral-sweep prompt was not sent. No pan, zoom, or orbit was encoded.

Method is **static-ambient**, the same contingency as Denmark pack1 and France pack1. Each genuine daytime 4:5 master was downloaded from `main` through the GitHub API, then `ffmpeg crop=864:1080:0:0` removed the 190px label bar. The camera stays locked. Sky, water, foliage, and flags already in the plate move only inside their own masks. A plate whose life mask is under 4% is a locked-off still for 10.0s. Architecture outside those masks is not displaced. Night masters were not opened. Approval status stays Candidate. Cosmo QC was not recorded.

Pack 1 is SE-01-002 through SE-01-010 (9 daytime scenes). SE-01-001 is night (06:41, before the 06:45 sunrise, `is_day` 0) and was skipped. SE-01-011 through SE-01-091 are night and were skipped.

| Scene | Caption | Variant | Duration | Dims | Drift |
| --- | --- | --- | --- | --- | --- |
| SE-01-002 | Vasa Museum, Stockholm | ambient | 10.0s | 864×1080 | 0.047 |
| SE-01-003 | City Hall, Stockholm | ambient | 10.0s | 864×1080 | 0.032 |
| SE-01-004 | Stortorget, Stockholm | ambient | 10.0s | 864×1080 | 0.039 |
| SE-01-005 | Nordic Museum, Stockholm | ambient | 10.0s | 864×1080 | 0.091 |
| SE-01-006 | Monteliusvägen, Stockholm | ambient | 10.0s | 864×1080 | 0.055 |
| SE-01-007 | Kungsträdgården, Stockholm | ambient | 10.0s | 864×1080 | 0.103 |
| SE-01-008 | Riddarholmen, Stockholm | ambient | 10.0s | 864×1080 | 0.046 |
| SE-01-009 | Skansen, Stockholm | ambient | 10.0s | 864×1080 | 0.085 |
| SE-01-010 | Strandvägen, Stockholm | ambient | 10.0s | 864×1080 | 0.077 |

Clip count: **9**. HOLD: 0.

Each shipped file is `assets/<scene-id-lower>-motion-10s-4x5.mp4`: 24 fps, 240 frames, h264, yuv420p, +faststart, no audio, 864×1080, 10.0s.

`▶ 360°` is rendered only for a scene whose mp4 is on disk. It switches to `✕ Close`. The clip is autoplay, muted, loop, playsinline, and controls is false. Format clicks stop the clip. `data.json` `motion` stays null because that field is the aerial slot and preflight rejects an aerial that was not produced. Approval status stays Candidate.

Evidence: `evidence/motion/wo-sweden-360-2026-10-02-pack1.json` and `evidence/motion/SE-01-002.json` through `evidence/motion/SE-01-010.json`.

Do not merge.
