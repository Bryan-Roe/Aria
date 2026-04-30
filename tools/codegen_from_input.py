#!/usr/bin/env python3
"""Generate starter code files from implementation_input.json.

Expected schema (keys):
- goal: str
- target_paths: list[str]
- language: str
- constraints: list[str]
- api_contract: str
- acceptance_criteria: list[str]
- validation_commands: list[str]
- notes: str

Usage:
  python3 tools/codegen_from_input.py --input implementation_input.json --out-root /workspaces/Aria --dry-run
  python3 tools/codegen_from_input.py --input implementation_input.json --out-root /workspaces/Aria --force
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ImplementationInput:
    goal: str
    target_paths: list[str]
    language: str
    constraints: list[str] = field(default_factory=list)
    api_contract: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    validation_commands: list[str] = field(default_factory=list)
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImplementationInput":
        return cls(
            goal=str(data.get("goal", "")).strip(),
            target_paths=[
                str(p).strip() for p in data.get("target_paths", []) if str(p).strip()
            ],
            language=str(data.get("language", "")).strip(),
            constraints=[
                str(c).strip() for c in data.get("constraints", []) if str(c).strip()
            ],
            api_contract=str(data.get("api_contract", "")).strip(),
            acceptance_criteria=[
                str(a).strip()
                for a in data.get("acceptance_criteria", [])
                if str(a).strip()
            ],
            validation_commands=[
                str(v).strip()
                for v in data.get("validation_commands", [])
                if str(v).strip()
            ],
            notes=str(data.get("notes", "")).strip(),
        )

    def validate(self) -> None:
        if not self.goal:
            raise ValueError("Missing required field: goal")
        if not self.target_paths:
            raise ValueError("Missing required field: target_paths (non-empty list)")
        if not self.language:
            raise ValueError("Missing required field: language")
        if not self.acceptance_criteria:
            raise ValueError(
                "Missing required field: acceptance_criteria (non-empty list)"
            )
        if not self.validation_commands:
            raise ValueError(
                "Missing required field: validation_commands (non-empty list)"
            )


HEADER_LINE = "#" * 78


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sanitize_identifier(text: str, fallback: str = "generated_handler") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", text).strip("_")
    if not cleaned:
        return fallback
    if cleaned[0].isdigit():
        cleaned = f"f_{cleaned}"
    return cleaned.lower()


def _python_template(spec: ImplementationInput, target: Path) -> str:
    stem = target.stem
    fn_name = _sanitize_identifier(stem if stem != "__init__" else "generated_handler")

    return f'''"""Auto-generated scaffold for: {target}

Goal:
- {spec.goal}

API Contract:
- {spec.api_contract or "(none specified)"}

Constraints:
{chr(10).join(f"- {c}" for c in spec.constraints) or "- (none)"}

Acceptance Criteria:
{chr(10).join(f"- {a}" for a in spec.acceptance_criteria)}

Validation Commands:
{chr(10).join(f"- {v}" for v in spec.validation_commands)}

Generated at: {_now_iso()}
"""

from __future__ import annotations

from typing import Any


def {fn_name}(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """TODO: Implement logic for '{spec.goal}'."""
    payload = payload or {{}}

    # TODO: Replace scaffold behavior with real implementation.
    return {{
        "status": "not_implemented",
        "goal": {spec.goal!r},
        "target": {str(target)!r},
        "received_keys": sorted(payload.keys()),
    }}
'''


def _js_template(spec: ImplementationInput, target: Path) -> str:
    fn_name = _sanitize_identifier(target.stem, fallback="generatedHandler")
    return f"""/**
 * Auto-generated scaffold for: {target}
 * Goal: {spec.goal}
 * API Contract: {spec.api_contract or "(none specified)"}
 * Generated at: {_now_iso()}
 */

export function {fn_name}(payload = {{}}) {{
  // TODO: Implement logic for: {spec.goal}
  return {{
    status: "not_implemented",
    goal: {json.dumps(spec.goal)},
    target: {json.dumps(str(target))},
    receivedKeys: Object.keys(payload).sort(),
  }};
}}
"""


def _ts_template(spec: ImplementationInput, target: Path) -> str:
    fn_name = _sanitize_identifier(target.stem, fallback="generatedHandler")
    return f"""/**
 * Auto-generated scaffold for: {target}
 * Goal: {spec.goal}
 * API Contract: {spec.api_contract or "(none specified)"}
 * Generated at: {_now_iso()}
 */

export type GeneratedResult = {{
  status: "not_implemented";
  goal: string;
  target: string;
  receivedKeys: string[];
}};

export function {fn_name}(payload: Record<string, unknown> = {{}}): GeneratedResult {{
  // TODO: Implement logic for: {spec.goal}
  return {{
    status: "not_implemented",
    goal: {json.dumps(spec.goal)},
    target: {json.dumps(str(target))},
    receivedKeys: Object.keys(payload).sort(),
  }};
}}
"""


def _html_template(spec: ImplementationInput, target: Path) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{target.stem}</title>
  </head>
  <body>
    <main>
      <h1>Scaffold: {target.name}</h1>
      <p><strong>Goal:</strong> {spec.goal}</p>
      <p><strong>API Contract:</strong> {spec.api_contract or "(none specified)"}</p>
      <p><strong>Generated:</strong> {_now_iso()}</p>
    </main>
  </body>
</html>
"""


