"""
Quick model comparison script - evaluates multiple models with new diversity metrics
"""
import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

def evaluate_model(model_path: str, dataset: str, max_samples: int = 50) -> Dict[str, Any]:
    """Evaluate a single model and return metrics."""
    print(f"\n{'='*70}")
    print(f"Evaluating: {model_path}")
    print(f"{'='*70}")
    
    cmd = [
        sys.executable,
        "scripts/evaluate_lora_model.py",
        "--dataset", dataset,
        "--model", model_path,
        "--max-samples", str(max_samples),
        "--metric", "perplexity",
        "--metric", "diversity",
        "--output-format", "json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Try to parse JSON from output
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith('{'):
                try:
                    metrics = json.loads(line)
                    return {
                        "model": model_path,
                        "status": "success",
                        "metrics": metrics
                    }
                except json.JSONDecodeError:
                    continue
        
        # If no JSON found, check for errors
        if result.returncode != 0:
            return {
                "model": model_path,
                "status": "failed",
                "error": result.stderr or "No output"
            }
        else:
            return {
                "model": model_path,
                "status": "completed",
                "note": "No JSON metrics found"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "model": model_path,
            "status": "timeout",
            "error": "Evaluation timed out after 5 minutes"
        }
    except Exception as e:
        return {
            "model": model_path,
            "status": "error",
            "error": str(e)
        }

def main():
    # List of models to compare (relative to workspace root)
    models = [
        "data_out/lora_training/phi35",
        "data_out/lora_training/phi35_lr_low",
        "data_out/lora_training/phi35_lr_high",
        "data_out/lora_training/phi35_drop_low",
        "data_out/lora_training/phi35_drop_high",
        "data_out/lora_training/lora_adapter",
    ]
    
    # Check which models exist
    root = Path(__file__).parent.parent
    existing_models = []
    for model in models:
        model_path = root / model
        if model_path.exists():
            existing_models.append(model)
        else:
            print(f"⚠️  Model not found: {model}")
    
    if not existing_models:
        print("\n❌ No models found to evaluate!")
        return
    
    print(f"\n✅ Found {len(existing_models)} models to evaluate")
    print("\nModels:")
    for model in existing_models:
        print(f"  - {model}")
    
    # Evaluate all models
    results = []
    for model in existing_models:
        result = evaluate_model(model, "datasets/chat/mixed_chat", max_samples=30)
        results.append(result)
    
    # Print comparison table
    print("\n" + "="*70)
    print("MODEL COMPARISON RESULTS")
    print("="*70)
    print(f"\n{'Model':<50} {'Status':<15} {'Perplexity':<12} {'Diversity':<10}")
    print("-"*70)
    
    for r in results:
        model_name = r['model'].split('/')[-1]
        status = r['status']
        
        if status == 'success' and 'metrics' in r:
            m = r['metrics'].get('metrics', {})
            perplexity = f"{m.get('perplexity', 'N/A'):.2f}" if isinstance(m.get('perplexity'), (int, float)) else "N/A"
            diversity = f"{m.get('diversity', 'N/A'):.3f}" if isinstance(m.get('diversity'), (int, float)) else "N/A"
        else:
            perplexity = "N/A"
            diversity = "N/A"
        
        print(f"{model_name:<50} {status:<15} {perplexity:<12} {diversity:<10}")
    
    # Save detailed results
    output_file = root / "data_out" / "model_comparison_results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Detailed results saved to: {output_file}")
    
    # Show best model based on combined metric
    successful_results = [r for r in results if r['status'] == 'success' and 'metrics' in r]
    if successful_results:
        best = None
        best_score = -float('inf')
        
        for r in successful_results:
            m = r['metrics'].get('metrics', {})
            perplexity = m.get('perplexity')
            diversity = m.get('diversity')
            
            if perplexity and diversity and isinstance(perplexity, (int, float)) and isinstance(diversity, (int, float)):
                # Combined score: lower perplexity is better, higher diversity is better
                # Normalize: invert perplexity (1/perplexity) and combine
                combined = (1.0 / perplexity) * 0.7 + diversity * 0.3
                
                if combined > best_score:
                    best_score = combined
                    best = r
        
        if best:
            print(f"\n🏆 Best Model (Combined Score: {best_score:.4f}):")
            print(f"   {best['model']}")
            m = best['metrics'].get('metrics', {})
            print(f"   Perplexity: {m.get('perplexity'):.2f}")
            print(f"   Diversity: {m.get('diversity'):.3f}")
            if 'distinct_1' in m:
                print(f"   Distinct-1: {m.get('distinct_1'):.3f}")
            if 'distinct_2' in m:
                print(f"   Distinct-2: {m.get('distinct_2'):.3f}")

if __name__ == "__main__":
    main()
