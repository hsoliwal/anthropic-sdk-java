# M3 quality gates for the Gradle-based Anthropic Java SDK

The SDK already uses **ktfmt**, **Palantir Java Format**, **Detekt**, generated
API-compatibility and consumer tests. Its existing `anthropic.java` convention
is applied to every Java module. This PR adds built-in Gradle Checkstyle, PMD
and JaCoCo in that one convention so each module owns its own quality reports.

## Opt-in gates and non-regression

```bash
./scripts/m3-quality
# Equivalent: ./gradlew -Pm3Quality=true m3Quality
```

Default `./scripts/lint`, `./scripts/build`, `./scripts/test` retain their
existing semantics. With `-Pm3Quality=true`, each module evaluates
`checkstyleMain`, `checkstyleTest`, `pmdMain`, `pmdTest` and
`jacocoTestReport`. Reports are non-mutating and use the existing JDK 21
Gradle toolchain. The quality profile does not change SDK Java 8-compatible
bytecode, generated source, public API or runtime dependencies.

Checkstyle/PMD are **Java-only**. Detekt and ktfmt remain authoritative for
Kotlin; the Palantir Java formatter is not replaced. The conservative
Checkstyle starter includes unused/star imports and empty blocks. Full Sun
checks require their own reviewed baseline in this heavily generated SDK.

**Dependency lock prerequisite:** this SDK uses STRICT Gradle dependency
locking. The newly applied Checkstyle/PMD configurations need pinned lock
entries before the opt-in tasks can resolve from a clean checkout. Generate
them through the existing `./scripts/lock` workflow in a networked Gradle
9.5.1 environment and review every lockfile delta. Until those dependencies
are locked and the scans have passed, this is a **draft**, not a green quality
gate.

SpotBugs and Error Prone Gradle plugins also require buildSrc classpath and
lockfile changes. Their versions must be pinned and integrated through a
separate convention recipe with compilation/consumer test evidence. Sonar
needs server configuration and a token; OWASP scanning needs an NVD database.
Do not claim those as enabled by this patch.

No bulk formatting or generated-model rewriting is performed.
