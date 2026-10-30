"""Ensure mock test teardown never kills a listener it did not start."""

import os
from pathlib import Path
from subprocess import Popen, run
from tempfile import TemporaryDirectory
import unittest


TEST_SCRIPT = Path(__file__).resolve().parents[1] / "test"


class MockOwnershipTests(unittest.TestCase):
    def invoke(self, *, wrong_listener=False, existing_healthy=False, override=False):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "bin").mkdir()
            (root / "scripts/test").write_bytes(TEST_SCRIPT.read_bytes())
            (root / "scripts/steady-health").write_text(
                '#!/usr/bin/env bash\n'
                '[[ "${STEADY_HEALTHY:-}" == yes || -f .mock-started ]]\n'
            )
            (root / "scripts/mock").write_text(
                '#!/usr/bin/env bash\n'
                'touch .mock-started\n'
            )
            (root / "gradlew").write_text(
                '#!/usr/bin/env bash\n'
                'touch .tests-ran\n'
            )
            (root / "bin/lsof").write_text(
                '#!/usr/bin/env bash\n'
                'if [[ "${WRONG_LISTENER:-}" == yes || -f .mock-started ]]; then\n'
                '  echo "$LISTENER_PID"\n'
                '  exit 0\n'
                'fi\n'
                'exit 1\n'
            )
            for script in (root / "scripts/mock", root / "gradlew", root / "bin/lsof"):
                script.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = str(root / "bin") + os.pathsep + environment["PATH"]
            environment["TEST_API_BASE_URL"] = "http://example.invalid" if override else ""
            environment["STEADY_HEALTHY"] = "yes" if existing_healthy else "no"
            environment["WRONG_LISTENER"] = "yes" if wrong_listener else "no"
            listener = Popen(["sleep", "60"])
            try:
                environment["LISTENER_PID"] = str(listener.pid)
                result = run(["bash", str(root / "scripts/test")], cwd=root,
                             env=environment, capture_output=True, text=True,
                             timeout=10, check=False)
                return result, listener.poll() is None, (root / ".tests-ran").exists(), (root / ".mock-started").exists()
            finally:
                if listener.poll() is None:
                    listener.terminate()
                listener.wait(timeout=5)

    def test_refuses_unhealthy_unrelated_listener_without_killing_it(self):
        result, alive, ran, spawned = self.invoke(wrong_listener=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(alive, "an unrelated listener must survive startup failure")
        self.assertFalse(ran)
        self.assertFalse(spawned)

    def test_only_stops_mock_server_started_by_this_test_run(self):
        result, alive, ran, spawned = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(alive, "started mock must be stopped after the tests")
        self.assertTrue(ran)
        self.assertTrue(spawned)

    def test_preserves_preexisting_healthy_mock(self):
        result, alive, ran, spawned = self.invoke(existing_healthy=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(alive)
        self.assertTrue(ran)
        self.assertFalse(spawned)

    def test_override_never_starts_or_kills_a_local_mock(self):
        result, alive, ran, spawned = self.invoke(override=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(alive)
        self.assertTrue(ran)
        self.assertFalse(spawned)


if __name__ == "__main__":
    unittest.main()
