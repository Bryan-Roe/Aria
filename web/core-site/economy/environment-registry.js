import { addMemory } from "../memory.js";

// Environment Registry
// Enables cross-environment expansion across deployed systems

const environments = new Map();

export function registerEnvironment(env) {
  const id = env.id || `${env.name.toLowerCase().replace(/\s+/g, "-")}-${Date.now()}`;

  const record = {
    id,
    name: env.name,
    type: env.type,
    capabilities: env.capabilities || [],
    constraints: env.constraints || {},
    active: true,
    load: 0,
    domains: env.domains || []
  };

  environments.set(id, record);

  addMemory({
    type: "environment_registered",
    environment: record
  });

  return record;
}

export function listEnvironments() {
  return Array.from(environments.values());
}

export function getEnvironment(id) {
  return environments.get(id);
}

export function updateEnvironmentLoad(id, delta) {
  const env = environments.get(id);
  if (!env) return null;

  env.load = Math.max(0, env.load + delta);
  return env;
}

export function attachDomain(envId, domain) {
  const env = environments.get(envId);
  if (!env) return null;

  if (!env.domains.includes(domain)) {
    env.domains.push(domain);
  }

  addMemory({
    type: "domain_attached",
    envId,
    domain
  });

  return env;
}