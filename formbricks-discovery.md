# CTM Formbricks creation and embed discovery (read-only)

**Retrieved:** 2026-07-24T15:47:25Z  
**Scope:** Existing CTM production deployment and local Friday/CTM source only. No survey, webhook, response, message, credential, or production state was created or changed.

## Outcome

The safe current path is:

1. Use the existing self-hosted Formbricks instance at `https://intake.clearlinetechmethods.com`.
2. Create the first version as a **Link Survey** in the Formbricks UI when practical. Formbricks' current official create-survey documentation explicitly recommends the UI for better visual feedback.
3. If repeatable automation is required, use the **v1 survey Management API** (not the v2 survey path):
   - create/list: `POST|GET /api/v1/management/surveys`
   - read/update: `GET|PUT /api/v1/management/surveys/{surveyId}`
   - authentication: `x-api-key: $FORMBRICKS_API_KEY`
4. Create as `draft`, read it back, configure and preview it, then make the explicit publication change to `inProgress` only in an approved mutation window.
5. Obtain the returned `data.id`; the confirmed public URL pattern is `https://intake.clearlinetechmethods.com/s/{surveyId}`.
6. Prefer a normal link/CTA unless inline presentation is required. For an inline embed, use Formbricks' generated iframe snippet and append `?embed=true` for minimalist embed mode.

Do **not** use the local direct-Postgres bootstrap helper against production. It predates the current API-backed workflow and updates the first survey row directly.

## Confirmed current deployment identifiers

| Item | Confirmed value | Evidence |
|---|---|---|
| Public base URL | `https://intake.clearlinetechmethods.com` | `formbricks/docker-compose.prod.yml:4-5,152`; live GET 200 |
| Organization ID | `cmqpyibwk000201o2hvdf5fy8` | authenticated read-only `GET /api/v2/me` |
| Workspace ID | `cmqpyibx2000301o21q2nx6y7` | authenticated read-only `GET /api/v2/me`; `formbricks/scripts/register-labops-webhook.py:20` |
| Existing survey ID (reference only) | `cmqpyiiaj000a01o25cx7mb6j` | authenticated read-only v1 list/get; `Contact.tsx:8-9` |
| Existing survey | `CTM LabOps Fit Check`, `type=link`, `status=inProgress`, slug `labops-fit-check` | authenticated read-only `GET /api/v1/management/surveys/{id}` |
| Existing public URL | `https://intake.clearlinetechmethods.com/s/cmqpyiiaj000a01o25cx7mb6j` | live GET 200; local source references |

### Project/environment naming caveat

This deployment's current API contract is workspace-centric. `GET /api/v2/me` returned one `workspacePermission`, no `environmentPermissions`, and no project identifier. The current v1 create route accepts `workspaceId` and resolves it to the workspace's production environment internally; current Formbricks source also accepts `environmentId` as a compatibility alternative. For this deployment, use the confirmed **workspace ID** above. Do not invent or copy a legacy project/environment ID.

## Authentication and local helper

- Secret file: `/Users/citadel/Projects/CTMWebsite2025/formbricks/.api.env`
- Variable name: `FORMBRICKS_API_KEY`
- File mode observed: `0600`
- Value intentionally omitted.
- Current official survey API authentication header: `x-api-key`.
- The existing webhook helper sends both `x-api-key` and `Authorization: Bearer ...` for compatibility (`formbricks/scripts/register-labops-webhook.py:44-55`), but `x-api-key` is the documented requirement.

Safe shell loading pattern (do not echo the variable):

```bash
cd /Users/citadel/Projects/CTMWebsite2025/formbricks
set -a
. ./.api.env
set +a
```

## Exact create/read/update procedure for a forthcoming Pews survey

### Option A — recommended initial build in UI

1. Sign in to `https://intake.clearlinetechmethods.com`.
2. In workspace `cmqpyibx2000301o21q2nx6y7`, create a **Link Survey**.
3. Keep it draft while questions, hidden fields, welcome card, endings, privacy copy, and mobile behavior are reviewed.
4. From the survey summary, use **Share** to copy the canonical public link or generated website embed code.
5. Preview without submitting. Publish only after copy/routing approval.

This is the lowest-risk method because Formbricks itself recommends UI creation for visual feedback and it avoids hand-authoring evolving question/block schemas.

