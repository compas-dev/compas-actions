import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

from packaging.tags import Tag

MODULE = Path(__file__).parents[1] / "package" / "verify_distributions.py"
SPEC = importlib.util.spec_from_file_location("verify_distributions", MODULE)
assert SPEC and SPEC.loader
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)


class PackageVerificationTest(unittest.TestCase):
    def test_find_distributions_requires_artifact(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            self.assertRaisesRegex(ValueError, "no Python distributions"),
        ):
            verify.find_distributions(Path(directory))

    def test_inspect_wheel_accepts_complete_dist_info(self):
        with tempfile.TemporaryDirectory() as directory:
            wheel = Path(directory) / "example-1.0-py3-none-any.whl"
            with zipfile.ZipFile(wheel, "w") as archive:
                archive.writestr(
                    "example-1.0.dist-info/METADATA", "Name: example\nVersion: 1.0\n"
                )
                archive.writestr("example-1.0.dist-info/WHEEL", "Wheel-Version: 1.0\n")
                archive.writestr("example-1.0.dist-info/RECORD", "")
            verify.inspect_wheel(wheel)

    def test_inspect_wheel_rejects_incomplete_dist_info(self):
        with tempfile.TemporaryDirectory() as directory:
            wheel = Path(directory) / "example-1.0-py3-none-any.whl"
            with zipfile.ZipFile(wheel, "w") as archive:
                archive.writestr("example-1.0.dist-info/METADATA", "Name: example\n")
            with self.assertRaisesRegex(ValueError, "complete dist-info"):
                verify.inspect_wheel(wheel)

    def test_wheel_compatibility_is_tag_aware(self):
        wheel = Path("example-1.0-cp312-cp312-manylinux_2_17_x86_64.whl")
        self.assertTrue(
            verify.wheel_is_compatible(
                wheel, {Tag("cp312", "cp312", "manylinux_2_17_x86_64")}
            )
        )
        self.assertFalse(
            verify.wheel_is_compatible(
                wheel, {Tag("cp312", "cp312", "macosx_14_0_arm64")}
            )
        )

    def test_import_modules_must_be_dotted_identifiers(self):
        verify.validate_import_modules(["package", "package.module_name"])
        with self.assertRaisesRegex(ValueError, "invalid import module"):
            verify.validate_import_modules(["package; raise RuntimeError"])


if __name__ == "__main__":
    unittest.main()
