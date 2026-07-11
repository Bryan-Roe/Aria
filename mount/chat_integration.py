"""
Chat Integration Module
Interfaces with talk-to-ai chat providers and conversation management
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class ChatIntegration:
    """Integration layer for chat operations"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.workspace_root = Path(config["paths"]["workspace_root"])
        self.chat_path = Path(config["paths"]["talk_to_ai"])
        self.logs_dir = self.chat_path / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        configured_providers = config.get("chat", {}).get("providers", {})
        self.allowed_providers: set[str] = set(configured_providers.keys()) or {"local", "openai", "azure", "lora"}

    def _is_safe_cli_message(self, message: str) -> bool:
        """Validate untrusted message before passing it as a CLI argument."""
        if message.startswith("-"):
            return False
        if any(ch in message for ch in ("\n", "\r", "\x00")):
            return False
        return True

    async def get_status(self) -> dict[str, Any]:
        """Get current chat system status"""
        return {
            "enabled": self.config["chat"]["enabled"],
            "default_provider": self.config["chat"].get("default_provider", "local"),
            "providers": self._get_provider_status(),
            "recent_conversations": self._get_recent_conversations(),
        }

    def _get_provider_status(self) -> dict[str, dict[str, Any]]:
        """Check status of all chat providers"""
        import os

        providers = {}

        # Local provider (always available)
        providers["local"] = {
            "enabled": True,
            "available": True,
            "offline": True,
            "cost": "free",
        }

        # Azure OpenAI
        azure_keys = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT",
            "AZURE_OPENAI_API_VERSION",
        ]
        providers["azure"] = {
            "enabled": self.config["chat"]["providers"]["azure"]["enabled"],
            "available": all(os.getenv(key) for key in azure_keys),
            "configured": all(os.getenv(key) for key in azure_keys),
            "cost": "paid",
        }

        # OpenAI
        providers["openai"] = {
            "enabled": True,
            "available": bool(os.getenv("OPENAI_API_KEY")),
            "configured": bool(os.getenv("OPENAI_API_KEY")),
            "cost": "paid",
        }

        # LoRA adapter
        lora_path = Path(self.config["chat"]["providers"]["lora"]["adapter_path"])
        lora_available = (lora_path / "adapter_config.json").exists()

        providers["lora"] = {
            "enabled": self.config["chat"]["providers"]["lora"]["enabled"],
            "available": lora_available,
            "adapter_path": str(lora_path) if lora_available else None,
            "cost": "free",
        }

        return providers

    def _get_recent_conversations(self, limit: int = 5) -> list[dict[str, Any]]:
        """Get recent conversation logs"""
        conversations = []

        if not self.logs_dir.exists():
            return conversations

        # Find all JSONL conversation files
        jsonl_files = sorted(
            self.logs_dir.glob("chat_*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:limit]

        for jsonl_file in jsonl_files:
            try:
                messages = []
                with open(jsonl_file) as f:
                    for line in f:
                        if line.strip():
                            messages.append(json.loads(line))

                conversations.append(
                    {
                        "file": jsonl_file.name,
                        "timestamp": messages[0].get("timestamp") if messages else None,
                        "message_count": len(messages),
                        "preview": (messages[0].get("content", "")[:100] if messages else ""),
                    }
                )
            except Exception:
                continue

        return conversations

    async def chat(
        self,
        message: str,
        provider: str | None = None,
        stream: bool = False,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a chat message and get response"""
        try:
            normalized_provider = (provider or self.config["chat"]["default_provider"]).strip().lower()
            if normalized_provider not in self.allowed_providers:
                return {"success": False, "error": f"Unsupported provider: {normalized_provider}"}

            provider_arg_map = {
                "local": "local",
                "openai": "openai",
                "azure": "azure",
                "lora": "lora",
            }
            provider_arg = provider_arg_map.get(normalized_provider)
            if provider_arg is None:
                return {"success": False, "error": f"Unsupported provider: {normalized_provider}"}

            if not isinstance(message, str):
                return {"success": False, "error": "Message must be a string"}
            message = message.strip()
            if not message:
                return {"success": False, "error": "Message cannot be empty"}
            if len(message) > 8000:
                return {"success": False, "error": "Message is too long"}
            if not self._is_safe_cli_message(message):
                return {"success": False, "error": "Message contains unsafe characters for CLI execution"}

            # For now, we'll use subprocess to call the chat CLI
            # In production, you'd import the provider classes directly
            chat_script = self.chat_path / "src" / "chat_cli.py"

            cmd = [
                sys.executable,
                str(chat_script),
                "--provider",
                provider_arg,
                "--once",
            ]

            result = subprocess.run(
                cmd,
                input=message,
                capture_output=True,
                text=True,
                cwd=str(self.chat_path),
            )

            return {
                "success": result.returncode == 0,
                "provider": normalized_provider,
                "message": message,
                "response": result.stdout.strip(),
                "conversation_id": conversation_id or f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_conversations(self) -> list[dict[str, Any]]:
        """List all saved conversations"""
        return self._get_recent_conversations(limit=50)

    async def get_conversation(self, filename: str) -> list[dict[str, Any]]:
        """Get full conversation from a log file"""
        file_path = self.logs_dir / filename

        if not file_path.exists():
            return []

        messages = []
        with open(file_path) as f:
            for line in f:
                if line.strip():
                    messages.append(json.loads(line))

        return messages

    async def save_conversation(self, messages: list[dict[str, Any]], filename: str | None = None) -> dict[str, Any]:
        """Save conversation to JSONL file"""
        try:
            if not filename:
                filename = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

            file_path = self.logs_dir / filename

            with open(file_path, "w") as f:
                for msg in messages:
                    f.write(json.dumps(msg) + "\n")

            return {
                "success": True,
                "filename": filename,
                "message_count": len(messages),
                "path": str(file_path),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def detect_provider(self) -> str:
        """Auto-detect best available chat provider"""
        providers = self._get_provider_status()

        # Priority: Azure > OpenAI > LoRA > Local
        if providers["azure"]["available"]:
            return "azure"
        elif providers["openai"]["available"]:
            return "openai"
        elif providers["lora"]["available"]:
            return "lora"
        else:
            return "local"