### Option B — repeatable Management API creation

Use this only during an approved mutation window. Start with `status: "draft"`.

```bash
BASE='https://intake.clearlinetechmethods.com'
WORKSPACE_ID='cmqpyibx2000301o21q2nx6y7'

curl --fail-with-body \
  -X POST "$BASE/api/v1/management/surveys" \
  -H "x-api-key: $FORMBRICKS_API_KEY" \
  -H 'content-type: application/json' \
  --data @pews-survey-create.json
```

Minimum required create fields in the current documented contract:

```json
{
  "workspaceId": "cmqpyibx2000301o21q2nx6y7",
  "name": "Pews Early Access",
  "type": "link",
  "status": "draft"
}
```

A useful first complete payload should also include:

- `questions`: array of question objects with unique lowercase cuid-like IDs;
- `endings`: at least one `endScreen` with a unique ID;
- `welcomeCard`;
- `hiddenFields`: `{ "enabled": true, "fieldIds": [...] }` when attribution is required;
- `languages`: usually `[]` unless translations are configured;
- `triggers`: usually `[]` for a link survey;
- `singleUse` if needed;
- `styling`, `redirectUrl`, and related controls only when reviewed.

The current server route accepts legacy `questions` and transforms them into current `blocks`; GET responses expose both `blocks` and derived `questions`. This is safer than constructing `blocks` manually.

Supported question types documented by the current create endpoint include `openText`, `multipleChoiceSingle`, `multipleChoiceMulti`, `contactInfo`, `consent`, `cta`, `date`, `fileUpload`, `matrix`, `nps`, `pictureSelection`, `rating`, `cal`, `ranking`, and `address`. Question-type-specific fields still need validation (for example `inputType`, `choices`, `required`, and `shuffleOption`).

Immediately capture and read back the created ID:

```bash
SURVEY_ID='<data.id from POST response>'

curl --fail-with-body \
  -H "x-api-key: $FORMBRICKS_API_KEY" \
  "$BASE/api/v1/management/surveys/$SURVEY_ID"
```

Update only reviewed fields with `PUT`:

```bash
curl --fail-with-body \
  -X PUT "$BASE/api/v1/management/surveys/$SURVEY_ID" \
  -H "x-api-key: $FORMBRICKS_API_KEY" \
  -H 'content-type: application/json' \
  --data @pews-survey-update.json
```

The current update route merges the supplied fields with the existing survey before validation, so a focused payload such as `{ "name": "..." }` is supported. For question changes, supply the complete intended `questions` array, then read back both `questions` and `blocks`.

### Publication gate

After preview and routing review, publish with an explicit update:

```json
{ "status": "inProgress" }
```

Treat that as a production mutation. Do not combine create, full content update, webhook creation, and publication into one unaudited command.

## Public link and embed

### Link / CTA (preferred default)

```text
https://intake.clearlinetechmethods.com/s/{surveyId}
```

Hidden fields and campaign attribution can be appended as query parameters, but only fields configured in the survey's hidden-field allowlist will be retained. Existing CTM code demonstrates this pattern in:

- `ctm-website/client/src/components/CalButton.tsx:18-50`
- `ctm-website/client/src/pages/Contact.tsx:8-9`
- `docs/ctm-formbricks-intake-conversion-spec.md:48-56,114-123`

### Inline iframe

Current Formbricks source generates this shape:

```html
<div style="position: relative; height:80dvh; overflow:auto;">
  <iframe
    title="Pews Early Access"
    src="https://intake.clearlinetechmethods.com/s/SURVEY_ID?embed=true"
    frameborder="0"
    style="position:absolute; left:0; top:0; width:100%; height:100%; border:0;">
  </iframe>
</div>
```

If the URL already has query parameters, append `&embed=true`, not a second `?`.

The iframe posts `formbricksSurveyCompleted` on completion. Verify the origin before acting:

```js
window.addEventListener("message", (event) => {
  if (
    event.origin === "https://intake.clearlinetechmethods.com" &&
    event.data === "formbricksSurveyCompleted"
  ) {
    // Local UI action only unless a separately approved workflow says otherwise.
  }
});
```

Read-only response-header proof on 2026-07-24:

- `/s/cmqpyiiaj000a01o25cx7mb6j` returned `200`;
- the survey route had no `X-Frame-Options` header;
- its CSP included `frame-ancestors *`.

The Formbricks admin/root route is not equivalent: it returned `X-Frame-Options: SAMEORIGIN` and CSP `frame-ancestors 'self'`. Embed only the `/s/{surveyId}` route.

## Proven CTM create/update workflow vs historical shortcuts

### Confirmed current

- Production survey CRUD is available under **API v1**, authenticated with the current key:
  - `GET /api/v1/management/surveys?limit=100` → 200, one survey;
  - `GET /api/v1/management/surveys/{existingId}` → 200.
- Current API identity/webhook/response surfaces are **API v2**:
  - `GET /api/v2/me` → 200;
  - `GET /api/v2/management/webhooks?limit=100` → 200;
  - `GET /api/v2/management/responses?limit=1` → 200.
- `GET /api/v2/management/surveys` → 404. Do not assume every management resource moved to v2.
- Existing website embedding is presently link/CTA based, not iframe based.

### Historical/local-only — do not use for the new production survey

- `formbricks/scripts/configure-labops-survey.py` directly updates the first `Survey` row in local Postgres (`lines 181-220`). It was explicitly written as a local-dev bootstrap helper and can overwrite the wrong survey if reused.
- `formbricks/README.md:19-27` describes older local setup and manual public-link copying.
- Historical session `20260622_214715_f10964` established the API key and local v1/v2 behavior; current production GETs above supersede its local-only assumptions.
- The compose file currently defaults `FORMBRICKS_TAG` to `latest`; no exact Formbricks application version is pinned in the repository. Therefore this report cites live endpoint behavior and current Formbricks source/docs rather than claiming an exact deployed semantic version.

## Mattermost DM helper used by Friday (read-only discovery)

Established cached Petie DM target:

- `/Users/citadel/.hermes/profiles/friday/mattermost-dm-target.json`
- target username: `pclark`
- target user ID: `jgq78iefoiyejx4ibakgo68b9h`
- existing direct channel ID: `ch9zi1nmo38yffbnrjjntbj3jo`

Current read-only proof:

- `GET /api/v4/users/me` → 200, Friday bot username `hermes`;
- `GET /api/v4/users/jgq78iefoiyejx4ibakgo68b9h` → 200, username `pclark`;
- `GET /api/v4/channels/ch9zi1nmo38yffbnrjjntbj3jo` → 200, type `D` (direct).

Existing helper/API paths:

- `/Users/citadel/.hermes/profiles/friday/scripts/send_basin_packet_mattermost.py`
  - reads the cached DM channel ID;
  - optional attachment: `POST /api/v4/files`;
  - message: `POST /api/v4/posts` with `channel_id`;
  - verification: `GET /api/v4/posts/{postId}`.
- `/Users/citadel/.hermes/profiles/friday/scripts/mattermost_deliverable_packet.py`
  - preferred reusable review-packet helper;
  - resolves a configured channel alias, uploads previewable files, posts, and verifies the returned post.

If no cached direct channel existed, Mattermost's direct-channel resolution/creation path would require `POST /api/v4/channels/direct` with the two user IDs. That is a mutation and was not called. No Mattermost message or file was sent during this discovery.

## Read-only verification results

| Probe | Result |
|---|---|
| `GET https://intake.clearlinetechmethods.com/` | 200 |
| `GET .../s/cmqpyiiaj000a01o25cx7mb6j` | 200, HTML |
| unauthenticated `GET .../api/v2/me` | 401 (expected) |
| authenticated `GET .../api/v2/me` | 200 |
| authenticated `GET .../api/v2/management/webhooks?limit=100` | 200, one webhook |
| authenticated `GET .../api/v2/management/responses?limit=1` | 200 |
| authenticated `GET .../api/v1/management/surveys?limit=100` | 200, one survey |
| authenticated `GET .../api/v1/management/surveys/{existingId}` | 200 |
| authenticated `GET .../api/v2/management/surveys` | 404 (endpoint absent) |
| authenticated environment/workspace list guesses under v1/v2 | 404; identifiers come from `/api/v2/me` |
| Mattermost identity/user/direct-channel GETs | 200/200/200 |

## Sanitized tool/command list

