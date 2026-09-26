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
            "CHARACTERS", "CHARACTER CARD DESIGNER", "POWERS", "JOURNAL",
            "CAMPAIGN", "CARD INDEX", "DICE &amp; TOOLS", "RULEBOOKS", "ASSET DESIGNER",
            "PERCEIVER", "ReLiC OBSERVER", "ACCESSIBILITY",
        ):
            self.assertIn(f"<strong>{label}</strong>", self.source)

    def test_gamemaster_group_starts_with_simple_create_world_play_studio_front_door(self):
        for label in ("CREATE", "WORLD", "RUN / PLAY", "STUDIO TOOLS"):
            self.assertIn(f"<strong>{label}</strong>", self.source)
        self.assertIn("launcher-gm-core", self.source)
        self.assertIn("@if(_gmStudioToolsOpen)", self.source)

    def test_gamemaster_specialized_tools_are_preserved_behind_studio_tools(self):
        for label in (
            "WORLDBUILDER", "REGION DEFINER", "LOCAL STAGING", "INSTANCE BUILDER",
            "HISTORY", "LORE", "WEATHER", "GEOLOGICAL EVENTS", "ASTRONOMY",
            "ASTROLOGY", "TICKER", "TRACKER", "GUEST CHARACTERS", "ENCOUNTERS",
            "CHARACTER CARD DESIGNER", "POWERS",
        ):
            self.assertIn(f"<strong>{label}</strong>", self.source)

    def test_gamemaster_keeps_shared_tools_in_familiar_roleplay_order(self):
        gm_start = self.source.index('id="launcher-gamemaster-tools"')
        gm_end = self.source.index("</section>", gm_start)
        gm = self.source[gm_start:gm_end]
        self.assertIn("SHARED TOOLS", gm)
        labels = (
            "CHARACTERS", "CHARACTER CARD DESIGNER", "POWERS", "JOURNAL",
            "CAMPAIGN", "CARD INDEX", "DICE &amp; TOOLS", "RULEBOOKS",
            "ASSET DESIGNER", "PERCEIVER", "ReLiC OBSERVER",
            "ACCESSIBILITY",
        )
        positions = [gm.index(f"<strong>{label}</strong>") for label in labels]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(gm.index("SHARED TOOLS"), positions[0])

    def test_character_card_designer_has_dedicated_workspace(self):
        router = (
            Path(__file__).resolve().parents[1]
            / "Components"
            / "TaskWorkspaceRouter.razor"
        ).read_text(encoding="utf-8")
        designer = (
            Path(__file__).resolve().parents[1]
            / "Components"
            / "CharacterCardDesignerWorkspace.razor"
        ).read_text(encoding="utf-8")
        self.assertIn('Mode == "charactercards"', router)
        self.assertIn("<CharacterCardDesignerWorkspace />", router)
        self.assertIn("CHARACTER CARD DESIGNER", designer)
        self.assertIn("RequirementStorageKey", designer)
        self.assertIn("LayoutStorageKey", designer)
        self.assertIn("ValueStorageKey", designer)

    def test_campaign_is_shared_roleplay_and_gamemaster_workspace(self):
        router = (
            Path(__file__).resolve().parents[1]
            / "Components"
            / "TaskWorkspaceRouter.razor"
        ).read_text(encoding="utf-8")
        self.assertGreaterEqual(self.source.count('@onclick="OpenCampaign"'), 2)
        self.assertIn('case "campaign"', self.source)
        self.assertIn('Mode == "campaign"', router)
        self.assertIn("<CampaignWorkspace />", router)

    def test_powers_is_shared_roleplay_and_gamemaster_workspace(self):
        router = (
            Path(__file__).resolve().parents[1]
            / "Components"
            / "TaskWorkspaceRouter.razor"
        ).read_text(encoding="utf-8")
        self.assertGreaterEqual(self.source.count('@onclick="OpenPowers"'), 2)
        self.assertIn('case "powers"', self.source)
        self.assertIn('Mode == "powers"', router)
        self.assertIn("<PowerCardWorkspace />", router)

    def test_tracker_is_live_gamemaster_report_workspace(self):
        router = (
            Path(__file__).resolve().parents[1]
            / "Components"
            / "TaskWorkspaceRouter.razor"
        ).read_text(encoding="utf-8")
        self.assertIn('@onclick="OpenTracker"', self.source)
        self.assertIn('case "tracker"', self.source)
        self.assertIn('Mode == "tracker"', router)
        self.assertIn("<GmReportWorkspace />", router)

    def test_tool_groups_keep_simple_primary_grid_and_two_column_specialized_layout(self):
        self.assertIn(".launcher-gm-core{display:grid;grid-template-columns:repeat(4,minmax(0,1fr))", self.css)
        self.assertIn(".launcher-tool-grid{display:grid;grid-template-columns:1fr 1fr", self.css)
        self.assertIn(".launcher-tool-wide{grid-column:1/-1}", self.css)

    def test_create_has_dedicated_private_workbench_route(self):
        router = (
            Path(__file__).resolve().parents[1]
            / "Components"
            / "TaskWorkspaceRouter.razor"
        ).read_text(encoding="utf-8")
        self.assertIn('Mode == "create"', router)
        self.assertIn("<CreativeWorkbenchWorkspace", router)
        self.assertIn('"create","world","local"', self.source)


if __name__ == "__main__":
    unittest.main()