def _css_template(spec: ImplementationInput, target: Path) -> str:
    return f"""/* Auto-generated scaffold for: {target}
 * Goal: {spec.goal}
 * Generated at: {_now_iso()}
 */

:root {{
  --accent: #4f46e5;
}}

body {{
  font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  margin: 0;
  padding: 1rem;
}}

/* TODO: add styles required by acceptance criteria */
"""


def _md_template(spec: ImplementationInput, target: Path) -> str:
    constraints = "\n".join(f"- {c}" for c in spec.constraints) or "- (none)"
    acceptance = "\n".join(f"- [ ] {a}" for a in spec.acceptance_criteria)
    validation = "\n".join(f"- `{v}`" for v in spec.validation_commands)

    return f"""# {target.stem}

## Goal
{spec.goal}

## API Contract
{spec.api_contract or "(none specified)"}

## Constraints
{constraints}

## Acceptance Criteria
{acceptance}

## Validation Commands
{validation}

_Generated at {_now_iso()}_
"""


def render_template(spec: ImplementationInput, target: Path) -> str:
    suffix = target.suffix.lower()
    if suffix == ".py":
        return _python_template(spec, target)
    if suffix in {".js", ".mjs", ".cjs"}:
        return _js_template(spec, target)
    if suffix in {".ts", ".tsx"}:
        return _ts_template(spec, target)
    if suffix in {".html", ".htm"}:
        return _html_template(spec, target)
    if suffix == ".css":
        return _css_template(spec, target)
    return _md_template(spec, target)


def load_spec(path: Path) -> ImplementationInput:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be an object")
    spec = ImplementationInput.from_dict(data)
    spec.validate()
    return spec


def write_or_preview(
    out_root: Path,
    spec: ImplementationInput,
    dry_run: bool,
    force: bool,
) -> tuple[list[str], list[str], list[str]]:
    created: list[str] = []
    skipped: list[str] = []
    previews: list[str] = []

    for rel_path in spec.target_paths:
        target = (out_root / rel_path).resolve()
        try:
            target.relative_to(out_root.resolve())
        except ValueError as exc:
            raise ValueError(f"Target path escapes out-root: {rel_path}") from exc

        content = render_template(spec, Path(rel_path))

        if dry_run:
            previews.append(f"[DRY-RUN] would create/update: {target}")
            continue

        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists() and not force:
            skipped.append(f"exists (use --force to overwrite): {target}")
            continue

        target.write_text(content, encoding="utf-8")
        created.append(str(target))

    return created, skipped, previews


def write_report(
    out_root: Path,
    input_path: Path,
    spec: ImplementationInput,
    created: list[str],
    skipped: list[str],
    previews: list[str],
    dry_run: bool,
) -> Path:
    report_path = out_root / "CODEGEN_REPORT.md"

    content = [
        "# Codegen Report",
        "",
        f"- Generated at: {_now_iso()}",
        f"- Input spec: `{input_path}`",
        f"- Mode: {'dry-run' if dry_run else 'write'}",
        "",
        "## Goal",
        spec.goal,
        "",
        "## Target Paths",
        *[f"- `{p}`" for p in spec.target_paths],
        "",
        "## Created",
        *([f"- `{p}`" for p in created] if created else ["- (none)"]),
        "",
        "## Skipped",
        *([f"- {p}" for p in skipped] if skipped else ["- (none)"]),
        "",
        "## Preview",
        *([f"- {p}" for p in previews] if previews else ["- (none)"]),
        "",
        "## Validation Commands",
        *[f"- `{v}`" for v in spec.validation_commands],
    ]

    report_path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate scaffold code from implementation_input JSON"
    )
    parser.add_argument(
        "--input",
        default="implementation_input.json",
        help="Path to implementation input JSON",
    )
    parser.add_argument(
        "--out-root", default=".", help="Workspace root where target_paths are resolved"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview files without writing"
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    out_root = Path(args.out_root).resolve()

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}")
        return 2

    spec = load_spec(input_path)
    created, skipped, previews = write_or_preview(
        out_root=out_root,
        spec=spec,
        dry_run=args.dry_run,
        force=args.force,
    )

    report_path = write_report(
        out_root=out_root,
        input_path=input_path,
        spec=spec,
        created=created,
        skipped=skipped,
        previews=previews,
        dry_run=args.dry_run,
    )

    print(HEADER_LINE)
    print("Code generation complete")
    print(f"Input: {input_path}")
    print(f"Out root: {out_root}")
    print(f"Mode: {'dry-run' if args.dry_run else 'write'}")
    print(f"Created: {len(created)}")
    print(f"Skipped: {len(skipped)}")
    print(f"Report: {report_path}")
    if previews:
        print("Preview:")
        for line in previews:
            print(f"  - {line}")
    if skipped:
        print("Skipped:")
        for line in skipped:
            print(f"  - {line}")
    print(HEADER_LINE)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
