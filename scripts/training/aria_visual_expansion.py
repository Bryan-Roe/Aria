#!/usr/bin/env python
"""Expand Aria character visuals - more actions, expressions, animations"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Expanded Aria command set with visual actions
expanded_commands = [
    # === MOVEMENT (existing) ===
    {"messages": [{"role": "user", "content": "move left"}, {"role": "assistant", "content": "[aria:move:left]"}]},
    {"messages": [{"role": "user", "content": "move right"}, {"role": "assistant", "content": "[aria:move:right]"}]},
    {"messages": [{"role": "user", "content": "move up"}, {"role": "assistant", "content": "[aria:move:up]"}]},
    {"messages": [{"role": "user", "content": "move down"}, {"role": "assistant", "content": "[aria:move:down]"}]},
    {"messages": [{"role": "user", "content": "walk left"}, {"role": "assistant", "content": "[aria:walk:left]"}]},
    {"messages": [{"role": "user", "content": "walk right"}, {"role": "assistant", "content": "[aria:walk:right]"}]},
    {"messages": [{"role": "user", "content": "run left"}, {"role": "assistant", "content": "[aria:run:left]"}]},
    {"messages": [{"role": "user", "content": "run right"}, {"role": "assistant", "content": "[aria:run:right]"}]},
    
    # === EXPRESSIONS ===
    {"messages": [{"role": "user", "content": "aria smile"}, {"role": "assistant", "content": "[aria:expression:smile]"}]},
    {"messages": [{"role": "user", "content": "make her smile"}, {"role": "assistant", "content": "[aria:expression:smile]"}]},
    {"messages": [{"role": "user", "content": "aria happy"}, {"role": "assistant", "content": "[aria:expression:happy]"}]},
    {"messages": [{"role": "user", "content": "look happy"}, {"role": "assistant", "content": "[aria:expression:happy]"}]},
    {"messages": [{"role": "user", "content": "aria sad"}, {"role": "assistant", "content": "[aria:expression:sad]"}]},
    {"messages": [{"role": "user", "content": "look sad"}, {"role": "assistant", "content": "[aria:expression:sad]"}]},
    {"messages": [{"role": "user", "content": "aria surprised"}, {"role": "assistant", "content": "[aria:expression:surprised]"}]},
    {"messages": [{"role": "user", "content": "look surprised"}, {"role": "assistant", "content": "[aria:expression:surprised]"}]},
    {"messages": [{"role": "user", "content": "aria confused"}, {"role": "assistant", "content": "[aria:expression:confused]"}]},
    {"messages": [{"role": "user", "content": "aria thinking"}, {"role": "assistant", "content": "[aria:expression:thinking]"}]},
    {"messages": [{"role": "user", "content": "aria wink"}, {"role": "assistant", "content": "[aria:expression:wink]"}]},
    
    # === GESTURES ===
    {"messages": [{"role": "user", "content": "wave"}, {"role": "assistant", "content": "[aria:gesture:wave]"}]},
    {"messages": [{"role": "user", "content": "aria wave"}, {"role": "assistant", "content": "[aria:gesture:wave]"}]},
    {"messages": [{"role": "user", "content": "thumbs up"}, {"role": "assistant", "content": "[aria:gesture:thumbs_up]"}]},
    {"messages": [{"role": "user", "content": "aria thumbs up"}, {"role": "assistant", "content": "[aria:gesture:thumbs_up]"}]},
    {"messages": [{"role": "user", "content": "point left"}, {"role": "assistant", "content": "[aria:gesture:point:left]"}]},
    {"messages": [{"role": "user", "content": "point right"}, {"role": "assistant", "content": "[aria:gesture:point:right]"}]},
    {"messages": [{"role": "user", "content": "clap"}, {"role": "assistant", "content": "[aria:gesture:clap]"}]},
    {"messages": [{"role": "user", "content": "aria clap"}, {"role": "assistant", "content": "[aria:gesture:clap]"}]},
    {"messages": [{"role": "user", "content": "shrug"}, {"role": "assistant", "content": "[aria:gesture:shrug]"}]},
    {"messages": [{"role": "user", "content": "aria shrug"}, {"role": "assistant", "content": "[aria:gesture:shrug]"}]},
    
    # === ANIMATIONS ===
    {"messages": [{"role": "user", "content": "jump"}, {"role": "assistant", "content": "[aria:animate:jump]"}]},
    {"messages": [{"role": "user", "content": "aria jump"}, {"role": "assistant", "content": "[aria:animate:jump]"}]},
    {"messages": [{"role": "user", "content": "dance"}, {"role": "assistant", "content": "[aria:animate:dance]"}]},
    {"messages": [{"role": "user", "content": "aria dance"}, {"role": "assistant", "content": "[aria:animate:dance]"}]},
    {"messages": [{"role": "user", "content": "spin"}, {"role": "assistant", "content": "[aria:animate:spin]"}]},
    {"messages": [{"role": "user", "content": "aria spin"}, {"role": "assistant", "content": "[aria:animate:spin]"}]},
    {"messages": [{"role": "user", "content": "bow"}, {"role": "assistant", "content": "[aria:animate:bow]"}]},
    {"messages": [{"role": "user", "content": "aria bow"}, {"role": "assistant", "content": "[aria:animate:bow]"}]},
    {"messages": [{"role": "user", "content": "flip"}, {"role": "assistant", "content": "[aria:animate:flip]"}]},
    {"messages": [{"role": "user", "content": "backflip"}, {"role": "assistant", "content": "[aria:animate:backflip]"}]},
    
    # === POSES ===
    {"messages": [{"role": "user", "content": "sit down"}, {"role": "assistant", "content": "[aria:pose:sit]"}]},
    {"messages": [{"role": "user", "content": "aria sit"}, {"role": "assistant", "content": "[aria:pose:sit]"}]},
    {"messages": [{"role": "user", "content": "stand up"}, {"role": "assistant", "content": "[aria:pose:stand]"}]},
    {"messages": [{"role": "user", "content": "aria stand"}, {"role": "assistant", "content": "[aria:pose:stand]"}]},
    {"messages": [{"role": "user", "content": "lie down"}, {"role": "assistant", "content": "[aria:pose:lie]"}]},
    {"messages": [{"role": "user", "content": "aria lie down"}, {"role": "assistant", "content": "[aria:pose:lie]"}]},
    {"messages": [{"role": "user", "content": "crouch"}, {"role": "assistant", "content": "[aria:pose:crouch]"}]},
    {"messages": [{"role": "user", "content": "aria crouch"}, {"role": "assistant", "content": "[aria:pose:crouch]"}]},
    
    # === CAMERA/VIEW ===
    {"messages": [{"role": "user", "content": "center"}, {"role": "assistant", "content": "[aria:camera:center]"}]},
    {"messages": [{"role": "user", "content": "aria center"}, {"role": "assistant", "content": "[aria:camera:center]"}]},
    {"messages": [{"role": "user", "content": "zoom in"}, {"role": "assistant", "content": "[aria:camera:zoom_in]"}]},
    {"messages": [{"role": "user", "content": "zoom out"}, {"role": "assistant", "content": "[aria:camera:zoom_out]"}]},
    {"messages": [{"role": "user", "content": "face left"}, {"role": "assistant", "content": "[aria:camera:face:left]"}]},
    {"messages": [{"role": "user", "content": "face right"}, {"role": "assistant", "content": "[aria:camera:face:right]"}]},
    
    # === EFFECTS ===
    {"messages": [{"role": "user", "content": "sparkle"}, {"role": "assistant", "content": "[aria:effect:sparkle]"}]},
    {"messages": [{"role": "user", "content": "aria sparkle"}, {"role": "assistant", "content": "[aria:effect:sparkle]"}]},
    {"messages": [{"role": "user", "content": "glow"}, {"role": "assistant", "content": "[aria:effect:glow]"}]},
    {"messages": [{"role": "user", "content": "aria glow"}, {"role": "assistant", "content": "[aria:effect:glow]"}]},
    {"messages": [{"role": "user", "content": "hearts"}, {"role": "assistant", "content": "[aria:effect:hearts]"}]},
    {"messages": [{"role": "user", "content": "show hearts"}, {"role": "assistant", "content": "[aria:effect:hearts]"}]},
    
    # === COMBINATIONS ===
    {"messages": [{"role": "user", "content": "walk left and wave"}, {"role": "assistant", "content": "[aria:walk:left] [aria:gesture:wave]"}]},
    {"messages": [{"role": "user", "content": "jump and smile"}, {"role": "assistant", "content": "[aria:animate:jump] [aria:expression:smile]"}]},
    {"messages": [{"role": "user", "content": "center and dance"}, {"role": "assistant", "content": "[aria:camera:center] [aria:animate:dance]"}]},
    {"messages": [{"role": "user", "content": "spin with sparkles"}, {"role": "assistant", "content": "[aria:animate:spin] [aria:effect:sparkle]"}]},
]

# Test data
test_data = [
    {"messages": [{"role": "user", "content": "make aria smile"}, {"role": "assistant", "content": "[aria:expression:smile]"}]},
    {"messages": [{"role": "user", "content": "aria jump high"}, {"role": "assistant", "content": "[aria:animate:jump]"}]},
    {"messages": [{"role": "user", "content": "show thumbs up"}, {"role": "assistant", "content": "[aria:gesture:thumbs_up]"}]},
    {"messages": [{"role": "user", "content": "dance with sparkles"}, {"role": "assistant", "content": "[aria:animate:dance] [aria:effect:sparkle]"}]},
    {"messages": [{"role": "user", "content": "look surprised"}, {"role": "assistant", "content": "[aria:expression:surprised]"}]},
]

# Save expanded dataset
dataset_dir = REPO_ROOT / "datasets" / "chat" / "aria_expanded"
dataset_dir.mkdir(parents=True, exist_ok=True)

with open(dataset_dir / "train.json", "w", encoding="utf-8") as f:
    json.dump(expanded_commands, f, indent=2, ensure_ascii=False)

with open(dataset_dir / "test.json", "w", encoding="utf-8") as f:
    json.dump(test_data, f, indent=2, ensure_ascii=False)

print("✅ Created EXPANDED Aria Visual Dataset!")
print("=" * 70)
print(f"📍 Location: {dataset_dir.relative_to(REPO_ROOT)}")
print(f"📊 Train samples: {len(expanded_commands)}")
print(f"📊 Test samples: {len(test_data)}")
print("\n🎭 Command Categories:")
print("   • Movement: move, walk, run (left/right/up/down)")
print("   • Expressions: smile, happy, sad, surprised, confused, thinking, wink")
print("   • Gestures: wave, thumbs_up, point, clap, shrug")
print("   • Animations: jump, dance, spin, bow, flip, backflip")
print("   • Poses: sit, stand, lie, crouch")
print("   • Camera: center, zoom, face direction")
print("   • Effects: sparkle, glow, hearts")
print("   • Combinations: Multiple commands in sequence")
