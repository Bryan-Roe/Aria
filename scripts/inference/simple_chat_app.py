#!/usr/bin/env python3
"""
Simple Chat Web App with Model Support
Serves a web UI and provides chat API with multiple provider support
"""
import os
import sys
import json
from pathlib import Path
from flask import Flask, request, Response, jsonify, send_from_directory

# Add paths (workspace root is one level up from scripts/)
_WORKSPACE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_WORKSPACE / 'src'))
sys.path.insert(0, str(_WORKSPACE / 'shared'))

app = Flask(__name__, static_folder='.')

# HTML for the chat interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Chat Interface</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .chat-container {
            width: 90%;
            max-width: 800px;
            height: 80vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .chat-header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
        }
        .provider-info {
            background: rgba(255,255,255,0.1);
            padding: 8px;
            font-size: 12px;
            text-align: center;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
        }
        .message.user {
            justify-content: flex-end;
        }
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
            white-space: pre-wrap;
        }
        .message.user .message-content {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 4px;
        }
        .message.assistant .message-content {
            background: white;
            color: #333;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .chat-input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
            display: flex;
            gap: 10px;
        }
        .chat-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #eee;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        .chat-input:focus {
            border-color: #667eea;
        }
        .send-button {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, opacity 0.3s;
        }
        .send-button:hover:not(:disabled) {
            transform: translateY(-2px);
        }
        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .error {
            background: #ff4444 !important;
            color: white !important;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            AI Chat Interface
            <div class="provider-info" id="provider-info">Loading...</div>
        </div>
        <div class="chat-messages" id="messages">
            <div class="message assistant">
                <div class="message-content">
                    👋 Hello! I'm your AI assistant. How can I help you today?
                </div>
            </div>
        </div>
        <div class="chat-input-area">
            <input 
                type="text" 
                class="chat-input" 
                id="input" 
                placeholder="Type your message..."
                onkeypress="if(event.key === 'Enter') sendMessage()"
            />
            <button class="send-button" id="send-btn" onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const messagesDiv = document.getElementById('messages');
        const inputField = document.getElementById('input');
        const sendBtn = document.getElementById('send-btn');
        const providerInfo = document.getElementById('provider-info');

        // Load provider info
        fetch('/api/status')
            .then(r => r.json())
            .then(data => {
                providerInfo.textContent = `Provider: ${data.provider || 'unknown'} | Status: ${data.status}`;
            })
            .catch(e => {
                providerInfo.textContent = 'Provider: offline';
            });

        function addMessage(role, content, isError = false) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${role}`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = `message-content ${isError ? 'error' : ''}`;
            contentDiv.textContent = content;
            
            msgDiv.appendChild(contentDiv);
            messagesDiv.appendChild(msgDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            return contentDiv;
        }

        async function sendMessage() {
            const message = inputField.value.trim();
            if (!message) return;

            // Add user message
            addMessage('user', message);
            inputField.value = '';
            sendBtn.disabled = true;

            // Add loading indicator
            const loadingDiv = addMessage('assistant', '');
            loadingDiv.innerHTML = '<div class="loading"></div>';

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                
                if (data.error) {
                    loadingDiv.textContent = `Error: ${data.error}`;
                    loadingDiv.classList.add('error');
                } else {
                    loadingDiv.textContent = data.response || 'No response';
                    loadingDiv.classList.remove('error');
                }
            } catch (error) {
                loadingDiv.textContent = `Error: ${error.message}`;
                loadingDiv.classList.add('error');
            } finally {
                sendBtn.disabled = false;
                inputField.focus();
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the chat interface"""
    return HTML_TEMPLATE

@app.route('/api/status')
def status():
    """Get provider status"""
    try:
        # Import directly from src.chat to avoid circular import
        sys.path.insert(0, str(Path(__file__).parent / 'src' / 'chat'))
        import chat_providers as cp
        provider = cp.detect_provider()
        return jsonify({'status': 'ok', 'provider': provider})
    except ImportError:
        # Fallback if chat_providers not available
        return jsonify({'status': 'ok', 'provider': 'local-fallback'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e), 'provider': 'unknown'})

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Try to use real chat providers
        try:
            # Import directly from src.chat to avoid circular import
            sys.path.insert(0, str(Path(__file__).parent / 'src' / 'chat'))
            import chat_providers as cp
            
            provider = cp.detect_provider()
            print(f"Using provider: {provider}")
            
            messages = [{'role': 'user', 'content': message}]
            response = cp.get_chat_completion(messages, stream=False)
            
            return jsonify({'response': response, 'provider': provider})
        
        except ImportError as e:
            # Fallback to simple echo if providers not available
            print(f"Chat providers not available: {e}")
            return jsonify({
                'response': f"Echo (no provider available): {message}",
                'provider': 'echo-fallback'
            })
    
    except Exception as e:
        print(f"Error in chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.after_request
def after_request(response):
    """Add CORS headers"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 AI Chat Interface Starting")
    print("=" * 60)
    print(f"📡 URL: http://localhost:8080")
    print(f"📂 Working Directory: {Path.cwd()}")
    print("=" * 60)
    
    # Check provider availability
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'src' / 'chat'))
        import chat_providers as cp
        provider = cp.detect_provider()
        print(f"✅ Provider detected: {provider}")
    except Exception as e:
        print(f"⚠️  Provider detection failed: {e}")
        print("   Will use echo fallback")
    
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8080, debug=False)
