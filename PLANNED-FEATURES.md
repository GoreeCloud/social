# GoreeCloud Social — Planned Features

> **Authority:** Repository-native planned-feature record. Google Drive roadmap/changelog mirrors are retired and must not be maintained as competing feature authority.

**Status:** Active roadmap control  
**As of:** 2026-09-30  
**Canonical repository:** `GoreeCloud/social`  
**Current Development source:** `0.1.0-dev.7`  
**Platform Contract:** `2.0` — lifecycle `forge`; nine systems represented; application remains nonconformant

## Roadmap

| ID | Feature / obligation | Priority | Current state |
| --- | --- | --- | --- |
| FR-001 | Maintain repository-native implemented/planned feature state and changelog from verified source. | P0 | Ongoing control |
| FR-010 | Community Governance: public/private/invite-only discovery, scoped reads, named capabilities, and internal privileged queues. | P0 | **Bounded source implemented in dev.7.** Public mutation APIs and accepted Identity-backed authorization remain open. |
| FR-011 | Community membership workflows: invitations, join requests, approvals/rejections, member removal, suspension, role changes, and ownership transfer. | P0 | Domain groundwork exists; authenticated mutation workflows remain planned. |
| FR-012 | Community moderation operations: moderator teams, scoped moderation queues, ban/unban operations, reversible actions, appeals, attributable audit evidence, and anti-abuse controls. | P0 | Internal models and dev.7 scoped moderation read exist; production workflows and accepted platform integrations remain planned. |
| FR-013 | Community presentation features: pinned content, announcements, rule acknowledgement, member directory, community profile/about surface, and scoped search/discovery. | P1 | Planned |
| FR-014 | Community authorization integration with GoreeCloud Identity and GoreeCloud Policy. | P0 | dev.7 has fail-closed subject/capability contract only; runtime integration and acceptance remain blocked. |
| FR-015 | Community privacy/security integration with Privacy Shield and Wardveil Security, including moderation evidence purpose/retention and privileged-operation protection. | P0 | Planned / blocked pending producer contracts and acceptance |
| FR-020 | Public authenticated publishing, editing, replies, bookmarks, poll creation/voting, reactions, reposts, mentions, hashtags, and deletion APIs. | P0 | Domain groundwork partial; public mutation APIs remain planned |
| FR-030 | Public Following/Chronological APIs plus Discover/For You, Video, media, and recommendation controls with transparent user choice. | P1 | Internal Following/Chronological read models exist; public delivery and recommendation systems remain planned |
| FR-040 | Production media pipeline: authorized upload, validation, Wardveil evaluation, metadata handling, image derivatives, transcoding, captions/subtitles, storage, streaming, deletion, and export. | P0 | Planned |
| FR-050 | Glaze UI V1.6 / 1.6.0 consumer adoption with Social-specific responsive, accessibility, form-factor, performance, rollback, Human Visual Excellence, and production acceptance. | P0 | Required; current shell is Development-only and unaccepted |
| FR-060 | Complete Platform Contract 2.0 integrations for Manager, Privacy Shield, Wardveil Security, Everkeep, Glaze UI, Mesh, Identity, Policy, and Observability. | P0 | Manifest reconciled to 2.0 / Forge; all application-specific acceptance remains fail-closed |
| FR-070 | Everkeep backup/restore, portable export, migration, retention reconciliation, and recovery testing for permitted Social data. | P0 | Planned |
| FR-080 | Notifications, Messenger sharing, Universal Search, authorized Contacts discovery, deep links, and bounded Social events through GoreeCloud Mesh. | P1 | Planned |

## Community dev.7 boundary

`0.1.0-dev.7` is a **source implementation milestone**, not a production authorization milestone.

It implements an original GoreeCloud community policy/read layer that:
- distinguishes community visibility from membership-only content;
- keeps active community bans fail-closed for scoped reads;
- evaluates named moderator/administrator/owner capabilities;
- requires an explicitly authoritative actor subject matching the profile's external Identity subject before a privileged decision becomes positive;
- keeps community authority local to one community;
- exposes no public community mutation endpoint.

Remaining Community work includes authenticated mutations, accepted Identity/Policy authority, Privacy Shield and Wardveil integration, abuse/rate controls, moderator audit evidence, pinned/announcement data behavior, rule acknowledgement, mature discovery/search, UI surfaces, and application acceptance.

## Reconciliation rule

At each material feature change, reconcile this file against current source, `IMPLEMENTED-FEATURES.md`, `CHANGELOGS.md`, the authoritative project specification, and GoreeCloud Tasks Management. Do not mark a feature complete, Stable, deployed, production-ready, or accepted without the evidence required for that claim.
