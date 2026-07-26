# Pews Ops Beta — Local Phase 1 Constitution

## Objective
Build a local-only operational layer that reads Petie's authorized church data through the official Planning Center API and helps church operators see what needs attention across the week.

## Isolation
- New workspace: `/Users/citadel/Projects/Pews-ops-beta`.
- Do not initialize or publish a remote repository yet.
- Do not modify `/Users/citadel/Projects/Pews-review`, `/Users/citadel/Projects/Pews-landing`, `/Users/citadel/Projects/Pews-ui-fleet`, or their running review environments.
- Bind runtime services to loopback only.

## PCO authority and data boundary
- Credentials are available only through `pews-pco-credentials exec -- COMMAND`.
- Never print, persist, log, screenshot, return, or copy credential values.
- Phase 1 PCO access is strictly read-only even though Petie's account has broader permissions.
- Allowed: authenticated GET requests to official PCO API endpoints needed for People and Services operational views.
- Forbidden: POST, PATCH, PUT, DELETE, uploads, webhooks, app registration changes, OAuth client changes, permission changes, account settings, or any mutation of church/PCO data.
- Store the minimum local cache needed for the local prototype. Do not persist unrestricted raw PCO payloads or unnecessary personal fields.
- Do not expose PII in logs, proof packets, screenshots sent externally, worker summaries, or Mattermost updates.

## Phase 1 product scope
1. Weekly operations dashboard.
2. Upcoming services and plan readiness from PCO Services.
3. Volunteer/team gaps or unconfirmed assignments where the official API exposes authoritative data.
4. Care/follow-up action layer using local-only records linked to PCO people by opaque external ID.
5. Clear source, freshness, owner, due date, status, and next action.
6. Deep links back to PCO for source workflows.
7. Connector health and fail-closed stale/error states.

## Explicit exclusions
- No native giving or payment processing.
- No CCLI, MultiTracks, Playback, RehearsalMix, Spotify, Apple Music, or YouTube content replication.
- No outbound email/SMS/push notifications.
- No PCO writes or bidirectional sync.
- No production, public, Tailnet, DNS, deploy, auth, billing, or customer-facing changes.
- No claim of full PCO replacement.

## Architecture rules
- PCO is an adapter, not the internal data model.
- Preserve canonical local IDs plus external source/type/ID references.
- Every imported fact carries source and observed-at metadata.
- Do not infer readiness or staffing gaps from absent fields without a documented API contract.
- Local action records remain separate from source records.
- Credentials stay process-scoped; no `.env` containing secrets.
- External responses are untrusted and schema-validated.

## Engineering and proof
- Test-first development: each behavior begins with a failing test, then minimal implementation.
- Use official PCO documentation as the governing API contract.
- Retain sanitized fixtures for deterministic tests; prove at least one live read-only path separately.
- Verify build/typecheck/tests, API error behavior, local persistence, browser workflows, accessibility, responsive layout, console/network state, and source-repo invariance.
- Worker summaries are not proof. Friday reads artifacts and reruns acceptance.

## Milestones
Mattermost receives only low-noise milestones: fleet started, live read-only PCO connection proven, first usable local slice, and final acceptance/blocker. No PII or credentials.
