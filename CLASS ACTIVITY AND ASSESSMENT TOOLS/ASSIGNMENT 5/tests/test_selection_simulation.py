import unittest
from demonstrator import selection as s, simulation as sim


class TestSelection(unittest.TestCase):
    def test_weights_sum_100(self):
        self.assertEqual(sum(s.W0.values()), 100)
        self.assertEqual(sum(s.W_REVISED.values()), 100)
        for w, _ in s.SENS.values():
            self.assertEqual(sum(w.values()), 100)

    def test_hand_calculation_for_A(self):
        # 15*3 + 10*2 + 20*4 + 15*5 + 15*3 + 15*5 + 10*5 = 390 -> 3.90
        self.assertEqual(s.weighted(s.S0["A"], s.W0), 3.90)

    def test_scores_in_range(self):
        for a in s.S0.values():
            self.assertTrue(all(1 <= v <= 5 for v in a.values()))

    def test_selection_can_change(self):
        self.assertEqual(max(s.sensitivity()["S6 labels + institutions + usefulness/trust-heavy"].items(),
                             key=lambda kv: kv[1])[0], "D")


class TestSimulation(unittest.TestCase):
    def test_seeded_and_repeatable(self):
        self.assertEqual(sim.simulate_subject("Databases", 0.05), sim.simulate_subject("Databases", 0.05))

    def test_kappa_perfect_and_chance(self):
        a = ["Low", "Medium", "High"] * 10
        self.assertAlmostEqual(sim.cohen_kappa(a, a), 1.0)

    def test_noise_lowers_kappa(self):
        lo = sim.simulate_subject("Databases", 0.05)["examiner_kappa"]
        hi = sim.simulate_subject("Operating Systems", 0.35)["examiner_kappa"]
        self.assertGreater(lo, hi)
