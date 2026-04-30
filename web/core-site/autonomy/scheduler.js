import { enqueueTask } from "../background/agent-runner.js";
import { generateProjectIdea, expandProject } from "./project-factory.js";
import { deployProject } from "./deployer.js";
import { addMemory } from "../memory.js";
import { runSwarmCompetition } from "../swarm/competition.js";

// Autonomous Scheduler (v2)
// Now uses swarm-based competition for task generation

let active = false;

async function cycle() {
  // 1. Generate competing swarm-driven ideas
  const competition = await runSwarmCompetition(
    "Generate best next software project to build",
    3
  );

  const winner = competition.winner;

  // 2. Expand winning idea
  const idea = await generateProjectIdea();
  const expanded = await expandProject(idea);

  // 3. Enqueue build task based on swarm winner
  enqueueTask({
    mode: "multi",
    input: `Build project inspired by swarm winner: ${JSON.stringify(winner)}`,
    source: "swarm-scheduler"
  });

  // 4. Optional deployment
  if (Math.random() > 0.5) {
    await deployProject(idea);
  }

  addMemory({ type: "scheduler_cycle_complete", winner });
}

export function startScheduler(interval = 30000) {
  if (active) return;
  active = true;

  addMemory({ type: "scheduler_started" });

  setInterval(() => {
    cycle().catch(err =>
      addMemory({ type: "scheduler_error", error: err.message })
    );
  }, interval);
}

export function stopScheduler() {
  active = false;
  addMemory({ type: "scheduler_stopped" });
}