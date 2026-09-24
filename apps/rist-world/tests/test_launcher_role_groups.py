from pathlib import Path
import unittest


class LauncherRoleGroupingContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (
            Path(__file__).resolve().parents[1]
            / "Components"
            / "PublicAlphaShell.razor"
        ).read_text(encoding="utf-8")
        cls.css = (
            Path(__file__).resolve().parents[1]
            / "Components"
            / "PublicAlphaShell.razor.css"
        ).read_text(encoding="utf-8")

    def test_primary_launcher_is_collapsed_role_selector(self):
        self.assertIn('class="launcher-mode-toggle roleplay', self.source)
        self.assertIn('class="launcher-mode-toggle gamemaster', self.source)
        self.assertIn('@if(_launcherMenu=="roleplay")', self.source)
        self.assertIn('else if(_launcherMenu=="gamemaster")', self.source)
        self.assertNotIn('<section class="launcher-primary" aria-label="Shaelvien categories">', self.source)

    def test_roleplay_group_contains_requested_tools(self):
        for label in (
            "CHARACTERS", "JOURNAL", "CARD INDEX", "DICE &amp; TOOLS",
            "RULEBOOKS", "ASSET DESIGNER", "PERCEIVER", "ReLiC OBSERVER",
            "ACCESSIBILITY",
        ):
            self.assertIn(f"<strong>{label}</strong>", self.source)

    def test_gamemaster_group_contains_requested_tools(self):
        for label in (
            "WORLDBUILDER", "REGION DEFINER", "LOCAL STAGING", "INSTANCES",
            "HISTORY", "LORE", "WEATHER", "GEOLOGICAL EVENTS", "ASTRONOMY",
            "ASTROLOGY", "TICKER", "TRACKER", "GUEST CHARACTERS", "ENCOUNTERS",
        ):
            self.assertIn(f"<strong>{label}</strong>", self.source)

    def test_tool_groups_keep_two_column_pair_layout(self):
        self.assertIn(
            ".launcher-tool-grid{display:grid;grid-template-columns:1fr 1fr",
            self.css,
        )
        self.assertIn(".launcher-tool-wide{grid-column:1/-1}", self.css)


if __name__ == "__main__":
    unittest.main()
