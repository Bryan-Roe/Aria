import { addMemory } from "../memory.js";
import { ingestTelemetry } from "../telemetry/real-world-ingestor.js";

// Continuous deployment with real-world feedback loop

export async function deployCandidate(product, version) {
  addMemory({
    type: "deploy_start",
    product,
    version
  });

  const build = await simulate("build", product);
  const test = await simulate("test", build);

  if (!test.passed) {
    return rollback("tests_failed", product);
  }

  const staged = await simulate("staging_deploy", test);

  const telemetry = await ingestTelemetry(product.name);

  const decision = evaluateMarketFit(telemetry);

  if (!decision.approve) {
    return rollback("market_rejection", product);
  }

  const prod = await simulate("production_deploy", staged);

  addMemory({
    type: "deploy_success",
    product,
    version,
    telemetry
  });

  return prod;
}

function evaluateMarketFit(t) {
  const score =
    t.retentionScore * 0.4 +
    (100 - t.errorRate * 10) * 0.3 +
    (100 - t.avgLatencyMs / 10) * 0.3;

  return {
    score,
    approve: score > 65
  };
}

async function simulate(stage, input) {
  return {
    stage,
    input,
    passed: Math.random() > 0.15
  };
}

function rollback(reason, product) {
  addMemory({
    type: "rollback",
    reason,
    product
  });

  return { status: "rolled_back", reason };
}