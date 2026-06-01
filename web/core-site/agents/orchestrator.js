import { getRole } from "./roles.js";
import { sendToAI } from "../api.js";
import { executeTool } from "../tools.js";
import { addMemory } from "../memory.js";
import { evolveAgent } from "./evolver.js";

// Multi-Agent Orchestrator (v2)
// Now supports evolution mode

export async function runMultiAgentTask(task, options = {}) {
  addMemory({ type: "multi_agent_task_start", task, options });

  const planner = getRole("planner");
  const planRes = await sendToAI(task, { system: planner.systemPrompt });

  addMemory({ type: "planner_output", planRes });

  const executor = getRole("executor");
  const execRes = await sendToAI(planRes.response || planRes, { system: executor.systemPrompt });

  addMemory({ type: "executor_output", execRes });

  let toolResults = [];
  const tools = execRes.tools || [];

  for (const t of tools) {
    const result = await executeTool(t.name, t.params || {});
    toolResults.push(result);
    addMemory({ type: "tool_exec", tool: t, result });
  }

  const analyst = getRole("analyst");
  const final = await sendToAI(
    JSON.stringify({ execRes, toolResults }),
    { system: analyst.systemPrompt }
  );

  let output = {
    plan: planRes,
    execution: execRes,
    tools: toolResults,
    final: final.response || final
  };

  if (options.evolve) {
    const evolved = await evolveAgent(
      options.evolveSpec || { role: "auto" },
      task,
      options.iterations || 2
    );

    output.evolution = evolved;
  }

  addMemory({ type: "multi_agent_final", output });

  return output;
}
