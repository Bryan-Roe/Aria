"""
AI-Powered Website Maker and Updater

This module provides functionality to automatically generate and update HTML websites
using natural language descriptions. It leverages the existing chat provider infrastructure
to generate HTML, CSS, and JavaScript code.
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Import chat providers using the pattern from tool_maker.py
try:
    from shared.chat_providers import detect_provider
except ImportError:
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
    from shared.chat_providers import detect_provider


class WebsiteMaker:
    """
    Generates and updates complete HTML websites using AI.
    """

    def __init__(self, provider_name: Optional[str] = None):
        """
        Initialize the WebsiteMaker.

        Args:
            provider_name: Optional provider name (azure, openai, local).
                          If None, auto-detects based on environment.
        """
        # detect_provider() returns the provider instance directly
        self.provider = detect_provider()

        self.output_dir = os.path.join(
            os.path.dirname(__file__), "..", "generated_sites"
        )
        os.makedirs(self.output_dir, exist_ok=True)

    def create_website(
        self,
        name: str,
        description: str,
        style: str = "modern",
        pages: Optional[List[str]] = None,
        features: Optional[List[str]] = None,
    ) -> Dict:
        """
        Generate a complete website from natural language description.

        Args:
            name: Name of the website/project
            description: What the website should do/show
            style: Visual style (modern, minimal, corporate, creative)
            pages: List of page names (e.g., ["index", "about", "contact"])
            features: List of features to include (e.g., ["navigation", "footer", "contact form"])

        Returns:
            Dict with 'success', 'files' (dict of filename->content), 'path', 'message'
        """
        if not pages:
            pages = ["index"]
        if not features:
            features = ["responsive design", "modern styling"]

        # Create prompt for the AI
        prompt = self._build_website_prompt(name, description, style, pages, features)

        try:
            # Generate the website code using the AI provider
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert web developer who creates clean, modern, responsive websites.",
                },
                {"role": "user", "content": prompt},
            ]

            response = self.provider.complete(messages, stream=False)

            # Extract HTML, CSS, and JS from the response
            files = self._extract_code_blocks(response)

            if not files:
                return {
                    "success": False,
                    "message": "Failed to extract website code from AI response",
                    "files": {},
                    "path": None,
                }

            # Save files to disk
            project_path = os.path.join(self.output_dir, name)
            os.makedirs(project_path, exist_ok=True)

            for filename, content in files.items():
                filepath = os.path.join(project_path, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

            # Create metadata file
            metadata = {
                "name": name,
                "description": description,
                "style": style,
                "pages": pages,
                "features": features,
                "created_at": datetime.now().isoformat(),
                "files": list(files.keys()),
            }

            with open(os.path.join(project_path, "metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)

            return {
                "success": True,
                "message": f"Website '{name}' created successfully",
                "files": files,
                "path": project_path,
                "metadata": metadata,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating website: {str(e)}",
                "files": {},
                "path": None,
            }

    def update_website(
        self, name: str, update_description: str, target_file: Optional[str] = None
    ) -> Dict:
        """
        Update an existing website based on natural language instructions.

        Args:
            name: Name of the website to update
            update_description: What changes to make
            target_file: Optional specific file to update (e.g., "index.html")

        Returns:
            Dict with 'success', 'updated_files', 'path', 'message'
        """
        project_path = os.path.join(self.output_dir, name)

        if not os.path.exists(project_path):
            return {
                "success": False,
                "message": f"Website '{name}' not found",
                "updated_files": {},
                "path": None,
            }

        # Load metadata
        metadata_path = os.path.join(project_path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        else:
            metadata = {"files": []}

        # Determine which files to update
        if target_file:
            files_to_update = (
                [target_file] if target_file in metadata.get("files", []) else []
            )
        else:
            files_to_update = metadata.get("files", [])

        if not files_to_update:
            return {
                "success": False,
                "message": "No files to update",
                "updated_files": {},
                "path": project_path,
            }

        # Read current file contents
        current_files = {}
        for filename in files_to_update:
            filepath = os.path.join(project_path, filename)
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    current_files[filename] = f.read()

        # Create update prompt
        prompt = self._build_update_prompt(name, update_description, current_files)

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert web developer who updates websites based on user requirements.",
                },
                {"role": "user", "content": prompt},
            ]

            response = self.provider.complete(messages, stream=False)

            # Extract updated code
            updated_files = self._extract_code_blocks(response)

            if not updated_files:
                return {
                    "success": False,
                    "message": "Failed to extract updated code from AI response",
                    "updated_files": {},
                    "path": project_path,
                }

            # Save updated files
            for filename, content in updated_files.items():
                filepath = os.path.join(project_path, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

            # Update metadata
            metadata["last_updated"] = datetime.now().isoformat()
            metadata["last_update_description"] = update_description

            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            return {
                "success": True,
                "message": f"Website '{name}' updated successfully",
                "updated_files": updated_files,
                "path": project_path,
                "metadata": metadata,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error updating website: {str(e)}",
                "updated_files": {},
                "path": project_path,
            }

    def list_websites(self) -> List[Dict]:
        """
        List all generated websites.

        Returns:
            List of dicts with website metadata
        """
        websites = []

        if not os.path.exists(self.output_dir):
            return websites

        for name in os.listdir(self.output_dir):
            project_path = os.path.join(self.output_dir, name)
            if not os.path.isdir(project_path):
                continue

            metadata_path = os.path.join(project_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    metadata["path"] = project_path
                    websites.append(metadata)

        return websites

    def delete_website(self, name: str) -> Dict:
        """
        Delete a generated website.

        Args:
            name: Name of the website to delete

        Returns:
            Dict with 'success' and 'message'
        """
        project_path = os.path.join(self.output_dir, name)

        if not os.path.exists(project_path):
            return {"success": False, "message": f"Website '{name}' not found"}

        try:
            import shutil

            shutil.rmtree(project_path)
            return {
                "success": True,
                "message": f"Website '{name}' deleted successfully",
            }
        except Exception as e:
            return {"success": False, "message": f"Error deleting website: {str(e)}"}

    def _build_website_prompt(
        self,
        name: str,
        description: str,
        style: str,
        pages: List[str],
        features: List[str],
    ) -> str:
        """Build prompt for website generation."""
        prompt = f"""Create a complete, modern, responsive website with the following specifications:

