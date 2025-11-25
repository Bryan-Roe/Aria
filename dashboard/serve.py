"""Simple HTTP server for training dashboard"""
import http.server
import socketserver
import webbrowser
import sys
import json
import yaml
import subprocess
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Import GPU monitoring
sys.path.insert(0, str(Path(__file__).parent))
from gpu_monitor import get_gpu_info, get_gpu_processes, get_system_resources

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        root_dir = Path(__file__).parent.parent
        
        # API: Training status
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            status_file = root_dir / 'data_out' / 'autotrain' / 'status.json'
            try:
                with open(status_file, 'r') as f:
                    data = json.load(f)
                self.wfile.write(json.dumps(data).encode())
            except Exception as e:
                error_data = {"error": str(e), "jobs": []}
                self.wfile.write(json.dumps(error_data).encode())
            return
        
        # API: List available datasets
        elif self.path == '/api/datasets':
            self.send_json_response(self.get_datasets())
            return
        
        # API: List trained models
        elif self.path == '/api/models':
            self.send_json_response(self.get_models())
            return
        
        # API: List training configs
        elif self.path == '/api/configs':
            self.send_json_response(self.get_configs())
            return
        
        # API: Get job details
        elif self.path.startswith('/api/job/'):
            job_name = self.path.split('/')[-1]
            self.send_json_response(self.get_job_details(job_name))
            return
        
        # API: Get training logs
        elif self.path.startswith('/api/logs/'):
            job_name = self.path.split('/')[-1]
            self.send_json_response(self.get_job_logs(job_name))
            return
        
        # API: GPU monitoring
        elif self.path == '/api/gpu':
            self.send_json_response(get_gpu_info())
            return
        
        # API: GPU processes
        elif self.path == '/api/gpu-processes':
            self.send_json_response({'processes': get_gpu_processes()})
            return
        
        # API: System resources
        elif self.path == '/api/system':
            self.send_json_response(get_system_resources())
            return
        
        # API: Training history/timeline
        elif self.path == '/api/history':
            self.send_json_response(self.get_training_history())
            return
        
        # Default file serving
        super().do_GET()
    
    def do_POST(self):
        root_dir = Path(__file__).parent.parent
        
        # API: Start training
        if self.path == '/api/start-training':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data.decode())
            result = self.start_training(params)
            self.send_json_response(result)
            return
        
        self.send_error(404)
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_datasets(self):
        root_dir = Path(__file__).parent.parent
        datasets_dir = root_dir / 'datasets' / 'chat'
        datasets = []
        
        try:
            for d in datasets_dir.iterdir():
                if d.is_dir():
                    train_file = d / 'train.json'
                    test_file = d / 'test.json'
                    if train_file.exists():
                        with open(train_file) as f:
                            train_data = json.load(f)
                        datasets.append({
                            'name': d.name,
                            'path': str(d.relative_to(root_dir)),
                            'train_samples': len(train_data),
                            'test_samples': len(json.load(open(test_file))) if test_file.exists() else 0
                        })
        except Exception as e:
            return {'error': str(e), 'datasets': []}
        
        return {'datasets': datasets}
    
    def get_models(self):
        root_dir = Path(__file__).parent.parent
        models_dir = root_dir / 'data_out' / 'lora_training' / 'marathon'
        models = []
        
        try:
            if models_dir.exists():
                for model_dir in models_dir.iterdir():
                    if model_dir.is_dir():
                        adapter_config = model_dir / 'lora_adapter' / 'adapter_config.json'
                        if adapter_config.exists():
                            with open(adapter_config) as f:
                                config = json.load(f)
                            models.append({
                                'name': model_dir.name,
                                'path': str(model_dir.relative_to(root_dir)),
                                'base_model': config.get('base_model_name_or_path', 'unknown'),
                                'rank': config.get('r', 'unknown')
                            })
        except Exception as e:
            return {'error': str(e), 'models': []}
        
        return {'models': models}
    
    def get_configs(self):
        root_dir = Path(__file__).parent.parent
        configs = []
        
        try:
            for yaml_file in root_dir.glob('autotrain*.yaml'):
                if 'autogen' not in yaml_file.name:
                    with open(yaml_file) as f:
                        config = yaml.safe_load(f)
                    configs.append({
                        'name': yaml_file.stem,
                        'path': yaml_file.name,
                        'jobs': len(config.get('jobs', []))
                    })
        except Exception as e:
            return {'error': str(e), 'configs': []}
        
        return {'configs': configs}
    
    def get_job_details(self, job_name):
        root_dir = Path(__file__).parent.parent
        status_file = root_dir / 'data_out' / 'autotrain' / 'status.json'
        
        try:
            with open(status_file) as f:
                data = json.load(f)
            
            for job in data.get('jobs', []):
                if job.get('name') == job_name:
                    # Add output directory contents if available
                    if 'output_dir' in job and job['output_dir']:
                        output_path = root_dir / job['output_dir']
                        if output_path.exists():
                            job['output_files'] = [f.name for f in output_path.rglob('*') if f.is_file()]
                    return {'job': job}
            
            return {'error': 'Job not found'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_job_logs(self, job_name):
        root_dir = Path(__file__).parent.parent
        status_file = root_dir / 'data_out' / 'autotrain' / 'status.json'
        
        try:
            with open(status_file) as f:
                data = json.load(f)
            
            for job in data.get('jobs', []):
                if job.get('name') == job_name and 'log' in job:
                    log_file = Path(job['log'])
                    if log_file.exists():
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            # Get last 500 lines
                            lines = f.readlines()
                            return {'logs': ''.join(lines[-500:])}
            
            return {'logs': 'No logs available'}
        except Exception as e:
            return {'error': str(e), 'logs': ''}
    
    def start_training(self, params):
        # This would start a training job - simplified version
        config = params.get('config')
        job_name = params.get('job_name')
        
        try:
            # In a real implementation, this would launch autotrain.py with the config
            return {
                'status': 'started',
                'message': f'Training job {job_name} queued',
                'job_name': job_name
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_training_history(self):
        """Get historical training data for charts"""
        root_dir = Path(__file__).parent.parent
        status_file = root_dir / 'data_out' / 'autotrain' / 'status.json'
        
        try:
            with open(status_file) as f:
                data = json.load(f)
            
            history = {
                'jobs': [],
                'timeline': []
            }
            
            for job in data.get('jobs', []):
                if job.get('metrics'):
                    history['jobs'].append({
                        'name': job['name'],
                        'pre_loss': job['metrics'].get('pre_eval_loss'),
                        'post_loss': job['metrics'].get('post_eval_loss'),
                        'pre_perplexity': job['metrics'].get('pre_eval_perplexity'),
                        'post_perplexity': job['metrics'].get('post_eval_perplexity'),
                        'duration': job.get('duration_sec'),
                        'status': job.get('status')
                    })
                
                if job.get('start_time'):
                    history['timeline'].append({
                        'name': job['name'],
                        'start': job['start_time'],
                        'duration': job.get('duration_sec', 0),
                        'status': job.get('status', 'unknown')
                    })
            
            return history
        except Exception as e:
            return {'error': str(e), 'jobs': [], 'timeline': []}
    
    def end_headers(self):
        # Enable CORS for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def main():
    # Change to dashboard directory
    dashboard_dir = Path(__file__).parent
    import os
    os.chdir(dashboard_dir)
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"🚀 QAI Training Dashboard")
        print(f"=" * 50)
        print(f"Server running at: {url}")
        print(f"Press Ctrl+C to stop")
        print(f"=" * 50)
        
        # Open browser
        try:
            webbrowser.open(url)
        except:
            pass
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ Dashboard server stopped")
            sys.exit(0)

if __name__ == "__main__":
    main()
