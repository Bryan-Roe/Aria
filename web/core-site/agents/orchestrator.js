import { getRole } from "./roles.js";
import { sendToAI } from "../api.js";
import { executeTool } from "../tools.js";
import { addMemory } from "../memory.js";

// Multi-Agent Orchestrator (v1)
// Coordinates specialized agents

export async function runMultiAgentTask(task) {
  addMemory({ type: "multi_agent_task_start", task });

  // 1. Planner phase
  const planner = getRole("planner");
  const planRes = await sendToAI(task, { system: planner.systemPrompt });

  addMemory({ type: "planner_output", planRes });

  // 2. Execution phase
  const executor = getRole("executor");
  const execRes = await sendToAI(planRes.response || planRes, { system: executor.systemPrompt });

  addMemory({ type: "executor_output", execRes });

  // 3. Tool execution if needed
  let toolResults = [];
  const tools = execRes.tools || [];

  for (const t of tools) {
    const result = await executeTool(t.name, t.params || {});
    toolResults.push(result);
    addMemory({ type: "tool_exec", tool: t, result });
  }

  // 4. Analyst phase
  const analyst = getRole("analyst");
  const final = await sendToAI(
    JSON.stringify({ execRes, toolResults }),
    { system: analyst.systemPrompt }
  );

  addMemory({ type: "multi_agent_final", final });

  return {
    plan: planRes,
    execution: execRes,
    tools: toolResults,
    final: final.response || final
  };
}