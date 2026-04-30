import { addMemory } from "../memory.js";
import { sendToAI } from "../api.js";

// Project Factory (v1)
// Autonomous app/project generation system

export async function generateProjectIdea() {
  const prompt = `Generate a useful software project idea for a modern AI system. Return JSON: {name, description, features[]}`;

  const res = await sendToAI(prompt, { system: "You generate software ideas." });

  const idea = typeof res.response === "string"
    ? safeParse(res.response)
    : res.response;

  addMemory({ type: "project_idea_generated", idea });

  return idea;
}

export async function expandProject(idea) {
  const prompt = `Expand this project into implementation steps and architecture:\n${JSON.stringify(idea)}`;

  const res = await sendToAI(prompt, { system: "You design software architecture." });

  addMemory({ type: "project_expanded", res });

  return res.response || res;
}

function safeParse(str) {
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
}