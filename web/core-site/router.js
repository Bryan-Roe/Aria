const routes = {
  "/chat": () => loadView("Chat module coming online..."),
  "/studio": () => loadExternal("./studio/ai-studio.html"),
  "/store": () => loadView("Store module loading..."),
  "/showcase": () => loadView("Showcase module loading...")
};

function loadView(text) {
  const view = document.getElementById("view");
  view.innerHTML = `
    <div class="panel">
      <h2>${text}</h2>
    </div>
  `;
}

async function loadExternal(path) {
  const view = document.getElementById("view");
  const html = await fetch(path).then(r => r.text());
  view.innerHTML = html;
}

function navigate(path) {
  window.history.pushState({}, path, window.location.origin + path);
  if (routes[path]) routes[path]();
}

window.addEventListener("popstate", () => {
  const path = window.location.pathname;
  if (routes[path]) routes[path]();
});

document.addEventListener("click", (e) => {
  const route = e.target.getAttribute("data-route");
  if (route) navigate(route);
});

export { navigate };