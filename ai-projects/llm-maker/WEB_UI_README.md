# LLM Maker - Web UI

User-friendly web interface for creating and managing AI tools with LLM Maker.

## 🚀 Quick Start

1. **Start the web server:**
   ```bash
   cd llm-maker
   python web_server.py
   ```

   Or use the helper script:
   ```bash
   ./start_web_ui.sh
   ```

2. **Open your browser:**
   Navigate to [http://localhost:8090](http://localhost:8090)

## ✨ Features

### Create Tools
- **Natural Language Description**: Describe what you want your tool to do
- **Parameters**: Define input parameters with types (int, str, dict, etc.)
- **Return Types**: Specify expected output type
- **AI-Powered Generation**: LLM automatically creates validated Python code

### View Tools
- **Tool Library**: Browse all created tools
- **Code Preview**: View generated Python code
- **Statistics**: Track tool usage and validation status

### Test Tools
- **Interactive Testing**: Test tools directly in the browser
- **Parameter Input**: Enter test values with type validation
- **Execution Results**: See output, errors, and execution time
- **Real-time Feedback**: Immediate validation and error messages

### Manage Tools
- **Delete Tools**: Remove unwanted tools
- **Search & Filter**: Find tools quickly
- **Export**: Share tools with others

## 🎨 Interface

### Dashboard
- **Tool Creation Form**: Left panel for creating new tools
- **Statistics Panel**: Right panel showing tool metrics
- **Tool Library**: Bottom panel listing all tools

### Tool Creation
1. Enter a descriptive tool name (e.g., `calculate_fibonacci`)
2. Describe what the tool should do
3. Add parameters (click "+ Add Parameter")
   - Parameter name: `n`
   - Parameter type: `int`
4. Specify return type (e.g., `int`)
5. Click "Create Tool"

### Tool Testing
1. Click "🧪 Test Tool" on any tool
2. Enter parameter values
3. Click "▶️ Run Tool"
4. View results or errors

## 🔧 API Endpoints

The web server provides these REST endpoints:

### GET /api/tools
List all tools with statistics
```json
{
  "tools": [...],
  "stats": {
    "total_tools": 5,
    "validated_tools": 5,
    "total_executions": 12
  }
}
```

### POST /api/tools
Create a new tool
```json
{
  "name": "calculate_fibonacci",
  "description": "Calculate nth Fibonacci number",
  "parameters": {"n": "int"},
  "return_type": "int"
}
```

### POST /api/tools/execute
Execute a tool
```json
{
  "tool_id": "tool_xyz",
  "arguments": {"n": 10}
}
```

### DELETE /api/tools/{tool_id}
Delete a tool

## 🎯 Use Cases

1. **Quick Prototyping**: Generate utility functions on-demand
2. **Educational**: Learn function creation and Python patterns
3. **Code Assistant**: Create reusable functions for projects
4. **Experimentation**: Test LLM code generation capabilities

## 🔒 Security

All tools are:
- ✅ Validated before execution
- ✅ Run in sandboxed environment
- ✅ Limited to 5 second timeout
- ✅ Blocked from file/network access

## 📸 Screenshots

### Creating a Tool
The creation form allows you to describe your tool in natural language:
- Tool name: `calculate_fibonacci`
- Description: "Calculate the nth Fibonacci number"
- Parameters: `n: int`
- Return type: `int`

### Testing a Tool
Interactive testing interface:
- Enter parameter values
- View execution results
- See errors with traceback
- Check execution statistics

### Tool Library
Browse and manage all your tools:
- View code
- Test execution
- Delete tools
- Track usage

## 💡 Tips

1. **Be Specific**: Detailed descriptions produce better code
2. **Use Examples**: Add example inputs/outputs for better generation
3. **Test Early**: Test tools immediately after creation
4. **Start Simple**: Begin with simple functions, then add complexity
5. **Check Validation**: Ensure tools are validated (green checkmark)

## 🐛 Troubleshooting

### Server won't start
- Check if port 8090 is available
- Verify Python dependencies are installed
- Run from the `llm-maker` directory

### Tool creation fails
- Check AI provider is configured (Azure OpenAI, OpenAI, or local)
- Verify environment variables are set
- Check logs for validation errors

### Tool execution fails
- Verify parameter types match
- Check for syntax errors in generated code
- Review error traceback in test modal

### Browser can't connect
- Ensure server is running (`python web_server.py`)
- Check firewall settings
- Try http://127.0.0.1:8090 instead

## 🚀 Advanced Usage

### Custom Port
```bash
# Edit web_server.py and change:
port = 8090  # Change to your preferred port
```

### Remote Access
By default, server binds to `0.0.0.0` allowing remote access.
For local-only, change to `127.0.0.1`:
```python
host = '127.0.0.1'  # localhost only
```

### Production Deployment
For production use:
1. Use a proper WSGI server (gunicorn, uWSGI)
2. Add authentication
3. Enable HTTPS
4. Set up rate limiting
5. Add request logging

## 📚 Learn More

- [Main README](README.md) - Full LLM Maker documentation
- [Quick Start](QUICKSTART.md) - Getting started guide
- [API Documentation](README.md#api-reference) - Detailed API docs

---

**Built with ❤️ for the LLM Maker project**
