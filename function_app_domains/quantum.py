from __future__ import annotations

from function_app_domains.access import require_access


def quantum_classify(req, ctx):
    unauthorized = require_access(req, ctx, "quantum")
    if unauthorized is not None:
        return unauthorized

    ctx.logging.info("Quantum classify endpoint invoked")
    try:
        try:
            import numpy as np
            import torch
            from quantum_classifier import QuantumClassifier
        except ImportError as exc:
            return ctx.func.HttpResponse(
                ctx.json.dumps({"error": f"Quantum dependencies not available: {exc}"}),
                status_code=500,
                mimetype="application/json",
                headers=ctx.create_cors_response_headers(),
            )

        req_body = req.get_json()
        features = req_body.get("features", [])
        n_qubits = req_body.get("n_qubits", 4)
        n_layers = req_body.get("n_layers", 2)
        if not features:
            return ctx.func.HttpResponse(
                ctx.json.dumps({"error": "No features provided"}),
                status_code=400,
                mimetype="application/json",
                headers=ctx.create_cors_response_headers(),
            )

        classifier = QuantumClassifier()
        feature_array = np.array(features[:n_qubits])
        if len(feature_array) < n_qubits:
            feature_array = np.pad(feature_array, (0, n_qubits - len(feature_array)))

        inputs = torch.tensor(feature_array, dtype=torch.float32) * 2 * np.pi
        weights = torch.randn(n_layers, n_qubits, 2, dtype=torch.float32) * 0.1
        output = classifier.forward(inputs.unsqueeze(0), weights)
        avg_value = float(output.mean())
        confidence = abs(avg_value)
        classification = "positive" if avg_value > 0.3 else "negative" if avg_value < -0.3 else "neutral"

        return ctx.func.HttpResponse(
            ctx.json.dumps(
                {
                    "classification": classification,
                    "confidence": confidence,
                    "quantum_state": {
                        "expectation_values": output.tolist(),
                        "average": avg_value,
                        "n_qubits": n_qubits,
                        "n_layers": n_layers,
                    },
                }
            ),
            status_code=200,
            mimetype="application/json",
            headers=ctx.create_cors_response_headers(),
        )
    except Exception as exc:
        ctx.logging.error("Quantum classify error: %s", exc)
        return ctx.func.HttpResponse(
            ctx.json.dumps({"error": f"Quantum classification failed: {exc}"}),
            status_code=500,
            mimetype="application/json",
            headers=ctx.create_cors_response_headers(),
        )


def quantum_circuit(req, ctx):
    unauthorized = require_access(req, ctx, "quantum")
    if unauthorized is not None:
        return unauthorized

    ctx.logging.info("Quantum circuit endpoint invoked")
    try:
        req_body = req.get_json()
        n_qubits = req_body.get("n_qubits", 4)
        n_layers = req_body.get("n_layers", 2)
        entanglement = req_body.get("entanglement", "linear")

        gates = []
        for index in range(n_qubits):
            gates.append({"type": "RY", "qubit": index, "layer": 0, "parameter": "input[i]"})

        for layer in range(n_layers):
            for index in range(n_qubits):
                gates.append({"type": "RY", "qubit": index, "layer": layer + 1, "parameter": f"θ_{layer}_{index}_0"})
                gates.append({"type": "RZ", "qubit": index, "layer": layer + 1, "parameter": f"θ_{layer}_{index}_1"})

            if entanglement == "linear":
                for index in range(n_qubits - 1):
                    gates.append({"type": "CNOT", "control": index, "target": index + 1, "layer": layer + 1})
            elif entanglement == "circular":
                for index in range(n_qubits):
                    gates.append(
                        {"type": "CNOT", "control": index, "target": (index + 1) % n_qubits, "layer": layer + 1}
                    )
            elif entanglement == "full":
                for left in range(n_qubits):
                    for right in range(left + 1, n_qubits):
                        gates.append({"type": "CNOT", "control": left, "target": right, "layer": layer + 1})

        for index in range(n_qubits):
            gates.append({"type": "Measure", "qubit": index, "layer": n_layers + 1, "observable": "PauliZ"})

        viz_parts = [
            f"Quantum Circuit ({n_qubits} qubits, {n_layers} layers, {entanglement} entanglement)\n",
            "=" * 60 + "\n\n",
        ]
        for layer in range(n_layers + 2):
            viz_parts.append(f"Layer {layer}:\n")
            for gate in [gate for gate in gates if gate.get("layer") == layer]:
                if gate["type"] in ["RY", "RZ"]:
                    viz_parts.append(f"  {gate['type']}({gate['parameter']}) on qubit {gate['qubit']}\n")
                elif gate["type"] == "CNOT":
                    viz_parts.append(f"  CNOT: control={gate['control']}, target={gate['target']}\n")
                elif gate["type"] == "Measure":
                    viz_parts.append(f"  Measure qubit {gate['qubit']} ({gate['observable']})\n")
            viz_parts.append("\n")

        return ctx.func.HttpResponse(
            ctx.json.dumps(
                {
                    "circuit_info": {
                        "n_qubits": n_qubits,
                        "n_layers": n_layers,
                        "entanglement": entanglement,
                        "total_gates": len(gates),
                        "depth": n_layers + 2,
                    },
                    "gates": gates,
                    "visualization": "".join(viz_parts),
                }
            ),
            status_code=200,
            mimetype="application/json",
            headers=ctx.create_cors_response_headers(),
        )
    except Exception as exc:
        ctx.logging.error("Quantum circuit error: %s", exc)
        return ctx.func.HttpResponse(
            ctx.json.dumps({"error": f"Circuit creation failed: {exc}"}),
            status_code=500,
            mimetype="application/json",
            headers=ctx.create_cors_response_headers(),
        )


