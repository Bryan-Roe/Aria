#!/usr/bin/env python3
"""
Standalone Local Inference - Run LLM without cloud APIs
No Azure/OpenAI keys needed. Uses LMStudio or LoRA.
"""
import os
import sys
import json
from pathlib import Path
from typing import Optional

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "chat"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "lora"))
sys.path.insert(0, str(PROJECT_ROOT / "shared"))
# Handle talk-to-ai if it exists
if (PROJECT_ROOT / "talk-to-ai" / "src").exists():
    sys.path.insert(0, str(PROJECT_ROOT / "talk-to-ai" / "src"))

def setup_path():
    """Add all necessary paths for imports."""
    # Add src/chat for chat providers (NOT shared to avoid circular import)
    sys.path.insert(0, str(PROJECT_ROOT / "src" / "chat"))
    # Add src/lora for lora provider
    sys.path.insert(0, str(PROJECT_ROOT / "src" / "lora"))

def print_header(title: str):
    """Print formatted header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def main():
    """Run local inference."""
    setup_path()
    
    from chat_providers import detect_provider, LocalEchoProvider
    
    print_header("Local LLM Inference (No Cloud APIs)")
    
    # Try to detect provider
    print("Detecting local provider...")
    print("-" * 70)
    
    try:
        provider, choice = detect_provider()
        print(f"✓ Provider detected: {choice.name}")
        print(f"  Model: {choice.model}")
    except Exception as e:
        print(f"⚠ Could not detect cloud providers: {e}")
        print("\nFalling back to LocalEchoProvider (deterministic, no LLM)")
        print("To use real LLM, set one of:")
        print("  • LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1  (for LMStudio)")
        print("  • Or: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT")
        print("  • Or: OPENAI_API_KEY\n")
        provider = LocalEchoProvider()
        choice_name = "local"
    
    print()
    
    # Test prompts
    test_prompts = [
        "Explain quantum computing in one sentence.",
        "What is the difference between machine learning and deep learning?",
        "How does a neural network learn?",
        "What is reinforcement learning used for?",
    ]
    
    print("Running inference on test prompts...\n")
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"[{i}/{len(test_prompts)}] Prompt: {prompt}")
        print("-" * 70)
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            # Non-streaming for simplicity
            response = provider.complete(messages, stream=False)
            
            if response:
                # Truncate long responses for readability
                if len(response) > 200:
                    print(f"{response[:200]}...\n")
                else:
                    print(f"{response}\n")
            else:
                print("(No response)\n")
        except Exception as e:
            print(f"Error: {e}\n")
    
    print_header("Inference Complete")
    print(f"✓ Local inference working with {choice_name} provider!")
    print("\nUsage examples:\n")
    print("1. Chat CLI:")
    print("   python src/chat/chat_cli.py --provider lmstudio\n")
    print("2. Programmatic:")
    print("""   from src.chat.chat_providers import detect_provider
   provider, choice = detect_provider()
   response = provider.complete([{"role": "user", "content": "Hello"}], stream=False)
   print(response)
   """)
    print("3. With streaming:")
    print("""   response_gen = provider.complete(messages, stream=True)
   for chunk in response_gen:
       print(chunk, end="", flush=True)
   """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
