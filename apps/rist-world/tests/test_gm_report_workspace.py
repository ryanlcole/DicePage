from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "Components" / "GmReportWorkspace.razor"
ADAPTER = ROOT / "wwwroot" / "gm-report-builder.js"


class GameMasterReportContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = REPORT.read_text(encoding="utf-8")
        cls.adapter = ADAPTER.read_text(encoding="utf-8")

    def test_report_uses_shared_character_and_encounter_join_rows(self):
        self.assertIn("rist.character-report-row.v1.", self.source)
        self.assertIn("rist.encounter-report-row.v1.", self.source)
        self.assertIn("SharedJoin", self.source)
        self.assertIn("EncounterJoins", self.source)
        self.assertIn("readJsonRows", self.adapter)

    def test_dragging_fields_creates_columns(self):
        self.assertIn('@ondragstart', self.source)
        self.assertIn('@ondrop="DropField"', self.source)
        self.assertIn("AddColumn(", self.source)
        self.assertIn("RemoveColumn(", self.source)

    def test_numeric_columns_support_requested_aggregates(self):
        for aggregate in ("Sum", "Average", "Min", "Max"):
            self.assertIn(f'"{aggregate}"', self.source)
        self.assertIn("AggregateText", self.source)

    def test_report_prefers_effective_values_and_preserves_modifier_provenance(self):
        self.assertIn("cell?.Effective??cell?.Number", self.source)
        self.assertIn("ModifierCount", self.source)
        self.assertIn("active effect", self.source)


if __name__ == "__main__":
    unittest.main()
