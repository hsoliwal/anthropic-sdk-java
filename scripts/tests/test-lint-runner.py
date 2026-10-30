"""CI lint argument regression tests; no Gradle download or third-party dependencies."""

import os
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import unittest


LINT = Path(__file__).resolve().parents[1] / "lint"


class LintRunnerTests(unittest.TestCase):
    def invoke(self, *, ci, repository=None):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "scripts/lint").write_bytes(LINT.read_bytes())
            gradlew = root / "gradlew"
            gradlew.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@" > "$ARGS_FILE"\n')
            gradlew.chmod(0o755)
            args_file = root / "args"
            environment = os.environ.copy()
            environment.pop("CI", None)
            environment.pop("GITHUB_REPOSITORY", None)
            if ci:
                environment["CI"] = "true"
            if repository:
                environment["GITHUB_REPOSITORY"] = repository
            environment["ARGS_FILE"] = str(args_file)
            result = run(["bash", str(root / "scripts/lint")], cwd=root,
                         env=environment, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            return args_file.read_text().splitlines()

    def test_fork_runs_full_lints_with_bounded_workers(self):
        args = self.invoke(ci=True, repository="hsoliwal/anthropic-sdk-java")
        self.assertEqual(args[-4:], ["detektMain", "detektTest", "lintKotlin", "lintJava"])
        self.assertIn("--max-workers=2", args)
        self.assertFalse(any("-Xmx16g" in value for value in args))

    def test_upstream_preserves_dedicated_runner_heap(self):
        args = self.invoke(ci=True, repository="anthropics/anthropic-sdk-java")
        self.assertTrue(any(value.startswith("-Dorg.gradle.jvmargs=-Xmx16g ") for value in args))
        self.assertNotIn("--max-workers=2", args)
        self.assertEqual(args[-4:], ["detektMain", "detektTest", "lintKotlin", "lintJava"])

    def test_local_keeps_changed_file_mode(self):
        args = self.invoke(ci=False)
        self.assertEqual(args, ["detektChangedMain", "detektChangedTest", "lintKotlin", "lintJava"])


if __name__ == "__main__":
    unittest.main()