def quantum_llm(req, ctx):
    unauthorized = require_access(req, ctx, "quantum")
    if unauthorized is not None:
        return unauthorized

    ctx.logging.info("Quantum LLM endpoint invoked: %s", req.method)
    try:
        repo_root = ctx.Path(__file__).resolve().parents[1]
        quantum_ml_src = repo_root / "ai-projects" / "quantum-ml" / "src"
        scripts_dir = repo_root / "scripts"
        for path in [str(quantum_ml_src), str(scripts_dir)]:
            if path not in ctx.sys.path:
                ctx.sys.path.insert(0, path)

        try:
            from quantum_llm_trainer import QUANTUM_AVAILABLE, QuantumEnhancedLLMTrainer, get_quantum_llm_status

            trainer_available = True
        except ImportError as exc:
            trainer_available = False
            QUANTUM_AVAILABLE = False
            trainer_import_error = str(exc)
            get_quantum_llm_status = None

        if req.method == "GET":
            readiness = None
            if trainer_available and get_quantum_llm_status is not None:
                readiness = get_quantum_llm_status(output_dir=repo_root / "data_out" / "quantum_llm_training")
            return ctx.func.HttpResponse(
                ctx.json.dumps(
                    {
                        "available": trainer_available,
                        "quantum_circuits": QUANTUM_AVAILABLE,
                        "model": "QuantumLLM (hybrid quantum-classical transformer)",
                        "capabilities": {
                            "generate": trainer_available,
                            "train": trainer_available,
                            "n_qubits": 4,
                            "backends": ["default.qubit", "lightning.qubit"],
                        },
                        "readiness": readiness,
                        "import_error": None if trainer_available else trainer_import_error,
                    }
                ),
                status_code=200,
                mimetype="application/json",
                headers=ctx.create_cors_response_headers(),
            )

        if not trainer_available:
            return ctx.func.HttpResponse(
                ctx.json.dumps({"error": "Quantum LLM trainer not available", "details": trainer_import_error}),
                status_code=503,
                mimetype="application/json",
                headers=ctx.create_cors_response_headers(),
            )

        try:
            body = req.get_json() if req.get_body() else {}
        except ValueError:
            return ctx.func.HttpResponse(
                ctx.json.dumps({"error": "Invalid JSON body"}),
                status_code=400,
                mimetype="application/json",
                headers=ctx.create_cors_response_headers(),
            )

        action = body.get("action", "generate")
        if action == "generate":
            prompt = str(body.get("prompt", "Quantum")).strip()[:256] or "Quantum"
            max_tokens = min(int(body.get("max_tokens", 50)), 200)
            trainer = QuantumEnhancedLLMTrainer(
                {"n_qubits": 4, "n_quantum_layers": 2, "d_model": 64, "max_seq_len": 32}
            )
            prompt_token_ids = [ord(char) % trainer.model_config["vocab_size"] for char in prompt[:32]]
            try:
                import torch

                prompt_ids = torch.tensor([prompt_token_ids], dtype=torch.long)
            except Exception:
                prompt_ids = [prompt_token_ids]

            generated = trainer.model.generate(prompt_ids, max_new_tokens=max_tokens, temperature=0.8, top_k=20)
            generated_row = generated[0]
            tokens = generated_row.tolist() if hasattr(generated_row, "tolist") else list(generated_row)
            text = "".join(chr(token % 128) if 32 <= (token % 128) < 127 else "?" for token in tokens)

            return ctx.func.HttpResponse(
                ctx.json.dumps(
                    {
                        "action": "generate",
                        "prompt": prompt,
                        "generated": text,
                        "tokens": len(tokens),
                        "quantum_available": QUANTUM_AVAILABLE,
                        "readiness": (
                            get_quantum_llm_status(output_dir=repo_root / "data_out" / "quantum_llm_training")
                            if get_quantum_llm_status is not None
                            else None
                        ),
                    }
                ),
                status_code=200,
                mimetype="application/json",
                headers=ctx.create_cors_response_headers(),
            )

        if action == "train":
            dataset_path_obj = ctx.Path(body.get("dataset_path", "datasets/chat"))
            if not dataset_path_obj.is_absolute():
                dataset_path_obj = repo_root / dataset_path_obj
            dataset_path_obj = dataset_path_obj.resolve(strict=False)
            try:
                dataset_path_obj.relative_to(repo_root.resolve())
            except ValueError:
                return ctx.func.HttpResponse(
                    ctx.json.dumps({"error": "dataset_path must point to a location inside the repository"}),
                    status_code=400,
                    mimetype="application/json",
                    headers=ctx.create_cors_response_headers(),
                )

            epochs = min(int(body.get("epochs", 1)), 5)
            output_dir = repo_root / "data_out" / "quantum_llm_api"
            trainer = QuantumEnhancedLLMTrainer({"n_qubits": 4, "n_quantum_layers": 2, "d_model": 64})
            results = trainer.train_with_quantum_enhancement(
                dataset_path=dataset_path_obj,
                output_dir=output_dir,
                epochs=epochs,
                model=None,
            )
            return ctx.func.HttpResponse(
                ctx.json.dumps(
                    {
                        "action": "train",
                        "status": results["status"],
                        "epochs_completed": results["epochs_completed"],
                        "final_loss": results["final_loss"],
                        "circuit_executions": results["quantum_metrics"]["circuit_executions"],
                        "checkpoint_path": results.get("checkpoint_path"),
                        "readiness": get_quantum_llm_status(output_dir=output_dir)
                        if get_quantum_llm_status is not None
                        else None,
                    }
                ),
                status_code=200,
                mimetype="application/json",
                headers=ctx.create_cors_response_headers(),
            )

        return ctx.func.HttpResponse(
            ctx.json.dumps({"error": f"Unknown action: {action!r}. Use 'generate' or 'train'."}),
            status_code=400,
            mimetype="application/json",
            headers=ctx.create_cors_response_headers(),
        )
    except Exception as exc:
        ctx.logging.error("Quantum LLM error: %s", exc, exc_info=True)
        return ctx.func.HttpResponse(
            ctx.json.dumps({"error": f"Quantum LLM request failed: {exc}"}),
            status_code=500,
            mimetype="application/json",
            headers=ctx.create_cors_response_headers(),
        )


