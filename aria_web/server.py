#!/usr/bin/env python
"""
Simple web server for Aria Visual Command System
Serves the HTML/JS frontend and provides API endpoint for command generation
"""
import sys
from pathlib import Path
from typing import List
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import re
from urllib.parse import urlparse, parse_qs

# Add project paths
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1"))

# Try to load the model (optional - will work without it using fallback)
MODEL = None
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    import torch
    
    print("🔍 Loading Aria model...")
    adapter_path = REPO_ROOT / "data_out" / "aria_models" / "aria_expanded_v2" / "lora_adapter"
    
    if adapter_path.exists():
        base_model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        model = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype=torch.float16, device_map="auto")
        MODEL = PeftModel.from_pretrained(model, str(adapter_path))
        print("✅ Model loaded successfully!")
    else:
        print("⚠️ Model not found, using rule-based fallback")
except Exception as e:
    print(f"⚠️ Could not load model: {e}")
    print("Using rule-based fallback parser")

def generate_tags_ai(command: str) -> List[str]:
    """Generate tags using AI model"""
    if MODEL is None:
        return []
    
    try:
        from transformers import AutoTokenizer
        base_model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        
        input_text = f"<|user|>\n{command}</s>\n<|assistant|>\n"
        inputs = tokenizer(input_text, return_tensors="pt").to(MODEL.device)
        
        with torch.no_grad():
            outputs = MODEL.generate(
                **inputs,
                max_new_tokens=30,
                temperature=0.1,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.5,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        tags = re.findall(r'\[aria:[^\]]+\]', response)
        return tags[:2]  # Return first 2 tags max
    except Exception as e:
        print(f"AI generation error: {e}")
        return []

def generate_tags_fallback(command: str) -> List[str]:
    """Simple rule-based fallback tag generation"""
    cmd = command.lower()
    tags = []
    
    # Track if limb commands are detected to avoid movement conflicts
    has_limb_command = any(k in cmd for k in [
        'left arm', 'arm left', 'left hand', 'right arm', 'arm right', 'right hand',
        'left leg', 'leg left', 'right leg', 'leg right'
    ])
    
    # Expressions
    if 'smile' in cmd or 'happy' in cmd:
        tags.append('[aria:expression:smile]')
    elif 'sad' in cmd:
        tags.append('[aria:expression:sad]')
    elif 'surprised' in cmd:
        tags.append('[aria:expression:surprised]')
    elif 'confused' in cmd:
        tags.append('[aria:expression:confused]')
    elif 'thinking' in cmd or 'think' in cmd:
        tags.append('[aria:expression:thinking]')
    elif 'wink' in cmd:
        tags.append('[aria:expression:wink]')
    
    # Animations
    if 'jump' in cmd:
        tags.append('[aria:animate:jump]')
    elif 'dance' in cmd:
        tags.append('[aria:animate:dance]')
    elif 'spin' in cmd:
        tags.append('[aria:animate:spin]')
    elif 'bow' in cmd:
        tags.append('[aria:animate:bow]')
    elif 'flip' in cmd:
        tags.append('[aria:animate:flip]')
    
    # Gestures
    if 'wave' in cmd:
        tags.append('[aria:gesture:wave]')
    elif 'thumbs up' in cmd:
        tags.append('[aria:gesture:thumbs_up]')
    elif 'clap' in cmd:
        tags.append('[aria:gesture:clap]')
    elif 'shrug' in cmd:
        tags.append('[aria:gesture:shrug]')
    
    # Limb controls and poses (AI may also emit these; fallback supports natural phrases)
    # Hands up / T-pose / Cross arms
    if 'hands up' in cmd or 'raise hands' in cmd:
        tags.append('[aria:limb:left_arm:raise]')
        tags.append('[aria:limb:right_arm:raise]')
    if 't-pose' in cmd or 'tpose' in cmd or 't pose' in cmd:
        tags.append('[aria:pose:t-pose]')
    if 'cross arms' in cmd or 'arms crossed' in cmd:
        tags.append('[aria:pose:cross_arms]')

    # Per-limb commands
    def limb_tag(part: str, action: str):
        tags.append(f'[aria:limb:{part}:{action}]')

    # Helper maps
    left_arm = any(k in cmd for k in ['left arm', 'arm left', 'left hand'])
    right_arm = any(k in cmd for k in ['right arm', 'arm right', 'right hand'])
    left_leg = any(k in cmd for k in ['left leg', 'leg left'])
    right_leg = any(k in cmd for k in ['right leg', 'leg right'])

    # Numeric angle if present (e.g., "left arm 45 degrees")
    angle_match = None
    try:
        angle_match = next((m for m in __import__('re').finditer(r'(-?\d{1,3})\s*(deg|degree|degrees)?', cmd)), None)
    except Exception:
        angle_match = None
    angle_val = angle_match.group(1) if angle_match else None

    # Arm actions
    if left_arm or right_arm or 'arm' in cmd:
        # Choose default arm if unspecified
        parts = []
        if left_arm:
            parts.append('left_arm')
        if right_arm:
            parts.append('right_arm')
        if not parts:
            parts = ['right_arm']
        if any(k in cmd for k in ['wave', 'wiggle']):
            for p in parts: limb_tag(p, 'wave')
        elif any(k in cmd for k in ['raise', 'up', 'lift']):
            for p in parts: limb_tag(p, 'raise')
        elif any(k in cmd for k in ['lower', 'down']):
            for p in parts: limb_tag(p, 'lower')
        elif any(k in cmd for k in ['forward', 'front']):
            for p in parts: limb_tag(p, 'forward')
        elif any(k in cmd for k in ['back', 'backward', 'behind']):
            for p in parts: limb_tag(p, 'back')
        elif angle_val is not None:
            for p in parts: limb_tag(p, angle_val)

    # Leg actions
    if left_leg or right_leg or 'leg' in cmd:
        parts = []
        if left_leg:
            parts.append('left_leg')
        if right_leg:
            parts.append('right_leg')
        if not parts:
            parts = ['left_leg']
        if 'kick' in cmd:
            for p in parts: limb_tag(p, 'kick')
        elif any(k in cmd for k in ['forward', 'front']):
            for p in parts: limb_tag(p, 'forward')
        elif any(k in cmd for k in ['back', 'backward', 'behind']):
            for p in parts: limb_tag(p, 'back')
        elif angle_val is not None:
            for p in parts: limb_tag(p, angle_val)

    # Movement - only add if not a limb command (to avoid conflicts like "left arm" -> "move:left")
    if not has_limb_command:
        # Determine movement style
        movement_style = None
        if 'skip' in cmd:
            movement_style = 'skip'
        elif 'strut' in cmd or 'swagger' in cmd:
            movement_style = 'strut'
        elif 'run' in cmd:
            movement_style = 'run'
        elif 'walk' in cmd:
            movement_style = 'walk'
        else:
            movement_style = 'move'
        
        # Determine direction - exclude if keywords could be part of limb commands
        has_forward_limb = 'leg' in cmd or 'arm' in cmd
        if 'left' in cmd:
            tags.append(f'[aria:{movement_style}:left]')
        elif 'right' in cmd:
            tags.append(f'[aria:{movement_style}:right]')
        elif ('up' in cmd or 'forward' in cmd) and not has_forward_limb:
            tags.append(f'[aria:{movement_style}:up]')
        elif ('down' in cmd or 'back' in cmd) and not has_forward_limb:
            tags.append(f'[aria:{movement_style}:down]')
    
    # Effects
    if 'sparkle' in cmd:
        tags.append('[aria:effect:sparkle]')
    elif 'glow' in cmd:
        tags.append('[aria:effect:glow]')
    elif 'hearts' in cmd:
        tags.append('[aria:effect:hearts]')
    
    # Camera
    if 'center' in cmd:
        tags.append('[aria:camera:center]')
    elif 'zoom' in cmd:
        tags.append('[aria:camera:zoom_in]' if 'in' in cmd else '[aria:camera:zoom_out]')
    
    # Poses (body positions)
    if 'sit' in cmd:
        tags.append('[aria:pose:sit]')
    elif 'stand' in cmd:
        tags.append('[aria:pose:stand]')
    elif 'crouch' in cmd:
        tags.append('[aria:pose:crouch]')
    elif 'lie' in cmd or 'lay' in cmd:
        tags.append('[aria:pose:lie]')
    
    return tags

class AriaRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        """Serve static files"""
        print(f"📥 GET request: {self.path}")
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()
    
    def do_POST(self):
        """Handle API requests"""
        if self.path == '/api/aria/command':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                data = json.loads(post_data.decode('utf-8'))
                command = data.get('command', '')
                
                print(f"📝 Command received: {command}")
                
                # Try AI first, fallback to rules
                tags = generate_tags_ai(command)
                if not tags:
                    tags = generate_tags_fallback(command)
                
                print(f"✨ Generated tags: {tags}")
                
                response = {
                    'command': command,
                    'tags': tags,
                    'model': 'ai' if (MODEL and tags) else 'fallback'
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except ConnectionAbortedError:
                # Client disconnected, ignore
                pass
            except Exception as e:
                print(f"❌ Error: {e}")
                try:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    error = {'error': str(e), 'tags': []}
                    self.wfile.write(json.dumps(error).encode('utf-8'))
                except:
                    pass
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Custom logging"""
        if 'favicon' not in args[0] if args else True:
            print(f"🌐 {args[0] if args else format}")

def main():
    import os
    
    # Change to aria_web directory
    web_dir = Path(__file__).parent
    os.chdir(web_dir)
    
    port = 8080
    server = HTTPServer(('0.0.0.0', port), AriaRequestHandler)
    
    print("\n" + "=" * 70)
    print("🎨 Aria Visual Command System - Web Server")
    print("=" * 70)
    print(f"🌐 Open in browser: http://localhost:{port}")
    print(f"🤖 Model: {'AI (aria_expanded_v2)' if MODEL else 'Rule-based fallback'}")
    print("📝 Type commands in the web interface to control Aria")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 70 + "\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == '__main__':
    main()
