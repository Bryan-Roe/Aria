import { runAgent } from "../agent.js";
import { runMultiAgentTask } from "../agents/orchestrator.js";
import { startAgentRunner } from "../background/agent-runner.js";

startAgentRunner();

const canvas = document.getElementById("canvas");

async function generateApp() {
  const prompt = "Generate a simple web app";

  const result = await runAgent(prompt);

  canvas.innerHTML = `
    <div class="panel">
      <h3>Generated Output</h3>
      <pre>${JSON.stringify(result.final, null, 2)}</pre>
    </div>
  `;
}

async function runMulti() {
  const task = "Design and build a dashboard app";

  const result = await runMultiAgentTask(task);

  canvas.innerHTML = `
    <div class="panel">
      <h3>Multi-Agent Result</h3>
      <pre>${JSON.stringify(result, null, 2)}</pre>
    </div>
  `;
}

document.getElementById("generate").onclick = generateApp;
document.getElementById("runMulti").onclick = runMulti;