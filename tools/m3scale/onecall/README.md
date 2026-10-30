# M3-SCALE: one Chrome AI call per source revision

This directory is an **offline, proposal-only** extension to the inventory and
OpenRewrite recipe baseline in PR #3. The SDK remains Gradle-based; the Maven
recipe JAR under `../recipes` stays isolated from its dependencies.

## Per-file phases in ONE model prompt

1. Inventory the tracked blob from the Git index and reject generated models,
   tests, Kotlin scripts, symlinks, oversized files and unknown paths.
2. Atomize source (methods, side effects, invariants); lexical anchors are
   navigation hints, **not AST or Java compiler facts**.
3. Patternize repeated structures and record candidates/counterexamples.
4. Generate an LLD with explicit contracts and a *specified* Java interface.
5. Generate a Java implementation proposal based on that LLD and interface.
6. Validate the identity of a single Chrome AI receipt; stage LLD, interface,
   implementation and acceptance checklist **outside the source tree**.

`../recipes/kinds/*.json` contains one named proposal recipe per refactoring
category (18 today). Foundational atomization, patternization, LLD, interface,
and implementation phases are always included. Optional kinds are topologically
ordered with dependencies and cannot auto-apply. Existing executable OpenRewrite
`JavaImportAtomization` remains a separate, deterministic recipe; declarative
M3-SCALE kinds are **not** misrepresented as executable OpenRewrite transforms.

## Use on one handwritten SDK file

From the repository root:

```bash
python3 tools/m3scale/onecall/onecall.py prepare --repo . \
  --path anthropic-java-core/src/main/kotlin/com/anthropic/core/http/RetryingHttpClient.kt \
  --recipe async-lifecycle --recipe characterization-tests \
  --out /tmp/m3scale-job.json

cd tools/m3scale/onecall/chrome
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765` in a desktop Chrome release with the built-in
Prompt API enabled and an available on-device model. Select
`/tmp/m3scale-job.json`, click **Generate one proposal**, and save the returned
JSON. Model availability, device requirements, local download and user activation
may prevent generation; there is no cloud fallback or hidden second call.

```bash
python3 tools/m3scale/onecall/onecall.py verify --repo . \
  --job /tmp/m3scale-job.json --result ~/Downloads/m3scale-<jobId>.json \
  --out /tmp/m3scale-review
```

The verification step checks the indexed blob, complete job fingerprint,
recipe dependency ordering and client-reported one-call receipt. The staging
directory contains `.proposal.txt` artifacts; it does **not** edit a Java or
Kotlin file and does **not** change a public API. If a safe Java translation
cannot be justified, the model should return `status=blocked` with no Java
sources. For a new attempt after a failed generation, create a new, explicitly
reviewed source revision rather than silently retrying the same file.

## One-call enforcement and limits

- The browser program contains exactly one `session.prompt()` per job.
- Its localStorage ledger records an attempt **before** model creation.
- `navigator.locks` serializes attempts per source key across tabs **within
  the same browser origin**, and failed calls still consume the budget.
- Neither a downloaded client receipt nor localStorage is tamper-resistant;
  across profiles/devices/origins this is a **workflow guarantee**, not a
  cryptographic attestation or global one-call accounting service.
- Files are never sent to a custom server; Chrome runs the built-in model
  locally when supported. A localhost static server only serves the UI files.
- Chrome prompts can still hallucinate; JSON constraints do not prove
  compilation or equivalence. Every proposal requires independent review.
- The prompt includes only the selected tracked file, not the whole reactor.
  Cross-file effects must escalate to package/module review.

## Verification

```bash
python3 -m unittest discover -s tools/m3scale/onecall/tests -p 'test_*.py' -v
node --test tools/m3scale/onecall/chrome/test_onecall.mjs
```

Run the repository's `scripts/lint`, `scripts/build`, `scripts/test`, ABI checks
and focused characterization tests *before accepting a source change*. No
production edit is approved by this tool. Preserve Java 8+ for core and Java
17+ for MCP unless a separate contract change is explicitly approved.