def quantum_info(req, ctx):
    unauthorized = require_access(req, ctx, "quantum")
    if unauthorized is not None:
        return unauthorized

    ctx.logging.info("Quantum info endpoint invoked")
    try:
        try:
            import pennylane  # noqa: F401
            import quantum_classifier  # noqa: F401

            quantum_available = True
            backends = [
                {"name": "default.qubit", "description": "PennyLane default simulator", "type": "simulator"},
                {"name": "lightning.qubit", "description": "Fast C++ simulator", "type": "simulator"},
                {"name": "qiskit.aer", "description": "Qiskit Aer simulator", "type": "simulator"},
            ]
            capabilities = {
                "max_qubits": 20,
                "supports_gpu": False,
                "variational_circuits": True,
                "hybrid_models": True,
                "azure_quantum_ready": True,
            }
        except ImportError:
            quantum_available = False
            backends = []
            capabilities = {}

        return ctx.func.HttpResponse(
            ctx.json.dumps(
                {
                    "available": quantum_available,
                    "backends": backends,
                    "capabilities": capabilities,
                    "quantum_provider": "quantum-enhanced-local",
                    "version": "1.0.0",
                }
            ),
            status_code=200,
            mimetype="application/json",
            headers=ctx.create_cors_response_headers(),
        )
    except Exception as exc:
        ctx.logging.error("Quantum info error: %s", exc)
        return ctx.func.HttpResponse(
            ctx.json.dumps({"error": f"Failed to get quantum info: {exc}"}),
            status_code=500,
            mimetype="application/json",
            headers=ctx.create_cors_response_headers(),
        )


