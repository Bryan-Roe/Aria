"""Generate a Markdown dependency graph for Python files in the repository."""

import ast
from pathlib import Path

ROOT = Path(".")
OUT = ROOT / "docs" / "reports"
OUT.mkdir(parents=True, exist_ok=True)

report = OUT / "dependency-graph.md"

with report.open("w", encoding="utf-8") as f:
    f.write("# Dependency Graph\n\n")

    for path in ROOT.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports: list[str] = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for imported_name in node.names:
                        imports.append(imported_name.name)
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    imports.append(node.module)

            f.write(f"## {path}\n")
            for imp in sorted(set(imports)):
                f.write(f"- {imp}\n")
            f.write("\n")
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            print(f"Skipping {path}: {exc}")

print(f"Generated {report}")
