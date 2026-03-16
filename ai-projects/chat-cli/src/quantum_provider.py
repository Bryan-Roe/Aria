"""
Quantum LLM Chat Provider
Uses a trained quantum-enhanced language model for chat interactions
Integrates real quantum circuits in the attention mechanism
"""
import sys
import logging
from pathlib import Path
from typing import Iterator, Optional, List, Dict
import json

import torch
import torch.nn.functional as F

# Add quantum-ml to path
repo_root = Path(__file__).resolve().parent.parent.parent.parent
quantum_ml_path = repo_root / "ai-projects" / "quantum-ml"
quantum_ml_src = quantum_ml_path / "src"
for p in [str(quantum_ml_path), str(quantum_ml_src)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from quantum_transformer import QuantumLLM, QUANTUM_AVAILABLE
    QUANTUM_LLM_AVAILABLE = True
except ImportError as e:
    QUANTUM_LLM_AVAILABLE = False
    logging.warning(f"QuantumLLM not available: {e}")

from chat_providers import BaseChatProvider, ProviderChoice, RoleMessage

logger = logging.getLogger(__name__)


class QuantumLLMChatProvider(BaseChatProvider):
    """
    Chat provider using a trained quantum-enhanced language model.
    
    Loads a checkpoint from training and uses the quantum LLM for text generation.
    Quantum circuits are integrated in the attention mechanism.
    """
    
    def __init__(
        self,
        model_path: str,
        temperature: float = 0.8,
        max_output_tokens: int = 200,
        **kwargs
    ):
        super().__init__()
        self.model_path = Path(model_path)
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model
        self.model = None
        self.char_to_idx = {}
        self.idx_to_char = {}
        self.vocab_size = 0
        
        if not QUANTUM_LLM_AVAILABLE:
            logger.error("QuantumLLM not available - cannot initialize provider")
            raise ImportError("QuantumLLM not available")
        
        try:
            self._load_model()
            logger.info(f"Quantum LLM loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load quantum LLM: {e}")
            raise
    
    def _load_model(self):
        """Load the trained quantum LLM from checkpoint."""
        checkpoint_path = self.model_path / "quantum_llm_checkpoint.pt"
        
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
        logger.info(f"Loading checkpoint from {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        # Extract config
        self.vocab_size = checkpoint['vocab_size']
        self.char_to_idx = checkpoint['char_to_idx']
        self.idx_to_char = checkpoint['idx_to_char']
        
        # Create model
        self.model = QuantumLLM(
            vocab_size=self.vocab_size,
            d_model=checkpoint['d_model'],
            n_heads=checkpoint['n_heads'],
            n_layers=checkpoint['n_layers'],
            d_ffn=checkpoint['d_ffn'],
            max_seq_length=checkpoint['max_seq_length'],
            n_qubits=checkpoint['n_qubits'],
            n_quantum_layers=2,
            dropout=0.0,  # No dropout for inference
            use_quantum=True
        ).to(self.device)
        
        # Load weights
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        logger.info(f"Model loaded: {self.vocab_size} vocab, "
                   f"{checkpoint['n_qubits']} qubits, "
                   f"{checkpoint['n_layers']} layers")
    
    def _encode_text(self, text: str) -> torch.Tensor:
        """Encode text to token IDs."""
        indices = [self.char_to_idx.get(c, 0) for c in text]
        return torch.tensor(indices, dtype=torch.long, device=self.device)
    
    def _decode_tokens(self, tokens: torch.Tensor) -> str:
        """Decode token IDs to text."""
        indices = tokens.cpu().tolist()
        chars = [self.idx_to_char.get(i, '') for i in indices]
        return ''.join(chars)
    
    def _generate(self, prompt: str, max_tokens: int) -> str:
        """Generate text using the quantum LLM."""
        # Encode prompt
        context = self._encode_text(prompt)
        
        # Limit context length
        max_context = 128  # Adjust based on model's max_seq_length
        if len(context) > max_context:
            context = context[-max_context:]
        
        context = context.unsqueeze(0)  # Add batch dimension
        
        generated = []
        
        with torch.no_grad():
            for _ in range(max_tokens):
                # Forward pass
                logits = self.model(context)  # [1, seq_len, vocab_size]
                
                # Get logits for last position
                next_logits = logits[0, -1, :] / self.temperature
                
                # Sample next token
                probs = F.softmax(next_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
                
                # Append to context
                context = torch.cat([context, next_token.unsqueeze(0)], dim=1)
                
                # Keep context window manageable
                if context.size(1) > max_context:
                    context = context[:, -max_context:]
                
                # Decode and collect
                char = self.idx_to_char.get(next_token.item(), '')
                generated.append(char)
                
                # Stop on newline after some content
                if char == '\n' and len(generated) > 20:
                    break
        
        return ''.join(generated)
    
    def complete(
        self, 
        messages: List[RoleMessage], 
        stream: bool = False
    ) -> str | Iterator[str]:
        """
        Generate a response using the quantum LLM.
        
        Args:
            messages: Conversation history
            stream: Whether to stream the response
            
        Returns:
            Response string or iterator of response chunks
        """
        if not self.model:
            error_msg = "Model not loaded"
            logger.error(error_msg)
            return error_msg if not stream else iter([error_msg])
        
        # Build prompt from conversation
        prompt_parts = []
        for msg in messages[-5:]:  # Use last 5 messages for context
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                prompt_parts.append(f"User: {content}\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")
        
        prompt_parts.append("Assistant: ")
        prompt = ''.join(prompt_parts)
        
        # Generate response
        try:
            response = self._generate(prompt, self.max_output_tokens)
            response = response.strip()
            
            # Add quantum indicator
            response = f"🔬 [Quantum LLM] {response}"
            
            if stream:
                return self._stream_response(response)
            else:
                return response
                
        except Exception as e:
            error_msg = f"Generation failed: {e}"
            logger.error(error_msg)
            return error_msg if not stream else iter([error_msg])
    
    def _stream_response(self, response: str) -> Iterator[str]:
        """Stream a response character by character."""
        for char in response:
            yield char


def create_quantum_llm_provider(
    model_path: str,
    temperature: float = 0.8,
    max_output_tokens: int = 200,
    **kwargs
) -> tuple[QuantumLLMChatProvider, ProviderChoice]:
    """
    Factory function to create a quantum LLM chat provider.
    
    Args:
        model_path: Path to trained model directory
        temperature: Sampling temperature
        max_output_tokens: Maximum tokens to generate
        **kwargs: Additional arguments
        
    Returns:
        Tuple of (provider instance, provider info)
    """
    if not QUANTUM_LLM_AVAILABLE:
        raise ImportError("QuantumLLM not available - cannot create provider")
    
    provider = QuantumLLMChatProvider(
        model_path=model_path,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        **kwargs
    )
    
    info = ProviderChoice(
        name="quantum-llm",
        model=f"quantum-llm ({Path(model_path).name})",
    )
    
    return provider, info