def quantum_llm_status(req, ctx):
    unauthorized = require_access(req, ctx, "quantum")
    if unauthorized is not None:
        return unauthorized

    ctx.logging.info("quantum-llm/status invoked")
    try:
        pipeline = ctx._get_quantum_llm_pipeline()
        if pipeline is None:
            return ctx.func.HttpResponse(
                ctx.json.dumps({"status": "unavailable", "error": "Pipeline not initialized"}),
                status_code=503,
                mimetype="application/json",
                headers=ctx.create_cors_response_headers(),
            )
        payload = {"status": "ok"}
        payload.update(pipeline.status())
        return ctx.func.HttpResponse(
            ctx.json.dumps(payload),
            status_code=200,
            mimetype="application/json",
            headers=ctx.create_cors_response_headers(),
        )
    except Exception as exc:
        ctx.logging.error("quantum-llm/status error: %s", exc)
        return ctx.func.HttpResponse(
            ctx.json.dumps({"status": "error", "error": str(exc)}),
            status_code=500,
            mimetype="application/json",
            headers=ctx.create_cors_response_headers(),
        )


def quantum_llm_chat(req, ctx):
    unauthorized = require_access(req, ctx, "quantum")
    if unauthorized is not None:
        return unauthorized

    ctx.logging.info("quantum-llm/chat invoked")
    try:
        body = req.get_json()
        prompt = body.get("prompt", "")
        if not prompt or not isinstance(prompt, str):
            return ctx.func.HttpResponse(
                ctx.json.dumps({"error": "prompt is required and must be a non-empty string"}),
                status_code=400,
                mimetype="application/json",
                headers=ctx.create_cors_response_headers(),
            )

        pipeline = ctx._get_quantum_llm_pipeline()
        if pipeline is None:

            def _unavail():
                yield b'data: {"error": "Quantum LLM pipeline unavailable"}\n\n'
                yield b"data: [DONE]\n\n"

            return ctx._sse_response(_unavail(), status_code=503)

        result = ctx.asyncio.run(pipeline.generate(prompt, provider=body.get("provider"), seed=body.get("seed")))
        return ctx.func.HttpResponse(
            ctx.json.dumps(result),
            status_code=200,
            mimetype="application/json",
            headers=ctx.create_cors_response_headers(),
        )
    except ValueError as exc:
        ctx.logging.warning("quantum-llm/chat validation error: %s", exc)
        return ctx.func.HttpResponse(
            ctx.json.dumps({"error": str(exc)}),
            status_code=400,
            mimetype="application/json",
            headers=ctx.create_cors_response_headers(),
        )
    except Exception as exc:
        ctx.logging.error("quantum-llm/chat error: %s", exc)
        return ctx.func.HttpResponse(
            ctx.json.dumps({"error": str(exc)}),
            status_code=500,
            mimetype="application/json",
            headers=ctx.create_cors_response_headers(),
        )


def quantum_llm_stream(req, ctx):
    unauthorized = require_access(req, ctx, "quantum")
    if unauthorized is not None:
        return unauthorized

    ctx.logging.info("quantum-llm/stream invoked")
    try:
        body = req.get_json()
        prompt = body.get("prompt", "")
        if not prompt or not isinstance(prompt, str):
            return ctx.func.HttpResponse(
                ctx.json.dumps({"error": "prompt is required"}),
                status_code=400,
                mimetype="application/json",
                headers=ctx.create_cors_response_headers(),
            )

        pipeline = ctx._get_quantum_llm_pipeline()
        if pipeline is None:

            def _unavail():
                yield b'data: {"error": "Quantum LLM pipeline unavailable"}\n\n'
                yield b"data: [DONE]\n\n"

            return ctx._sse_response(_unavail(), status_code=503)

        def _sse_generator():
            loop = ctx.asyncio.new_event_loop()
            try:

                async def _drain():
                    async for chunk in pipeline.stream(prompt, provider=body.get("provider"), seed=body.get("seed")):
                        yield chunk.encode("utf-8")

                async def _collect():
                    results = []
                    async for chunk in _drain():
                        results.append(chunk)
                    return results

                yield from loop.run_until_complete(_collect())
            finally:
                loop.close()

        return ctx._sse_response(_sse_generator(), status_code=200)
    except Exception as exc:
        ctx.logging.error("quantum-llm/stream error: %s", exc)
        error_message = str(exc)

        def _err():
            yield f"data: {ctx.json.dumps({'error': error_message})}\n\n".encode()
            yield b"data: [DONE]\n\n"

        return ctx._sse_response(_err(), status_code=200)
