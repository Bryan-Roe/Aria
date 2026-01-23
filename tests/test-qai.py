"""
QAI Workspace Verification Test
Tests all major components to ensure everything is working
"""
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path('talk-to-ai/src').absolute()))
sys.path.insert(0, str(Path('quantum-ai/src').absolute()))

def test_chat_providers():
    """Test chat provider detection and initialization"""
    print("Testing chat providers...")
    try:
        from talk_to_ai.providers import detect_provider, LocalEchoProvider
        
        # Test local provider
        provider, info = detect_provider(explicit="local")
        assert info.name == "local", f"Expected local provider, got {info.name}"
        print(f"  ✓ Local provider: {info.name} - {info.model}")
        
        # Test provider completion
        messages = [{"role": "user", "content": "Hello"}]
        response = provider.complete(messages, stream=False)
        assert isinstance(response, str), "Expected string response"
        print(f"  ✓ Provider completion works")
        
        return True
    except Exception as e:
        print(f"  ✗ Chat providers failed: {e}")
        return False


def test_quantum_classifier():
    """Test quantum classifier initialization and forward pass"""
    print("\nTesting quantum classifier...")
    try:
        from quantum_classifier import QuantumClassifier
        import torch
        import numpy as np
        
        # Initialize classifier
        classifier = QuantumClassifier()
        print(f"  ✓ QuantumClassifier initialized: {classifier.n_qubits} qubits, {classifier.n_layers} layers")
        
        # Test forward pass
        batch_size = 2
        n_qubits = classifier.n_qubits
        n_layers = classifier.n_layers
        
        # Create dummy inputs and weights
        inputs = torch.randn(batch_size, n_qubits) * 2 * np.pi
        weights = torch.randn(n_layers, n_qubits, 2) * 0.1
        
        # Run forward pass
        output = classifier.forward(inputs, weights)
        
        assert output.shape == (batch_size, n_qubits), f"Expected shape ({batch_size}, {n_qubits}), got {output.shape}"
        print(f"  ✓ Forward pass works: output shape {output.shape}")
        
        return True
    except Exception as e:
        print(f"  ✗ Quantum classifier failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quantum_provider():
    """Test quantum-enhanced chat provider"""
    print("\nTesting quantum provider...")
    try:
        from quantum_provider import create_quantum_provider, QuantumChatProvider
        
        # Create provider
        provider, info = create_quantum_provider()
        assert info.name == "quantum", f"Expected quantum provider, got {info.name}"
        print(f"  ✓ Quantum provider created: {info.name} - {info.model}")
        
        # Test if quantum classifier is available
        if provider.quantum_classifier:
            print(f"  ✓ Quantum classifier available in provider")
        else:
            print(f"  ⚠ Quantum classifier not available (fallback mode)")
        
        # Test completion
        messages = [{"role": "user", "content": "What is quantum computing?"}]
        response = provider.complete(messages, stream=False)
        assert isinstance(response, str), "Expected string response"
        assert len(response) > 0, "Expected non-empty response"
        print(f"  ✓ Quantum provider completion works ({len(response)} chars)")
        
        # Check for quantum insights in response
        if "quantum" in response.lower() or "🔬" in response:
            print(f"  ✓ Response contains quantum enhancements")
        
        return True
    except Exception as e:
        print(f"  ✗ Quantum provider failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_function_app_imports():
    """Test that function_app.py can import all required modules"""
    print("\nTesting function_app imports...")
    try:
        # Test imports that function_app.py uses
        from chat_providers import detect_provider, RoleMessage
        from token_utils import prune_messages
        print(f"  ✓ Chat provider imports OK")
        
        # Test quantum imports
        from quantum_classifier import QuantumClassifier
        print(f"  ✓ Quantum classifier import OK")
        
        return True
    except Exception as e:
        print(f"  ✗ Function app imports failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("QAI Workspace Verification")
    print("=" * 60)
    
    results = {
        "Chat Providers": test_chat_providers(),
        "Quantum Classifier": test_quantum_classifier(),
        "Quantum Provider": test_quantum_provider(),
        "Function App Imports": test_function_app_imports(),
    }
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests PASSED! QAI workspace is ready.")
    else:
        print("⚠️  Some tests FAILED. Check errors above.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
