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

    def test_gm_template_and_character_values_are_separate(self):
        self.assertIn('rist.character-card-template.v2.', self.source)
        self.assertIn('rist.character-card-values.v1.', self.source)
        self.assertIn('TemplateStorageKey', self.source)
        self.assertIn('ValueStorageKey', self.source)
        self.assertIn('Required=true,Authority="GM"', self.source)

    def test_field_creation_follows_search_type_asset_value_place(self):
        self.assertIn('SEARCH → TYPE → ASSET → VALUE → PLACE', self.source)
        self.assertIn('SAVE &amp; PLACE', self.source)
        self.assertIn('MatchingAssets=>Assets.Where', self.source)
        self.assertIn('BeginField(FieldOption option)', self.source)
        self.assertIn('SaveAndPlace()', self.source)
        self.assertIn('CharacterValueDraft', self.source)

    def test_existing_universal_character_field_types_are_supported(self):
        for kind in (
            "ATTRIBUTE", "TRACKER", "LIMIT", "VALUE", "FLARE", "TEXT",
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

    def test_custom_graphic_is_definition_not_runtime_value(self):
        self.assertIn('AssetDataUrl', self.source)
        self.assertIn('CREATE YOUR OWN', self.source)
        self.assertIn('Portrait data changes the character value only; the GM frame stays fixed.', self.source)


if __name__ == "__main__":
    unittest.main()
