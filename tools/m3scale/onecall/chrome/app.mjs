import { runOnce, localLedger } from "./onecall.mjs";

const selected = document.querySelector("#job");
const start = document.querySelector("#start");
const status = document.querySelector("#status");
let job = null;

selected.addEventListener("change", async () => {
  job = null;
  start.disabled = true;
  try {
    if (selected.files.length !== 1) throw new Error("Choose one prepared JSON job");
    job = JSON.parse(await selected.files[0].text());
    status.textContent = `Loaded ${job.sourcePath}: ${job.recipeIds.join(", ")}`;
    start.disabled = false;
  } catch (error) {
    status.textContent = String(error);
  }
});

start.addEventListener("click", async () => {
  start.disabled = true; // No automatic retry, including on model errors.
  if (!job) return;
  status.textContent = "Using the on-device model: one attempt for this file revision.";
  try {
    if (!window.isSecureContext || !navigator.locks?.request) {
      throw new Error("Secure localhost/HTTPS and Web Locks support are required");
    }
    const receipt = await navigator.locks.request(
      `m3scale-onecall-v1:${job.sourceKey}`,
      async () => runOnce(job, { model: window.LanguageModel, ledger: localLedger(localStorage) })
    );
    const blob = new Blob([JSON.stringify(receipt, null, 2) + "\n"], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `m3scale-${job.jobId}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    status.textContent = "Proposal receipt saved. Verify with onecall.py; no SDK source was edited.";
  } catch (error) {
    status.textContent = `Failed closed: ${error}. Do not retry the same source revision.`;
  }
});
