from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "Components" / "CharacterCardDesignerWorkspace.razor"
PLAYER = ROOT / "wwwroot" / "character-card-designer.js"


class CharacterCardDesignerContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = COMPONENT.read_text(encoding="utf-8")
        cls.player = PLAYER.read_text(encoding="utf-8")

    def test_gm_requirements_layout_and_character_values_are_separate(self):
        self.assertIn('rist.character-card-requirements.v1.', self.source)
        self.assertIn('rist.character-card-layout.v1.', self.source)
        self.assertIn('rist.character-card-values.v1.', self.source)
        self.assertIn('RequirementStorageKey', self.source)
        self.assertIn('LayoutStorageKey', self.source)
        self.assertIn('ValueStorageKey', self.source)
        self.assertIn('Required=true,Authority="GM"', self.source)
        self.assertIn('SharedJoin=rule.SharedJoin', self.source)
        self.assertIn('GM REQUIRED · CANNOT DELETE', self.source)

    def test_field_creation_follows_search_type_asset_value_place(self):
        self.assertIn('SEARCH → TYPE → ASSET → VALUE → PLACE', self.source)
        self.assertIn('SAVE &amp; PLACE', self.source)
        self.assertIn('MatchingAssets=>FieldAssets.Where', self.source)
        self.assertIn('BeginField(FieldOption option)', self.source)
        self.assertIn('SaveAndPlace()', self.source)
        self.assertIn('CharacterValueDraft', self.source)

    def test_existing_universal_character_field_types_are_supported(self):
        for kind in (
            "ATTRIBUTE", "TRACKER", "LIMIT", "VALUE", "FLARE", "POWER", "TEXT",
            "LONGTEXT", "PORTRAIT", "EQUIPMENT", "CONDITIONS",
            "LANGUAGE", "LINKED", "DICE",
        ):
            self.assertIn(f'"{kind}"', self.source)

    def test_card_fields_use_worldbuilder_style_direct_manipulation(self):
        self.assertIn('data-ccd-field="@field.Id"', self.source)
        self.assertIn('data-ccd-resize="nw"', self.source)
        self.assertIn('data-ccd-resize="ne"', self.source)
        self.assertIn('data-ccd-resize="sw"', self.source)
        self.assertIn('data-ccd-resize="se"', self.source)
        self.assertIn('SELECT · CHARACTER FIELDS', self.source)
        self.assertIn('WIDTH %', self.source)
        self.assertIn('HEIGHT %', self.source)
        self.assertIn('DELETE FIELD', self.source)
        self.assertIn("invokeMethodAsync('CommitFieldTransform'", self.player)
        self.assertIn("invokeMethodAsync('SelectFieldFromJs'", self.player)
        self.assertIn("root.addEventListener('contextmenu'", self.player)

    def test_required_field_name_becomes_stable_shared_join(self):
        self.assertIn("NormalizeJoin", self.source)
        self.assertIn("SharedJoin", self.source)
        self.assertIn("UniqueRequirementName", self.source)
        self.assertIn("RequirementId", self.source)
        self.assertIn("CHECK → NAME → PLAYER MUST KEEP", self.source)

    def test_joined_effects_support_activation_duration_and_effective_values(self):
        for marker in (
            "JOINED EFFECTS", "TARGET JOIN", "Requires activation",
            "RemainingDuration", "EffectiveNumeric", "ModifierIsActive",
            "ModifierCount",
        ):
            self.assertIn(marker, self.source)
        self.assertIn("BaseValue", self.source)
        self.assertIn("Current", self.source)
        self.assertIn("Max", self.source)

    def test_power_reuses_join_effect_engine_with_resolution(self):
        for marker in (
            '"POWER"', "Power", "TARGETING", "RESOLUTION",
            "Roll decides", "GM decides / alters", "TargetMode",
            "ResolutionMode", "AttemptState", "RollFormula",
            "Difficulty", "GmOverrideAmount", "ModifierResolutionAllows",
        ):
            self.assertIn(marker, self.source)

    def test_character_save_publishes_effective_shared_report_row(self):
        self.assertIn("rist.character-report-row.v1.", self.source)
        self.assertIn("BuildReportRow()", self.source)
        self.assertIn("ReportCellFrom", self.source)
        self.assertIn("Effective=effective", self.source)

    def test_custom_graphic_is_definition_not_runtime_value(self):
        self.assertIn('AssetDataUrl', self.source)
        self.assertIn('CREATE YOUR OWN', self.source)
        self.assertIn('Portrait data changes the character value only; the GM frame stays fixed.', self.source)


if __name__ == "__main__":
    unittest.main()
