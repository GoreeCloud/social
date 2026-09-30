# GoreeCloud Social — Changelogs

## 2026-09-30 — Community Governance dev.7

- Advanced Development source to `0.1.0-dev.7`.
- Added original Community Governance services for public/private/invite-only community discovery, community-scoped post/rule reads, and internal pending-join-request, membership, and moderation-case queries.
- Added explicit named community capabilities with conservative moderator/admin/owner mappings.
- Required both Social-local role eligibility and an explicitly authoritative actor subject matching the profile's external GoreeCloud Identity subject before privileged community query authorization succeeds.
- Kept community authority space-local; no community role grants platform-wide authority.
- Active community bans now fail closed for the new scoped community read/capability layer.
- Added dev.7 regression tests and multi-source Reforge research informed by Discourse, Lemmy, and Flarum without copying third-party implementation.
- Migrated `goreecloud.platform.yaml` from Platform Contract 0.2 to 0.4 with exactly nine Integral Platform Systems represented fail-closed; Policy and Observability are now explicit blocked systems.
- Reconciled the canonical repository identity to `GoreeCloud/social` and the shared Glaze target to V1.6 / 1.6.0 where repository documentation previously carried stale values.
- No public community mutation API, accepted Identity/Policy authorization, Privacy Shield acceptance, Wardveil acceptance, deployment, production acceptance, or Stable promotion is established by this tranche.

## 2026-09-27 — Drive feature-roadmap migration

- Retired the synchronized Google Drive roadmap after confirming material parity with the repository roadmap.
- Moved feature authority to `IMPLEMENTED-FEATURES.md`, `PLANNED-FEATURES.md`, and this `CHANGELOGS.md`.
- No lifecycle promotion, deployment, or production acceptance is implied.
