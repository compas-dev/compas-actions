import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).parents[1] / "release-assets" / "validate_assets.py"
SPEC = importlib.util.spec_from_file_location("validate_assets", MODULE)
assert SPEC and SPEC.loader
validate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate)


class AssetValidationTest(unittest.TestCase):
    def test_missing_pattern_fails(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            self.assertRaisesRegex(ValueError, "no files match"),
        ):
            validate.matched_files([str(Path(directory) / "*.zip")])

    def test_empty_file_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            asset = Path(directory) / "empty.zip"
            asset.touch()
            with self.assertRaisesRegex(ValueError, "empty release assets"):
                validate.matched_files([str(asset)])

    def test_multiple_nonempty_files_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.zip"
            second = Path(directory) / "second.zip"
            first.write_bytes(b"first")
            second.write_bytes(b"second")
            self.assertEqual(
                validate.matched_files([str(Path(directory) / "*.zip")]),
                [first, second],
            )


if __name__ == "__main__":
    unittest.main()
