import { sendToAI } from "./api.js";
import { executeTool } from "./tools.js";
import { addMemory } from "./memory.js";

// Aria Agent Loop (v1)
// Enables multi-step reasoning + tool execution chaining

const MAX_STEPS = 5;

function safeParse(json) {
  try {
    return JSON.parse(json);
  } catch {
    return null;
  }
}

export async function runAgent(input, context = {}) {
  let state = {
    input,
    context,
    steps: [],
    final: null
  };

  let currentInput = input;

  for (let i = 0; i < MAX_STEPS; i++) {
    const ai = await sendToAI(currentInput, {
      ...context,
      step: i,
      history: state.steps
    });

    addMemory({ type: "ai_step", data: ai });

    state.steps.push(ai);

    const toolCalls = ai.tools || [];

    if (toolCalls.length === 0) {
      state.final = ai.response || ai;
      break;
    }

    let toolResults = [];

    for (const tool of toolCalls) {
      const result = await executeTool(tool.name, tool.params || {});
      toolResults.push({ tool: tool.name, result });

      addMemory({ type: "tool_exec", tool, result });
    }

    currentInput = `Previous result: ${JSON.stringify(toolResults)}. Continue task: ${input}`;
  }

  if (!state.final) {
    state.final = state.steps[state.steps.length - 1];
  }

  addMemory({ type: "agent_final", result: state.final });

  return state;
}