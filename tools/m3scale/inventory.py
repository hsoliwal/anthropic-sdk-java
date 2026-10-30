#!/usr/bin/env python3
"""Read-only, deterministic Git-index inventory for M3-SCALE source atomization."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

INDEX_RECORD = re.compile(rb"^(\d{6}) ([0-9a-f]{40,64}) ([0-3])\t(.*)$", re.DOTALL)
FIELDS = ("path", "module", "source_set", "language", "role", "blob_sha", "mode")


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def describe(path: str) -> tuple[str, str, str, str]:
    head = path.split("/", 1)[0]
    module = head if (head.startswith("anthropic-java") or head == "buildSrc") else "root"
    source_set = "main" if "/src/main/" in path else "test" if "/src/test/" in path else "other"
    language = "java" if path.endswith(".java") else "kotlin" if path.endswith(".kt") else "kotlin-script"
    role = (
        "model" if "/models/" in path else
        "service" if "/services/" in path else
        "http" if "/http/" in path or "/client/okhttp/" in path else
        "handler" if "/handlers/" in path else
        "other"
    )
    return module, source_set, language, role


def inventory(repo: Path) -> list[dict[str, str]]:
    records = []
    for encoded in git(repo, "ls-files", "--stage", "-z").split(b"\0"):
        if not encoded:
            continue
        match = INDEX_RECORD.fullmatch(encoded)
        if match is None:
            raise ValueError("Git index contains a malformed entry")
        mode, blob_sha, stage, raw_path = match.groups()
        if stage != b"0":
            raise ValueError("Unmerged index entry: " + raw_path.decode("utf-8", "replace"))
        path = raw_path.decode("utf-8", "surrogateescape")
        if not path.endswith((".kt", ".java", ".kts")):
            continue
        module, source_set, language, role = describe(path)
        records.append(dict(zip(FIELDS, (path, module, source_set, language, role,
                                         blob_sha.decode("ascii"), mode.decode("ascii")))))
    return sorted(records, key=lambda record: record["path"])


def summarize(records: list[dict[str, str]], revision: str) -> dict:
    by_module: dict[str, Counter] = defaultdict(Counter)
    for record in records:
        by_module[record["module"]][record["language"]] += 1
        by_module[record["module"]][record["source_set"]] += 1
    return {
        "revision": revision,
        "tracked_source_files": len(records),
        "by_language": dict(sorted(Counter(x["language"] for x in records).items())),
        "by_source_set": dict(sorted(Counter(x["source_set"] for x in records).items())),
        "by_module": {key: dict(sorted(value.items())) for key, value in sorted(by_module.items())},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--format", choices=("summary", "json", "csv"), default="summary")
    args = parser.parse_args()
    repo = args.repo.resolve()
    try:
        root = Path(git(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
        if root != repo:
            parser.error("--repo must name the repository root (not a subdirectory)")
        revision = git(repo, "rev-parse", "HEAD").decode("ascii").strip()
        records = inventory(repo)
    except (subprocess.CalledProcessError, ValueError, UnicodeError) as error:
        parser.error(str(error))

    if args.format == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    else:
        result = summarize(records, revision)
        if args.format == "json":
            result["files"] = records
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
