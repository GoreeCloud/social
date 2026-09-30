# GoreeCloud Social — Architecture

## Current Development shape

The first native foundation is a Django server with one Social domain application, one relational development database, a read-only development shell, and bounded health/status routes.

The current separation is intentional:

- `SocialProfile` owns social presentation metadata but references an external GoreeCloud Identity subject.
- Social relationships and content metadata remain application-owned.
- `visible_posts_for()` centralizes the current read-side audience rules so clients do not decide authorization independently.
- `src/social/community.py` adds the dev.7 Community Governance layer: scoped community discovery/posts/rules, named community capabilities, and guarded internal membership/moderation queues. Social-local role eligibility is necessary but not sufficient for privileged access; a positive decision also requires an explicitly authoritative actor subject matching the profile's external GoreeCloud Identity subject.
- media records contain storage references only; production storage and media processing are separate future capabilities.
- no public write HTTP API exists before platform authorization, privacy, security, and abuse requirements are ready;
- community capability decisions are local policy/read decisions only: they do not authenticate sessions, grant platform-wide authority, or replace GoreeCloud Identity, Policy, Privacy Shield, Wardveil Security, or audit acceptance.

## Intended service boundaries

Long-term Social can split high-load responsibilities without splitting authority semantics:

- Social Core — profiles, posts, relationships, communities, permissions, moderation state;
- Feed & Discovery — eligible-candidate selection and transparent ranking;
- Media — upload, processing, storage, derivatives, playback metadata;
- Realtime — notification/fan-out transport;
- Search — authorized indexing and retrieval;
- Trust & Safety — abuse signals, queues, evidence, enforcement coordination.

These components should communicate through documented, versioned contracts and GoreeCloud Mesh where appropriate. They must not bypass GoreeCloud Identity, Privacy Shield, Wardveil Security, or application ownership boundaries.


## Community Governance Development boundary

Development version `0.1.0-dev.7` introduces an internal Community Governance layer without changing the public HTTP mutation surface.

The layer separates:
1. **community visibility** — whether a public/private/invitation-only community may be disclosed;
2. **content visibility** — reuse of the existing authoritative post-visibility service inside a visible community;
3. **local role eligibility** — whether an accepted member's local role permits a named community capability; and
4. **authoritative actor binding** — whether the caller supplies an explicitly authoritative actor subject matching the Social profile's external Identity subject.

All four remain distinct. A moderator role cannot create Identity authority, and community authority cannot become platform-wide authority.

The current layer is intentionally conservative: active community bans fail closed, unsupported/non-community scopes fail closed, private communities require membership/ownership, and privileged queues raise permission denial when the capability decision is not positive.

Authenticated mutations, Identity session integration, GoreeCloud Policy decisions, Privacy Shield processing authority, Wardveil privileged-operation enforcement, abuse/rate controls, audit/event acceptance, and production UI remain future work.
