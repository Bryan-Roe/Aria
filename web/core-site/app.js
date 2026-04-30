function initCommandInput() {
  const input = document.getElementById("commandInput");

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const value = input.value.trim();
      if (!value) return;

      handleCommand(value);
      input.value = "";
    }
  });
}

function handleCommand(cmd) {
  const view = document.getElementById("view");

  view.innerHTML = `
    <div class="panel">
      <h2>Processing command</h2>
      <p>${cmd}</p>
    </div>
  `;

  // future: connect to /api/chat
}

window.addEventListener("DOMContentLoaded", () => {
  initCommandInput();
});