import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


class ActionContractTest(unittest.TestCase):
    def test_ci_action_supports_locked_uv_and_legacy_invoke(self):
        content = (ROOT / "ci" / "action.yml").read_text(encoding="utf-8")
        self.assertIn("--frozen", content)
        self.assertIn("uv run --project", content)
        self.assertIn("invoke-tasks", content)
        self.assertIn("env_win.yml", content)
        self.assertIn("env_osx.yml", content)
        self.assertIn("env_linux.yml", content)
        self.assertIn("management-tool must be uv or conda", content)
        self.assertIn("frozen must be true or false", content)

    def test_invoke_is_optional_and_uv_scoped(self):
        for relative in [
            "docs/action.yml",
            "prepare-release/action.yml",
            "release-assets/action.yml",
        ]:
            content = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("optional", content.lower(), relative)
            self.assertIn("uv run --project", content, relative)

    def test_internal_external_actions_use_full_shas(self):
        for action in ROOT.glob("*/action.yml"):
            for line in action.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped.startswith("uses: ") or stripped.startswith("uses: ./"):
                    continue
                reference = stripped.split("#", 1)[0].rsplit("@", 1)[-1].strip()
                self.assertRegex(reference, FULL_SHA, f"{action}: {stripped}")

    def test_locked_setup_is_default(self):
        content = (ROOT / "setup-python" / "action.yml").read_text(encoding="utf-8")
        self.assertIn('default: "true"', content)
        self.assertIn("uv.lock not found", content)
        self.assertIn("args+=(--frozen)", content)

    def test_uv_list_inputs_are_trimmed_consistently(self):
        for relative in [
            "ci/action.yml",
            "setup-python/action.yml",
            "prepare-release/action.yml",
            "release-assets/action.yml",
        ]:
            content = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn('group="${group#${group%%[![:space:]]*}}"', content, relative)
            self.assertIn('extra="${extra#${extra%%[![:space:]]*}}"', content, relative)

    def test_optional_prebuilds_validate_frozen(self):
        for relative in ["prepare-release/action.yml", "release-assets/action.yml"]:
            content = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("frozen must be true or false", content, relative)

    def test_docs_config_is_relative_to_project_directory(self):
        content = (ROOT / "docs" / "action.yml").read_text(encoding="utf-8")
        self.assertIn('config_path="$PROJECT_DIRECTORY/$config_path"', content)

    def test_docs_can_use_a_caller_prepared_environment(self):
        content = (ROOT / "docs" / "action.yml").read_text(encoding="utf-8")
        self.assertIn("setup-project:", content)
        self.assertIn("setup-project must be true or false", content)
        self.assertIn(
            "prepared-conda-environment requires setup-project false", content
        )
        self.assertIn("if: inputs.setup-project == 'true'", content)
        self.assertIn("python -m invoke", content)
        self.assertIn("python -m mkdocs", content)
        self.assertNotIn("python -m mike", content)
        self.assertIn("-- mike --config-file", content)


if __name__ == "__main__":
    unittest.main()