**Project Name:** {name}
**Description:** {description}
**Visual Style:** {style}
**Pages:** {', '.join(pages)}
**Features:** {', '.join(features)}

Generate a fully functional website with:
1. Clean, semantic HTML5
2. Modern CSS3 with responsive design (mobile-friendly)
3. Optional JavaScript for interactivity if needed
4. Professional styling matching the "{style}" aesthetic
5. All code in separate files (HTML, CSS, JS if needed)

Requirements:
- Use modern best practices
- Include meta tags for SEO
- Make it mobile-responsive
- Add smooth animations/transitions
- Include comments in the code

Please provide the complete code for each file with clear file names.
Use markdown code blocks with the filename as the language tag, like:

```html:index.html
<!DOCTYPE html>
...
```

```css:styles.css
body {{
...
}}
```
"""
        return prompt

    def _build_update_prompt(
        self, name: str, update_description: str, current_files: Dict[str, str]
    ) -> str:
        """Build prompt for website update."""
        files_section = "\n\n".join(
            [
                f"**{filename}:**\n```\n{content}\n```"
                for filename, content in current_files.items()
            ]
        )

        prompt = f"""Update the website '{name}' with the following changes:

**Update Description:** {update_description}

**Current Files:**
{files_section}

Please provide the updated code for each file that needs changes.
Use markdown code blocks with the filename as the language tag, like:

```html:index.html
<!DOCTYPE html>
...
```

