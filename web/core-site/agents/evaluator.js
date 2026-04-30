import { sendToAI } from "../api.js";
import { addMemory } from "../memory.js";

// Agent Evaluator (v1)
// Scores and critiques agents + outputs

export async function evaluateAgent(agent, taskResult) {
  const prompt = `
You are an expert AI system evaluator.
Evaluate this agent and its output.

Agent:
${JSON.stringify(agent, null, 2)}

Output:
${JSON.stringify(taskResult, null, 2)}

Return JSON:
{
  score: number (0-100),
  strengths: string[],
  weaknesses: string[],
  improvements: string[]
}
`;

  const res = await sendToAI(prompt, { system: "You evaluate AI agents." });

  const evaluation = typeof res.response === "string"
    ? safeParse(res.response)
    : res.response;

  addMemory({ type: "agent_evaluation", evaluation });

  return evaluation;
}

function safeParse(str) {
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
}

export async function rankAgents(agents, results) {
  const scores = [];

  for (let i = 0; i < agents.length; i++) {
    const evalResult = await evaluateAgent(agents[i], results[i]);
    scores.push({ agent: agents[i], eval: evalResult });
  }

  scores.sort((a, b) => (b.eval?.score || 0) - (a.eval?.score || 0));

  addMemory({ type: "agent_ranking", scores });

  return scores;
}