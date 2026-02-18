#!/usr/bin/env python
"""
GPU Training Quick Start

One-liner commands to launch training with GPU acceleration enabled.
"""

# ============================================================================
# PHASE 1: QUICK TEST (5-15 min) ⚡
# ============================================================================
# python scripts/training/progressive_training.py --phase quick

# Expected: Single Phi-3.5 LR test with 64 samples
# GPU: ~50-70% utilization
# Speed: 100+ samples/sec


# ============================================================================
# PHASE 2: STANDARD (30-60 min) 📊  
# ============================================================================
# python scripts/training/progressive_training.py --phase standard

# Expected: Phi-3.5 + Qwen2.5 baseline comparison
# GPU: ~90-99% utilization
# Speed: 150-250 samples/sec


# ============================================================================
# PHASE 3: FULL (2-8 hours) 🚀
# ============================================================================
# python scripts/training/progressive_training.py --phase full

# Expected: All 12 jobs - comprehensive, domain, HPO, anime
# GPU: ~90-99% utilization
# Speed: 150-250 samples/sec


# ============================================================================
# COMBINED: RUN ALL PHASES (2-9 hours total) 🔄
# ============================================================================
# python scripts/training/progressive_training.py --all --auto-promote

# Runs: quick → standard → full with auto-deployment


# ============================================================================
# SINGLE JOB (dry-run, no GPU needed)
# ============================================================================
# python scripts/training/autotrain.py --job phi35_mixed_chat --dry-run


# ============================================================================
# SINGLE JOB (actual training with GPU)
# ============================================================================
# python scripts/training/autotrain.py --job phi35_mixed_chat


# ============================================================================
# MONITORING
# ============================================================================
# watch -n 1 nvidia-smi              # Real-time GPU stats
# tail -f data_out/training_*.log    # Watch training logs
# python scripts/resource_monitor.py --stream  # CPU/GPU/Memory dashboard


# ============================================================================
# CONFIGURATION
# ============================================================================
# GPU: ENABLED on all jobs
# Device: cuda (not auto, not cpu)
# Memory: 0 (use all available)
# Workers: 20 (parallel data loading)


# ============================================================================
# KEY FILES
# ============================================================================
# GPU_SETUP.md             - GPU installation guide
# TRAINING_PROGRESSION.md  - Detailed phase documentation
# config/training/autotrain.yaml          - Training job configs
# config/autonomous_training.yaml         - Autonomous mode settings
# scripts/training/progressive_training.py - Phase orchestrator


# ============================================================================
# STATUS/RESULTS
# ============================================================================
# data_out/training_quick_status.json
# data_out/training_standard_status.json
# data_out/training_full_status.json
# data_out/lora_training/*/metrics.json
# data_out/lora_training/*/adapter_model.safetensors


if __name__ == "__main__":
    print(__doc__)
