from pathlib import Path
import ast
import unittest


class RegionResetRetiredContract(unittest.TestCase):
    def test_request_handler_never_runs_destructive_region_reset(self):
        source_path = Path(__file__).resolve().parents[1] / "app.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        handler = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "handler"
        )
        reset_calls = [
            node for node in ast.walk(handler)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "ensure_region_z_reset"
        ]
        self.assertEqual(
            reset_calls,
            [],
            "A normal authenticated request must never trigger destructive RegionDefiner migration cleanup.",
        )


if __name__ == "__main__":
    unittest.main()
