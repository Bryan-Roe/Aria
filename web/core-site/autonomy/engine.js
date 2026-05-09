import { enqueueTask } from "../background/agent-runner.js";
import { addMemory } from "../memory.js";

// Aria Autonomy Engine (v1)
// Continuously generates, plans, and schedules work

let active = false;

function generateSeedTasks() {
  return [
    { mode: "multi", input: "Improve system performance" },
    { mode: "multi", input: "Generate new useful application ideas" },
    { mode: "single", input: "Refactor and optimize existing modules" }
  ];
}

export function startAutonomyLoop(interval = 10000) {
  if (active) return;
  active = true;

  addMemory({ type: "autonomy_started" });

  setInterval(() => {
    const tasks = generateSeedTasks();

    for (const t of tasks) {
      enqueueTask({
        ...t,
        source: "autonomy"
      });
    }

    addMemory({ type: "autonomy_cycle_triggered", tasks });
  }, interval);
}

export function stopAutonomyLoop() {
  active = false;
  addMemory({ type: "autonomy_stopped" });
}