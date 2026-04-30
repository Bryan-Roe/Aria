"""
GPU Training Optimization Profile
Automatically configures optimal training settings based on available hardware
"""

import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class GPUInfo:
    """GPU hardware information"""

    name: str
    memory_total_gb: float
    memory_available_gb: float
    compute_capability: str
    cuda_version: str
    driver_version: str
    gpu_count: int


@dataclass
class OptimizationProfile:
    """Training optimization configuration"""

    batch_size: int
    gradient_accumulation_steps: int
    gradient_checkpointing: bool
    fp16: bool
    bf16: bool
    max_grad_norm: float
    optimizer: str
    learning_rate: float
    warmup_steps: int
    use_8bit: bool
    use_4bit: bool
    lora_rank: int
    lora_alpha: int
    max_seq_length: int
    dataloader_num_workers: int
    pin_memory: bool

    # Advanced optimizations
    fused_optimizer: bool = False
    compile_model: bool = False
    flash_attention: bool = False
    cpu_offload: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self, path: str):
        """Save profile to YAML"""
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
        print(f"✓ Profile saved to {path}")


class GPUOptimizer:
    """GPU training optimizer"""

    def __init__(self):
        self.gpu_info: Optional[GPUInfo] = None

    def detect_hardware(self) -> GPUInfo:
        """Detect GPU hardware capabilities"""
        try:
            import torch

            if not torch.cuda.is_available():
                print("⚠ No CUDA GPU detected. Using CPU profile.")
                return self._cpu_fallback()

            gpu_count = torch.cuda.device_count()
            device = torch.cuda.current_device()

            gpu_info = GPUInfo(
                name=torch.cuda.get_device_name(device),
                memory_total_gb=torch.cuda.get_device_properties(device).total_memory
                / (1024**3),
                memory_available_gb=self._get_available_memory_gb(),
                compute_capability=f"{torch.cuda.get_device_capability(device)[0]}.{torch.cuda.get_device_capability(device)[1]}",
                cuda_version=torch.version.cuda or "N/A",
                driver_version=self._get_driver_version(),
                gpu_count=gpu_count,
            )

            self.gpu_info = gpu_info
            self._print_gpu_info(gpu_info)
            return gpu_info

        except ImportError:
            print("⚠ PyTorch not available. Using CPU profile.")
            return self._cpu_fallback()

    def _get_available_memory_gb(self) -> float:
        """Get available GPU memory"""
        import torch

        torch.cuda.empty_cache()
        return torch.cuda.mem_get_info()[0] / (1024**3)

    def _get_driver_version(self) -> str:
        """Get NVIDIA driver version"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
            )
            return result.stdout.strip().split("\n")[0]
        except:
            return "N/A"

    def _cpu_fallback(self) -> GPUInfo:
        """Fallback info for CPU-only systems"""
        return GPUInfo(
            name="CPU",
            memory_total_gb=0.0,
            memory_available_gb=0.0,
            compute_capability="N/A",
            cuda_version="N/A",
            driver_version="N/A",
            gpu_count=0,
        )

    def _print_gpu_info(self, info: GPUInfo):
        """Print GPU information"""
        print("\n=== GPU Hardware Detection ===")
        print(f"GPU Name: {info.name}")
        print(f"GPU Count: {info.gpu_count}")
        print(f"Total Memory: {info.memory_total_gb:.2f} GB")
        print(f"Available Memory: {info.memory_available_gb:.2f} GB")
        print(f"Compute Capability: {info.compute_capability}")
        print(f"CUDA Version: {info.cuda_version}")
        print(f"Driver Version: {info.driver_version}")

    def create_optimization_profile(
        self, model_size_gb: float = 7.0, target_memory_usage: float = 0.8
    ) -> OptimizationProfile:
        """
        Create optimal training profile for detected hardware

        Args:
            model_size_gb: Size of model in GB
            target_memory_usage: Target % of GPU memory to use (0.0-1.0)

        Returns:
            OptimizationProfile object
        """
        if self.gpu_info is None:
            self.detect_hardware()

        gpu = self.gpu_info

        # Determine if we have enough memory for full precision
        available_memory = gpu.memory_available_gb * target_memory_usage

        print("\n=== Optimization Profile Creation ===")
        print(f"Model size: {model_size_gb:.2f} GB")
        print(f"Available memory: {available_memory:.2f} GB")

        # Start with conservative defaults
        profile = OptimizationProfile(
            batch_size=1,
            gradient_accumulation_steps=4,
            gradient_checkpointing=True,
            fp16=False,
            bf16=False,
            max_grad_norm=1.0,
            optimizer="adamw_torch",
            learning_rate=2e-4,
            warmup_steps=10,
            use_8bit=False,
            use_4bit=False,
            lora_rank=8,
            lora_alpha=16,
            max_seq_length=512,
            dataloader_num_workers=2,
            pin_memory=True,
        )

        if gpu.gpu_count == 0:
            # CPU-only configuration
            return self._cpu_profile(profile)

        # GPU optimizations based on memory
        if available_memory < model_size_gb * 0.5:
            # Very limited memory - aggressive quantization
            print("Profile: Memory-Constrained (4-bit + CPU offload)")
            profile.use_4bit = True
            profile.cpu_offload = True
            profile.batch_size = 1
            profile.gradient_accumulation_steps = 8
            profile.max_seq_length = 256
            profile.lora_rank = 4

        elif available_memory < model_size_gb:
            # Limited memory - 8-bit quantization
            print("Profile: Memory-Efficient (8-bit)")
            profile.use_8bit = True
            profile.batch_size = 1
            profile.gradient_accumulation_steps = 4
            profile.max_seq_length = 512
            profile.lora_rank = 8

        elif available_memory < model_size_gb * 2:
            # Moderate memory - FP16/BF16
            print("Profile: Balanced (FP16/BF16)")
            profile.batch_size = 2
            profile.gradient_accumulation_steps = 2
            profile.max_seq_length = 1024
            profile.lora_rank = 16

            # Use BF16 if supported (Ampere+)
            if self._supports_bf16(gpu):
                profile.bf16 = True
            else:
                profile.fp16 = True

        else:
            # Plenty of memory - optimize for speed
            print("Profile: Performance (FP16/BF16 + optimizations)")
            profile.batch_size = 4
            profile.gradient_accumulation_steps = 1
            profile.gradient_checkpointing = False
            profile.max_seq_length = 2048
            profile.lora_rank = 32
            profile.dataloader_num_workers = 4

            if self._supports_bf16(gpu):
                profile.bf16 = True
            else:
                profile.fp16 = True

            # Enable advanced optimizations for modern GPUs
            if float(gpu.compute_capability.split(".")[0]) >= 8:
                profile.flash_attention = True
                profile.fused_optimizer = True
                profile.compile_model = True

        # Multi-GPU adjustments
        if gpu.gpu_count > 1:
            print(f"Multi-GPU setup detected ({gpu.gpu_count} GPUs)")
            profile.batch_size *= min(gpu.gpu_count, 4)  # Scale batch size
            profile.dataloader_num_workers *= 2

        self._print_profile(profile)
        return profile

    def _cpu_profile(self, profile: OptimizationProfile) -> OptimizationProfile:
        """Configure for CPU training"""
        print("Profile: CPU-Only")
        profile.batch_size = 1
        profile.gradient_accumulation_steps = 16
        profile.gradient_checkpointing = True
        profile.max_seq_length = 256
        profile.lora_rank = 4
        profile.dataloader_num_workers = 2
        profile.pin_memory = False
        return profile

    def _supports_bf16(self, gpu: GPUInfo) -> bool:
        """Check if GPU supports BF16 (Ampere or newer)"""
        try:
            major_version = int(gpu.compute_capability.split(".")[0])
            return major_version >= 8  # Ampere (A100, RTX 30xx) and newer
        except:
            return False

    def _print_profile(self, profile: OptimizationProfile):
        """Print optimization profile"""
        print("\n=== Recommended Settings ===")
        print(f"Batch Size: {profile.batch_size}")
        print(f"Gradient Accumulation: {profile.gradient_accumulation_steps}")
        print(
            f"Effective Batch Size: {profile.batch_size * profile.gradient_accumulation_steps}"
        )
        print(f"Max Sequence Length: {profile.max_seq_length}")
        print(f"LoRA Rank: {profile.lora_rank}")
        print(
            f"Precision: {'BF16' if profile.bf16 else 'FP16' if profile.fp16 else '8-bit' if profile.use_8bit else '4-bit' if profile.use_4bit else 'FP32'}"
        )
        print(f"Gradient Checkpointing: {profile.gradient_checkpointing}")
        print(f"Flash Attention: {profile.flash_attention}")
        print(f"Compiled Model: {profile.compile_model}")

        # Estimate throughput
        tokens_per_step = profile.batch_size * profile.max_seq_length
        print(f"\nEstimated tokens/step: {tokens_per_step:,}")

    def update_config_file(self, config_path: str, profile: OptimizationProfile):
        """Update training config file with optimized settings"""
        config_path = Path(config_path)

        # Load existing config
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Update with profile settings
        config.update(
            {
                "finetune_train_batch_size": profile.batch_size,
                "gradient_accumulation_steps": profile.gradient_accumulation_steps,
                "gradient_checkpointing": profile.gradient_checkpointing,
                "finetune_train_seqlen": profile.max_seq_length,
                "learning_rate": profile.learning_rate,
                "num_warmup_steps": profile.warmup_steps,
                "lora_dropout": 0.1,
                "max_grad_norm": profile.max_grad_norm,
            }
        )

        # Save updated config
        backup_path = config_path.with_suffix(".yaml.bak")
        config_path.rename(backup_path)
        print(f"  Backup saved: {backup_path}")

        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        print(f"✓ Config updated: {config_path}")


def main():
    """CLI for GPU optimization"""
    import argparse

    parser = argparse.ArgumentParser(description="GPU Training Optimization")
    parser.add_argument(
        "--model-size",
        type=float,
        default=7.0,
        help="Model size in GB (default: 7.0 for Phi-3)",
    )
    parser.add_argument(
        "--memory-usage", type=float, default=0.8, help="Target memory usage (0.0-1.0)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data_out/gpu_profile.yaml",
        help="Output profile path",
    )
    parser.add_argument(
        "--update-config",
        type=str,
        help="Update existing config file with optimizations",
    )
    parser.add_argument(
        "--export-env", action="store_true", help="Export as environment variables"
    )

    args = parser.parse_args()

    optimizer = GPUOptimizer()
    optimizer.detect_hardware()

    profile = optimizer.create_optimization_profile(
        model_size_gb=args.model_size, target_memory_usage=args.memory_usage
    )

    # Save profile
    profile.save(args.output)

    # Update config if requested
    if args.update_config:
        optimizer.update_config_file(args.update_config, profile)

    # Export environment variables if requested
    if args.export_env:
        print("\n=== Environment Variables ===")
        env_vars = {
            "CUDA_VISIBLE_DEVICES": "0",
            "PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:512",
            "TOKENIZERS_PARALLELISM": "false",
        }

        if profile.use_4bit or profile.use_8bit:
            env_vars["BNB_CUDA_VERSION"] = optimizer.gpu_info.cuda_version

        for key, value in env_vars.items():
            print(f"export {key}={value}")


if __name__ == "__main__":
    main()
