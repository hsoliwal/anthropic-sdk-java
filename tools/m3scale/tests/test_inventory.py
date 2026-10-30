"""M3-SCALE index inventory regression tests; no external dependencies."""

import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree


INVENTORY = Path(__file__).resolve().parents[1] / "inventory.py"


class InventoryTests(unittest.TestCase):
    def test_tracked_snapshot_is_sorted_and_ignores_unstaged_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)

            def command(*args):
                return subprocess.run(args, cwd=root, check=True, capture_output=True)

            command("git", "init", "-q")
            files = {
                "anthropic-java-core/src/main/kotlin/com/anthropic/models/Z.kt": "class Z {}\n",
                "anthropic-java-core/src/test/kotlin/com/anthropic/RetryTest.kt": "class T {}\n",
                "anthropic-java-example/src/main/java/com/anthropic/A.java": "class A {}\n",
                "buildSrc/src/main/kotlin/Plugin.kt": "class Plugin {}\n",
                "README.md": "not source\n",
            }
            for filename, content in files.items():
                path = root / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            command("git", "add", ".")
            command("git", "-c", "user.name=M3", "-c", "user.email=m3@example.invalid",
                    "commit", "-qm", "Fixture")

            def inventory(format_name):
                return command(sys.executable, str(INVENTORY), "--repo", str(root),
                               "--format", format_name).stdout.decode("utf-8")

            initial = inventory("summary")
            summary = json.loads(initial)
            self.assertEqual(summary["tracked_source_files"], 4)
            self.assertEqual(summary["by_language"], {"java": 1, "kotlin": 3})
            self.assertEqual(summary["by_source_set"], {"main": 3, "test": 1})
            rows = list(csv.DictReader(io.StringIO(inventory("csv"))))
            self.assertEqual([row["path"] for row in rows], sorted(row["path"] for row in rows))
            self.assertEqual(sum(row["language"] == "java" for row in rows), 1)
            self.assertEqual(len({row["blob_sha"] for row in rows}), 4)
            self.assertEqual(len(json.loads(inventory("json"))["files"]), 4)
            self.assertEqual(next(row for row in rows if row["role"] == "model")["source_set"], "main")

            (root / "anthropic-java-core/src/main/kotlin/com/anthropic/models/Z.kt").write_text(
                "class Z { fun changed() = true }\n"
            )
            self.assertEqual(inventory("summary"), initial)

    def test_recipe_is_separate_declarative_maven_artifact(self):
        recipe_root = INVENTORY.parent / "recipes"
        pom = ElementTree.parse(recipe_root / "pom.xml").getroot()
        ns = {"m": "http://maven.apache.org/POM/4.0.0"}
        self.assertEqual(pom.findtext("m:packaging", namespaces=ns), "jar")
        self.assertIsNone(pom.find("m:dependencies", namespaces=ns))
        yaml = (recipe_root / "src/main/resources/META-INF/rewrite/rewrite.yml").read_text()
        self.assertIn("name: com.synexia.m3scale.anthropic.JavaImportAtomization", yaml)
        self.assertIn("org.openrewrite.java.RemoveUnusedImports", yaml)
        self.assertIn("org.openrewrite.java.OrderImports", yaml)
        self.assertNotIn("ChangeType", yaml)

    def test_rejects_non_repository(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run(
                [sys.executable, str(INVENTORY), "--repo", folder],
                capture_output=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
