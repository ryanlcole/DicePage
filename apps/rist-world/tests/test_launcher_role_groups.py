from pathlib import Path
import unittest


class LauncherLearningPathContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.shell = (root / "Components" / "PublicAlphaShell.razor").read_text(encoding="utf-8")
        cls.router = (root / "Components" / "TaskWorkspaceRouter.razor").read_text(encoding="utf-8")
        cls.guide = (root / "Components" / "ShaelvienGmGuide.razor").read_text(encoding="utf-8")

    def test_shaelvien_is_guided_and_role_first(self):
        self.assertIn("SHAELVIEN · GUIDED", self.shell)
        self.assertIn("START SMALL. GROW THROUGH PLAY.", self.shell)
        self.assertIn("ROLEPLAYER", self.shell)
        self.assertIn("GAMEMASTER", self.shell)
        for label in ("LOOK", "BASICS", "PLAY", "GROW"):
            self.assertIn(f"<li>{label}</li>", self.shell)
        for label in ("OBJECTIVE", "SCENE", "ENCOUNTERS", "PLAY", "GROW"):
            self.assertIn(f"<li>{label}</li>", self.shell)

    def test_rist_is_direct_and_exposes_gm_quick_tools(self):
        self.assertIn("RIST · DIRECT", self.shell)
        self.assertIn("YOU KNOW WHAT YOU WANT. HERE ARE THE TOOLS.", self.shell)
        self.assertIn("Character. Game. Track.", self.shell)
        self.assertIn("Your GM desk.", self.shell)
        for label in ("DOCUMENTS", "TRACK", "ASSETS", "WORLD"):
            self.assertIn(f"<strong>{label}</strong>", self.shell)

    def test_shaelvien_gm_uses_guided_workspace_instead_of_creative_workbench(self):
        self.assertIn('OpenWorkspace("guidedgm","SHAELVIEN GAMEMASTER"', self.shell)
        self.assertIn('Mode == "guidedgm"', self.router)
        self.assertIn("<ShaelvienGmGuide", self.router)

    def test_guided_gm_teaches_inside_out_preparation(self):
        for phrase in (
            "What are the players trying to accomplish?",
            "Choose the scene.",
            "Choose the encounters.",
            "Run the small thing.",
            "What changed?",
            "OBJECTIVE → SCENE → ENCOUNTERS → PLAY → CONSEQUENCE",
        ):
            self.assertIn(phrase, self.guide)

    def test_guided_gm_keeps_encounter_guidance_system_agnostic(self):
        self.assertIn("If a ruleset is supplied, use that ruleset's encounter budget", self.guide)
        for kind in ("Conversation", "Discovery", "Obstacle", "Hazard", "Combat"):
            self.assertIn(f'"{kind}"', self.guide)

    def test_riskier_depth_is_still_available_without_being_front_door(self):
        for workspace in ("campaign", "tracker", "assets", "world", "create", "roleplay"):
            self.assertIn(f'"{workspace}"', self.shell)
        self.assertIn('<CreativeWorkbenchWorkspace', self.router)

    def test_mobile_layout_collapses_without_horizontal_dependency(self):
        self.assertIn("@@media(max-width:720px)", self.shell)
        self.assertIn("grid-template-columns:1fr", self.shell)
        self.assertIn("@@media(max-width:680px)", self.guide)


if __name__ == "__main__":
    unittest.main()
