from pathlib import Path
import ast
import unittest


class DeferredSeedContract(unittest.TestCase):
    def test_optional_seed_deferred_only_when_explicit_prerequisites_missing(self):
        source = (Path(__file__).resolve().parents[2] / "rist-platform-zone-seed" / "app.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("class SeedPrerequisiteUnavailable(RuntimeError)", source)
        self.assertIn('"deferred": True', source)
        self.assertIn('send_cloudformation_response(event, context, "SUCCESS", result)', source)
        self.assertIn('send_cloudformation_response(\n            event,\n            context,\n            "FAILED"', source)
        self.assertIn("Refusing to overwrite authored Shaelvien content.", source)


if __name__ == "__main__":
    unittest.main()
