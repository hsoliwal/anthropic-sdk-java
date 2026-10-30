import assert from "node:assert/strict";
import { test } from "node:test";
import { runOnce, localLedger } from "./onecall.mjs";

const job = {
  protocolVersion: 1,
  jobId: "a".repeat(64), sourceKey: "b".repeat(64), sourceSha256: "c".repeat(64),
  sourcePath: "anthropic-java-core/src/main/kotlin/Example.kt",
  recipeIds: ["atomize", "patternize", "lld-spec", "spec-interface", "spec-implementation"],
  instructions: "Preserve contracts", source: "class Example {}"
};
const output = { status: "proposal", manualReviewRequired: true };
function ledger() {
  const values = new Map();
  return localLedger({ getItem: k => values.has(k) ? values.get(k) : null,
    setItem: (k, v) => values.set(k, v) });
}

test("one prompt per source, even if called again", async () => {
  const seen = { prompts: 0, sessions: 0, destroyed: 0 };
  const model = {
    availability: async () => "available",
    create: async () => {
      seen.sessions++;
      return { prompt: async (text, options) => {
        seen.prompts++;
        assert.match(text, /class Example/);
        assert.equal(options.responseConstraint.type, "object");
        return JSON.stringify(output);
      }, destroy: () => seen.destroyed++ };
    }
  };
  const state = ledger();
  const result = await runOnce(job, { model, ledger: state });
  assert.equal(result.attempts, 1);
  assert.equal(result.output.status, "proposal");
  await assert.rejects(runOnce(job, { model, ledger: state }), /budget consumed/);
  assert.deepEqual(seen, { prompts: 1, sessions: 1, destroyed: 1 });
});

test("a failed call burns the budget and destroys the session", async () => {
  let calls = 0, destroyed = 0;
  const model = { availability: async () => "available", create: async () => ({
    prompt: async () => { calls++; throw Error("device error"); },
    destroy: () => destroyed++ }) };
  const state = ledger();
  await assert.rejects(runOnce(job, { model, ledger: state }), /device error/);
  await assert.rejects(runOnce(job, { model, ledger: state }), /budget consumed/);
  assert.equal(calls, 1);
  assert.equal(destroyed, 1);
});

test("unavailable model spends no prompt", async () => {
  const model = { availability: async () => "unavailable" };
  await assert.rejects(runOnce(job, { model, ledger: ledger() }), /unavailable/);
});
