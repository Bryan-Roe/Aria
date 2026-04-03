---
description: "Generate a safe Python tool using the LLM Maker system"
name: "Generate Tool"
argument-hint: "Tool spec + safety requirements (example: function purpose + input/output types + allowed operations)"
agent: llm-maker
---
# Generate Tool

Generate a safe, validated Python function using the ToolMaker system.

## Requirements

1. **Describe the tool clearly**: name, description, parameters with types, return type
2. **Include 2+ usage examples** for better generation quality
3. **Safety constraints are automatic**: no os/sys/subprocess/eval/exec/open

## Template

```
Tool Name: {name}
Description: {what it does}
Parameters:
  - {param_name}: {type} — {description}
Return Type: {type}
Examples:
  - Input: {example_input} → Output: {expected_output}
```

## Safety Rules (enforced by ToolValidator)

- **Banned imports**: os, sys, subprocess, shutil, pathlib, socket, urllib, requests, http, pickle, threading, multiprocessing, ctypes, cffi
- **Banned calls**: eval, exec, compile, __import__, open, input, breakpoint, exit
- **No file I/O, no network access, no dynamic code execution**
- Functions must be pure — no side effects

## Process

1. ToolMaker builds system prompt with safety constraints
2. LLM generates Python function
3. ToolValidator performs AST-based validation
4. Function signature verified against spec
5. Up to 3 retry attempts with error feedback injection
6. Output: validated, safe Python function

Generate the tool now using {{input}}.
