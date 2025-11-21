"""
Analyze Self-Learning Progress
Shows metrics, conversation quality, and model improvement over time
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter
import statistics

def analyze_conversations():
    """Analyze collected conversations"""
    repo_root = Path(__file__).resolve().parents[1]
    logs_dir = repo_root / "talk-to-ai" / "logs"
    
    if not logs_dir.exists():
        print(f"No logs directory found at: {logs_dir}")
        print("Start chatting to generate conversation data!")
        return
    
    log_files = list(logs_dir.glob("chat_*.jsonl"))
    
    if not log_files:
        print("No conversation logs found")
        return
    
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
    
    if user_messages:
        avg_user_len = statistics.mean(len(msg) for msg in user_messages)
        print(f"\nAverage user message length: {avg_user_len:.1f} characters")
    
    if assistant_messages:
        avg_asst_len = statistics.mean(len(msg) for msg in assistant_messages)
        print(f"Average assistant response length: {avg_asst_len:.1f} characters")
    
    print(f"\nProviders used:")
    for provider, count in providers.most_common():
        print(f"  {provider}: {count} messages ({count/total_messages*100:.1f}%)")
    
    print(f"\nModels used:")
    for model, count in models.most_common(5):
        print(f"  {model}: {count} messages")

def analyze_learning_status():
    """Show learning system status and history"""
    repo_root = Path(__file__).resolve().parents[1]
    status_file = repo_root / "data_out" / "self_learning" / "status.json"
    
    if not status_file.exists():
        print("\nNo learning status found - system not started yet")
        return
    
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
    if history:
        print(f"\nModel History ({len(history)} cycles):")
        for entry in history[-5:]:  # Show last 5
            cycle = entry.get('cycle')
            timestamp = datetime.fromisoformat(entry.get('timestamp')).strftime('%Y-%m-%d %H:%M')
            convs = entry.get('conversations_used', 0)
            print(f"  Cycle #{cycle} - {timestamp} - {convs} conversations")

def show_recommendations():
    """Provide recommendations for improving learning"""
    repo_root = Path(__file__).resolve().parents[1]
    status_file = repo_root / "data_out" / "self_learning" / "status.json"
    
    print(f"\n{'='*70}")
    print("RECOMMENDATIONS")
    print(f"{'='*70}\n")
    
    if not status_file.exists():
        print("[START] Start the self-learning system:")
        print("   python .\\scripts\\self_learning_chat.py --min-conversations 10")
        return
    
    with open(status_file, "r") as f:
        status = json.load(f)
    
    cycles = status.get('training_cycles', 0)
    new_convs = status.get('conversations_since_last_train', 0)
    
    if cycles == 0:
        print("[TRAINING] No training cycles yet")
        print(f"   Current conversations: {new_convs}")
        print("   Need: 50 conversations (or use --min-conversations flag)")
        print("\n[TIP] Generate test data:")
        print("   python .\\scripts\\generate_test_conversations.py")
    
    elif new_convs < 20:
        print("[STATUS] Need more conversations for next training cycle")
        print(f"   Current: {new_convs}")
        print("   Recommended: 50+ for good results")
        print("\n[TIP] Use the chat system more or generate test data")
    
    else:
        print("[READY] Ready for next training cycle!")
        print(f"   {new_convs} new conversations available")
        print("\n[ACTION] Run training:")
        print("   python .\\scripts\\self_learning_chat.py")
    
    if cycles > 0:
        print(f"\n[SUCCESS] {cycles} training cycle(s) completed")
        print("   Latest model available at:")
        print(f"   {status.get('best_model_path')}")
        print("\n[DEPLOY] To use new model: Restart Azure Functions")

def main():
    print(f"\n{'='*70}")
    print("SELF-LEARNING SYSTEM - Progress Analysis")
    print(f"{'='*70}")
    
    analyze_conversations()
    analyze_learning_status()
    show_recommendations()
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    main()
