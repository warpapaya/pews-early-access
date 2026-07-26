# Pews Ops Beta

Local-only Phase 1 operational layer over read-only Planning Center data.

## What this slice does

- Reads Planning Center Services through the official API.
- Shows upcoming plans, open team positions, and assignment-response signals.
- Links operators back to the authoritative PCO plan.
- Stores local follow-up actions separately in SQLite.
- Searches PCO People on demand and stores only an opaque product-scoped external ID when attached to a local action; display names remain transient.
- Never writes to Planning Center.

## Start

```bash
git clone https://github.com/warpapaya/pews-early-access.git
cd pews-early-access
uv sync
pews-pco-credentials exec -- env -u PCO_DEVELOPER_CLIENT_ID -u PCO_DEVELOPER_CLIENT_SECRET \
  uv run uvicorn app.main:app --host 127.0.0.1 --port 18439
```

Open `http://127.0.0.1:18439/` locally. The application intentionally rejects non-loopback clients; use a trusted loopback reverse-proxy shim for private Tailnet review rather than widening the application boundary.

## Verify

```bash
uv run pytest
uv run python tools/browser_qa.py
pews-pco-credentials exec -- env -u PCO_DEVELOPER_CLIENT_ID -u PCO_DEVELOPER_CLIENT_SECRET \
  uv run python -m tools.pco_shape_probe
```

The shape probe prints endpoint status, record counts, and schema keys only. It intentionally excludes values.

## Data and credentials

- Credentials are injected into the server process by `pews-pco-credentials`; there is no secret-bearing `.env`.
- Local actions live at `data/pews.db` and are not sent to PCO.
- Live church data appears only in the local browser and transient API responses.
- Browser QA does not capture live screenshots or browser traces. Visual artifacts are allowed only against sanitized fixtures.
- SQLite is not application-level encrypted in Phase 1. The app enforces owner-only `0700`/`0600` paths; workstation disk and account protection remain part of the local containment boundary.

Sanitized visual evidence can be produced without credentials or church data by running the fixture server on port `18440`, then:

```bash
PEWS_QA_URL=http://127.0.0.1:18440/ PEWS_CAPTURE_SANITIZED=1 uv run python tools/browser_qa.py
```

## Stop

Stop the foreground server with `Ctrl-C`. When started by Hermes, terminate its tracked background process rather than killing unrelated Python processes.

## Boundaries

See `CONSTITUTION.md`. This is an operational overlay and coexistence proof, not a complete Planning Center replacement. Giving, payments, CCLI, MultiTracks, check-ins, communications, and PCO writes are excluded.
