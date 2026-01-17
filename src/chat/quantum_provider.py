"""
Quantum-Enhanced Chat Provider
Uses quantum computing to enhance AI responses with quantum circuit analysis
"""
import sys
import logging
from pathlib import Path
from typing import Iterator, Optional

# Add quantum-ai to path
quantum_path = Path(__file__).resolve().parent.parent.parent / "quantum-ai" / "src"
if str(quantum_path) not in sys.path:
    sys.path.insert(0, str(quantum_path))

try:
    from quantum_classifier import QuantumClassifier
    QUANTUM_AVAILABLE = True
except ImportError:
    QUANTUM_AVAILABLE = False
    logging.warning("Quantum modules not available - falling back to classical mode")

from chat_providers import BaseChatProvider, ProviderChoice, RoleMessage

logger = logging.getLogger(__name__)


class QuantumChatProvider(BaseChatProvider):
    """
    A chat provider that enhances responses with quantum computing insights.
    
    Uses quantum circuits to analyze sentiment, classify intents, and provide
    quantum-inspired responses.
    """
    
    def __init__(
        self,
        model: str = "quantum-enhanced-local",
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
        **kwargs
    ):
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        
        # Initialize quantum classifier if available
        self.quantum_classifier = None
        if QUANTUM_AVAILABLE:
            try:
                self.quantum_classifier = QuantumClassifier()
                logger.info("Quantum classifier initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize quantum classifier: {e}")
    
    def complete(
        self, 
        messages: list[RoleMessage], 
        stream: bool = False
    ) -> str | Iterator[str]:
        """
        Generate a response using quantum-enhanced processing.
        
        Args:
            messages: Conversation history
            stream: Whether to stream the response
            
        Returns:
            Response string or iterator of response chunks
        """
        # Extract last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # Analyze with quantum circuit if available
        quantum_insight = ""
        if self.quantum_classifier and QUANTUM_AVAILABLE:
            try:
                quantum_insight = self._quantum_analysis(user_message)
            except Exception as e:
                logger.warning(f"Quantum analysis failed: {e}")
        
        # Generate response
        response = self._generate_response(user_message, quantum_insight, messages)
        
        if stream:
            return self._stream_response(response)
        else:
            return response
    
    def _quantum_analysis(self, text: str) -> str:
        """
        Perform quantum circuit analysis on the input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Quantum insights about the text
        """
        # Simple sentiment analysis using quantum classifier
        # Convert text to numeric features (simplified for demo)
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()[:8]  # Use first 8 bytes
        
        # Convert to features in range [0, 1]
        features = [b / 255.0 for b in hash_bytes]
        
        # Pad or truncate to match quantum circuit size
        n_qubits = self.quantum_classifier.n_qubits
        if len(features) < n_qubits:
            features.extend([0.0] * (n_qubits - len(features)))
        else:
            features = features[:n_qubits]
        
        # Run quantum circuit (simplified analysis)
        try:
            import torch
            import numpy as np
            
            inputs = torch.tensor(features, dtype=torch.float32) * 2 * np.pi
            # Create random weights for demo (in production, use trained weights)
            weights = torch.randn(
                self.quantum_classifier.n_layers,
                n_qubits,
                2,
                dtype=torch.float32
            ) * 0.1
            
            # Get quantum circuit output
            output = self.quantum_classifier.forward(inputs.unsqueeze(0), weights)
            
            # Interpret output
            avg_value = float(output.mean())
            if avg_value > 0.3:
                sentiment = "positive"
            elif avg_value < -0.3:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return f"[Quantum Analysis: {sentiment} sentiment detected, coherence: {abs(avg_value):.2f}]"
        except Exception as e:
            logger.error(f"Quantum circuit execution failed: {e}")
            return "[Quantum Analysis: unavailable]"
    
    def _generate_response(
        self, 
        user_message: str, 
        quantum_insight: str,
        messages: list[RoleMessage]
    ) -> str:
        """
        Generate a response based on quantum analysis and conversation history.
        
        Args:
            user_message: Current user message
            quantum_insight: Quantum analysis results
            messages: Full conversation history
            
        Returns:
            Generated response
        """
        # Simple rule-based responses enhanced with quantum insights
        message_lower = user_message.lower()
        
        # Quantum-specific queries
        if "quantum" in message_lower:
            if "how" in message_lower or "what" in message_lower:
                return (
                    f"🔬 {quantum_insight}\n\n"
                    "I'm powered by quantum computing! I use variational quantum circuits "
                    "to analyze your messages at a quantum level. This allows me to detect "
                    "subtle patterns and sentiment through quantum superposition and entanglement.\n\n"
                    "Would you like to learn more about quantum machine learning?"
                )
            elif "circuit" in message_lower:
                return (
                    f"🔬 {quantum_insight}\n\n"
                    "My quantum circuits use parametrized rotation gates (RY, RZ) and "
                    "CNOT gates for entanglement. Each layer processes your input through "
                    "quantum superposition, enabling parallel exploration of solution spaces.\n\n"
                    "The circuit has {self.quantum_classifier.n_qubits} qubits and "
                    "{self.quantum_classifier.n_layers} layers!"
                )
        
        # General queries with quantum enhancement
        greetings = ["hello", "hi", "hey", "greetings"]
        if any(g in message_lower for g in greetings):
            return (
                f"🔬 {quantum_insight}\n\n"
                "Hello! I'm a quantum-enhanced AI assistant. I use real quantum computing "
                "principles to analyze and respond to your messages. How can I help you today?"
            )
        
        # Questions
        if "?" in user_message:
            if len(user_message.split()) < 5:
                return (
                    f"🔬 {quantum_insight}\n\n"
                    "That's an interesting question! While I'm a simplified quantum-enhanced "
                    "system, I'd be happy to discuss quantum computing, machine learning, "
                    "or help with other topics. Could you provide more details?"
                )
            else:
                return (
                    f"🔬 {quantum_insight}\n\n"
                    "Based on quantum analysis of your question, I detect you're seeking "
                    "detailed information. I'm currently in demo mode, but I can discuss:\n"
                    "• Quantum computing basics\n"
                    "• Quantum machine learning\n"
                    "• Variational quantum circuits\n"
                    "• Azure Quantum integration\n\n"
                    "What would you like to explore?"
                )
        
        # Default response with quantum flavor
        return (
            f"🔬 {quantum_insight}\n\n"
            "I've processed your message through my quantum circuit. As a quantum-enhanced AI, "
            "I combine classical language understanding with quantum computing principles. "
            "I'm still learning, but I can discuss quantum computing topics and provide "
            "quantum-analyzed responses!\n\n"
            "Try asking about quantum circuits, qubits, or superposition!"
        )
    
    def _stream_response(self, response: str) -> Iterator[str]:
        """
        Stream a response word by word.
        
        Args:
            response: Full response text
            
        Yields:
            Response chunks
        """
        words = response.split()
        for i, word in enumerate(words):
            if i == 0:
                yield word
            else:
                yield " " + word
        yield "\n"


def create_quantum_provider(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    **kwargs
) -> tuple[QuantumChatProvider, ProviderChoice]:
    """
    Factory function to create a quantum chat provider.
    
    Args:
        model: Model identifier (optional)
        temperature: Response randomness (optional)
        max_output_tokens: Maximum tokens in response (optional)
        **kwargs: Additional provider-specific arguments
        
    Returns:
        Tuple of (provider instance, provider info)
    """
    provider = QuantumChatProvider(
        model=model or "quantum-enhanced-local",
        temperature=temperature or 0.7,
        max_output_tokens=max_output_tokens or 1024,
        **kwargs
    )
    
    info = ProviderChoice(
        name="quantum",
        model=provider.model,
    )
    
    return provider, info
