"""
Quantum API endpoints for Aria server.
These endpoints are integrated with the main AriaRequestHandler.
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Import quantum functions (will be None if unavailable)
try:
    from quantum_3d_bridge import (
        quantum_predict_behavior,
        quantum_generate_world,
        quantum_visualize_state,
        QUANTUM_AVAILABLE
    )
except ImportError:
    QUANTUM_AVAILABLE = False
    quantum_predict_behavior = None
    quantum_generate_world = None
    quantum_visualize_state = None


def handle_quantum_state(handler) -> Dict[str, Any]:
    """Handle GET /api/aria/quantum/state - Get quantum state visualization."""
    if not QUANTUM_AVAILABLE or quantum_visualize_state is None:
        return {
            'enabled': False,
            'message': 'Quantum computing unavailable'
        }
    
    try:
        result = quantum_visualize_state()
        return result
    except Exception as e:
        logger.error(f"Quantum state visualization error: {e}")
        return {
            'enabled': False,
            'error': str(e)
        }


def handle_quantum_predict(handler, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST /api/aria/quantum/predict - Predict behavior using quantum computing."""
    if not QUANTUM_AVAILABLE or quantum_predict_behavior is None:
        return {
            'status': 'error',
            'message': 'Quantum computing unavailable',
            'action': {'action': 'wait', 'duration': 1.0},
            'method': 'classical_fallback'
        }
    
    try:
        context = request_data.get('context', {})
        
        # Ensure context has required fields
        if 'position' not in context:
            from server import stage_state
            context['position'] = stage_state['aria']['position']
        if 'expression' not in context:
            context['expression'] = 'neutral'
        if 'objects' not in context:
            context['objects'] = {}
        
        result = quantum_predict_behavior(context)
        return {
            'status': 'success',
            **result
        }
    except Exception as e:
        logger.error(f"Quantum behavior prediction error: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'action': {'action': 'wait', 'duration': 1.0},
            'method': 'error_fallback'
        }


def handle_quantum_world(handler, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST /api/aria/world with use_quantum=true - Generate world using quantum computing."""
    if not QUANTUM_AVAILABLE or quantum_generate_world is None:
        return {
            'status': 'error',
            'message': 'Quantum world generation unavailable',
            'objects': {},
            'environment': {},
            'method': 'classical_fallback'
        }
    
    try:
        theme = request_data.get('theme', 'default')
        result = quantum_generate_world(theme)
        
        return {
            'status': 'success',
            **result
        }
    except Exception as e:
        logger.error(f"Quantum world generation error: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'objects': {},
            'environment': {},
            'method': 'error_fallback'
        }


def add_quantum_routes(handler):
    """
    Add quantum API routes to the request handler.
    
    This function extends the AriaRequestHandler with quantum-specific endpoints.
    Call it from do_GET and do_POST methods.
    
    Returns:
        True if route was handled, False otherwise
    """
    path = handler.path
    
    # GET routes
    if path == '/api/aria/quantum/state':
        result = handle_quantum_state(handler)
        handler.send_response(200)
        handler.send_header('Content-Type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(result).encode('utf-8'))
        return True
    
    # POST routes require reading body
    if path in ['/api/aria/quantum/predict', '/api/aria/world']:
        if handler.command != 'POST':
            return False
        
        try:
            content_length = int(handler.headers.get('Content-Length', 0))
            if content_length > 0:
                body = handler.rfile.read(content_length)
                request_data = json.loads(body.decode('utf-8'))
            else:
                request_data = {}
        except Exception as e:
            handler.send_response(400)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'error': f'Invalid JSON: {e}'}).encode('utf-8'))
            return True
        
        # Route to appropriate handler
        if path == '/api/aria/quantum/predict':
            result = handle_quantum_predict(handler, request_data)
        elif path == '/api/aria/world':
            # Check if quantum is requested
            if request_data.get('use_quantum', False):
                result = handle_quantum_world(handler, request_data)
            else:
                return False  # Let main handler deal with it
        else:
            return False
        
        handler.send_response(200)
        handler.send_header('Content-Type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(result).encode('utf-8'))
        return True
    
    return False
