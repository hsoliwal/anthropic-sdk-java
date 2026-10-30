/** Chrome built-in Prompt API, one attempted prompt per source path+digest per origin. */
export const outputSchema = {
  type: "object",
  properties: {
    status: { type: "string", enum: ["proposal", "blocked"] },
    atoms: { type: "array", items: { type: "object", properties: {
      name: { type: "string" }, responsibility: { type: "string" },
      preconditions: { type: "string" }, postconditions: { type: "string" }
    }, required: ["name", "responsibility", "preconditions", "postconditions"] } },
    patterns: { type: "array", items: { type: "string" } },
    lld: { type: "object", properties: {
      targetPackage: { type: "string" },
      interfaceName: { type: "string" },
      implementationName: { type: "string" },
      operations: { type: "array", items: {
        type: "object", properties: {
          signature: { type: "string" },
          sourceAnchor: { type: "integer" },
          preconditions: { type: "array", items: { type: "string" } },
          postconditions: { type: "array", items: { type: "string" } },
          exceptionBehavior: { type: "array", items: { type: "string" } },
          sideEffects: { type: "array", items: { type: "string" } }
        }, required: ["signature", "sourceAnchor", "preconditions", "postconditions",
          "exceptionBehavior", "sideEffects"]
      } },
      invariants: { type: "array", items: { type: "string" } },
      dependencies: { type: "array", items: { type: "string" } }
    }, required: ["targetPackage", "interfaceName", "implementationName", "operations",
      "invariants", "dependencies"] },
    interfaceJava: { type: "string" },
    implementationJava: { type: "string" },
    preservedContracts: { type: "array", items: { type: "string" } },
    risks: { type: "array", items: { type: "string" } },
    manualReviewRequired: { type: "boolean" }
  },
  required: ["status", "atoms", "patterns", "lld", "interfaceJava",
    "implementationJava", "preservedContracts", "risks", "manualReviewRequired"]
};

export const modalOptions = {
  expectedInputs: [{ type: "text", languages: ["en"] }],
  expectedOutputs: [{ type: "text", languages: ["en"] }]
};

function validateJob(job) {
  if (!job || job.protocolVersion !== 1 ||
      !/^[a-f0-9]{64}$/.test(job.jobId ?? "") ||
      !/^[a-f0-9]{64}$/.test(job.sourceKey ?? "") ||
      !/^[a-f0-9]{64}$/.test(job.sourceSha256 ?? "") ||
      typeof job.source !== "string" || typeof job.instructions !== "string" ||
      !Array.isArray(job.recipeIds) || job.recipeIds.length === 0) {
    throw new Error("Invalid one-file M3-SCALE job");
  }
}

/** The ledger.claim() operation must be durable and atomic for the caller's scope. */
export async function runOnce(job, { model, ledger }) {
  validateJob(job);
  if (!model || typeof model.availability !== "function") {
    throw new Error("Chrome built-in LanguageModel API unavailable");
  }
  const available = await model.availability(modalOptions);
  if (available === "unavailable") throw new Error("Chrome on-device model unavailable");
  // Burn the attempt *before* session creation; do not retry on errors/invalid JSON.
  if (!ledger.claim(job.sourceKey)) throw new Error("One-call budget consumed for this file revision");
  let session;
  try {
    session = await model.create(modalOptions);
    // There must be EXACTLY ONE prompt() invocation for this source revision.
    const response = await session.prompt(
      `${job.instructions}\n\n<source path=${JSON.stringify(job.sourcePath)}>\n${job.source}\n</source>`,
      { responseConstraint: outputSchema }
    );
    const output = typeof response === "string" ? JSON.parse(response) : response;
    if (!output || !["proposal", "blocked"].includes(output.status) ||
        output.manualReviewRequired !== true) {
      throw new Error("Unsafe or invalid model result; attempt remains consumed");
    }
    return {
      protocolVersion: 1, jobId: job.jobId, sourceKey: job.sourceKey,
      sourceSha256: job.sourceSha256, recipeIds: job.recipeIds,
      provider: "Chrome LanguageModel", attempts: 1, output
    };
  } finally {
    session?.destroy?.();
  }
}

/** localStorage records attempts across reloads; requires cross-tab lock in UI. */
export function localLedger(storage) {
  return {
    claim(sourceKey) {
      const key = `m3scale-onecall-v1:${sourceKey}`;
      if (storage.getItem(key) !== null) return false;
      storage.setItem(key, "attempted");
      if (storage.getItem(key) !== "attempted") throw new Error("Cannot persist one-call receipt");
      return true;
    }
  };
}
