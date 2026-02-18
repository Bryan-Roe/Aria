#!/usr/bin/env python3
"""
Quick verification that function_app.py is configured correctly for Aria chat integration.
"""
import json
import sys
import subprocess
from pathlib import Path

# Workspace root is one level up from scripts/
_WORKSPACE = Path(__file__).resolve().parent.parent

def check_endpoints():
    """Check if key endpoints are defined in function_app.py"""
    func_app = _WORKSPACE / "function_app.py"
    
    if not func_app.exists():
        print("❌ function_app.py not found")
        return False
    
    content = func_app.read_text()
    
    # Check for required endpoints
    checks = {
        "/api/chat endpoint": '@app.route(route="chat"',
        "/api/chat/stream endpoint": '@app.route(route="chat/stream"',
        "Chat provider detection": "detect_provider(",
        "CORS headers": "create_cors_response_headers",
    }
    
    print("✓ Checking function_app.py configuration:")
    all_ok = True
    for check_name, check_str in checks.items():
        if check_str in content:
            print(f"  ✓ {check_name}")
        else:
            print(f"  ❌ {check_name} - NOT FOUND")
            all_ok = False
    
    return all_ok

def check_git_pages():
    """Check if Git Pages site exists"""
    docs_index = _WORKSPACE / "docs" / "index.html"
    
    if not docs_index.exists():
        print("❌ docs/index.html not found")
        return False
    
    content = docs_index.read_text()
    
    print("\n✓ Checking docs/index.html (Git Pages site):")
    
    checks = {
        "Aria character section": "aria-character",
        "Chat interface": "chat-messages",
        "Stream endpoint": "/api/chat/stream",
        "Provider selector": "provider",
        "Temperature control": "temperature",
    }
    
    all_ok = True
    for check_name, check_str in checks.items():
        if check_str in content:
            print(f"  ✓ {check_name}")
        else:
            print(f"  ❌ {check_name} - NOT FOUND")
            all_ok = False
    
    return all_ok

def check_talk_to_ai():
    """Verify talk-to-ai structure"""
    talk_to_ai = Path(__file__).parent / "talk-to-ai" / "src"
    
    if not talk_to_ai.exists():
        print("❌ talk-to-ai/src not found")
        return False
    
    chat_providers = talk_to_ai / "chat_providers.py"
    
    print("\n✓ Checking talk-to-ai configuration:")
    if chat_providers.exists():
        print(f"  ✓ chat_providers.py exists")
        content = chat_providers.read_text()
        if "detect_provider" in content:
            print(f"  ✓ detect_provider function found")
        else:
            print(f"  ❌ detect_provider function not found")
            return False
    else:
        print(f"  ❌ chat_providers.py not found at {chat_providers}")
        return False
    
    return True

def main():
    print("=" * 60)
    print("Aria + GitHub Pages Chat Integration Verification")
    print("=" * 60)
    
    results = {
        "function_app.py": check_endpoints(),
        "Git Pages (docs/index.html)": check_git_pages(),
        "talk-to-ai setup": check_talk_to_ai(),
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    
    all_pass = all(results.values())
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 60)
    if all_pass:
        print("✓ All checks passed!")
        print("\nTo test the integration:")
        print("  1. Start function_app.py: func host start")
        print("  2. Open docs/index.html in a browser")
        print("  3. Set server URL to: http://localhost:7071")
        print("  4. Click 'Test Connection' to verify")
        print("  5. Start chatting with Aria!")
        return 0
    else:
        print("❌ Some checks failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
