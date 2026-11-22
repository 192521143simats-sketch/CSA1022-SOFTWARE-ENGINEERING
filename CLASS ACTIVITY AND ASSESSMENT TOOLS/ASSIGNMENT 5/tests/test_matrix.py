import unittest
from demonstrator import matrix


class TestMatrix(unittest.TestCase):
    def test_nine_cells(self):
        self.assertEqual(matrix.priority("Low", 0), "Routine")
        self.assertEqual(matrix.priority("High", 0), "Priority")
        self.assertEqual(matrix.priority("Medium", 2), "Urgent")

    def test_monotonic(self):
        r = matrix.PRIORITY_RANK
        for s in matrix.STAKES:
            for d in (0, 1):
                self.assertLessEqual(r[matrix.priority(s, d)], r[matrix.priority(s, d + 1)])

    def test_abstention_is_routine(self):
        self.assertEqual(matrix.moderation_priority("High", "Low", "Manual Review"), "Routine")

    def test_invalid(self):
        with self.assertRaises(ValueError):
            matrix.priority("Extreme", 0)
        with self.assertRaises(ValueError):
            matrix.priority("Low", 5)
