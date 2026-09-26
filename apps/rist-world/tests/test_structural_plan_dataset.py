from pathlib import Path
import json
import unittest


class StructuralPlanDatasetContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.path = root / "data" / "shaelvien_rist_structural_plan_v1.json"
        cls.plan = json.loads(cls.path.read_text(encoding="utf-8"))

    def test_format_and_build_rule_are_versioned(self):
        self.assertEqual(self.plan["format"], "SHAELVIEN_RIST_STRUCTURAL_PLAN_V1")
        self.assertIn("Phase 1", self.plan["build_rule"])
        self.assertIn("Phase 2", self.plan["build_rule"])

    def test_product_modes_are_distinct_presentations_of_shared_truth(self):
        self.assertEqual(
            self.plan["product_matrix"]["SHAELVIEN"]["purpose"],
            "guided emergence",
        )
        self.assertEqual(
            self.plan["product_matrix"]["RIST"]["purpose"],
            "direct construction and operation",
        )
        rules = {item["id"]: item["rule"] for item in self.plan["non_negotiable_invariants"]}
        self.assertEqual(rules["INV-001"], "One underlying truth, multiple presentations.")

    def test_spatial_truth_and_authority_remain_locked(self):
        rules = {item["id"]: item["rule"] for item in self.plan["non_negotiable_invariants"]}
        self.assertIn("WORLD -> REGION -> LOCAL -> INSTANCE -> ENCOUNTER", rules["INV-003"])
        self.assertEqual(rules["INV-005"], "Permissions remain server-authoritative.")

    def test_guided_gm_has_persistence_and_run_blockers_recorded(self):
        blockers = {item["id"]: item for item in self.plan["blockers"]}
        self.assertEqual(blockers["BLK-001"]["area"], "guided_gm_persistence")
        self.assertEqual(blockers["BLK-002"]["area"], "play_loop")
        self.assertEqual(blockers["BLK-003"]["area"], "promotion")

    def test_truth_lifecycle_requires_explicit_promotion(self):
        states = [item["state"] for item in self.plan["truth_lifecycle"]]
        self.assertEqual(
            states,
            [
                "PRIVATE_DRAFT",
                "PREPARED",
                "IN_PLAY",
                "PLAY_RECORDED",
                "CONSEQUENCE_ACCEPTED",
                "PROMOTED",
            ],
        )

    def test_implementation_sequence_builds_foundation_before_more_shell(self):
        phases = {item["phase"]: item["name"] for item in self.plan["implementation_sequence"]}
        self.assertEqual(phases[1], "FOUNDATION_MODE_AND_NAVIGATION")
        self.assertEqual(phases[2], "GUIDED_GM_DATA")
        self.assertEqual(phases[3], "GUIDED_GM_RUN_LOOP")


if __name__ == "__main__":
    unittest.main()
