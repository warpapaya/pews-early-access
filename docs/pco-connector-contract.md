# Planning Center connector decisions

## Governing sources

- Authentication: https://api.planningcenteronline.com/docs/overview/authentication
- API applications: https://api.planningcenteronline.com/docs/apps
- Rate limiting: https://api.planningcenteronline.com/docs/overview/rate-limiting
- Developer overview: https://www.planningcenter.com/developers

Verified behavior on 2026-07-24 through the authorized local PAT wrapper:

- `GET /people/v2/me` authenticates successfully.
- `GET /services/v2/service_types` returns the service types visible to Petie's PCO user.
- Future plans are available under each service type.
- Plan attributes include source dates, sort date, PCO URL, and needed-position count.
- Team-member records expose assignment status and team-position labels.
- Needed-position records expose quantity and team-position labels.

No credential values, names, plan titles, or other church values are retained in this document.

## Contract decisions

1. PCO is a source adapter, not the Pews domain model.
2. The data-plane adapter exposes only `get`/`get_all`; there is no generic method parameter. It rejects foreign origins, redirects, fragments, user-info, protocol-relative URLs, and paths outside `/services/v2/` or `/people/v2/` before transport.
3. Source observations are stamped with `observed_at`.
4. Failed refresh with no cache renders `unavailable`; failed refresh with a prior successful cache renders `stale`.
5. Pews does not infer readiness from missing source fields.
6. Local actions are never sent to PCO.
7. Phase 1 uses a PAT only for the authorized single-church local proof. Multi-church beta requires OAuth and per-organization grants.
8. The default PCO rate limit is documented as 100 requests per 20 seconds per authenticated user. The connector caches the aggregate dashboard for five minutes, limits the operational window to seven days, and limits detailed team reads to the next four plans.
9. Requests pin Services `2018-11-01` and People `2026-06-04`, use sparse fieldsets, cap pagination, and de-duplicate resources by JSON:API type and ID.
10. The application process refuses OAuth developer credentials, consumes PAT values from the environment at connector construction, and stores no raw PCO payloads.
11. Deep links are built from an allowlisted Planning Center Services route and opaque plan ID; upstream URL values are never rendered directly.

## Known limitations

- Some PCO plans have no specific title; the UI labels those records `Untitled service` rather than inventing a name.
- PCO's `dates` string can represent a broad or multi-date plan. The prototype displays the source value honestly; a later slice should model individual plan times for a tighter weekly view.
- Response-status semantics must remain tied to observed PCO values and official resource documentation; no generic absence-equals-gap rule is allowed.
- The local prototype has no multi-user authentication. Loopback binding, Host/Origin checks, and a per-launch HttpOnly SameSite=Strict browser capability are part of the current containment boundary, not a production security model.
