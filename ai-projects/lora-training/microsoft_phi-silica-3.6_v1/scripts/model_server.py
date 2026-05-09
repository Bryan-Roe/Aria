"""
Model Deployment & Serving
REST API and batch inference capabilities
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer


# Request/Response Models
class GenerationRequest(BaseModel):
    """Request for text generation"""

    prompt: str = Field(..., description="Input prompt")
    max_tokens: int = Field(100, description="Maximum tokens to generate")
    temperature: float = Field(0.7, description="Sampling temperature")
    top_p: float = Field(0.9, description="Top-p sampling")
    top_k: int = Field(50, description="Top-k sampling")
    stream: bool = Field(False, description="Stream response")
    stop_sequences: Optional[List[str]] = Field(None, description="Stop sequences")


class GenerationResponse(BaseModel):
    """Response from text generation"""

    text: str
    tokens_generated: int
    inference_time_ms: float
    model_name: str
    timestamp: str


class BatchRequest(BaseModel):
    """Batch generation request"""

    prompts: List[str]
    max_tokens: int = 100
    temperature: float = 0.7


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    model_loaded: bool
    device: str
    uptime_seconds: float


# Model Server
class ModelServer:
    """Production model serving with REST API"""

    def __init__(
        self,
        model_path: str,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        max_batch_size: int = 32,
        max_queue_size: int = 100,
    ):
        self.model_path = model_path
        self.device = device
        self.max_batch_size = max_batch_size
        self.max_queue_size = max_queue_size

        self.model = None
        self.tokenizer = None
        self.start_time = time.time()

        # Request queue for batching
        self.request_queue = asyncio.Queue(maxsize=max_queue_size)

        print("Initializing Model Server...")
        print(f"Model: {model_path}")
        print(f"Device: {device}")

        self._load_model()

    def _load_model(self):
        """Load model and tokenizer"""
        print("Loading model...")

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model.eval()

        print("✓ Model loaded successfully")
        print(f"  Parameters: {self.model.num_parameters() / 1e9:.2f}B")
        print(
            f"  Memory: {torch.cuda.memory_allocated() / 1e9:.2f}GB"
            if self.device == "cuda"
            else ""
        )

    def generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        stop_sequences: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate text from prompt"""
        start_time = time.perf_counter()

        # Tokenize
        inputs = self.tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=2048
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        # Decode
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove prompt from output
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt) :]

        # Apply stop sequences
        if stop_sequences:
            for stop_seq in stop_sequences:
                if stop_seq in generated_text:
                    generated_text = generated_text[: generated_text.index(stop_seq)]

        inference_time = (time.perf_counter() - start_time) * 1000
        tokens_generated = len(outputs[0]) - len(inputs["input_ids"][0])

        return {
            "text": generated_text.strip(),
            "tokens_generated": tokens_generated,
            "inference_time_ms": inference_time,
            "model_name": Path(self.model_path).name,
            "timestamp": datetime.now().isoformat(),
        }

    def generate_batch(
        self, prompts: List[str], max_tokens: int = 100, temperature: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Batch generation for multiple prompts"""
        results = []

        # Process in batches
        for i in range(0, len(prompts), self.max_batch_size):
            batch_prompts = prompts[i : i + self.max_batch_size]

            # Tokenize batch
            inputs = self.tokenizer(
                batch_prompts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=2048,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate batch
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                )

            # Decode batch
            for j, output in enumerate(outputs):
                generated_text = self.tokenizer.decode(output, skip_special_tokens=True)
                prompt = batch_prompts[j]

                if generated_text.startswith(prompt):
                    generated_text = generated_text[len(prompt) :]

                results.append(
                    {
                        "text": generated_text.strip(),
                        "prompt": prompt,
                        "model_name": Path(self.model_path).name,
                    }
                )

        return results

    def get_health(self) -> Dict[str, Any]:
        """Get server health status"""
        return {
            "status": "healthy" if self.model is not None else "unhealthy",
            "model_loaded": self.model is not None,
            "device": self.device,
            "uptime_seconds": time.time() - self.start_time,
        }


# FastAPI Application
app = FastAPI(
    title="AI Model Serving API",
    description="Production-ready API for AI model inference",
    version="1.0.0",
)

# Global model server instance
model_server: Optional[ModelServer] = None


@app.on_event("startup")
async def startup_event():
    """Initialize model server on startup"""
    global model_server

    # Get model path from environment or config
    import os

    model_path = os.getenv("MODEL_PATH", "data_out/lora_training")

    model_server = ModelServer(model_path)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if model_server is None:
        raise HTTPException(status_code=503, detail="Model server not initialized")

    health = model_server.get_health()
    return HealthResponse(**health)


@app.post("/generate", response_model=GenerationResponse)
async def generate_text(request: GenerationRequest):
    """Generate text from prompt"""
    if model_server is None:
        raise HTTPException(status_code=503, detail="Model server not initialized")

    try:
        result = model_server.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            stop_sequences=request.stop_sequences,
        )

        return GenerationResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/batch")
async def batch_generate(request: BatchRequest):
    """Batch generation endpoint"""
    if model_server is None:
        raise HTTPException(status_code=503, detail="Model server not initialized")

    try:
        results = model_server.generate_batch(
            prompts=request.prompts,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        return {"results": results, "count": len(results)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/models")
async def list_models():
    """List available models"""
    if model_server is None:
        raise HTTPException(status_code=503, detail="Model server not initialized")

    return {"current_model": model_server.model_path, "device": model_server.device}


def main():
    """CLI for model server"""
    import argparse

    parser = argparse.ArgumentParser(description="Model Serving API")
    parser.add_argument(
        "--model", type=str, default="data_out/lora_training", help="Path to model"
    )
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")

    args = parser.parse_args()

    # Set model path as environment variable
    import os

    os.environ["MODEL_PATH"] = args.model

    print("\n🚀 Starting Model Server")
    print(f"Model: {args.model}")
    print(f"Host: {args.host}:{args.port}")
    print(f"\nAPI Documentation: http://{args.host}:{args.port}/docs")
    print(f"Health Check: http://{args.host}:{args.port}/health\n")

    # Run server
    uvicorn.run(app, host=args.host, port=args.port, workers=args.workers)


if __name__ == "__main__":
    main()
