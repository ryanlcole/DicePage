from pathlib import Path
import unittest


class LauncherLearningPathContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.shell = (root / "Components" / "PublicAlphaShell.razor").read_text(encoding="utf-8")
        cls.router = (root / "Components" / "TaskWorkspaceRouter.razor").read_text(encoding="utf-8")
        cls.guide = (root / "Components" / "ShaelvienGmGuide.razor").read_text(encoding="utf-8")
        cls.guided_state = (root / "WorldSession.GuidedGameMaster.cs").read_text(encoding="utf-8")

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

    def test_environment_switching_returns_to_role_hubs(self):
        self.assertIn("@onclick="OpenShaelvienHubAsync"", self.shell)
        self.assertIn('_worldGateIntent="rist-hub"', self.shell)
        self.assertIn('string.Equals(intent,"rist-hub",StringComparison.Ordinal)', self.shell)
        rist_method = self.shell[self.shell.index("async Task OpenRistAsync()"):self.shell.index("void OpenCreate()")]
        self.assertIn('PersistWorkspaceAsync("hub")', rist_method)
        self.assertNotIn('OpenWorkspace("create"', rist_method)

    def test_world_management_keeps_worldbuilder_intent(self):
        self.assertIn('_worldGateIntent="worldbuilder";_worldGateOpen=true', self.shell)
        self.assertIn('OpenWorkspace("world","WORLDBUILDER","SANDBOX → TIER → LAYER → CUBE")', self.shell)

    def test_shaelvien_gm_uses_guided_workspace_instead_of_creative_workbench(self):
        self.assertIn('OpenWorkspace("guidedgm","SHAELVIEN GAMEMASTER"', self.shell)
        self.assertIn('"guidedgm"', self.shell)
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

    def test_guided_gm_persists_private_preparation(self):
        self.assertIn("LoadGuidedGameMasterAsync", self.guide)
        self.assertIn("SaveGuidedGameMasterLocalAsync", self.guide)
        self.assertIn("SaveGuidedGameMasterAsync", self.guide)
        self.assertIn("RIST_GUIDED_GAMEMASTER_V1", self.guided_state)
        self.assertIn("/campaign/guided-gamemaster.json", self.guided_state)
        self.assertIn("localStorage.setItem", self.guided_state)
        self.assertIn("auth.UploadTextAsync", self.guided_state)

    def test_guided_gm_preserves_truth_lifecycle(self):
        for status in (
            "PRIVATE_DRAFT",
            "PREPARED",
            "IN_PLAY",
            "PLAY_RECORDED",
            "CONSEQUENCE_ACCEPTED",
            "PROMOTED",
        ):
            self.assertIn(f'"{status}"', self.guided_state)
        self.assertIn("does not become shared", self.guided_state)
        self.assertIn("Promotion remains an explicit, authorized action.", self.guide)

    def test_guided_gm_uses_difficulty_intent_not_false_balance_claim(self):
        self.assertIn("DIFFICULTY INTENT", self.guide)
        self.assertIn("This is not a mathematical balance claim.", self.guide)
        for kind in ("Conversation", "Discovery", "Obstacle", "Hazard", "Combat"):
            self.assertIn(f'"{kind}"', self.guide)

    def test_advanced_workspaces_remain_available(self):
        for workspace in ("campaign", "tracker", "assets", "world", "create", "roleplay"):
            self.assertIn(f'"{workspace}"', self.shell)
        self.assertIn("<CreativeWorkbenchWorkspace", self.router)

    def test_mobile_layout_and_focus_are_explicit(self):
        self.assertIn("@@media(max-width:720px)", self.shell)
        self.assertIn("grid-template-columns:1fr", self.shell)
        self.assertIn("@@media(max-width:680px)", self.guide)
        self.assertIn(":focus-visible", self.guide)
        self.assertIn("min-height:44px", self.guide)


if __name__ == "__main__":
    unittest.main()
