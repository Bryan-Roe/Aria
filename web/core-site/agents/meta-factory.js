import { roles } from "./roles.js";
import { sendToAI } from "../api.js";
import { addMemory } from "../memory.js";

// Meta-Agent Factory (v1)
// Creates new agents dynamically using AI

export async function createAgent(spec) {
  addMemory({ type: "meta_create_start", spec });

  const prompt = `
You are an AI agent designer.
Create a new specialized agent based on this specification:
${JSON.stringify(spec, null, 2)}

Return JSON in this format:
{
  name: string,
  role: string,
  systemPrompt: string,
  capabilities: string[]
}
`;

  const res = await sendToAI(prompt, { system: "You design AI agents." });

  const agent = typeof res.response === "string"
    ? safeParse(res.response)
    : res.response;

  addMemory({ type: "meta_agent_created", agent });

  return agent;
}

function safeParse(str) {
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
}

export async function spawnAgentSwarm(specs = []) {
  const agents = [];

  for (const spec of specs) {
    const agent = await createAgent(spec);
    agents.push(agent);
  }

  addMemory({ type: "swarm_created", agents });

  return agents;
}
