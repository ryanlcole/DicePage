from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "Components" / "ImmersionBuilderWorkspace.razor"
SESSION = ROOT / "WorldSession.Immersion.cs"
CONTRACT = ROOT / "IMMERSION_BUILDER_CONTRACT.md"
SHELL = ROOT / "Components" / "PublicAlphaShell.razor"
BRIDGE = ROOT / "wwwroot" / "immersion-builder-host.js"
PROTOTYPE = ROOT / "wwwroot" / "prototype" / "prototype.js"


class ImmersionBuilderContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.component = COMPONENT.read_text(encoding="utf-8")
        cls.session = SESSION.read_text(encoding="utf-8")
        cls.contract = CONTRACT.read_text(encoding="utf-8")
        cls.shell = SHELL.read_text(encoding="utf-8")
        cls.bridge = BRIDGE.read_text(encoding="utf-8")
        cls.prototype = PROTOTYPE.read_text(encoding="utf-8")

    def test_authoring_sequence_places_immersion_before_instances(self):
        gm = self.shell[self.shell.index('id="launcher-gamemaster-tools"'):]
        self.assertLess(gm.index("<strong>WORLDBUILDER</strong>"), gm.index("<strong>REGION DEFINER</strong>"))
        self.assertLess(gm.index("<strong>REGION DEFINER</strong>"), gm.index("<strong>LOCAL STAGING</strong>"))
        self.assertLess(gm.index("<strong>LOCAL STAGING</strong>"), gm.index("<strong>IMMERSION BUILDER</strong>"))
        self.assertLess(gm.index("<strong>IMMERSION BUILDER</strong>"), gm.index("<strong>INSTANCES</strong>"))

    def test_builder_captures_world_region_and_region_local_switches(self):
        for marker in (
            "SET REGION SWITCH HERE",
            "SET LOCAL SWITCH HERE",
            "WORLD → REGION",
            "REGION → LOCAL",
            "RESET DEFAULTS",
            "SAVE PROFILE",
        ):
            self.assertIn(marker, self.component)
        self.assertIn("_zoomRatio", self.component)
        self.assertIn("UpdateCameraFromPrototypeAsync", self.component)

    def test_defaults_come_from_actual_region_and_local_footprints(self):
        self.assertIn("(region.MaxColumn-region.MinColumn+1)/30d", self.component)
        self.assertIn("Math.Max(local.Width", self.component)
        self.assertIn("ResetDefaults()", self.component)

    def test_profile_persists_as_presentation_data(self):
        self.assertIn("WorldImmersionProfile", self.session)
        self.assertIn("WorldToRegionZoom", self.session)
        self.assertIn("RegionToLocalZoom", self.session)
        self.assertIn("FocusX", self.session)
        self.assertIn("FocusY", self.session)
        self.assertIn("TransitionMode", self.session)
        self.assertIn("UploadTextAsync", self.session)
        self.assertIn("localStorage.setItem", self.session)

    def test_builder_uses_canonical_viewer_camera(self):
        self.assertIn("mode=immersion", self.component)
        self.assertIn("ShaelvienPrototype", self.bridge)
        self.assertIn("getViewerState", self.bridge)
        self.assertIn("focusNormalizedBounds", self.prototype)
        self.assertIn("fitWorld", self.prototype)

    def test_contract_keeps_immersion_out_of_spatial_truth(self):
        self.assertIn("ImmersionBuilder is presentation authority, not spatial authority.", self.contract)
        self.assertIn("Instance follows ImmersionBuilder in the authoring sequence.", self.contract)


if __name__ == "__main__":
    unittest.main()
