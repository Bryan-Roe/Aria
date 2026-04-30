async function sendToAI(message, context = {}) {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      message,
      context
    })
  });

  if (!res.ok) {
    throw new Error("AI request failed");
  }

  return await res.json();
}

async function runCommandOrAI(input) {
  // lightweight hybrid layer:
  // 1. detect explicit commands
  // 2. otherwise fallback to AI

  const trimmed = input.trim();

  if (trimmed.startsWith("/")) {
    return {
      type: "command",
      output: `Command received: ${trimmed}`
    };
  }

  const ai = await sendToAI(trimmed);

  return {
    type: "ai",
    output: ai.response || ai
  };
}

export { sendToAI, runCommandOrAI };