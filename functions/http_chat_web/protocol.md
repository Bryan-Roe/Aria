# Aria AI Tool Protocol (v1)

Aria supports hybrid AI + tool execution.

## Request Format
{
  "message": "user input",
  "context": {},
  "toolMode": true
}

## Response Format
{
  "response": "text",
  "tools": [
    {
      "name": "toolName",
      "params": {}
    }
  ]
}

## Tool Execution Rules
- Frontend executes `/commands` via tool registry
- AI may suggest tools via `tools[]`
- System may auto-execute safe tools

## Future Expansion
- multi-step agent workflows
- persistent memory
- chained tool execution
