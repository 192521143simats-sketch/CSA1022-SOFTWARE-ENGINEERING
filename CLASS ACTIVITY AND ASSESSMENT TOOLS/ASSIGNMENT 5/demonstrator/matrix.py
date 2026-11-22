"""Stakes-discrepancy moderation-priority matrix (deterministic lookup)."""
from . import BANDS

STAKES = ("Low", "Medium", "High")
PRIORITY_RANK = {"Routine": 0, "Priority": 1, "Urgent": 2}

# rows = stakes, columns = band discrepancy 0, 1, 2
MATRIX = {
    "Low":    ("Routine", "Routine",  "Priority"),
    "Medium": ("Routine", "Priority", "Urgent"),
    "High":   ("Priority", "Urgent",  "Urgent"),
}


def discrepancy(examiner_band, assistant_band):
    return abs(BANDS.index(examiner_band) - BANDS.index(assistant_band))


def priority(stakes, disc):
    if stakes not in MATRIX:
        raise ValueError(f"unknown stakes level: {stakes}")
    if disc not in (0, 1, 2):
        raise ValueError(f"discrepancy must be 0, 1 or 2, got {disc}")
    return MATRIX[stakes][disc]


def moderation_priority(stakes, examiner_band, assistant_band):
    """Abstention (no suggestion) cannot raise or lower priority by discrepancy."""
    if assistant_band not in BANDS:
        return "Routine"
    return priority(stakes, discrepancy(examiner_band, assistant_band))
