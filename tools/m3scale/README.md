# M3-SCALE: inventory before transformation

This is an **opt-in, source-only** bootstrap. Nothing here is applied to SDK sources,
changes the SDK's Gradle build, or adds a runtime dependency. The Maven artifact is
an OpenRewrite recipe catalogue for a later controlled Java-only trial; the SDK remains
Gradle-based. Do not equate an import-only edit with proof of behavior equivalence.

## Deterministic source catalogue (read-only)

    python3 tools/m3scale/inventory.py --format summary
    python3 tools/m3scale/inventory.py --format csv > /tmp/anthropic-source-inventory.csv
    python3 -m unittest discover -s tools/m3scale/tests -p 'test_*.py' -v

The source list is derived from **Git's stage-0 index**, not directory walking:
tracked Java/Kotlin/Kotlin-script paths are sorted and include the indexed blob SHA,
mode, module, source set, and path-based classification. It reports the HEAD SHA as
context, but an uncommitted staged change may differ from HEAD. Check git status
and compare with a clean committed baseline before treating it as a commit snapshot.
Unmerged index entries cause a hard error. No generated files are written unless a
caller redirects stdout. The inventory requires no third-party dependencies.

## Recipe-first development

The independent Maven packaging crate is in recipes/:

    mvn -f tools/m3scale/recipes/pom.xml -DskipTests package

The com.synexia.m3scale.anthropic.JavaImportAtomization OpenRewrite YAML recipe
composes org.openrewrite.java.RemoveUnusedImports and
org.openrewrite.java.OrderImports. To use it, install the recipe JAR in an
**isolated** OpenRewrite-enabled runner with a matching rewrite-java library;
dry-run, inspect each per-file diff, and validate fixed-point behavior before applying.
The recipe JAR itself has no SDK dependencies. OpenRewrite distribution may require
separate repository credentials; it is intentionally not wired into the production
Gradle build or CI.

## Mandatory convergence gates

1. Record the exact base commit and a clean indexed source catalogue.
2. Classify handwritten versus generated sources; never hand-edit generated models.
3. Describe API, unknown variants, request order, retry, streaming, and resource contracts.
4. Add characterization tests before behavior-affecting changes.
5. Dry-run selected Java files, review diffs, rerun recipe to verify fixed point.
6. Run format/lint, compilation, tests, dependency inspection and public API checks.
7. Preserve history: no rebase, squash, force-push, or silent public-contract changes.

Core supports Java 8+, and the MCP module requires Java 17+. Java 21-specific
optimizations must be separately gated until an explicit migration is approved.
JNI and third-party source convergence need licensing, provenance, fallback,
correctness and performance evidence, not performance claims alone.

The discovery backlog is at docs/m3scale/algorithm-catalogue.csv; these are
candidates for evaluation, **not copied or implemented code**.
