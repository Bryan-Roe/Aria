import { addMemory } from "../memory.js";

// Converts telemetry into economic pressure signals

export function computeMarketScore(telemetry) {
  const demand = telemetry.activeUsers * 0.3;
  const stability = (100 - telemetry.errorRate * 10) * 0.3;
  const performance = (100 - telemetry.avgLatencyMs / 10) * 0.2;
  const retention = telemetry.retentionScore * 0.2;

  const score = demand + stability + performance + retention;

  addMemory({
    type: "market_score",
    score,
    telemetry
  });

  return {
    score,
    trend: score > 70 ? "growing" : "declining"
  };
}