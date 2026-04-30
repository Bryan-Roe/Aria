import { generateSwarm, runSwarmTask } from "./swarm-engine.js";
import { addMemory } from "../memory.js";

// Swarm Competition System (v1)
// Runs competitive evaluation between multiple agent swarms

export async function runSwarmCompetition(task, swarmCount = 3) {
  const swarmSpec = {
    role: "competitor",
    objective: "solve task optimally"
  };

  const swarm = await generateSwarm(swarmSpec, swarmCount);

  const result = await runSwarmTask(task, swarm);

  const winner = result.best;

  addMemory({
    type: "swarm_competition_complete",
    winner: winner.agent?.name,
    score: winner.evaluation?.score
  });

  return {
    winner,
    leaderboard: result.all
  };
}