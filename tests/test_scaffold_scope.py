"""Scaffold checks must separate generated exports from maintained source."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_scaffold import source_files, validate


class ScaffoldScopeTests(unittest.TestCase):
    def test_output_readmes_remain_checked_but_generated_copies_do_not(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = ["README.md", "docs/guide.md", "docs/artifacts/source.md",
                     "docs/codex-session-note.md", "codex-session-example.md",
                     "artifacts/README.md", "artifacts/copied/report.md",
                     "data/README.md", "data/generated.md",
                     "models/README.md", "models/generated.md"]
            for name in paths:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("[missing](absent.md)\n")
            checked = {str(path.relative_to(root)) for path in source_files(root)}
            self.assertEqual(checked, {"README.md", "docs/guide.md",
                                      "docs/artifacts/source.md", "docs/codex-session-note.md",
                                      "artifacts/README.md", "data/README.md", "models/README.md"})
            errors, _ = validate(root)
            broken = [error for error in errors if "broken local link" in error]
            self.assertEqual(len(broken), len(checked))

    def test_ordinary_untracked_source_is_still_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "proposal.md").write_text("[missing](absent.md)\n")
            (root / "invalid.toml").write_text("broken = [\n")
            errors, _ = validate(root)
            self.assertTrue(any("proposal.md: broken local link" in error for error in errors))
            self.assertTrue(any("invalid.toml: invalid TOML" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
