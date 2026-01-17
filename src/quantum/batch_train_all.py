#!/usr/bin/env python
"""
Batch train quantum AI on all datasets, tracking results
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Already trained
TRAINED = {
    "banknote": "100.00",
    "ionosphere": "91.43",
    "heart_disease": "90.16",
    "iris": "90.00",
    "parkinsons": "84.62",
    "sonar": "73.81",
    "diabetes": "70.13",
    "liver_disorders": "52.17",
    "haberman": "~80",  # just finished
    "balance_scale": "~90",  # just finished
}

# All datasets
all_datasets = [
    "balance_scale", "blood_transfusion", "breast_cancer", "contraceptive", 
    "dermatology", "ecoli", "glass", "haberman", "magic_gamma", "optical_recognition",
    "pendigits", "seeds", "statlog_australian", "statlog_heart", "thyroid", 
    "vertebral_column", "wheat_seeds", "wine_quality_combined", "wine_red", 
    "wine_white", "yeast"
]

results = {}
os.chdir('/workspaces/AI/quantum-ai')

for dataset in all_datasets:
    if dataset in TRAINED:
        print(f"⏭️  Skipping {dataset} (already trained)")
        continue
    
    print(f"\n🚀 Training on {dataset}...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'train_custom_dataset.py', 
             '--csv', f'../datasets/quantum/{dataset}.csv',
             '--n-qubits', '4', '--epochs', '25', '--batch-size', '16',
             '--learning-rate', '0.001'],
            capture_output=True, text=True, timeout=180
        )
        
        # Extract accuracy from output
        output = result.stderr + result.stdout
        accuracy = None
        
        # Look for validation accuracy
        for line in output.split('\n'):
            if 'Val Acc:' in line:
                try:
                    acc_str = line.split('Val Acc:')[1].strip()
                    accuracy = float(acc_str.split()[0])
                except:
                    pass
        
        if accuracy:
            acc_pct = accuracy * 100
            results[dataset] = f"{acc_pct:.2f}%"
            tier = "🥇" if acc_pct >= 90 else "🥈" if acc_pct >= 80 else "🥉" if acc_pct >= 70 else "⚠️"
            print(f"   {tier} {dataset}: {acc_pct:.2f}%")
        else:
            results[dataset] = "ERROR"
            print(f"   ❌ {dataset}: Failed to extract accuracy")
            
    except subprocess.TimeoutExpired:
        results[dataset] = "TIMEOUT"
        print(f"   ⏱️  {dataset}: Timeout after 180s")
    except Exception as e:
        results[dataset] = f"ERROR: {str(e)[:30]}"
        print(f"   ❌ {dataset}: {str(e)[:50]}")

# Summary
print("\n" + "="*60)
print("📊 BATCH TRAINING SUMMARY")
print("="*60)

tier1 = {k: v for k, v in results.items() if '%' in v and float(v.rstrip('%')) >= 90}
tier2 = {k: v for k, v in results.items() if '%' in v and 80 <= float(v.rstrip('%')) < 90}
tier3 = {k: v for k, v in results.items() if '%' in v and 70 <= float(v.rstrip('%')) < 80}
errors = {k: v for k, v in results.items() if '%' not in v}

print(f"\n🥇 TIER 1 (90%+): {len(tier1)} models")
for name, acc in sorted(tier1.items(), key=lambda x: float(x[1].rstrip('%')), reverse=True):
    print(f"   ✅ {name}: {acc}")

print(f"\n🥈 TIER 2 (80-90%): {len(tier2)} models")
for name, acc in sorted(tier2.items(), key=lambda x: float(x[1].rstrip('%')), reverse=True):
    print(f"   ✅ {name}: {acc}")

print(f"\n🥉 TIER 3 (70-80%): {len(tier3)} models")
for name, acc in sorted(tier3.items(), key=lambda x: float(x[1].rstrip('%')), reverse=True):
    print(f"   ⚠️  {name}: {acc}")

if errors:
    print(f"\n❌ ERRORS/SKIPPED: {len(errors)} datasets")
    for name, reason in errors.items():
        print(f"   {name}: {reason}")

# Save results
results_file = '../data_out/quantum_batch_training_results.json'
os.makedirs('../data_out', exist_ok=True)
with open(results_file, 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'results': results,
        'tier1': len(tier1),
        'tier2': len(tier2),
        'tier3': len(tier3),
        'errors': len(errors)
    }, f, indent=2)
print(f"\n📁 Results saved to {results_file}")
