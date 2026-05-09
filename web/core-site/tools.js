// Aria Tool Registry
// This is the bridge between AI responses and real system actions

const tools = {
  async generateSite(params) {
    return {
      status: "ok",
      message: "Site generation triggered",
      params
    };
  },

  async openModule({ name }) {
    window.location.hash = `#/${name}`;
    return { status: "ok", module: name };
  },

  async runStoreAction(params) {
    return {
      status: "ok",
      action: "store",
      params
    };
  }
};

export async function executeTool(name, params) {
  if (!tools[name]) {
    return { error: "Unknown tool", name };
  }

  return await tools[name](params);
}

export default tools;