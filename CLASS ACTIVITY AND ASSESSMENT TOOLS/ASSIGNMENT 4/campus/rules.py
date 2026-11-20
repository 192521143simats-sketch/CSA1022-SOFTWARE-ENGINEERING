"""Pure business rules (no I/O). Every rule here is unit-testable in isolation."""
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

LEVELS = ("High", "Medium", "Low")

# Impact x Urgency -> priority (approved planning policy, nine cells)
MATRIX = {
    ("High", "High"): "M1", ("High", "Medium"): "M2", ("High", "Low"): "M3",
    ("Medium", "High"): "M2", ("Medium", "Medium"): "M3", ("Medium", "Low"): "M4",
    ("Low", "High"): "M3", ("Low", "Medium"): "M4", ("Low", "Low"): "M4",
}
# Planning assumption: SLA hours per priority
SLA_HOURS = {"M1": 4, "M2": 8, "M3": 24, "M4": 72}

KEYWORDS = {
    "Facilities": ["leak", "flood", "ceiling", "door", "lock"],
    "HVAC": ["ac", "compressor", "temperature", "cooling"],
    "AV-Network": ["projector", "display", "wifi", "network"],
}

# Planning assumptions (v1 global policy)
DEFAULT_MAX_MINUTES = 180
DEFAULT_TEMP_LIMIT = "28.0"

TRANSITIONS = {
    "New": ["Assigned"], "Assigned": ["In Progress"], "In Progress": ["Resolved"],
    "Resolved": ["Closed"], "Closed": [],
}


class RuleError(ValueError):
    """A business-rule or validation failure (maps to HTTP 400)."""


class TransitionError(RuleError):
    """Illegal ticket state change (maps to HTTP 409)."""


def priority(impact, urgency):
    if (impact, urgency) not in MATRIX:
        raise RuleError("invalid impact/urgency: %r/%r" % (impact, urgency))
    return MATRIX[(impact, urgency)]


def classify(text):
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    scores = {c: sum(1 for w in words if w in kws) for c, kws in KEYWORDS.items()}
    best = max(scores.values())
    top = [c for c, s in scores.items() if s == best]
    if best == 0 or len(top) != 1:
        return "Manual Review"
    return top[0]


def to_decimal(value):
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise RuleError("value is not numeric: %r" % (value,))
    if not d.is_finite():
        raise RuleError("value is not finite")
    return d


def breached(value, limit=DEFAULT_TEMP_LIMIT):
    """Strict greater-than policy: exactly the limit does NOT breach."""
    return to_decimal(value) > to_decimal(limit)


def valid_duration(minutes, max_minutes=DEFAULT_MAX_MINUTES):
    return 0 < minutes <= max_minutes


def overlaps(s1, e1, s2, e2):
    """Half-open intervals [s, e): back-to-back bookings do not overlap."""
    return s1 < e2 and s2 < e1


def parse_utc(text):
    """Accept only ISO-8601 with an explicit UTC offset; normalise to UTC."""
    if not isinstance(text, str):
        raise RuleError("timestamp must be a string")
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise RuleError("invalid timestamp: %r" % (text,))
    if dt.tzinfo is None:
        raise RuleError("timestamp needs an explicit UTC offset")
    return dt.astimezone(timezone.utc).replace(microsecond=0)


def fmt_utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sla_due(created, prio):
    return created + timedelta(hours=SLA_HOURS[prio])


def is_overdue(now, due):
    """Decision: a ticket is overdue only when now is strictly after the deadline."""
    return now > due


def check_transition(state, target, notes):
    if target not in TRANSITIONS.get(state, []):
        raise TransitionError("invalid transition %s -> %s" % (state, target))
    if target == "Resolved" and not (notes and notes.strip()):
        raise RuleError("resolution notes required")
