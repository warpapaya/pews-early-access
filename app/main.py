from __future__ import annotations

import secrets
from pathlib import Path

import httpx
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app.pco import PCOClient
from app.store import ActionStore

ROOT = Path(__file__).resolve().parent.parent


def create_app(*, pco=None, db_path=None) -> Starlette:
    app = Starlette()
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    templates = Jinja2Templates(directory=ROOT / "templates")
    store = ActionStore(db_path or ROOT / "data" / "pews.db")
    connector = pco
    session_capability = secrets.token_urlsafe(32)

    async def local_only(request: Request, call_next):
        host = (request.client.host if request.client else "")
        if host not in {"127.0.0.1", "::1", "testclient"}:
            return JSONResponse({"detail": "Local access only"}, status_code=403)
        origin = request.headers.get("origin")
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            if request.cookies.get("pews_session") != session_capability:
                return JSONResponse({"detail": "Local session required"}, status_code=403)
            expected_host = request.headers.get("host", "")
            if origin and origin != f"http://{expected_host}":
                return JSONResponse({"detail": "Cross-origin mutation rejected"}, status_code=403)
        response = await call_next(request)
        if request.method == "GET" and request.cookies.get("pews_session") != session_capability:
            response.set_cookie(
                "pews_session",
                session_capability,
                httponly=True,
                samesite="strict",
                secure=False,
                path="/",
            )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; frame-ancestors 'none'; object-src 'none'; base-uri 'none'"
        )
        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=local_only)

    def get_connector():
        nonlocal connector
        if connector is None:
            connector = PCOClient.from_environment()
        return connector

    async def dashboard(request: Request):
        source = get_connector().dashboard()
        actions = store.list_actions()
        position_counts = [plan.get("needed_positions_count") for plan in source["plans"]]
        open_positions = (
            sum(position_counts)
            if source["connection"]["state"] != "unavailable"
            and all(value is not None for value in position_counts)
            else None
        )
        return templates.TemplateResponse(request, "dashboard.html", {
            "source": source,
            "actions": actions,
            "open_positions": open_positions,
        })

    async def people(request: Request):
        form = await request.form(max_fields=8, max_part_size=4096)
        q = str(form.get("q", ""))
        try:
            return JSONResponse({"data": get_connector().search_people(q)})
        except (httpx.HTTPError, ValueError, KeyError):
            raise HTTPException(status_code=503, detail="Planning Center people search is unavailable")

    async def create_action(request: Request):
        form = await request.form(max_fields=12, max_part_size=4096)
        try:
            store.create_action(
                str(form.get("title", "")),
                str(form.get("source_type", "manual")),
                str(form.get("external_id", "")),
                str(form.get("owner", "")),
                str(form.get("due_date", "")),
                str(form.get("priority", "normal")),
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error))
        return RedirectResponse("/", status_code=303)

    async def set_status(request: Request):
        action_id = request.path_params["action_id"]
        form = await request.form(max_fields=4, max_part_size=1024)
        try:
            store.set_status(action_id, str(form.get("status", "")))
        except (ValueError, KeyError):
            raise HTTPException(status_code=422, detail="Invalid action or status")
        return RedirectResponse("/", status_code=303)

    async def health(request: Request):
        return JSONResponse({"status": "ok", "mode": "local-only", "pco": "read-only"})

    app.router.routes.extend([
        Route("/", dashboard, methods=["GET"]),
        Route("/api/people/search", people, methods=["POST"]),
        Route("/actions", create_action, methods=["POST"]),
        Route("/actions/{action_id:str}/status", set_status, methods=["POST"]),
        Route("/health", health, methods=["GET"]),
    ])

    return app


app = create_app()
