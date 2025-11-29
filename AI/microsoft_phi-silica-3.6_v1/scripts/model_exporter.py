"""
Model Export & Optimization
Export models to ONNX, TensorRT, and other formats for deployment
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import onnx


class ModelExporter:
    """Export models to various formats for deployment"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.export_dir = Path("data_out/exported_models")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Loading model from {model_path}...")
        self.model = AutoModelForCausalLM.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        print(f"✓ Model loaded")
        print(f"  Parameters: {self.model.num_parameters() / 1e6:.1f}M")
    
    def export_to_onnx(
        self,
        output_name: str = "model.onnx",
        opset_version: int = 14,
        optimize: bool = True
    ) -> Path:
        """
        Export model to ONNX format
        
        Args:
            output_name: Output filename
            opset_version: ONNX opset version
            optimize: Whether to optimize the model
            
        Returns:
            Path to exported model
        """
        print("\n📦 Exporting to ONNX...")
        
        output_path = self.export_dir / output_name
        
        # Prepare dummy input
        dummy_input = self.tokenizer(
            "Hello, world!",
            return_tensors="pt"
        )
        
        # Export
        torch.onnx.export(
            self.model,
            (dummy_input['input_ids'],),
            output_path,
            export_params=True,
            opset_version=opset_version,
            do_constant_folding=True,
            input_names=['input_ids'],
            output_names=['logits'],
            dynamic_axes={
                'input_ids': {0: 'batch_size', 1: 'sequence'},
                'logits': {0: 'batch_size', 1: 'sequence'}
            }
        )
        
        print(f"✓ ONNX export complete: {output_path}")
        
        # Optimize if requested
        if optimize:
            self._optimize_onnx(output_path)
        
        # Validate
        self._validate_onnx(output_path)
        
        return output_path
    
    def _optimize_onnx(self, onnx_path: Path):
        """Optimize ONNX model"""
        try:
            from onnxruntime.transformers import optimizer
            
            print("  Optimizing ONNX model...")
            
            optimized_path = onnx_path.parent / f"{onnx_path.stem}_optimized.onnx"
            
            # Optimize
            optimizer.optimize_model(
                str(onnx_path),
                model_type='gpt2',  # Use GPT-2 optimization for decoder models
                num_heads=self.model.config.num_attention_heads,
                hidden_size=self.model.config.hidden_size,
                optimization_options=optimizer.FusionOptions('gpt2')
            ).save_model_to_file(str(optimized_path))
            
            print(f"  ✓ Optimized model saved: {optimized_path}")
            
        except ImportError:
            print("  ⚠ onnxruntime not available, skipping optimization")
        except Exception as e:
            print(f"  ⚠ Optimization failed: {e}")
    
    def _validate_onnx(self, onnx_path: Path):
        """Validate ONNX model"""
        try:
            model = onnx.load(str(onnx_path))
            onnx.checker.check_model(model)
            print(f"  ✓ ONNX model validation passed")
            
            # Get model info
            file_size = onnx_path.stat().st_size / (1024 ** 2)
            print(f"  Model size: {file_size:.1f} MB")
            
        except Exception as e:
            print(f"  ⚠ Validation failed: {e}")
    
    def export_to_torchscript(
        self,
        output_name: str = "model_scripted.pt"
    ) -> Path:
        """
        Export model to TorchScript
        
        Args:
            output_name: Output filename
            
        Returns:
            Path to exported model
        """
        print("\n📦 Exporting to TorchScript...")
        
        output_path = self.export_dir / output_name
        
        # Set model to eval mode
        self.model.eval()
        
        # Trace model
        dummy_input = self.tokenizer(
            "Hello, world!",
            return_tensors="pt"
        )
        
        try:
            # Try scripting first
            scripted_model = torch.jit.script(self.model)
            torch.jit.save(scripted_model, output_path)
            print(f"  Using scripting")
        
        except Exception as e:
            print(f"  Scripting failed, trying tracing: {e}")
            
            # Fallback to tracing
            traced_model = torch.jit.trace(
                self.model,
                (dummy_input['input_ids'],)
            )
            torch.jit.save(traced_model, output_path)
            print(f"  Using tracing")
        
        file_size = output_path.stat().st_size / (1024 ** 2)
        print(f"✓ TorchScript export complete: {output_path}")
        print(f"  Model size: {file_size:.1f} MB")
        
        return output_path
    
    def quantize_model(
        self,
        quantization_type: str = "dynamic",
        output_name: str = "model_quantized"
    ) -> Path:
        """
        Quantize model for faster inference
        
        Args:
            quantization_type: Type of quantization ('dynamic', 'static', 'qat')
            output_name: Output directory name
            
        Returns:
            Path to quantized model
        """
        print(f"\n⚡ Quantizing model ({quantization_type})...")
        
        output_path = self.export_dir / output_name
        output_path.mkdir(exist_ok=True)
        
        if quantization_type == "dynamic":
            # Dynamic quantization
            quantized_model = torch.quantization.quantize_dynamic(
                self.model,
                {torch.nn.Linear},
                dtype=torch.qint8
            )
            
            # Save
            quantized_model.save_pretrained(output_path)
            self.tokenizer.save_pretrained(output_path)
            
            print(f"✓ Dynamic quantization complete: {output_path}")
            
        else:
            print(f"  ⚠ Quantization type '{quantization_type}' not yet implemented")
            return None
        
        # Get size comparison
        original_size = sum(p.numel() * p.element_size() for p in self.model.parameters()) / (1024 ** 2)
        quantized_size = sum(p.numel() * p.element_size() for p in quantized_model.parameters()) / (1024 ** 2)
        
        print(f"  Original size: {original_size:.1f} MB")
        print(f"  Quantized size: {quantized_size:.1f} MB")
        print(f"  Reduction: {(1 - quantized_size/original_size) * 100:.1f}%")
        
        return output_path
    
    def export_to_huggingface(
        self,
        repo_name: str,
        organization: Optional[str] = None,
        private: bool = False
    ):
        """
        Upload model to Hugging Face Hub
        
        Args:
            repo_name: Repository name
            organization: Organization name (optional)
            private: Whether to make repo private
        """
        print(f"\n🤗 Uploading to Hugging Face Hub...")
        
        try:
            from huggingface_hub import HfApi, create_repo
            
            # Create repo
            repo_id = f"{organization}/{repo_name}" if organization else repo_name
            
            print(f"  Creating repository: {repo_id}")
            create_repo(repo_id, private=private, exist_ok=True)
            
            # Upload model
            api = HfApi()
            api.upload_folder(
                folder_path=self.model_path,
                repo_id=repo_id,
                repo_type="model"
            )
            
            print(f"✓ Model uploaded to https://huggingface.co/{repo_id}")
            
        except ImportError:
            print("  ⚠ huggingface_hub not installed")
        except Exception as e:
            print(f"  ⚠ Upload failed: {e}")
    
    def benchmark_formats(
        self,
        num_runs: int = 10
    ) -> Dict[str, Dict[str, float]]:
        """
        Benchmark different export formats
        
        Args:
            num_runs: Number of benchmark runs
            
        Returns:
            Dictionary with benchmark results
        """
        print(f"\n⏱️  Benchmarking formats ({num_runs} runs)...")
        
        results = {}
        
        # Benchmark PyTorch
        results['pytorch'] = self._benchmark_pytorch(num_runs)
        
        # TODO: Benchmark ONNX, TorchScript, etc.
        
        # Print results
        print("\n📊 Benchmark Results:")
        for format_name, metrics in results.items():
            print(f"\n  {format_name}:")
            for metric, value in metrics.items():
                print(f"    {metric}: {value:.2f}")
        
        return results
    
    def _benchmark_pytorch(self, num_runs: int) -> Dict[str, float]:
        """Benchmark PyTorch model"""
        self.model.eval()
        
        # Prepare input
        inputs = self.tokenizer(
            "Hello, world!",
            return_tensors="pt"
        )
        
        # Warmup
        with torch.no_grad():
            for _ in range(3):
                _ = self.model(**inputs)
        
        # Benchmark
        times = []
        with torch.no_grad():
            for _ in range(num_runs):
                start = time.perf_counter()
                _ = self.model(**inputs)
                end = time.perf_counter()
                times.append((end - start) * 1000)
        
        return {
            "avg_latency_ms": sum(times) / len(times),
            "min_latency_ms": min(times),
            "max_latency_ms": max(times)
        }


def main():
    """CLI for model export"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Model Export & Optimization")
    parser.add_argument("--model", type=str, required=True,
                        help="Path to model")
    parser.add_argument("--format", type=str, choices=['onnx', 'torchscript', 'quantize', 'hf', 'all'],
                        default='all', help="Export format")
    parser.add_argument("--quantization", type=str, default="dynamic",
                        help="Quantization type")
    parser.add_argument("--benchmark", action="store_true",
                        help="Run benchmarks")
    
    args = parser.parse_args()
    
    exporter = ModelExporter(args.model)
    
    if args.format in ['onnx', 'all']:
        exporter.export_to_onnx()
    
    if args.format in ['torchscript', 'all']:
        exporter.export_to_torchscript()
    
    if args.format in ['quantize', 'all']:
        exporter.quantize_model(quantization_type=args.quantization)
    
    if args.benchmark:
        exporter.benchmark_formats()
    
    print("\n✅ Export complete!")


if __name__ == "__main__":
    main()
