# Anthropic SDK M3-SCALE source baseline

Inspected against main at ff39b4120a61859af6d16c969a418140e388841a
(the merge commit for PR #1). This is a Git-tree inventory, **not** a successful
build or behavioral certification.

- Tree entries (files and directories): **6,050**; tracked blobs: **5,470**.
- Tracked source/build files: **5,388** = **5,298 Kotlin** (.kt), **68 Java**
  (.java), **22 Kotlin script** (.kts).
- Under src/main: **2,995**; under src/test: **2,375**; other: **18**.
- anthropic-java-core: 5,229 Kotlin, 4 Java and 1 Kotlin build script.

| Module | Kotlin | Java | Kotlin script | Main | Test |
| --- | ---: | ---: | ---: | ---: | ---: |
| anthropic-java-core | 5229 | 4 | 1 | 2890 | 2343 |
| anthropic-java-example | 0 | 54 | 1 | 54 | 0 |
| anthropic-java-detekt-rules | 23 | 0 | 1 | 22 | 1 |
| anthropic-java-client-okhttp | 10 | 1 | 1 | 4 | 7 |
| anthropic-java-aws | 7 | 1 | 1 | 3 | 5 |
| anthropic-java-bedrock | 9 | 1 | 1 | 3 | 7 |
| anthropic-java-foundry | 4 | 1 | 1 | 2 | 3 |
| anthropic-java-google-cloud | 4 | 1 | 1 | 2 | 3 |
| anthropic-java-mcp | 3 | 0 | 1 | 2 | 1 |
| anthropic-java-vertex | 4 | 1 | 1 | 2 | 3 |
| anthropic-java-ecosystem-test | 1 | 3 | 1 | 0 | 2 |
| anthropic-java | 0 | 1 | 1 | 1 | 0 |
| buildSrc | 4 | 0 | 8 | 10 | 0 |
| root build | 0 | 0 | 2 | 0 | 0 |

Counts include tracked generated files. inventory.py independently recomputes
the source index from Git. Path-based labels do not constitute compiler or AST analysis.

## Contracts / acceptance baseline

- Preserve the published Java API and the SDK 3.3.0 dependency graph.
- Preserve Java 8+ support for core and Java 17+ for MCP.
- Preserve generated models, unknown JSON fields/union variants, request forwarding,
  retries, timeouts, streamed resource cleanup and error propagation.
- Follow REVIEW.md; a recipe pass is never proof of semantic equivalence.
- Run scripts/lint, scripts/build and scripts/test once CI resources and the mock
  prerequisites are available. Save their outcomes before source transformations.

No algorithm donors have been copied or inlined. The accompanying catalogue is
only a candidate evaluation backlog.
