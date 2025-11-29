"""
Analyze Self-Learning Progress
Shows metrics, conversation quality, and model improvement over time
"""

import json
import argparse
import statistics
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from collections import Counter
import math

def analyze_conversations() -> Dict[str, Any]:
    """Analyze collected conversations and return metrics dict"""
    repo_root = Path(__file__).resolve().parents[1]
    logs_dir = repo_root / "talk-to-ai" / "logs"
    
    if not logs_dir.exists():
        print(f"No logs directory found at: {logs_dir}")
        print("Start chatting to generate conversation data!")
        return {"available": False}
    
    log_files = list(logs_dir.glob("chat_*.jsonl"))
    
    if not log_files:
        print("No conversation logs found")
        return {"available": False}
    
    print(f"\n{'='*70}")
    print("CONVERSATION ANALYSIS")
    print(f"{'='*70}\n")
    
    total_messages = 0
    user_messages = []
    assistant_messages = []
    providers = Counter()
    models = Counter()
    
    for log_file in log_files:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    msg = json.loads(line)
                    total_messages += 1
                    
                    role = msg.get("role")
                    content = msg.get("content", "")
                    
                    if role == "user":
                        user_messages.append(content)
                    elif role == "assistant":
                        assistant_messages.append(content)
                    
                    providers[msg.get("provider", "unknown")] += 1
                    models[msg.get("model", "unknown")] += 1
    
    print(f"Total conversation files: {len(log_files)}")
    print(f"Total messages: {total_messages}")
    print(f"User messages: {len(user_messages)}")
    print(f"Assistant responses: {len(assistant_messages)}")
    
    avg_user_len = statistics.mean(len(msg) for msg in user_messages) if user_messages else 0
    avg_asst_len = statistics.mean(len(msg) for msg in assistant_messages) if assistant_messages else 0
    if user_messages:
        print(f"\nAverage user message length: {avg_user_len:.1f} characters")
    if assistant_messages:
        print(f"Average assistant response length: {avg_asst_len:.1f} characters")
    
    print(f"\nProviders used:")
    provider_stats = []
    for provider, count in providers.most_common():
        pct = count/total_messages*100 if total_messages else 0
        provider_stats.append({"provider": provider, "count": count, "percent": round(pct, 2)})
        print(f"  {provider}: {count} messages ({pct:.1f}%)")
    
    print(f"\nModels used:")
    model_stats = []
    for model, count in models.most_common(5):
        model_stats.append({"model": model, "count": count})
        print(f"  {model}: {count} messages")
    # Lexical diversity (simple): unique assistant words / total assistant words
    diversity = 0.0
    if assistant_messages:
        words = [w for msg in assistant_messages for w in msg.split()]
        if words:
            diversity = len(set(words))/len(words)
    return {
        "available": True,
        "files": len(log_files),
        "total_messages": total_messages,
        "user_messages": len(user_messages),
        "assistant_messages": len(assistant_messages),
        "avg_user_len": avg_user_len,
        "avg_assistant_len": avg_asst_len,
        "providers": provider_stats,
        "models": model_stats,
        "assistant_lexical_diversity": round(diversity, 4)
    }

