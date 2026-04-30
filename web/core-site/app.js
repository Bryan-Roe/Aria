import { runCommandOrAI } from "./api.js";

function initCommandInput() {
  const input = document.getElementById("commandInput");

  input.addEventListener("keydown", async (e) => {
    if (e.key === "Enter") {
      const value = input.value.trim();
      if (!value) return;

      await handleCommand(value);
      input.value = "";
    }
  });
}

async function handleCommand(cmd) {
  const view = document.getElementById("view");

  view.innerHTML = `
    <div class="panel">
      <h2>Processing...</h2>
      <p>${cmd}</p>
    </div>
  `;

  try {
    const result = await runCommandOrAI(cmd);

    view.innerHTML = `
      <div class="panel">
        <h2>${result.type.toUpperCase()}</h2>
        <pre>${typeof result.output === "string" ? result.output : JSON.stringify(result.output, null, 2)}</pre>
      </div>
    `;
  } catch (err) {
    view.innerHTML = `
      <div class="panel">
        <h2>Error</h2>
        <p>${err.message}</p>
      </div>
    `;
  }
}

window.addEventListener("DOMContentLoaded", () => {
  initCommandInput();
});