Only include files that need to be updated. Keep the same structure and style unless the update requires changes.
"""
        return prompt

    def _extract_code_blocks(self, text: str) -> Dict[str, str]:
        """
        Extract code blocks from AI response.

        Looks for patterns like:
        ```html:index.html
        <html>...</html>
        ```

        or

        ```index.html
        <html>...</html>
        ```

        Returns:
            Dict mapping filename to code content
        """
        files = {}

        # Pattern 1: ```language:filename
        pattern1 = r"```(?:\w+):([^\n]+)\n(.*?)```"
        matches1 = re.findall(pattern1, text, re.DOTALL)

        for filename, content in matches1:
            filename = filename.strip()
            files[filename] = content.strip()

        # Pattern 2: ```filename (without language)
        if not files:
            pattern2 = r"```([^\n]+\.(html|css|js))\n(.*?)```"
            matches2 = re.findall(pattern2, text, re.DOTALL | re.IGNORECASE)

            for filename, ext, content in matches2:
                filename = filename.strip()
                files[filename] = content.strip()

        # Pattern 3: Generic code blocks with filename mentioned before
        if not files:
            pattern3 = r"(?:File|Filename|Save as):\s*[`'\"]?([^\n`'\"]+\.(html|css|js))[`'\"]?\s*\n+```(?:\w+)?\n(.*?)```"
            matches3 = re.findall(pattern3, text, re.DOTALL | re.IGNORECASE)

            for filename, ext, content in matches3:
                filename = filename.strip()
                files[filename] = content.strip()

        return files


class WebsiteValidator:
    """
    Validates generated website code for common issues.
    """

    @staticmethod
    def validate_html(html: str) -> Tuple[bool, List[str]]:
        """
        Validate HTML content.

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []

        # Check for DOCTYPE
        if "<!DOCTYPE" not in html.upper():
            warnings.append("Missing DOCTYPE declaration")

        # Check for basic structure
        if "<html" not in html.lower():
            warnings.append("Missing <html> tag")
        if "<head" not in html.lower():
            warnings.append("Missing <head> tag")
        if "<body" not in html.lower():
            warnings.append("Missing <body> tag")

        # Check for title
        if "<title" not in html.lower():
            warnings.append("Missing <title> tag")

        # Check for viewport meta tag (responsive design)
        if "viewport" not in html.lower():
            warnings.append(
                "Missing viewport meta tag (important for mobile responsiveness)"
            )

        is_valid = len(warnings) == 0
        return is_valid, warnings

    @staticmethod
    def validate_css(css: str) -> Tuple[bool, List[str]]:
        """
        Validate CSS content.

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []

        # Check for basic responsive design
        if "@media" not in css.lower():
            warnings.append(
                "No media queries found (consider adding for responsive design)"
            )

        # Check for potential syntax errors (very basic)
        open_braces = css.count("{")
        close_braces = css.count("}")
        if open_braces != close_braces:
            warnings.append(
                f"Mismatched braces: {open_braces} opening, {close_braces} closing"
            )

        is_valid = open_braces == close_braces
        return is_valid, warnings


def create_website_cli():
    """Command-line interface for website creation."""
    import argparse

    parser = argparse.ArgumentParser(description="AI-Powered Website Maker")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new website")
    create_parser.add_argument("name", help="Website name")
    create_parser.add_argument("description", help="Website description")
    create_parser.add_argument("--style", default="modern", help="Visual style")
    create_parser.add_argument("--pages", nargs="+", help="Page names")
    create_parser.add_argument("--features", nargs="+", help="Features to include")
    create_parser.add_argument("--provider", help="AI provider (azure, openai, local)")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update an existing website")
    update_parser.add_argument("name", help="Website name")
    update_parser.add_argument("description", help="Update description")
    update_parser.add_argument("--file", help="Specific file to update")
    update_parser.add_argument("--provider", help="AI provider")

    # List command
    list_parser = subparsers.add_parser("list", help="List all websites")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a website")
    delete_parser.add_argument("name", help="Website name")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    maker = WebsiteMaker(provider_name=getattr(args, "provider", None))

    if args.command == "create":
        result = maker.create_website(
            name=args.name,
            description=args.description,
            style=args.style,
            pages=args.pages,
            features=args.features,
        )
        print(json.dumps(result, indent=2))

    elif args.command == "update":
        result = maker.update_website(
            name=args.name,
            update_description=args.description,
            target_file=getattr(args, "file", None),
        )
        print(json.dumps(result, indent=2))

    elif args.command == "list":
        websites = maker.list_websites()
        print(json.dumps(websites, indent=2))

    elif args.command == "delete":
        result = maker.delete_website(args.name)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    create_website_cli()
