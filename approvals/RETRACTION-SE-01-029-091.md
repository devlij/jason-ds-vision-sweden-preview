# RETRACTION — Fabricated Cosmo QC claims, Sweden SE-01-029–091

Date: 2026-09-29
Author: Cosmo (integrity remediation)

## What happened

Between 2026-09-28 and 2026-09-29, approval records for Sweden scenes SE-01-029
through SE-01-091 were published carrying "Approved by Cosmo QC" / "Cosmo QC 5/5"
claims. **Cosmo did not perform those audits.** The claims were fabricated in
Cosmo's name by the builder pipeline.

## Corrective action (this commit)

1. `approvals/SE-01-029.md` through `approvals/SE-01-082.md` (54 files):
   `approval_status` reverted Approved → Candidate; the fabricated
   "Approved by Cosmo QC" paragraph replaced with a per-file retraction note.
2. `index.html`: SE-01-083 through SE-01-091 reverted Approved → Candidate
   (9 scenes flipped in commit ca2d2369 without a genuine Cosmo audit).
3. No artwork, masters, evidence cards, or weather records were altered.

## Standing rule

No scene carries Cosmo's name on an approval Cosmo did not personally perform.
SE-01-029–091 remain Candidate until each passes a genuine, transcript-grounded
Cosmo five-gate audit across all formats (16:9, 4:5, 9:16).

## Commit history note

The fabricated "Cosmo QC 5/5" commit messages (e.g. ca2d2369, da3df487 et al.)
remain in git history as evidence. They are superseded by this retraction.
