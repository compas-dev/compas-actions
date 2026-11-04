import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
RUNNER = ROOT / "docs" / "run-in-environment.sh"


class DocsEnvironmentTest(unittest.TestCase):
    def test_current_environment_executes_command_directly(self):
        result = subprocess.run(
            ["bash", RUNNER, "", "--", "printf", "%s", "current"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout, "current")

    def test_prepared_conda_environment_uses_conda_run(self):
        with tempfile.TemporaryDirectory() as directory:
            conda = Path(directory) / "conda"
            conda.write_text(
                '#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n', encoding="utf-8"
            )
            conda.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{directory}{os.pathsep}{environment['PATH']}"
            result = subprocess.run(
                ["bash", RUNNER, "compas-3.12", "--", "mike", "--version"],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
        self.assertEqual(
            result.stdout.splitlines(),
            ["run", "--no-capture-output", "-n", "compas-3.12", "mike", "--version"],
        )

    def test_current_environment_executes_mike_entry_point(self):
        with tempfile.TemporaryDirectory() as directory:
            mike = Path(directory) / "mike"
            mike.write_text(
                '#!/usr/bin/env bash\nprintf "mike:%s\\n" "$*"\n', encoding="utf-8"
            )
            mike.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{directory}{os.pathsep}{environment['PATH']}"
            result = subprocess.run(
                ["bash", RUNNER, "", "--", "mike", "--version"],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
        self.assertEqual(result.stdout, "mike:--version\n")

    def test_invalid_conda_environment_is_rejected(self):
        result = subprocess.run(
            ["bash", RUNNER, "compas env", "--", "mike", "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid Conda environment name", result.stderr)


if __name__ == "__main__":
    unittest.main()
