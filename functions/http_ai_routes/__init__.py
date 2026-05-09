import json
from pathlib import Path

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    """List discovered Azure Function HTTP routes for quick diagnostics."""
    functions_root = Path(__file__).resolve().parent.parent
    discovered = []

    for entry in sorted(functions_root.iterdir()):
        if not entry.is_dir():
            continue
        function_json = entry / "function.json"
        if not function_json.exists():
            continue
        try:
            data = json.loads(function_json.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            discovered.append(
                {
                    "function": entry.name,
                    "error": f"failed to parse function.json: {exc}",
                }
            )
            continue

        bindings = data.get("bindings", [])
        trigger = next(
            (b for b in bindings if b.get("type") == "httpTrigger"),
            None,
        )
        if trigger is None:
            continue

        discovered.append(
            {
                "function": entry.name,
                "route": trigger.get("route"),
                "methods": trigger.get("methods", []),
                "authLevel": trigger.get("authLevel"),
            }
        )

    payload = {
        "count": len(discovered),
        "functions": discovered,
    }
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        status_code=200,
        mimetype="application/json",
    )
