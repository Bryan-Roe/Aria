import { createAgent } from "../agents/meta-factory.js";
import { evaluateAgent } from "../agents/evaluator.js";
import { addMemory } from "../memory.js";

// Aria Swarm Engine (v1)
// Multiple agents compete to produce best solutions

export async function generateSwarm(spec, size = 3) {
  const swarm = [];

  for (let i = 0; i < size; i++) {
    const agent = await createAgent({
      ...spec,
      variant: i
    });
    swarm.push(agent);
  }

  addMemory({ type: "swarm_generated", swarmSize: size });

  return swarm;
}

export async function runSwarmTask(task, swarm) {
  const results = [];

  for (const agent of swarm) {
    const result = await agentRun(agent, task);
    const evaluation = await evaluateAgent(agent, result);

    results.push({ agent, result, evaluation });
  }

  results.sort((a, b) => (b.evaluation?.score || 0) - (a.evaluation?.score || 0));

  addMemory({ type: "swarm_task_completed", results });

  return {
    best: results[0],
    all: results
  };
}

async function agentRun(agent, task) {
  // placeholder execution bridge
  return {
    agent: agent.name,
    output: `Executed task: ${task} by ${agent.name}`
  };
}