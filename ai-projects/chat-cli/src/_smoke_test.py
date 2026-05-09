from __future__ import annotations

from chat_providers import detect_provider


def main() -> int:
    provider, info = detect_provider(explicit="local")
    messages = [
        {"role": "system", "content": "You are concise."},
        {"role": "user", "content": "Say one short sentence about AI."},
    ]
    result = provider.complete(messages, stream=False)
    assert isinstance(result, str)
    print("Smoke test provider:", info)
    print("Reply:", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
