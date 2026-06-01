// Aria Memory Layer (v1)

const MEMORY_KEY = "aria_memory_v1";

function loadMemory() {
  try {
    const raw = localStorage.getItem(MEMORY_KEY);
    return raw ? JSON.parse(raw) : { logs: [], facts: {}, context: {} };
  } catch {
    return { logs: [], facts: {}, context: {} };
  }
}

function saveMemory(memory) {
  localStorage.setItem(MEMORY_KEY, JSON.stringify(memory));
}

export function addMemory(entry) {
  const memory = loadMemory();
  memory.logs.push({ time: Date.now(), entry });
  if (memory.logs.length > 200) memory.logs = memory.logs.slice(-200);
  saveMemory(memory);
}

export function setFact(key, value) {
  const memory = loadMemory();
  memory.facts[key] = value;
  saveMemory(memory);
}

export function getFact(key) {
  return loadMemory().facts[key];
}

export function getContext() {
  return loadMemory().context;
}

export function updateContext(ctx) {
  const memory = loadMemory();
  memory.context = { ...memory.context, ...ctx };
  saveMemory(memory);
}

export function getRecentMemory(limit = 10) {
  return loadMemory().logs.slice(-limit);
}

export default {
  addMemory,
  setFact,
  getFact,
  getContext,
  updateContext,
  getRecentMemory
};
