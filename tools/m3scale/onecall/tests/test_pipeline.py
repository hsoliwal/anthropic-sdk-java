"""Contract tests for the offline handoff; no Chrome/device or network required."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PIPELINE = Path(__file__).resolve().parents[1] / "onecall.py"
FOUNDATION = ["atomize", "patternize", "lld-spec", "spec-interface", "spec-implementation"]
PATH = "anthropic-java-core/src/main/kotlin/com/anthropic/core/Foo.kt"
MODEL_PATH = "anthropic-java-core/src/main/kotlin/com/anthropic/models/Generated.kt"


def cmd(cwd: Path, *args: str, success: bool = True):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if success and result.returncode != 0:
        raise AssertionError(f"{args}: {result.stdout}\n{result.stderr}")
    return result


class OneCallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        cmd(self.repo, "git", "init", "-q")
        for name, content in {
            PATH: "package com.anthropic.core\nclass Foo { fun value(): Int = 7 }\n",
            MODEL_PATH: "package com.anthropic.models\nclass Generated {}\n",
            "README.md": "test\n"
        }.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        cmd(self.repo, "git", "add", ".")
        cmd(self.repo, "git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
            "commit", "-qm", "test")
        self.job = Path(self.temp.name) / "job.json"
        self.response = Path(self.temp.name) / "receipt.json"
        self.out = Path(self.temp.name) / "review"

    def pipeline(self, *args: str, success: bool = True):
        return cmd(self.repo, sys.executable, str(PIPELINE), *args, success=success)

    def prepare(self, *recipes: str):
        command = ["prepare", "--repo", str(self.repo), "--path", PATH, "--out", str(self.job)]
        for recipe in recipes:
            command += ["--recipe", recipe]
        self.pipeline(*command)
        return json.loads(self.job.read_text())

    @staticmethod
    def receipt(job, output=None):
        return {**{key: job[key] for key in (
            "protocolVersion", "jobId", "sourceKey", "sourceSha256", "recipeIds")},
            "provider": "Chrome LanguageModel", "attempts": 1,
            "output": output or {
                "status": "proposal", "manualReviewRequired": True,
                "atoms": [{"name": "value", "responsibility": "returns 7"}],
                "patterns": ["value"], "lld": {
                    "targetPackage": "com.anthropic.core",
                    "interfaceName": "Foo", "implementationName": "FooImpl",
                    "operations": [{"signature": "int value()", "sourceAnchor": 2,
                                    "preconditions": [], "postconditions": ["returns 7"],
                                    "exceptionBehavior": [], "sideEffects": []}],
                    "invariants": ["returns 7"], "dependencies": []},
                "interfaceJava": "interface Foo { int value(); }",
                "implementationJava": "final class FooImpl implements Foo { public int value() { return 7; } }",
                "preservedContracts": ["value"] , "risks": []
            }}

    def test_foundation_and_optional_recipe_are_assembled_in_order(self):
        job = self.prepare("extract-helper")
        self.assertEqual(job["recipeIds"], FOUNDATION + ["extract-helper"])
        self.assertEqual(len(job["jobId"]), 64)
        self.assertEqual(len(job["sourceKey"]), 64)
        self.assertEqual(job["classification"], "lexical-hints-not-AST")
        self.assertIn("value", job["source"])
        self.assertNotIn("README", job["source"])
        self.assertNotIn("../../", job["sourcePath"])
        self.assertFalse((self.repo / "tools").exists())

    def test_result_is_staged_but_source_is_untouched(self):
        job = self.prepare("resource-lifecycle")
        self.response.write_text(json.dumps(self.receipt(job)))
        self.pipeline("verify", "--repo", str(self.repo), "--job", str(self.job),
                      "--result", str(self.response), "--out", str(self.out))
        review = self.out / job["jobId"]
        self.assertTrue((review / "lld.json").is_file())
        self.assertTrue((review / "interface.java.proposal.txt").is_file())
        self.assertTrue((review / "implementation.java.proposal.txt").is_file())
        self.assertTrue((review / "ACCEPTANCE.md").is_file())
        self.assertEqual(cmd(self.repo, "git", "status", "--porcelain").stdout.strip(), "")
        again = self.pipeline("verify", "--repo", str(self.repo), "--job", str(self.job),
                              "--result", str(self.response), "--out", str(self.out), success=False)
        self.assertNotEqual(again.returncode, 0)

    def test_rejects_stale_index_and_changed_receipt(self):
        job = self.prepare("loop-to-stream")
        receipt = self.receipt(job)
        receipt["sourceKey"] = "a" * 64
        self.response.write_text(json.dumps(receipt))
        result = self.pipeline("verify", "--repo", str(self.repo), "--job", str(self.job),
                               "--result", str(self.response), "--out", str(self.out), success=False)
        self.assertIn("mismatch", result.stderr)
        receipt["sourceKey"] = job["sourceKey"]
        self.response.write_text(json.dumps(receipt))
        (self.repo / PATH).write_text("class Foo { fun value() = 9 }\n")
        cmd(self.repo, "git", "add", PATH)
        result = self.pipeline("verify", "--repo", str(self.repo), "--job", str(self.job),
                               "--result", str(self.response), "--out", str(self.out), success=False)
        self.assertIn("Stale source", result.stderr)

    def test_generated_and_unsafe_sources_fail_closed(self):
        for path in (MODEL_PATH, "../README.md", "README.md", "missing.java"):
            result = self.pipeline("prepare", "--repo", str(self.repo), "--path", path,
                                   "--out", str(self.job), success=False)
            self.assertNotEqual(result.returncode, 0, path)
        result = self.pipeline("prepare", "--repo", str(self.repo), "--path", PATH,
                               "--recipe", "not-a-recipe", "--out", str(self.job), success=False)
        self.assertIn("Unknown recipe", result.stderr)

    def test_blocked_proposal_is_valid_without_java_output(self):
        job = self.prepare()
        output = self.receipt(job)["output"]
        output.update(status="blocked", interfaceJava="", implementationJava="",
                      risks=["Kotlin ABI cannot be demonstrated"])
        self.response.write_text(json.dumps(self.receipt(job, output)))
        self.pipeline("verify", "--repo", str(self.repo), "--job", str(self.job),
                      "--result", str(self.response), "--out", str(self.out))
        self.assertFalse((self.out / job["jobId"] / "interface.java.proposal.txt").exists())

    def test_duplicate_and_cyclic_recipe_rejected(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("onecall", PIPELINE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        recipes = mod.load_recipes()
        self.assertEqual(len(recipes), 18)
        self.assertEqual(len(set(recipes)), len(recipes))
        cyclic = {**recipes, "a": {"dependsOn": ["b"]}, "b": {"dependsOn": ["a"]}}
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            mod.ordered_recipes(cyclic, ["a"])


if __name__ == "__main__":
    unittest.main()
