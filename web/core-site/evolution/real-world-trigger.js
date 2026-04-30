import { ingestTelemetry } from "../telemetry/real-world-ingestor.js";
import { runSwarmCompetition } from "../swarm/competition.js";
import { enqueueTask } from "../background/agent-runner.js";
import { addMemory } from "../memory.js";

// Triggers evolution based on real-world degradation or opportunity

export async function evaluateEvolutionPressure(product) {
  const telemetry = await ingestTelemetry(product.name);

  const pressure = computePressure(telemetry);

  if (pressure > 70) {
    await triggerEvolution(product, telemetry, pressure);
  }

  return pressure;
}

function computePressure(t) {
  const instability = t.errorRate * 10;
  const slowness = t.avgLatencyMs / 20;
  const churn = 100 - t.retentionScore;

  return instability + slowness + churn;
}

async function triggerEvolution(product, telemetry, pressure) {
  const competition = await runSwarmCompetition(
    `Improve product: ${product.name} based on real-world failures`,
    4
  );

  enqueueTask({
    mode: "evolve",
    input: {
      product,
      winner: competition.winner,
      telemetry
    },
    source: "real_world_evolution"
  });

  addMemory({
    type: "evolution_triggered",
    product,
    pressure
  });
}