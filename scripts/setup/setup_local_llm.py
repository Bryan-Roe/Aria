#!/usr/bin/env python3
"""
Quick Local LLM Setup Script
Configures environment for LMStudio, LoRA, and local inference
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional

def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def ask(prompt: str, default: str = "") -> str:
    """Ask user for input with optional default."""
    if default:
        prompt += f" [{default}]: "
    else:
        prompt += ": "
    result = input(prompt).strip()
    return result or default

def check_lmstudio() -> bool:
    """Check if LMStudio server is running."""
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=1)
        return True
    except Exception:
        return False

def check_provider_setup(settings_path: Path) -> dict:
    """Check current provider setup from local.settings.json"""
    if not settings_path.exists():
        return {}
    with open(settings_path) as f:
        data = json.load(f)
    return data.get("Values", {})

def setup_lmstudio(settings_path: Path):
    """Configure LMStudio settings."""
    print_section("LMStudio Setup")
    
    print("LMStudio is an offline AI server that runs locally.")
    print("1. Download from https://lmstudio.ai")
    print("2. Run the app and download a model (Phi-3-mini recommended)")
    print("3. Start the Local Server (port 1234)")
    
    if check_lmstudio():
        print("\n✓ LMStudio server is running on http://127.0.0.1:1234")
    else:
        print("\n⚠ LMStudio server is NOT running")
        print("  Start it now: Open LMStudio → Local Server tab → Start Server")
    
    base_url = ask("LMStudio base URL", "http://127.0.0.1:1234/v1")
    model_name = ask("Model name in LMStudio", "phi-3-mini-instruct")
    
    return {
        "LMSTUDIO_BASE_URL": base_url,
        "LMSTUDIO_MODEL": model_name,
    }

def setup_lora(settings_path: Path):
    """Configure LoRA adapter settings."""
    print_section("LoRA Adapter Setup")
    
    print("LoRA adapters are fine-tuned models that run locally.")
    print("Option 1: Use an existing adapter (directory with adapter_config.json + adapter_model.safetensors)")
    print("Option 2: Train a new adapter")
    
    choice = ask("Use existing (E) or train new (T)?", "E").upper()
    
    if choice == "E":
        adapter_path = ask("Path to adapter directory", "./my_adapter")
        return {
            "QAI_LORA_ADAPTER": adapter_path,
            "QAI_DEFAULT_PROVIDER": "lora",
        }
    else:
        print("\nTo train a new LoRA adapter:")
        print("  cd AI/microsoft_phi-silica-3.6_v1")
        print("  pip install -r requirements.txt")
        print("  python scripts/training/lora_quick_train.py --output-dir ../../my_adapter")
        print("\nAfter training completes, run this script again and select 'E' for existing.")
        return {}

def setup_inference():
    """Configure local inference settings."""
    print_section("Local Inference Setup")
    
    print("Local inference runs models on your machine without cloud APIs.")
    print("No additional setup needed - uses LMStudio or LoRA above.")
    print("\nYou can run inference via:")
    print("  • Chat CLI: python src/chat/chat_cli.py --provider lmstudio")
    print("  • Function API: curl http://localhost:7071/api/chat")
    print("  • Aria web: http://localhost:8080")
    
    return {
        "QAI_ENABLE_LOCAL_TTS": "true",  # Use local text-to-speech fallback
    }

def setup_env_file(settings_path: Path, updates: dict):
    """Update local.settings.json with new values."""
    print_section("Saving Configuration")
    
    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)
    else:
        settings = {
            "IsEncrypted": False,
            "Values": {}
        }
    
    # Merge updates
    for key, value in updates.items():
        settings["Values"][key] = value
    
    # Write back
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
    
    print(f"✓ Updated {settings_path}")
    print("\nConfiguration saved:")
    for key, value in updates.items():
        print(f"  {key}={value}")

def test_provider():
    """Quick test of configured provider."""
    print_section("Testing Provider")
    
    test_cmd = [
        sys.executable, "src/chat/chat_cli.py",
        "--once", "What is a neural network?"
    ]
    
    try:
        print("Running: " + " ".join(test_cmd))
        result = subprocess.run(test_cmd, timeout=30, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Test successful!")
            print("\nResponse:")
            print(result.stdout[:500])
        else:
            print("✗ Test failed")
            if result.stderr:
                print(result.stderr[:500])
    except subprocess.TimeoutExpired:
        print("✗ Test timed out (30s)")
    except Exception as e:
        print(f"✗ Error: {e}")

def show_next_steps(settings: dict):
    """Show what to do next."""
    print_section("Next Steps")
    
    if "LMSTUDIO_BASE_URL" in settings:
        print("1. Start LMStudio")
        print("   • Open LMStudio app")
        print("   • Go to 'Local Server' tab")
        print("   • Click 'Start Server'")
        print()
    
    if "QAI_LORA_ADAPTER" in settings:
        print("2. Or use LoRA adapter")
        print(f"   python src/chat/chat_cli.py --provider lora")
        print()
    
    print("3. Test local chat:")
    print("   python src/chat/chat_cli.py --once 'Hello'")
    print()
    
    print("4. Run Aria web with local LLM:")
    print("   cd src/web/aria/aria_web && python server.py")
    print()
    
    print("5. Or use via function app API:")
    print("   func host start  # In one terminal")
    print("   curl http://localhost:7071/api/chat ...")

def main():
    """Main setup flow."""
    workspace = Path(__file__).parent
    settings_path = workspace / "local.settings.json"
    
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  ARIA LOCAL LLM SETUP".center(58) + "║")
    print("║" + "  Configure LMStudio, LoRA, or Local Inference".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    # Check current setup
    current = check_provider_setup(settings_path)
    if current:
        print(f"\nCurrent setup detected in {settings_path}:")
        for key in ["LMSTUDIO_BASE_URL", "LMSTUDIO_MODEL", "QAI_LORA_ADAPTER", "QAI_DEFAULT_PROVIDER"]:
            if key in current:
                print(f"  {key}={current[key]}")
    
    # Ask which options to setup
    print("\nWhich local LLM options would you like to set up?")
    print("(You can configure multiple)\n")
    
    options = {
        "L": ("LMStudio (offline OpenAI API-compatible server)", setup_lmstudio),
        "A": ("LoRA Adapter (fine-tuned local model)", setup_lora),
        "I": ("Local Inference (smoke test)", setup_inference),
        "T": ("Test after setup", None),
    }
    
    for key, (desc, _) in options.items():
        print(f"  [{key}] {desc}")
    
    choices = ask("Enter choices (e.g., LAI or press Enter for all)", "LAI").upper()
    
    all_updates = {}
    
    if "L" in choices:
        all_updates.update(setup_lmstudio(settings_path))
    
    if "A" in choices:
        all_updates.update(setup_lora(settings_path))
    
    if "I" in choices:
        all_updates.update(setup_inference())
    
    # Save configuration
    if all_updates:
        setup_env_file(settings_path, all_updates)
    
    # Test if requested
    if "T" in choices or ask("\nRun quick test?", "Y").upper() == "Y":
        try:
            test_provider()
        except Exception as e:
            print(f"Test error: {e}")
    
    # Show next steps
    show_next_steps(all_updates or current)
    
    print("\n✓ Setup complete!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
