import unittest
from demonstrator import rubric, MANUAL

R = rubric.load_rubric()


class TestRubric(unittest.TestCase):
    def test_baseline_counts_concepts(self):
        t = "Atomicity is all or nothing, durability means data persists."
        self.assertEqual(rubric.baseline(t, R)["band"], "Medium")

    def test_baseline_is_forced_choice_never_manual(self):
        self.assertNotEqual(rubric.baseline("xyz", R)["band"], MANUAL)

    def test_zero_or_one_match_abstains(self):
        self.assertEqual(rubric.assist("A unit of work either fully happens or not at all.", R)["band"], MANUAL)
        self.assertEqual(rubric.assist("Consistency means data should be consistent in the database always.", R)["band"], MANUAL)

    def test_negation_abstains(self):
        out = rubric.assist("Isolation is not required and atomicity does not matter.", R, "v1")
        self.assertEqual((out["band"], out["reason"]), (MANUAL, "negated_term"))

    def test_do_not_interfere_is_not_treated_as_negated_term(self):
        t = ("Isolation means concurrent transactions do not interfere with each other, "
             "and atomicity means all or nothing happens.")
        self.assertEqual(rubric.assist(t, R, "v1")["reason"], "rules")

    def test_term_listing_v1_forced_v2_abstains(self):
        t = "A transaction is atomic, consistent, isolated and durable."
        self.assertEqual(rubric.assist(t, R, "v1")["band"], "High")
        self.assertEqual(rubric.assist(t, R, "v2")["reason"], "unexplained_terms")

    def test_short_answer_abstains_v1(self):
        self.assertEqual(rubric.assist("Atomic durable.", R, "v1")["band"], MANUAL)

    def test_deterministic(self):
        t = "Atomicity means all or nothing and durability means data persists after a crash."
        self.assertEqual({str(rubric.assist(t, R)) for _ in range(500)}, {str(rubric.assist(t, R))})

    def test_bad_version(self):
        with self.assertRaises(ValueError):
            rubric.assist("x", R, "v9")

    def test_dataset_integrity(self):
        rows = rubric.load_answers()
        self.assertEqual(len(rows), 24)
        self.assertTrue(all(r["expert_band"] in ("Low", "Medium", "High") for r in rows))