Only read-only HTTP methods and local reads were used. Secret values were loaded in-process and never printed.

```text
search_files / read_file:
  /Users/citadel/Projects/CTMWebsite2025/formbricks/**
  /Users/citadel/Projects/CTMWebsite2025/docs/**
  /Users/citadel/Projects/CTMWebsite2025/ctm-website/client/**
  /Users/citadel/.hermes/profiles/friday/scripts/**
  /Users/citadel/.hermes/profiles/friday/mattermost-dm-target.json

session_search:
  "Formbricks survey create update embed"
  "intake.clearlinetechmethods.com"
  "/api/v2/management/surveys"
  "FORMBRICKS_API_KEY survey"

HTTP GET/HEAD only:
  curl/urllib GET https://intake.clearlinetechmethods.com/
  curl/urllib GET https://intake.clearlinetechmethods.com/s/<existing-id>
  urllib GET /api/v2/me
  urllib GET /api/v2/management/webhooks?limit=100
  urllib GET /api/v2/management/responses?limit=1
  urllib GET /api/v1/management/surveys?limit=100
  urllib GET /api/v1/management/surveys/<existing-id>
  urllib GET Mattermost /api/v4/users/me
  urllib GET Mattermost /api/v4/users/<target-id>
  urllib GET Mattermost /api/v4/channels/<cached-direct-channel-id>

Authoritative source retrieval (GET only):
  https://formbricks.com/docs/api-reference/management-api--survey/create-survey.md
  https://formbricks.com/docs/api-reference/management-api--survey/update-survey.md
  https://raw.githubusercontent.com/formbricks/formbricks/main/docs/surveys/link-surveys/embed-surveys.mdx
  current Formbricks API v1 survey route source under apps/web/app/api/v1/management/surveys/
```

## Sources

### Local, deployment-specific

- `/Users/citadel/Projects/CTMWebsite2025/formbricks/docker-compose.prod.yml`
- `/Users/citadel/Projects/CTMWebsite2025/formbricks/README.md`
- `/Users/citadel/Projects/CTMWebsite2025/formbricks/scripts/configure-labops-survey.py`
- `/Users/citadel/Projects/CTMWebsite2025/formbricks/scripts/register-labops-webhook.py`
- `/Users/citadel/Projects/CTMWebsite2025/formbricks/pipeline-runbook.md`
- `/Users/citadel/Projects/CTMWebsite2025/docs/ctm-formbricks-intake-conversion-spec.md`
- `/Users/citadel/Projects/CTMWebsite2025/ctm-website/client/src/components/CalButton.tsx`
- `/Users/citadel/Projects/CTMWebsite2025/ctm-website/client/src/pages/Contact.tsx`
- `/Users/citadel/.hermes/profiles/friday/scripts/send_basin_packet_mattermost.py`
- `/Users/citadel/.hermes/profiles/friday/scripts/mattermost_deliverable_packet.py`
- `/Users/citadel/.hermes/profiles/friday/mattermost-dm-target.json`
- Friday session `20260622_214715_f10964` (historical API setup; current GETs used for final confirmation)

### Current authoritative Formbricks sources

- https://formbricks.com/docs/api-reference/management-api--survey/create-survey
- https://formbricks.com/docs/api-reference/management-api--survey/update-survey
- https://github.com/formbricks/formbricks/blob/main/docs/surveys/link-surveys/embed-surveys.mdx
- https://github.com/formbricks/formbricks/blob/main/apps/web/app/api/v1/management/surveys/route.ts
- https://github.com/formbricks/formbricks/blob/main/apps/web/app/api/v1/management/surveys/%5BsurveyId%5D/route.ts
- https://github.com/formbricks/formbricks/blob/main/apps/web/app/(app)/workspaces/%5BworkspaceId%5D/surveys/%5BsurveyId%5D/(analysis)/summary/components/shareEmbedModal/website-embed-tab.tsx

## Remaining uncertainty / approval gates

- The repository uses `FORMBRICKS_TAG=latest`; the exact running semantic version was not exposed by the public HTML and was not claimed.
- No Pews question schema, privacy copy, retention policy, hidden-field allowlist, or routing destination was supplied here. Those must be reviewed before creation/publication.
- No API create/update/publish, webhook mutation, response submission, external message, or Formbricks admin mutation was performed.
