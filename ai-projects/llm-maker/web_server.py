"""
LLM Maker Web Server
Provides HTTP API for the web UI to interact with LLM Maker
"""

import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tool_executor import ToolExecutor
from tool_maker import ToolMaker
from tool_registry import ToolRegistry
from tool_validator import ToolValidator
from website_maker import WebsiteMaker

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
maker = ToolMaker()
validator = ToolValidator()
executor = ToolExecutor()
registry = ToolRegistry()
website_maker = WebsiteMaker()


class LLMMakerHandler(BaseHTTPRequestHandler):
    """HTTP request handler for LLM Maker web UI"""

    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path

        # Serve the web UI
        if path == "/" or path == "/index.html":
            self.serve_file("web_ui.html", "text/html")

        # Serve website maker UI
        elif path == "/website-maker" or path == "/website-maker.html":
            self.serve_file("website_maker_ui.html", "text/html")

        # API: List tools
        elif path == "/api/tools":
            self.handle_list_tools()

        # API: Get registry stats
        elif path == "/api/stats":
            self.handle_get_stats()

        # API: Get specific tool
        elif path.startswith("/api/tools/"):
            tool_id = path.split("/")[-1]
            self.handle_get_tool(tool_id)

        # API: List websites
        elif path == "/api/websites":
            self.handle_list_websites()

        # API: Get specific website
        elif path.startswith("/api/websites/"):
            website_name = path.split("/")[-1]
            self.handle_get_website(website_name)

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """Handle POST requests"""
        parsed = urlparse(self.path)
        path = parsed.path

        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, 400)
            return

        # API: Create tool
        if path == "/api/tools":
            self.handle_create_tool(data)

        # API: Execute tool
        elif path == "/api/tools/execute":
            self.handle_execute_tool(data)

        # API: Validate tool
        elif path == "/api/tools/validate":
            self.handle_validate_tool(data)

        # API: Create website
        elif path == "/api/websites":
            self.handle_create_website(data)

        # API: Update website
        elif path == "/api/websites/update":
            self.handle_update_website(data)

        else:
            self.send_error(404, "Not Found")

    def do_DELETE(self):
        """Handle DELETE requests"""
        parsed = urlparse(self.path)
        path = parsed.path

        # API: Delete tool
        if path.startswith("/api/tools/"):
            tool_id = path.split("/")[-1]
            self.handle_delete_tool(tool_id)

        # API: Delete website
        elif path.startswith("/api/websites/"):
            website_name = path.split("/")[-1]
            self.handle_delete_website(website_name)

        else:
            self.send_error(404, "Not Found")

    def serve_file(self, filename, content_type):
        """Serve a static file"""
        try:
            filepath = Path(__file__).parent / filename
            with open(filepath, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, f"File not found: {filename}")

    def send_json_response(self, data, status=200):
        """Send JSON response"""
        response = json.dumps(data, indent=2)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response.encode())

    def handle_create_tool(self, data):
        """Handle tool creation request"""
        try:
            name = data.get("name")
            description = data.get("description")
            parameters = data.get("parameters", {})
            return_type = data.get("return_type", "Any")

            if not name or not description:
                self.send_json_response(
                    {
                        "success": False,
                        "error": "Missing required fields: name and description",
                    },
                    400,
                )
                return

            logger.info(f"Creating tool: {name}")

            # Create the tool using ToolMaker
            tool = maker.create_tool(
                name=name,
                description=description,
                parameters=parameters,
                return_type=return_type,
            )

            if tool:
                # Register the tool
                tool_id = registry.register(tool)

                self.send_json_response(
                    {
                        "success": True,
                        "tool_id": tool_id,
                        "message": f"Tool '{name}' created successfully",
                        "tool": {
                            "id": tool.id,
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters,
                            "return_type": tool.return_type,
                            "validated": tool.validated,
                            "code": tool.code,
                        },
                    }
                )
            else:
                self.send_json_response(
                    {
                        "success": False,
                        "error": "Failed to create tool - validation failed or generation error",
                    },
                    500,
                )

        except Exception as e:
            logger.error(f"Error creating tool: {e}", exc_info=True)
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_list_tools(self):
        """Handle list tools request"""
        try:
            tools = registry.list_tools()
            tools_data = [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                    "return_type": t.return_type,
                    "created_at": t.created_at,
                    "validated": t.validated,
                    "execution_count": t.execution_count,
                    "code": t.code,
                }
                for t in tools
            ]

            stats = registry.get_stats()

            self.send_json_response({"tools": tools_data, "stats": stats})

        except Exception as e:
            logger.error(f"Error listing tools: {e}", exc_info=True)
            self.send_json_response({"error": str(e)}, 500)

    def handle_get_tool(self, tool_id):
        """Handle get specific tool request"""
        try:
            tool = registry.get(tool_id)

            if not tool:
                tool = registry.get_by_name(tool_id)

            if tool:
                self.send_json_response(
                    {
                        "success": True,
                        "tool": {
                            "id": tool.id,
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters,
                            "return_type": tool.return_type,
                            "created_at": tool.created_at,
                            "validated": tool.validated,
                            "execution_count": tool.execution_count,
                            "code": tool.code,
                        },
                    }
                )
            else:
                self.send_json_response(
                    {"success": False, "error": f"Tool '{tool_id}' not found"}, 404
                )

        except Exception as e:
            logger.error(f"Error getting tool: {e}", exc_info=True)
            self.send_json_response({"error": str(e)}, 500)

    def handle_execute_tool(self, data):
        """Handle tool execution request"""
        try:
            tool_id = data.get("tool_id")
            arguments = data.get("arguments", {})

            if not tool_id:
                self.send_json_response(
                    {"success": False, "error": "Missing tool_id"}, 400
                )
                return

            # Get the tool
            tool = registry.get(tool_id)
            if not tool:
                tool = registry.get_by_name(tool_id)

            if not tool:
                self.send_json_response(
                    {"success": False, "error": f"Tool '{tool_id}' not found"}, 404
                )
                return

            logger.info(f"Executing tool: {tool.name}")

            # Execute the tool
            result = executor.execute(tool.code, tool.name, arguments)

            # Update statistics
            if result.get("success"):
                registry.update_stats(tool.id)

            self.send_json_response(result)

        except Exception as e:
            logger.error(f"Error executing tool: {e}", exc_info=True)
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_validate_tool(self, data):
        """Handle tool validation request"""
        try:
            tool_id = data.get("tool_id")

            if not tool_id:
                self.send_json_response(
                    {"success": False, "error": "Missing tool_id"}, 400
                )
                return

            tool = registry.get(tool_id)
            if not tool:
                tool = registry.get_by_name(tool_id)

            if not tool:
                self.send_json_response(
                    {"success": False, "error": f"Tool '{tool_id}' not found"}, 404
                )
                return

            is_valid, errors = validator.validate(tool.code)

            self.send_json_response(
                {
                    "tool_id": tool.id,
                    "tool_name": tool.name,
                    "is_valid": is_valid,
                    "errors": errors,
                }
            )

        except Exception as e:
            logger.error(f"Error validating tool: {e}", exc_info=True)
            self.send_json_response({"error": str(e)}, 500)

    def handle_delete_tool(self, tool_id):
        """Handle tool deletion request"""
        try:
            success = registry.delete(tool_id)

            if success:
                self.send_json_response(
                    {"success": True, "message": f"Tool '{tool_id}' deleted"}
                )
            else:
                self.send_json_response(
                    {"success": False, "error": f"Tool '{tool_id}' not found"}, 404
                )

        except Exception as e:
            logger.error(f"Error deleting tool: {e}", exc_info=True)
            self.send_json_response({"error": str(e)}, 500)

    def handle_get_stats(self):
        """Handle get registry statistics request"""
        try:
            stats = registry.get_stats()
            self.send_json_response(stats)

        except Exception as e:
            logger.error(f"Error getting stats: {e}", exc_info=True)
            self.send_json_response({"error": str(e)}, 500)

    def handle_create_website(self, data):
        """Handle website creation request"""
        try:
            name = data.get("name")
            description = data.get("description")
            style = data.get("style", "modern")
            pages = data.get("pages", ["index"])
            features = data.get("features", ["responsive design", "modern styling"])

            if not name or not description:
                self.send_json_response(
                    {
                        "success": False,
                        "error": "Missing required fields: name and description",
                    },
                    400,
                )
                return

            logger.info(f"Creating website: {name}")

            result = website_maker.create_website(
                name=name,
                description=description,
                style=style,
                pages=pages,
                features=features,
            )

            self.send_json_response(result)

        except Exception as e:
            logger.error(f"Error creating website: {e}", exc_info=True)
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_update_website(self, data):
        """Handle website update request"""
        try:
            name = data.get("name")
            update_description = data.get("update_description")
            target_file = data.get("target_file")

            if not name or not update_description:
                self.send_json_response(
                    {
                        "success": False,
                        "error": "Missing required fields: name and update_description",
                    },
                    400,
                )
                return

            logger.info(f"Updating website: {name}")

            result = website_maker.update_website(
                name=name,
                update_description=update_description,
                target_file=target_file,
            )

            self.send_json_response(result)

        except Exception as e:
            logger.error(f"Error updating website: {e}", exc_info=True)
            self.send_json_response({"success": False, "error": str(e)}, 500)

    def handle_list_websites(self):
        """Handle list websites request"""
        try:
            websites = website_maker.list_websites()
            self.send_json_response({"websites": websites, "count": len(websites)})

        except Exception as e:
            logger.error(f"Error listing websites: {e}", exc_info=True)
            self.send_json_response({"error": str(e)}, 500)

    def handle_get_website(self, name):
        """Handle get specific website request"""
        try:
            websites = website_maker.list_websites()
            website = next((w for w in websites if w["name"] == name), None)

            if website:
                # Read website files
                import os

                files_content = {}
                for filename in website.get("files", []):
                    filepath = os.path.join(website["path"], filename)
                    if os.path.exists(filepath):
                        with open(filepath, "r", encoding="utf-8") as f:
                            files_content[filename] = f.read()

                website["files_content"] = files_content

                self.send_json_response({"success": True, "website": website})
            else:
                self.send_json_response(
                    {"success": False, "error": f"Website '{name}' not found"}, 404
                )

        except Exception as e:
            logger.error(f"Error getting website: {e}", exc_info=True)
            self.send_json_response({"error": str(e)}, 500)

    def handle_delete_website(self, name):
        """Handle website deletion request"""
        try:
            result = website_maker.delete_website(name)
            self.send_json_response(result)

        except Exception as e:
            logger.error(f"Error deleting website: {e}", exc_info=True)
            self.send_json_response({"error": str(e)}, 500)

    def log_message(self, format, *args):
        """Custom log message format"""
        logger.info(f"{self.address_string()} - {format % args}")


def main():
    """Start the web server"""
    host = "0.0.0.0"
    port = 8090

    server = HTTPServer((host, port), LLMMakerHandler)

    print("=" * 60)
    print("LLM Maker Web Server")
    print("=" * 60)
    print(f"Server running at http://localhost:{port}")
    print(f"Open http://localhost:{port} in your browser")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    main()
