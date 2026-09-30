# GoreeCloud Social dev.7 — Community Governance Reforge Research

**Research date:** 2026-09-30  
**Scope:** Community visibility, space-scoped capabilities, membership review, moderation boundaries, and internal community read models.

## Sources reviewed

### Discourse
- Project: Discourse.
- License: GPL-2.0-or-later.
- Primary references: official Discourse Meta documentation for user roles/permissions and category moderation, plus the official discourse/discourse repository.
- Relevant finding: site-wide administrator authority is distinct from category- or group-scoped moderation and membership-management authority.
- GoreeCloud requirement extracted: a community-local role must never silently become platform-wide authority; community ownership and moderation should be explicit and scope-bounded.

### Lemmy
- Project: Lemmy.
- License: AGPL-3.0.
- Primary references: official Lemmy moderation documentation, API community visibility documentation, and the official LemmyNet/lemmy repository.
- Relevant finding: community moderators are distinct from instance administrators; community bans are community-local; community visibility is explicitly modeled.
- GoreeCloud requirement extracted: community moderation, bans, visibility, and membership access must remain scoped to one community and must not imply platform-wide account authority.

### Flarum
- Project: Flarum.
- License: MIT.
- Primary references: official Flarum API documentation for permission groups and permission checks, plus the official Flarum framework repository.
- Relevant finding: permissions are evaluated as explicit abilities rather than inferred merely from presentation.
- GoreeCloud requirement extracted: Social should evaluate named community capabilities rather than treat role labels as a blanket authorization grant.

## Current landscape and tradeoffs

Community platforms generally converge on explicit membership, roles, scoped moderation, and visibility controls, but they differ in how much authority is attached to a role and whether moderation is community-local or site-wide.

GoreeCloud Social already has local community membership, invitation, join-request, rules, bans, moderation cases, and role labels. The missing architectural gap is an explicit policy layer that can distinguish local role eligibility from authoritative actor identity and can fail closed when the Identity binding is absent.

The dev.7 implementation therefore does not add public mutation APIs. It adds internal capability and read services that can later be called by authenticated endpoints after accepted GoreeCloud Identity, Privacy Shield, Wardveil Security, rate/resource, and audit controls exist.

## Independent implementation boundary

These projects were reviewed to understand mature community interaction patterns and authorization tradeoffs.

No Discourse, Lemmy, or Flarum source code, database schema, component implementation, branded terminology, ranking logic, visual design, token values, or product-specific architecture is copied into GoreeCloud Social.

The implementation is original Django/Python code using the existing GoreeCloud Social domain model.

## GoreeCloud-specific requirements

The dev.7 Community Governance tranche requires:

- community discovery to distinguish public communities from private/invitation-only communities;
- active community-local bans to fail closed for scoped community reads;
- public community posts to remain distinct from membership-only space-audience posts;
- community rules to follow community visibility;
- named privileged capabilities instead of blanket role authority;
- role eligibility to remain only a Social-local prerequisite;
- a positive privileged decision to additionally require an explicitly authoritative actor subject matching the Social profile's external GoreeCloud Identity subject;
- moderator, administrator, and owner capability sets to remain distinct;
- community authority to remain local to that community;
- join-request, membership, and moderation queues to remain internal and deny access when capability evaluation fails;
- no public mutation API, permission grant, session authentication, or platform-wide authority to be created by this tranche.

## Acceptance boundary

This research and source tranche do not establish accepted GoreeCloud Identity integration, Privacy Shield policy, Wardveil enforcement, public API authorization, abuse/rate protection, audit pipeline acceptance, rendered UI acceptance, deployment, production acceptance, or Stable lifecycle status.
