# Build and quality gate baseline

Scope: `hsoliwal/anthropic-sdk-java`, inspected at `main`
`ff39b4120a61859af6d16c969a418140e388841a` (2026-10-30).
This is a **configuration inventory**, not evidence of a green build.

The SDK is built with **Gradle 9.5.1, Kotlin DSL**, not Maven. Do not replace
its Gradle lifecycle or add Maven plugins to the SDK reactor. The independent
M3-SCALE recipe packaging crate, if introduced, remains opt-in and separate.

## Enabled gates and sources of truth

| Gate | Current owner | Invocation | Acceptance |
| --- | --- | --- | --- |
| Dependency graph | `settings.gradle.kts`, per-module `gradle.lockfile`, `anthropic.java` | `./gradlew --offline help` only after artifacts are available; actual build resolves lock state | No missing/out-of-sync lock state |
| Java and Kotlin compile | `anthropic.java`, `anthropic.kotlin` in `buildSrc` | `./scripts/build` (`assemble testClasses`) | No compile warnings promoted to errors, no failing test-source compile |
| Java formatting | `palantir-java-format` in `anthropic.java` | `./scripts/lint` (`lintJava`) | No unformatted Java sources |
| Kotlin formatting | `ktfmt` in `Ktfmt.kt` / `anthropic.ktfmt` | `./scripts/lint` (`lintKotlin`) | No unformatted Kotlin or buildSrc sources |
| Kotlin rules | `detekt` plus custom rules and module baselines | `./scripts/lint` (`detektMain detektTest` on CI) | No new findings outside reviewed baselines |
| Tests and runtime | JUnit Platform; mock via `scripts/mock`, `scripts/test` | `./scripts/test` (`check`) | Full test suite and mock prerequisite pass |
| Consumer compatibility | `anthropic-java-ecosystem-test` | `./scripts/test` | Java 8 and compatible Kotlin consumer tests run, not silently skipped |
| API break detector | `.github/workflows/ci.yml`, `scripts/detect-breaking-changes` | CI `detect-breaking-changes` job | Old model/service tests compile against new API |

### Preferred local order

```bash
./scripts/build
./scripts/lint
./scripts/test
```

These are separate existing entrypoints, so a failure belongs to its owner.
Do **not** run `./scripts/format` as a supposed repair before inspecting the
formatting diff. On CI, lint uses the full Detekt task set rather than the
incremental changed-file optimization used locally.

## Additional quality plugins: not yet enabled

Checkstyle, PMD/CPD, SpotBugs, FindSecBugs, Spotless, JaCoCo, Sonar and
Error Prone are **not** claimed as active Gradle verification gates based on
the inspected root `buildSrc` and version catalogue. They must not be represented
as passing checks. Expansion requires separate recipe-owned, opt-in Gradle
configuration, a recorded baseline for generated code, lockfile updates, no new
runtime/downstream dependencies, and testable acceptance criteria. Avoid
parallel formatters with contradictory styles.

## Evidence required before promotion

1. Capture exact commit SHA, module inventory, Gradle version and toolchain.
2. Verify dependency resolution and compile/testClasses first.
3. Run every enabled formatter and Detekt gate; fix violations in small,
   contract-preserving commits, not bulk generated-model rewrites.
4. Run tests with a proven healthy mock, consumer tests, and API-break checks.
5. Archive relevant CI job IDs and failures; classify tooling errors separately
   from production bugs. Re-run the affected gate, then the full matrix.
6. Only promote PRs with traceable validation; never infer green from a queued,
   missing, skipped, or runnerless job.

Current execution limitation: no Gradle distribution or network-accessible
Maven repositories are available in the local execution environment. The
exact-head GitHub Actions results, not a static inventory, must establish
whether the above gates actually pass.
