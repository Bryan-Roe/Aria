"""
QAI Integration Service - FastAPI Application
Unified API for quantum AI, chat, and training operations
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import yaml
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from chat_integration import ChatIntegration
from quantum_integration import QuantumIntegration
from training_integration import TrainingIntegration


# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None
    stream: bool = False
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    success: bool
    provider: Optional[str] = None
    message: Optional[str] = None
    response: Optional[str] = None
    conversation_id: Optional[str] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None


class TrainQuantumRequest(BaseModel):
    dataset: str
    n_qubits: int = Field(default=4, ge=2, le=20)
    n_layers: int = Field(default=2, ge=1, le=10)
    epochs: int = Field(default=10, ge=1, le=1000)
    backend: str = "qiskit_aer"


class TrainLoRARequest(BaseModel):
    dataset: str
    max_train_samples: int = Field(default=64, ge=1)
    max_eval_samples: int = Field(default=16, ge=1)
    epochs: int = Field(default=1, ge=1)


class OrchestratorRequest(BaseModel):
    job_name: Optional[str] = None
    dry_run: bool = False


# Load configuration
config_path = Path(__file__).parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)


# Initialize integration modules
quantum_integration = QuantumIntegration(config)
chat_integration = ChatIntegration(config)
training_integration = TrainingIntegration(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    print("🚀 QAI Integration Service starting...")
    print(f"📊 Quantum enabled: {config['quantum']['enabled']}")
    print(f"💬 Chat enabled: {config['chat']['enabled']}")
    print(f"🎓 Training enabled: {config['training']['enabled']}")
    yield
    # Shutdown
    print("🛑 QAI Integration Service shutting down...")


# Create FastAPI app
app = FastAPI(
    title="QAI Integration Service",
    description="Unified API for Quantum AI, Chat, and Training operations",
    version=config["service"]["version"],
    lifespan=lifespan,
)

# CORS configuration
if config["api"]["cors_enabled"]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config["api"]["cors_origins"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# ============================================================================
# Root & Health Endpoints
# ============================================================================


@app.get("/")
async def root():
    """Serve the web UI"""
    static_index = Path(__file__).parent / "static" / "index.html"
    if static_index.exists():
        return FileResponse(str(static_index))

    # Fallback to API info if no UI
    return {
        "service": config["service"]["name"],
        "version": config["service"]["version"],
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "quantum": "/quantum/*",
            "chat": "/chat/*",
            "training": "/training/*",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": config["service"]["name"],
        "version": config["service"]["version"],
    }


@app.get("/status")
async def get_full_status():
    """Get comprehensive system status"""
    quantum_status = await quantum_integration.get_status()
    chat_status = await chat_integration.get_status()
    training_status = await training_integration.get_status()

    return {
        "service": config["service"]["name"],
        "version": config["service"]["version"],
        "quantum": quantum_status,
        "chat": chat_status,
        "training": training_status,
    }


# ============================================================================
# Quantum Endpoints
# ============================================================================


@app.get("/quantum/status")
async def get_quantum_status():
    """Get quantum system status"""
    return await quantum_integration.get_status()


@app.get("/quantum/datasets")
async def list_quantum_datasets():
    """List available quantum datasets"""
    return await quantum_integration.list_datasets()


@app.get("/quantum/backends")
async def list_quantum_backends():
    """List available quantum backends"""
    status = await quantum_integration.get_status()
    return {
        "backends": status["available_backends"],
        "azure_connected": status["azure_connected"],
    }


@app.post("/quantum/train")
async def train_quantum_classifier(
    request: TrainQuantumRequest, background_tasks: BackgroundTasks
):
    """Train a quantum classifier"""
    result = await quantum_integration.train_classifier(
        dataset=request.dataset,
        n_qubits=request.n_qubits,
        n_layers=request.n_layers,
        epochs=request.epochs,
        backend=request.backend,
    )
    return result


@app.post("/quantum/autorun")
async def run_quantum_autorun(request: OrchestratorRequest):
    """Run a quantum autorun job"""
    if not request.job_name:
        raise HTTPException(status_code=400, detail="job_name is required")

    result = await quantum_integration.run_autorun_job(
        job_name=request.job_name, dry_run=request.dry_run
    )
    return result


@app.get("/quantum/circuit-info")
async def get_circuit_info(circuit_type: str = "variational"):
    """Get quantum circuit information"""
    return await quantum_integration.get_circuit_info(circuit_type)


# ============================================================================
# Chat Endpoints
# ============================================================================


@app.get("/chat/status")
async def get_chat_status():
    """Get chat system status"""
    return await chat_integration.get_status()


@app.post("/chat/message", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """Send a chat message and get response"""
    result = await chat_integration.chat(
        message=request.message,
        provider=request.provider,
        stream=request.stream,
        conversation_id=request.conversation_id,
    )
    return ChatResponse(**result)


@app.get("/chat/providers")
async def get_chat_providers():
    """Get available chat providers"""
    status = await chat_integration.get_status()
    return status["providers"]


@app.get("/chat/detect-provider")
async def detect_best_provider():
    """Auto-detect best available chat provider"""
    provider = await chat_integration.detect_provider()
    return {"provider": provider}


@app.get("/chat/conversations")
async def list_conversations():
    """List all saved conversations"""
    return await chat_integration.list_conversations()


@app.get("/chat/conversations/{filename}")
async def get_conversation(filename: str):
    """Get a specific conversation"""
    messages = await chat_integration.get_conversation(filename)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"filename": filename, "messages": messages}


# ============================================================================
# Training Endpoints
# ============================================================================


@app.get("/training/status")
async def get_training_status():
    """Get training system status"""
    return await training_integration.get_status()


@app.get("/training/datasets")
async def list_training_datasets():
    """List available training datasets"""
    return await training_integration.list_datasets()


@app.post("/training/lora")
async def train_lora(request: TrainLoRARequest, background_tasks: BackgroundTasks):
    """Train a LoRA adapter"""
    result = await training_integration.train_lora(
        dataset=request.dataset,
        max_train_samples=request.max_train_samples,
        max_eval_samples=request.max_eval_samples,
        epochs=request.epochs,
    )
    return result


@app.post("/training/autotrain")
async def run_autotrain(request: OrchestratorRequest):
    """Run AutoTrain orchestrator"""
    result = await training_integration.run_autotrain(
        job_name=request.job_name, dry_run=request.dry_run
    )
    return result


@app.get("/training/autotrain/jobs")
async def list_autotrain_jobs():
    """List all configured AutoTrain jobs"""
    jobs = await training_integration.list_autotrain_jobs()
    return {"jobs": jobs}


@app.get("/training/lora-adapter")
async def get_lora_adapter_info():
    """Get LoRA adapter information"""
    status = await training_integration.get_status()
    return status["lora_adapter"]


@app.get("/training/runs")
async def list_training_runs():
    """List recent training runs"""
    status = await training_integration.get_status()
    return status["recent_trainings"]


@app.get("/training/runs/{run_name}")
async def get_training_metrics(run_name: str):
    """Get metrics for a specific training run"""
    metrics = await training_integration.get_training_metrics(run_name)
    if "error" in metrics:
        raise HTTPException(status_code=404, detail=metrics["error"])
    return metrics


# ============================================================================
# Main entry point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=config["service"]["host"],
        port=config["service"]["port"],
        reload=config["service"]["debug"],
    )
