# Sweden 360 pack 1 proof (Candidate)

Work order `wo-sweden-360-2026-10-02`. Directive `wo-360-technical-directive-2026-10-02`. Orbit was not used.

Pack 1 is the daytime set that actually exists in this catalog: **SE-01-002 through SE-01-010** (9 scenes). SE-01-001 is night (06:41, before the 06:45 sunrise, `is_day` 0) and was skipped. SE-01-011 through SE-01-091 are night and were skipped. No scene already had `motion-10s-4x5.mp4`. The daytime pool stops at 9, short of 12.

Each of those nine masters was read through the GitHub API (`assets/sweden/Stockholm/<id>-4x5.png` on `main`). They are 864×1270. `ffmpeg` crop `864:1080:0:0` was checked on SE-01-002 and yields 864×1080. No clip was encoded.

Image-to-video is unavailable here: `media.generate_video` is not in this runtime, and `https://api.x.ai/v1` returns 401 with no `XAI_API_KEY`. The static-ambient prompt needs that same generator, so it was not submitted. Nothing was faked. All nine are **HOLD**. `data.json` `motion` stays null, so no 360° gallery button was wired. Approval status stays Candidate. No Cosmo QC was recorded.

Evidence: `evidence/motion/wo-sweden-360-2026-10-02-pack1.json` and `evidence/motion/SE-01-002.json` through `SE-01-010.json`.

Do not merge.
