# Sweden 360 pack 1 proof (Candidate)

Work order `wo-sweden-360-2026-10-05` pack 1. Directive `wo-360-technical-directive-2026-10-02`. Date 2026-10-05.

Method is **static-ambient**. Jason re-authorized static-ambient (Ken Burns / ffmpeg) for this round, the same contingency class as 2026-10-02. Image-to-video was not called. No orbit was encoded. Night masters were not opened. Approval status stays Candidate. Cosmo QC was not recorded.

Each genuine daylight 4:5 master on `main` was cropped with `ffmpeg crop=864:1080:0:0`, which drops the 190px label bar. A centered Ken Burns zoom (1.00 → 1.07 over 240 frames, no lateral pan) was encoded with ffmpeg `zoompan` to `assets/<scene-id-lower>-motion-10s-4x5.mp4`.

Self-QC is one attempt. A failed check holds that scene and deletes the partial. Three holds in a row stop the pack. This run did not get a second try.

| Scene | Caption | Status | Duration | Dims | frame0 mad | motion mad |
| --- | --- | --- | --- | --- | --- | --- |
| SE-01-002 | Vasa Museum, Stockholm | shipped | 10.0s | 864×1080 | 1.483 | 12.522 |
| SE-01-003 | City Hall, Stockholm | shipped | 10.0s | 864×1080 | 1.317 | 14.042 |
| SE-01-004 | Stortorget, Stockholm | shipped | 10.0s | 864×1080 | 1.589 | 16.884 |
| SE-01-005 | Nordic Museum, Stockholm | shipped | 10.0s | 864×1080 | 1.291 | 13.88 |
| SE-01-006 | Monteliusvägen, Stockholm | shipped | 10.0s | 864×1080 | 1.602 | 22.225 |
| SE-01-007 | Kungsträdgården, Stockholm | shipped | 10.0s | 864×1080 | 2.026 | 17.889 |
| SE-01-008 | Riddarholmen, Stockholm | shipped | 10.0s | 864×1080 | 1.452 | 17.09 |
| SE-01-009 | Skansen, Stockholm | shipped | 10.0s | 864×1080 | 1.824 | 18.667 |
| SE-01-010 | Strandvägen, Stockholm | shipped | 10.0s | 864×1080 | 1.712 | 20.763 |

Clip count: **9**. HOLD: 0. Stopped early: no.

Each shipped file is 24 fps, 240 frames, h264, yuv420p, +faststart, no audio, 864×1080, 10.0s.

`▶ 360°` is rendered only for a scene whose mp4 is on disk. It switches to `✕ Close`. The clip is autoplay, muted, loop, playsinline, and controls is false. Format clicks stop the clip. `data.json` `motion` stays null because that field is the aerial slot. Approval status stays Candidate.

Evidence: `evidence/motion/wo-sweden-360-2026-10-05-pack1.json`.

Do not merge.
