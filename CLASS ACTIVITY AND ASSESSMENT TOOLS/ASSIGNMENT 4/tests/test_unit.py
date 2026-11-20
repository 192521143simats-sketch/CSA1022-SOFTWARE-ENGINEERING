"""UNIT tests: pure rules, no database, no HTTP."""
from datetime import datetime, timedelta, timezone

import pytest

from campus import auth, rules

pytestmark = pytest.mark.unit
T0 = datetime(2026, 11, 20, 8, 0, 0, tzinfo=timezone.utc)

MATRIX_EXPECTED = [
    ("High", "High", "M1"), ("High", "Medium", "M2"), ("High", "Low", "M3"),
    ("Medium", "High", "M2"), ("Medium", "Medium", "M3"), ("Medium", "Low", "M4"),
    ("Low", "High", "M3"), ("Low", "Medium", "M4"), ("Low", "Low", "M4"),
]


@pytest.mark.parametrize("impact,urgency,expected", MATRIX_EXPECTED)
def test_U1_priority_matrix_all_nine_cells(impact, urgency, expected):
    assert rules.priority(impact, urgency) == expected


@pytest.mark.parametrize("impact,urgency", [("Critical", "High"), ("High", None), ("", ""), ("high", "high")])
def test_U2_priority_rejects_values_outside_the_matrix(impact, urgency):
    with pytest.raises(rules.RuleError):
        rules.priority(impact, urgency)


@pytest.mark.parametrize("value,expected", [
    ("27.99", False), ("28.00", False), (28, False), (28.0, False), ("28.01", True), (28.01, True), (90, True)])
def test_U3_sensor_threshold_boundary_is_strictly_greater_than(value, expected):
    assert rules.breached(value) is expected


@pytest.mark.parametrize("bad", ["abc", None, float("nan"), float("inf")])
def test_U3b_sensor_value_must_be_finite_number(bad):
    with pytest.raises(rules.RuleError):
        rules.breached(bad)


@pytest.mark.parametrize("minutes,ok", [(-5, False), (0, False), (1, True), (179, True), (180, True), (181, False)])
def test_U4_booking_duration_boundaries(minutes, ok):
    assert rules.valid_duration(minutes) is ok


@pytest.mark.parametrize("a,b,expected", [
    ((600, 720), (700, 800), True),     # partial overlap
    ((600, 720), (720, 800), False),    # back-to-back (end == start)
    ((600, 720), (540, 600), False),    # back-to-back other side
    ((600, 720), (600, 720), True),     # identical
    ((600, 720), (610, 620), True),     # contained
    ((600, 720), (800, 900), False),    # disjoint
])
def test_U5_overlap_is_half_open(a, b, expected):
    assert rules.overlaps(*a, *b) is expected
    assert rules.overlaps(*b, *a) is expected   # symmetric


@pytest.mark.parametrize("prio,hours", [("M1", 4), ("M2", 8), ("M3", 24), ("M4", 72)])
def test_U6_sla_due_and_overdue_boundaries(prio, hours):
    due = rules.sla_due(T0, prio)
    assert due == T0 + timedelta(hours=hours)
    assert rules.is_overdue(due - timedelta(seconds=1), due) is False
    assert rules.is_overdue(due, due) is False                     # decision: equality is NOT overdue
    assert rules.is_overdue(due + timedelta(seconds=1), due) is True


@pytest.mark.parametrize("text,expected", [
    ("Water leak from lab ceiling", "Facilities"),
    ("AC compressor tripping", "HVAC"),
    ("leak and projector fault", "Manual Review"),        # tie
    ("strange noise somewhere", "Manual Review"),          # unknown
    ("", "Manual Review"), (None, "Manual Review"),
])
def test_U7_classification_and_ambiguity_goes_to_review(text, expected):
    assert rules.classify(text) == expected


def test_U8_transition_rules():
    rules.check_transition("New", "Assigned", None)
    with pytest.raises(rules.TransitionError):
        rules.check_transition("New", "Resolved", "x")          # skip
    with pytest.raises(rules.TransitionError):
        rules.check_transition("Closed", "New", None)           # reopen
    for notes in (None, "", "   "):
        with pytest.raises(rules.RuleError):
            rules.check_transition("In Progress", "Resolved", notes)
    rules.check_transition("In Progress", "Resolved", "Replaced breaker")


@pytest.mark.parametrize("bad", ["2026-11-21T10:00:00", "yesterday", "", None, 12345])
def test_U9_timestamps_need_explicit_offset(bad):
    with pytest.raises(rules.RuleError):
        rules.parse_utc(bad)


def test_U9b_offsets_are_normalised_to_utc():
    assert rules.fmt_utc(rules.parse_utc("2026-11-21T15:30:00+05:30")) == "2026-11-21T10:00:00Z"


def test_U10_token_expiry_tamper_and_wrong_secret():
    tok = auth.issue_token("s1", "alice", "student", 1000, ttl=60)
    assert auth.verify_token("s1", tok, 1060) == ("alice", "student")     # last valid second
    with pytest.raises(auth.AuthError):
        auth.verify_token("s1", tok, 1061)                                # expired
    with pytest.raises(auth.AuthError):
        auth.verify_token("other", tok, 1000)                             # wrong secret
    body, sig = tok.split(".")
    with pytest.raises(auth.AuthError):
        auth.verify_token("s1", body + "." + "0" * len(sig), 1000)        # tampered signature
