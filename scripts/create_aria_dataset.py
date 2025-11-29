#!/usr/bin/env python
"""Generate optimized Aria training data with stronger command patterns"""
import json
from pathlib import Path

# Expanded training data with clearer patterns
training_data = [
    # Basic movements - left
    {"messages": [{"role": "user", "content": "move left"}, {"role": "assistant", "content": "[aria:move:left]"}]},
    {"messages": [{"role": "user", "content": "go left"}, {"role": "assistant", "content": "[aria:move:left]"}]},
    {"messages": [{"role": "user", "content": "aria left"}, {"role": "assistant", "content": "[aria:move:left]"}]},
    
    # Basic movements - right
    {"messages": [{"role": "user", "content": "move right"}, {"role": "assistant", "content": "[aria:move:right]"}]},
    {"messages": [{"role": "user", "content": "go right"}, {"role": "assistant", "content": "[aria:move:right]"}]},
    {"messages": [{"role": "user", "content": "aria right"}, {"role": "assistant", "content": "[aria:move:right]"}]},
    
    # Basic movements - up
    {"messages": [{"role": "user", "content": "move up"}, {"role": "assistant", "content": "[aria:move:up]"}]},
    {"messages": [{"role": "user", "content": "go up"}, {"role": "assistant", "content": "[aria:move:up]"}]},
    {"messages": [{"role": "user", "content": "aria up"}, {"role": "assistant", "content": "[aria:move:up]"}]},
    
    # Basic movements - down
    {"messages": [{"role": "user", "content": "move down"}, {"role": "assistant", "content": "[aria:move:down]"}]},
    {"messages": [{"role": "user", "content": "go down"}, {"role": "assistant", "content": "[aria:move:down]"}]},
    {"messages": [{"role": "user", "content": "aria down"}, {"role": "assistant", "content": "[aria:move:down]"}]},
    
    # Actions - jump
    {"messages": [{"role": "user", "content": "jump"}, {"role": "assistant", "content": "[aria:jump]"}]},
    {"messages": [{"role": "user", "content": "aria jump"}, {"role": "assistant", "content": "[aria:jump]"}]},
    {"messages": [{"role": "user", "content": "make her jump"}, {"role": "assistant", "content": "[aria:jump]"}]},
    
    # Actions - wave
    {"messages": [{"role": "user", "content": "wave"}, {"role": "assistant", "content": "[aria:wave]"}]},
    {"messages": [{"role": "user", "content": "aria wave"}, {"role": "assistant", "content": "[aria:wave]"}]},
    {"messages": [{"role": "user", "content": "wave hello"}, {"role": "assistant", "content": "[aria:wave]"}]},
    
    # Actions - dance
    {"messages": [{"role": "user", "content": "dance"}, {"role": "assistant", "content": "[aria:dance]"}]},
    {"messages": [{"role": "user", "content": "aria dance"}, {"role": "assistant", "content": "[aria:dance]"}]},
    {"messages": [{"role": "user", "content": "start dancing"}, {"role": "assistant", "content": "[aria:dance]"}]},
    
    # Center
    {"messages": [{"role": "user", "content": "center"}, {"role": "assistant", "content": "[aria:center]"}]},
    {"messages": [{"role": "user", "content": "aria center"}, {"role": "assistant", "content": "[aria:center]"}]},
    {"messages": [{"role": "user", "content": "go to center"}, {"role": "assistant", "content": "[aria:center]"}]},
    
    # Walk commands
    {"messages": [{"role": "user", "content": "walk left"}, {"role": "assistant", "content": "[aria:walk:left]"}]},
    {"messages": [{"role": "user", "content": "walk right"}, {"role": "assistant", "content": "[aria:walk:right]"}]},
    {"messages": [{"role": "user", "content": "walk up"}, {"role": "assistant", "content": "[aria:walk:up]"}]},
    {"messages": [{"role": "user", "content": "walk down"}, {"role": "assistant", "content": "[aria:walk:down]"}]},
]

# Test data (same format)
test_data = [
    {"messages": [{"role": "user", "content": "aria go left"}, {"role": "assistant", "content": "[aria:move:left]"}]},
    {"messages": [{"role": "user", "content": "make aria jump"}, {"role": "assistant", "content": "[aria:jump]"}]},
    {"messages": [{"role": "user", "content": "dance now"}, {"role": "assistant", "content": "[aria:dance]"}]},
    {"messages": [{"role": "user", "content": "return to center"}, {"role": "assistant", "content": "[aria:center]"}]},
    {"messages": [{"role": "user", "content": "wave at me"}, {"role": "assistant", "content": "[aria:wave]"}]},
]

# Save datasets
REPO_ROOT = Path(__file__).resolve().parents[1]
dataset_dir = REPO_ROOT / "datasets" / "chat" / "aria_simple"
dataset_dir.mkdir(parents=True, exist_ok=True)

with open(dataset_dir / "train.json", "w", encoding="utf-8") as f:
    json.dump(training_data, f, indent=2, ensure_ascii=False)

with open(dataset_dir / "test.json", "w", encoding="utf-8") as f:
    json.dump(test_data, f, indent=2, ensure_ascii=False)

print(f"✅ Created simplified Aria dataset:")
print(f"   Train: {len(training_data)} samples")
print(f"   Test:  {len(test_data)} samples")
print(f"   Location: {dataset_dir}")
