// Aria Multi-Agent Roles (v1)
// Defines specialized AI agents inside the system

export const roles = {
  planner: {
    name: "planner",
    description: "Breaks tasks into structured steps",
    systemPrompt: "You are a planning agent. Decompose tasks into clear actionable steps."
  },

  coder: {
    name: "coder",
    description: "Generates and modifies code",
    systemPrompt: "You are a coding agent. Produce clean, functional code and explain structure briefly."
  },

  executor: {
    name: "executor",
    description: "Executes tools and system actions",
    systemPrompt: "You are an execution agent. You run tools and validate outputs."
  },

  analyst: {
    name: "analyst",
    description: "Analyzes outputs and results",
    systemPrompt: "You are an analytical agent. Evaluate results and suggest improvements."
  }
};

export function getRole(name) {
  return roles[name] || roles.analyst;
}