def analyze_learning_status() -> Dict[str, Any]:
    """Show learning system status and history and return dict"""
    repo_root = Path(__file__).resolve().parents[1]
    status_file = repo_root / "data_out" / "self_learning" / "status.json"
    
    if not status_file.exists():
        print("\nNo learning status found - system not started yet")
        return {"available": False}
    
    with open(status_file, "r") as f:
        status = json.load(f)
    
    print(f"\n{'='*70}")
    print("LEARNING SYSTEM STATUS")
    print(f"{'='*70}\n")
    
    print(f"Started: {status.get('started_at', 'Unknown')}")
    print(f"Training cycles: {status.get('training_cycles', 0)}")
    print(f"Total conversations: {status.get('total_conversations', 0)}")
    print(f"New conversations: {status.get('conversations_since_last_train', 0)}")
    
    last_training = status.get('last_training')
    if last_training:
        dt = datetime.fromisoformat(last_training)
        print(f"Last training: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("Last training: Never")
    
    best_model = status.get('best_model_path')
    if best_model:
        print(f"Current model: {best_model}")
    
    # Show model history if available
    history = status.get('model_history', [])
    history_view = []
    if history:
        print(f"\nModel History ({len(history)} cycles):")
        for entry in history[-5:]:  # Show last 5
            cycle = entry.get('cycle')
            ts_raw = entry.get('timestamp')
            timestamp_fmt = datetime.fromisoformat(ts_raw).strftime('%Y-%m-%d %H:%M') if ts_raw else "?"
            convs = entry.get('conversations_used', 0)
            history_view.append({"cycle": cycle, "timestamp": ts_raw, "conversations_used": convs})
            print(f"  Cycle #{cycle} - {timestamp_fmt} - {convs} conversations")
    return {
        "available": True,
        "started_at": status.get('started_at'),
        "training_cycles": status.get('training_cycles', 0),
        "total_conversations": status.get('total_conversations', 0),
        "new_conversations": status.get('conversations_since_last_train', 0),
        "last_training": status.get('last_training'),
        "best_model_path": best_model,
        "history_recent": history_view
    }

def show_recommendations() -> Dict[str, Any]:
    """Provide recommendations for improving learning and return advice dict"""
    repo_root = Path(__file__).resolve().parents[1]
    status_file = repo_root / "data_out" / "self_learning" / "status.json"
    
    print(f"\n{'='*70}")
    print("RECOMMENDATIONS")
    print(f"{'='*70}\n")
    
    if not status_file.exists():
        print("[START] Start the self-learning system:")
        print("   python .\\scripts\\self_learning_chat.py --min-conversations 10")
        return {"available": False, "action": "start", "min_conversations": 10}
    
    with open(status_file, "r") as f:
        status = json.load(f)
    
    cycles = status.get('training_cycles', 0)
    new_convs = status.get('conversations_since_last_train', 0)
    
    advice = {"available": True, "state": None, "details": {"new_conversations": new_convs}}
    if cycles == 0:
        print("[TRAINING] No training cycles yet")
        print(f"   Current conversations: {new_convs}")
        print("   Need: 50 conversations (or use --min-conversations flag)")
        print("\n[TIP] Generate test data:")
        print("   python .\\scripts\\generate_test_conversations.py")
    
        advice["state"] = "initial"
        advice["details"]["needed"] = 50
    elif new_convs < 20:
        print("[STATUS] Need more conversations for next training cycle")
        print(f"   Current: {new_convs}")
        print("   Recommended: 50+ for good results")
        print("\n[TIP] Use the chat system more or generate test data")
    
        advice["state"] = "low_data"
        advice["details"]["recommended"] = 50
    else:
        print("[READY] Ready for next training cycle!")
        print(f"   {new_convs} new conversations available")
        print("\n[ACTION] Run training:")
        print("   python .\\scripts\\self_learning_chat.py")
        advice["state"] = "ready"
    
    if cycles > 0:
        print(f"\n[SUCCESS] {cycles} training cycle(s) completed")
        print("   Latest model available at:")
        print(f"   {status.get('best_model_path')}")
        print("\n[DEPLOY] To use new model: Restart Azure Functions")
        advice["details"]["cycles"] = cycles
        advice["details"]["best_model_path"] = status.get('best_model_path')
    return advice

def analyze_quantum_autorun() -> Dict[str, Any]:
    """Analyze quantum autorun status file."""
    repo_root = Path(__file__).resolve().parents[1]
    status_file = repo_root / "data_out" / "quantum_autorun" / "status.json"
    if not status_file.exists():
        return {"available": False}
    try:
        data = json.loads(status_file.read_text(encoding="utf-8"))
    except Exception as e:
        return {"available": False, "error": str(e)}
    jobs = data.get("jobs", [])
    total = len(jobs)
    succeeded = sum(1 for j in jobs if j.get("status") == "succeeded")
    failed = sum(1 for j in jobs if j.get("status") == "failed")
    avg_duration = statistics.mean(j.get("duration_sec", 0) for j in jobs) if jobs else 0
    modes = Counter(j.get("mode", "?") for j in jobs)
    print(f"\n{'='*70}\nQUANTUM AUTORUN ANALYSIS\n{'='*70}\n")
    print(f"Jobs: {total} | Succeeded: {succeeded} | Failed: {failed} | Avg Duration: {avg_duration:.2f}s")
    print("Modes:")
    for m, c in modes.items():
        print(f"  {m}: {c}")
    if failed:
        print("Failed jobs:")
        for j in jobs:
            if j.get("status") == "failed":
                print(f"  - {j.get('name')} ({j.get('mode')})")
    return {
        "available": True,
        "total_jobs": total,
        "succeeded": succeeded,
        "failed": failed,
        "avg_duration_sec": round(avg_duration, 2),
        "modes": dict(modes)
    }

def analyze_lora_training() -> Dict[str, Any]:
    """Analyze LoRA training metrics."""
    repo_root = Path(__file__).resolve().parents[1]
    metrics_file = repo_root / "data_out" / "lora_training" / "metrics.jsonl"
    if not metrics_file.exists():
        return {"available": False}
    evals: List[Dict[str, Any]] = []
    for line in metrics_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if "eval_loss" in rec:
                evals.append(rec)
        except Exception:
            continue
    if not evals:
        return {"available": False}
    # Deduplicate by (step, phase)
    seen = set()
    unique = []
    for r in evals:
        key = (r.get("step"), r.get("phase"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    unique.sort(key=lambda r: (r.get("step", 0), r.get("timestamp", "")))
    start_loss = unique[0].get("eval_loss")
    end_loss = unique[-1].get("eval_loss")
    start_ppl = unique[0].get("eval_perplexity")
    end_ppl = unique[-1].get("eval_perplexity")
    loss_improvement = (start_loss - end_loss) if (start_loss is not None and end_loss is not None) else None
    ppl_improvement_pct = None
    if start_ppl and end_ppl and start_ppl > 0:
        ppl_improvement_pct = (start_ppl - end_ppl) / start_ppl * 100
    print(f"\n{'='*70}\nLORA TRAINING METRICS\n{'='*70}\n")
    print(f"Records: {len(unique)} | Loss: {start_loss:.3f} -> {end_loss:.3f} | Perplexity: {start_ppl:.2f} -> {end_ppl:.2f}")
    if ppl_improvement_pct is not None:
        print(f"Perplexity improvement: {ppl_improvement_pct:.2f}%")
    return {
        "available": True,
        "records": len(unique),
        "start_loss": start_loss,
        "end_loss": end_loss,
        "start_perplexity": start_ppl,
        "end_perplexity": end_ppl,
        "perplexity_improvement_pct": round(ppl_improvement_pct, 2) if ppl_improvement_pct is not None else None
    }

def analyze_autotrain() -> Dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    status_file = repo_root / "data_out" / "autotrain" / "status.json"
    if not status_file.exists():
        return {"available": False}
    try:
        data = json.loads(status_file.read_text(encoding="utf-8"))
    except Exception as e:
        return {"available": False, "error": str(e)}
    jobs = data.get("jobs", [])
    statuses = Counter(j.get("status", "unknown") for j in jobs)
    print(f"\n{'='*70}\nAUTOTRAIN STATUS\n{'='*70}\n")
    print(f"Jobs tracked: {len(jobs)}")
    for s, c in statuses.items():
        print(f"  {s}: {c}")
    return {"available": True, "job_count": len(jobs), "status_counts": dict(statuses)}

def parse_args():
    parser = argparse.ArgumentParser(description="Analyze self-learning and training progress.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--sections", default="all", help="Comma-separated sections: conversations,learning,recommendations,quantum,lora,autotrain")
    return parser.parse_args()

def main():
    args = parse_args()
    wanted = [s.strip().lower() for s in args.sections.split(',')]
    if "all" in wanted:
        wanted = ["conversations", "learning", "recommendations", "quantum", "lora", "autotrain"]
    results: Dict[str, Any] = {}
    if args.format == "text":
        print(f"\n{'='*70}")
        print("SELF-LEARNING SYSTEM - Progress Analysis")
        print(f"{'='*70}")
    if "conversations" in wanted:
        results["conversations"] = analyze_conversations()
    if "learning" in wanted:
        results["learning"] = analyze_learning_status()
    if "recommendations" in wanted:
        results["recommendations"] = show_recommendations()
    if "quantum" in wanted:
        results["quantum_autorun"] = analyze_quantum_autorun()
    if "lora" in wanted:
        results["lora_training"] = analyze_lora_training()
    if "autotrain" in wanted:
        results["autotrain"] = analyze_autotrain()
    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        print(f"\n{'='*70}\n")
    return results

if __name__ == "__main__":
    main()
