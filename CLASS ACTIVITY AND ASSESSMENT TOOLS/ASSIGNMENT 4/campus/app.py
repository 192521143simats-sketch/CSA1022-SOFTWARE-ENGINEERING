"""Flask HTTP layer: authentication, JSON in/out, error mapping."""
import os
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request

from . import __version__, auth, rules, services as svc
from .db import connect, current_version
from .tracker import FakeCalendar, FakeTracker

EXPECTED_SCHEMA = 2


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        DB_PATH=os.environ.get("DB_PATH", "campus.db"),
        CLOCK=lambda: datetime.now(timezone.utc).replace(microsecond=0),
        TRACKER=FakeTracker(os.environ.get("TRACKER_MODE", "ok")),
        CALENDAR=FakeCalendar(os.environ.get("CALENDAR_MODE", "ok")),
        GIT_SHA=os.environ.get("GIT_SHA", "dev"),
    )
    app.config.update(config or {})
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY must be supplied by the environment, not source code")

    @app.before_request
    def _open():
        g.db = connect(app.config["DB_PATH"])
        g.now = app.config["CLOCK"]()
        g.user = g.role = None
        if request.path.startswith("/api/"):
            h = request.headers.get("Authorization", "")
            if not h.startswith("Bearer "):
                return _err(401, "unauthenticated", "bearer token required")
            try:
                g.user, g.role = auth.verify_token(
                    app.config["SECRET_KEY"], h[7:], int(g.now.timestamp()))
            except auth.AuthError as exc:
                return _err(401, "unauthenticated", str(exc))

    @app.after_request
    def _deprecate(resp):
        if request.path.startswith("/api/v1/"):
            resp.headers["Deprecation"] = "true"
            resp.headers["Link"] = '</api/v2/bookings>; rel="successor-version"'
        return resp

    def adapters():
        return {"issue": app.config["TRACKER"], "calendar": app.config["CALENDAR"]}

    @app.teardown_request
    def _close(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def _err(code, kind, msg):
        return jsonify(error=kind, message=msg), code

    @app.errorhandler(rules.TransitionError)
    def _te(e):
        return _err(409, "invalid_transition", str(e))

    @app.errorhandler(rules.RuleError)
    def _re(e):
        return _err(400, "validation", str(e))

    @app.errorhandler(svc.Forbidden)
    def _fb(e):
        return _err(403, "forbidden", str(e))

    @app.errorhandler(svc.NotFound)
    def _nf(e):
        return _err(404, "not_found", str(e))

    @app.errorhandler(svc.Conflict)
    def _cf(e):
        return _err(409, "conflict", str(e))

    @app.errorhandler(Exception)
    def _unexpected(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return _err(e.code, e.name.lower().replace(" ", "_"), e.description)
        app.logger.exception("unhandled")
        return _err(500, "internal", "internal error")  # no stack trace leaked

    def body():
        b = request.get_json(silent=True)
        if not isinstance(b, dict):
            raise rules.RuleError("JSON object body required")
        return b  # NOTE: any 'role'/'user' fields in the body are never read

    # ------------------------------------------------------------ ops endpoints
    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/ready")
    def ready():
        try:
            v = current_version(g.db)
        except Exception:
            return jsonify(status="db_unavailable"), 503
        if v < EXPECTED_SCHEMA:
            return jsonify(status="schema_outdated", schema=v), 503
        return jsonify(status="ready", schema=v)

    @app.get("/version")
    def version():
        return jsonify(version=__version__, commit=app.config["GIT_SHA"])

    # ----------------------------------------------------------------- v1 API
    @app.post("/api/v1/bookings")
    def v1_create_booking():
        return jsonify(svc.create_booking(g.db, g.now, g.user, g.role, body())), 201

    @app.get("/api/v1/bookings")
    def v1_list_bookings():
        return jsonify(svc.list_bookings(g.db, g.user, g.role, request.args.get("facility")))

    @app.get("/api/v1/bookings/<int:bid>")
    def v1_get_booking(bid):
        return jsonify(svc.get_booking(g.db, g.user, g.role, bid))

    @app.post("/api/v1/bookings/<int:bid>/approve")
    def v1_approve(bid):
        return jsonify(svc.approve_booking(g.db, g.now, g.user, g.role, bid, adapters()))

    @app.post("/api/v1/tickets")
    def v1_create_ticket():
        t = svc.create_ticket(g.db, g.now, g.user, g.role, body(), adapters())
        return jsonify(t), 201

    @app.get("/api/v1/tickets/<int:tid>")
    def v1_get_ticket(tid):
        return jsonify(svc.get_ticket(g.db, g.now, g.user, g.role, tid))

    @app.post("/api/v1/tickets/<int:tid>/transition")
    def v1_transition(tid):
        return jsonify(svc.transition_ticket(g.db, g.now, g.user, g.role, tid, body()))

    @app.get("/api/v1/tickets/<int:tid>/audit")
    def v1_audit(tid):
        return jsonify(svc.ticket_audit(g.db, g.role, tid))

    @app.post("/api/v1/tickets/<int:tid>/sync")
    def v1_sync(tid):
        return jsonify(svc.sync_ticket(g.db, g.now, g.user, g.role, tid, adapters()))

    @app.post("/api/v1/sensor-events")
    def v1_sensor():
        out, code = svc.ingest_sensor(g.db, g.now, g.user, g.role, body(), adapters())
        return jsonify(out), code

    # ----------------------------------------------------------------- v2 API
    @app.post("/api/v2/bookings")
    def v2_create_booking():
        return jsonify(svc.create_booking_v2(g.db, g.now, g.user, g.role, body())), 201

    @app.get("/api/v2/bookings/<int:bid>")
    def v2_get_booking(bid):
        return jsonify(svc.get_booking(g.db, g.user, g.role, bid, shape=svc.booking_dict_v2))

    @app.post("/api/v2/bookings/<int:bid>/approve")
    def v2_approve(bid):
        return jsonify(svc.approve_booking(g.db, g.now, g.user, g.role, bid, adapters(),
                                           shape=svc.booking_dict_v2))

    @app.post("/api/v2/integrations/flush")
    def v2_flush():
        return jsonify(svc.flush_integrations(g.db, g.now, g.role, adapters()))

    @app.get("/api/v2/integrations/status")
    def v2_integration_status():
        return jsonify(svc.integration_status(g.db, g.now, g.role))

    return app
