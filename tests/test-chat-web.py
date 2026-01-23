"""
Test script to verify chat web functionality
"""
import sys
from pathlib import Path

# Add talk-to-ai to path
talk_to_ai_path = Path(__file__).resolve().parents[1] / "talk-to-ai" / "src"
sys.path.insert(0, str(talk_to_ai_path))

from talk_to_ai.providers import detect_provider

def test_local_provider():
    """Test that local provider works"""
    print("Testing local provider...")
    
    provider, info = detect_provider(explicit="local")
    print(f"✓ Provider: {info.name}, Model: {info.model}")
    
    messages = [{"role": "user", "content": "Hello"}]
    response = provider.complete(messages, stream=False)
    
    print(f"✓ Response: {response[:100]}...")
    print("✓ Local provider working!")
    assert info.name == "local"
    assert isinstance(response, str)
    assert len(response) > 0

def test_provider_detection():
    """Test auto provider detection"""
    print("\nTesting provider auto-detection...")
    
    provider, info = detect_provider(explicit="auto")
    print(f"✓ Auto-detected: {info.name}, Model: {info.model}")
    
    if info.name == "azure":
        print("  (Using Azure OpenAI - env vars detected)")
    elif info.name == "openai":
        print("  (Using OpenAI - API key detected)")
    else:
        print("  (Using local fallback - no API keys)")
    
    assert info.name in {"azure", "openai", "local", "auto", "lmstudio"}

def main():
    print("=" * 50)
    print("Chat Web - Functionality Test")
    print("=" * 50)
    print()
    
    try:
        test_local_provider()
        test_provider_detection()
        
        print()
        print("=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)
        print()
        print("Ready to start the server:")
        print("  powershell .\\start-chat-web.ps1")
        print()
        print("Or manually:")
        print("  func start")
        print()
        return 0
    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ Test failed: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
