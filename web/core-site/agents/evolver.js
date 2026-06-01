import { createAgent } from "./meta-factory.js";
import { evaluateAgent } from "./evaluator.js";
import { addMemory } from "../memory.js";
import { runAgent } from "../agent.js";

// Agent Evolution Engine (v1)
// Improves agents over iterations

export async function evolveAgent(baseSpec, task, iterations = 3) {
  let currentSpec = baseSpec;
  let bestAgent = null;
  let bestScore = -Infinity;

  for (let i = 0; i < iterations; i++) {
    const agent = await createAgent(currentSpec);

    const result = await runAgent(task, { agent });

    const evaluation = await evaluateAgent(agent, result);

    addMemory({ type: "evolution_step", i, evaluation });

    if ((evaluation?.score || 0) > bestScore) {
      bestScore = evaluation.score;
      bestAgent = agent;
    }

    // refine spec based on feedback
    currentSpec = {
      ...currentSpec,
      improvements: evaluation?.improvements || []
    };
  }

  addMemory({ type: "agent_evolved", bestAgent, bestScore });

  return {
    bestAgent,
    bestScore
  };
}

export async function selfImproveSwarm(specs, task) {
  const results = [];

  for (const spec of specs) {
    const evolved = await evolveAgent(spec, task);
    results.push(evolved);
  }

  addMemory({ type: "swarm_evolution_complete", results });

  return results;
}
