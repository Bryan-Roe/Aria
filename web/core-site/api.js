import { executeTool } from "./tools.js";
import { runAgent } from "./agent.js";

async function sendToAI(message, context = {}) {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      message,
      context,
      toolMode: true
    })
  });

  if (!res.ok) {
    throw new Error("AI request failed");
  }

  return await res.json();
}

async function runCommandOrAI(input) {
  const trimmed = input.trim();

  // 1. tool execution layer
  if (trimmed.startsWith("/")) {
    const [cmd, ...args] = trimmed.slice(1).split(" ");

    const result = await executeTool(cmd, { args });

    return {
      type: "tool",
      output: result
    };
  }

  // 2. FULL AGENT MODE (AI OS runtime)
  const agent = await runAgent(trimmed);

  return {
    type: "agent",
    output: agent.final,
    trace: agent.steps,
    memory: true
  };
}

export { sendToAI, runCommandOrAI };
