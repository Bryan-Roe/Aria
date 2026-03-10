"""WebSocket server for real-time job updates"""
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
import websockets
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Track connected clients
clients = set()

# Job status cache
job_status_cache = {}

class JobFileHandler(FileSystemEventHandler):
    """Monitor job status files for changes"""
    
    def __init__(self, broadcast_func):
        self.broadcast = broadcast_func
        
    def on_modified(self, event):
        if event.src_path.endswith('.json') and 'status' in event.src_path:
            asyncio.run(self.broadcast_status_update(event.src_path))
    
    async def broadcast_status_update(self, file_path):
        """Broadcast status update to all connected clients"""
        try:
            with open(file_path, 'r') as f:
                status = json.load(f)
            
            message = {
                'type': 'job_update',
                'timestamp': datetime.now().isoformat(),
                'data': status
            }
            
            await broadcast_message(message)
        except Exception as e:
            print(f"Error broadcasting update: {e}")

async def broadcast_message(message):
    """Send message to all connected clients"""
    if clients:
        message_str = json.dumps(message)
        await asyncio.gather(
            *[client.send(message_str) for client in clients],
            return_exceptions=True
        )

async def handler(websocket, path):
    """Handle WebSocket connections"""
    # Register client
    clients.add(websocket)
    print(f"Client connected. Total clients: {len(clients)}")
    
    try:
        # Send initial status
        initial_status = get_current_status()
        await websocket.send(json.dumps({
            'type': 'initial_status',
            'timestamp': datetime.now().isoformat(),
            'data': initial_status
        }))
        
        # Keep connection alive and handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                
                if data.get('type') == 'ping':
                    await websocket.send(json.dumps({'type': 'pong'}))
                
                elif data.get('type') == 'request_status':
                    status = get_current_status()
                    await websocket.send(json.dumps({
                        'type': 'status_response',
                        'timestamp': datetime.now().isoformat(),
                        'data': status
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send(json.dumps({'type': 'error', 'message': 'Invalid JSON'}))
                
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Unregister client
        clients.remove(websocket)
        print(f"Client disconnected. Total clients: {len(clients)}")

def get_current_status():
    """Get current training job status"""
    status_dir = Path('data_out/autotrain')
    jobs = []
    
    if status_dir.exists():
        for status_file in status_dir.glob('**/status.json'):
            try:
                with open(status_file, 'r') as f:
                    job_data = json.load(f)
                    jobs.append(job_data)
            except Exception as e:
                print(f"Error reading {status_file}: {e}")
    
    return {
        'jobs': jobs,
        'timestamp': datetime.now().isoformat(),
        'active_count': len([j for j in jobs if j.get('status') == 'running'])
    }

async def periodic_heartbeat():
    """Send periodic heartbeat to keep connections alive"""
    while True:
        await asyncio.sleep(30)
        
        if clients:
            status = get_current_status()
            message = {
                'type': 'heartbeat',
                'timestamp': datetime.now().isoformat(),
                'data': status
            }
            await broadcast_message(message)

async def main():
    """Start WebSocket server and file watcher"""
    print("Starting WebSocket server on ws://localhost:8765")
    
    # Setup file system watcher
    observer = Observer()
    handler = JobFileHandler(broadcast_message)
    
    watch_dir = Path('data_out')
    if watch_dir.exists():
        observer.schedule(handler, str(watch_dir), recursive=True)
        observer.start()
        print(f"Watching {watch_dir} for changes...")
    
    # Start WebSocket server
    async with websockets.serve(handler, "localhost", 8765):
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(periodic_heartbeat())
        
        print("WebSocket server ready!")
        print("Connect clients to: ws://localhost:8765")
        
        # Run forever
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down WebSocket server...")
