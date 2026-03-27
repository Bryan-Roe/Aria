"""Simple HTTP server for training dashboard"""
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import random
import re
import os
import time
import subprocess
import yaml
import json
import webbrowser
import socketserver
import http.server
from vram_calculator import calculate_safe_batch_size
from gpu_monitor import get_gpu_info, get_gpu_processes, get_system_resources
import sys
from pathlib import Path
# Make scripts/ importable when serve.py is run from apps/dashboard/
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

# Import GPU monitoring
sys.path.insert(0, str(Path(__file__).parent))

PORT = 8000
REPO_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DIR = Path(__file__).resolve().parent

# Simple rate limiting
request_counts = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 60


class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        # Always serve static dashboard assets from apps/dashboard.
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def log_request(self, code='-', size='-'):
        """Enhanced request logging with timestamps"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {self.command} {self.path} - {code}")

    def check_rate_limit(self):
        """Simple rate limiting per IP"""
        client_ip = self.client_address[0]
        now = time.time()

        # Clean old requests (older than 1 minute)
        request_counts[client_ip] = [
            t for t in request_counts[client_ip] if now - t < 60]

        # Check limit
        if len(request_counts[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
            return False

        request_counts[client_ip].append(now)
        return True

    def do_GET(self):
        # Check rate limit
        if not self.check_rate_limit():
            self.send_error(429, "Too Many Requests")
            return

        # Use the root_dir set by main()
        root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)

        # Redirect root to consolidated dashboard
        if self.path == '/' or self.path == '/index.html':
            self.send_response(302)
            self.send_header('Location', '/consolidated.html')
            self.end_headers()
            return

        # API: Training status (no cache)
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header(
                'Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()

            status_file = root_dir / 'data_out' / 'autotrain' / 'status.json'
            try:
                with open(status_file, 'r') as f:
                    data = json.load(f)
                data['server_time'] = datetime.now().isoformat()
                self.wfile.write(json.dumps(data).encode())
            except FileNotFoundError:
                error_data = {
                    "error": "Status file not found. No training jobs have been run yet.",
                    "jobs": [],
                    "server_time": datetime.now().isoformat()
                }
                self.wfile.write(json.dumps(error_data).encode())
            except Exception as e:
                error_data = {
                    "error": f"Failed to read status: {str(e)}",
                    "jobs": [],
                    "server_time": datetime.now().isoformat()
                }
                self.wfile.write(json.dumps(error_data).encode())
            return

        # API: Job progress
        if self.path.startswith('/api/job-progress/'):
            job_id = self.path.split('/')[-1]
            self.send_json_response(self.get_job_progress(job_id))
            return

        # API: Job metrics
        if self.path.startswith('/api/job-metrics/'):
            job_id = self.path.split('/')[-1]
            self.send_json_response(self.get_job_metrics(job_id))
            return

        # API: List available datasets
        elif self.path == '/api/datasets':
            self.send_json_response(self.get_datasets())
            return

        # API: Profile dataset for hyperparameter recommendations
        elif self.path.startswith('/api/profile-dataset'):
            parsed = urlparse(self.path)
            query_params = parse_qs(parsed.query)
            dataset_name = query_params.get('dataset', [None])[0]

            if not dataset_name:
                self.send_json_response({"error": "Missing dataset parameter"})
                return

            # Find dataset path
            datasets = self.get_datasets()
            dataset_path = None
            for ds in datasets.get('datasets', []):
                if ds.get('name') == dataset_name or ds.get('path', '').endswith(dataset_name):
                    dataset_path = Path(ds['path'])
                    break

            if not dataset_path or not dataset_path.exists():
                self.send_json_response(
                    {"error": f"Dataset not found: {dataset_name}"})
                return

            # Run profiler script
            profiler_script = root_dir / 'scripts' / 'dataset_profiler.py'
            if not profiler_script.exists():
                self.send_json_response({"error": "Profiler script not found"})
                return

            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, str(profiler_script), str(
                        dataset_path), '--recommend', '--quiet'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    profile_data = json.loads(result.stdout)
                    self.send_json_response(profile_data)
                else:
                    self.send_json_response(
                        {"error": f"Profiler failed: {result.stderr}"})
            except subprocess.TimeoutExpired:
                self.send_json_response(
                    {"error": "Profiler timed out (30s limit)"})
            except Exception as e:
                self.send_json_response({"error": f"Profiler error: {str(e)}"})
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

        # API: VRAM-aware batch size calculator
        elif self.path.startswith('/api/vram-info'):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)

            def _qs(key, default=''):
                vals = qs.get(key, [default])
                return vals[0] if vals else default
            model = _qs('model', '')
            params_b_str = _qs('params_b', '')
            params_b = float(params_b_str) if params_b_str else None
            lora_rank = int(_qs('lora_rank', '16'))
            seq_len = int(_qs('seq_len', '512'))
            dtype = _qs('dtype', 'fp16')
            self.send_json_response(calculate_safe_batch_size(
                model_name=model,
                params_b=params_b,
                lora_rank=lora_rank,
                seq_len=seq_len,
                dtype=dtype,
            ))
            return

        # API: System resources
        elif self.path == '/api/system':
            self.send_json_response(get_system_resources())
            return

        # API: Training history/timeline
        elif self.path == '/api/history':
            self.send_json_response(self.get_training_history())
            return

        # API: System health check
        elif self.path == '/api/health':
            self.send_json_response(self.get_system_health())
            return

        # API: Quick stats summary
        elif self.path == '/api/stats':
            self.send_json_response(self.get_quick_stats())
            return

        # API: Get active processes
        elif self.path == '/api/processes':
            self.send_json_response(self.get_active_processes())
            return

        # API: Job queue status
        elif self.path == '/api/job-queue':
            self.send_json_response(self.get_job_queue_status())
            return

        # Default file serving
        super().do_GET()

    def do_POST(self):
        # Use the root_dir set by main()
        root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)

        # API: Start training
        if self.path == '/api/start-training':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data.decode())
            result = self.start_training(params)
            self.send_json_response(result)
            return

        # API: Pause job
        if self.path.startswith('/api/job-control/') and self.path.endswith('/pause'):
            job_id = self.path.split('/')[-2]
            result = self.control_job(job_id, action='pause')
            self.send_json_response(result)
            return

        # API: Stop job
        if self.path.startswith('/api/job-control/') and self.path.endswith('/stop'):
            job_id = self.path.split('/')[-2]
            result = self.control_job(job_id, action='stop')
            self.send_json_response(result)
            return

        # API: Benchmark models
        if self.path == '/api/benchmark':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data.decode())
            model_ids = params.get('model_ids', [])
            results = self.run_benchmark(model_ids)
            self.send_json_response({'results': results})
            return

        self.send_error(404)

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def get_job_progress(self, job_id):
        """Return job progress information"""
        root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)
        status_file = root_dir / 'data_out' / 'autotrain' / 'status.json'
        try:
            with open(status_file, 'r') as f:
                data = json.load(f)
            job = next((j for j in data.get('jobs', [])
                       if j.get('name') == job_id), None)
            if not job:
                return {'error': 'Job not found', 'job_id': job_id}

            metrics = job.get('metrics', {})
            current_epoch = job.get('current_epoch') or metrics.get(
                'current_epoch') or 0
            total_epochs = job.get('epochs') or job.get(
                'config', {}).get('epochs') or 0
            post_loss = metrics.get('post_eval_loss')
            current_loss = metrics.get('current_loss', post_loss)
            lr = job.get('config', {}).get(
                'learning_rate') or metrics.get('learning_rate')
            steps_per_sec = metrics.get('steps_per_sec')
            status = job.get('status', 'unknown')
            duration = job.get('duration_sec')

            # Progress percent
            progress_percent = job.get('progress_percent')
            if progress_percent is None:
                try:
                    progress_percent = round(
                        (current_epoch / total_epochs) * 100, 2) if total_epochs else 0
                except Exception:
                    progress_percent = 0

            return {
                'job_id': job_id,
                'current_epoch': current_epoch,
                'total_epochs': total_epochs,
                'current_loss': current_loss,
                'learning_rate': lr,
                'steps_per_sec': steps_per_sec,
                'progress_percent': progress_percent,
                'status': status,
                'duration_sec': duration
            }
        except Exception as e:
            return {'error': str(e), 'job_id': job_id}

    def get_job_metrics(self, job_id):
        """Return arrays for charting training/validation loss"""
        root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)
        status_file = root_dir / 'data_out' / 'autotrain' / 'status.json'
        steps = []
        train_loss = []
        eval_loss = []
        try:
            with open(status_file, 'r') as f:
                data = json.load(f)
            job = next((j for j in data.get('jobs', [])
                       if j.get('name') == job_id), None)
            if not job:
                return {'error': 'Job not found', 'job_id': job_id}

            # Try metrics history
            history = job.get('metrics_history') or job.get('loss_history')
            if isinstance(history, list) and history:
                for i, h in enumerate(history):
                    steps.append(h.get('step', i))
                    if 'train_loss' in h:
                        train_loss.append(h['train_loss'])
                    if 'eval_loss' in h:
                        eval_loss.append(h['eval_loss'])
            else:
                # Fallback: parse log file for loss lines
                log_file = job.get('log')
                if log_file and Path(log_file).exists():
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            for i, line in enumerate(f):
                                m = re.search(
                                    r'step\s*(\d+).*?train_loss=([0-9\.]+).*?eval_loss=([0-9\.]+)', line)
                                if m:
                                    steps.append(int(m.group(1)))
                                    train_loss.append(float(m.group(2)))
                                    eval_loss.append(float(m.group(3)))
                    except Exception:
                        pass

            return {
                'job_id': job_id,
                'steps': steps,
                'train_loss': train_loss,
                'eval_loss': eval_loss
            }
        except Exception as e:
            return {'error': str(e), 'job_id': job_id, 'steps': steps, 'train_loss': train_loss, 'eval_loss': eval_loss}

    def get_datasets(self):
        # Use the root_dir set by main()
        root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)
        datasets_dir = root_dir / 'datasets' / 'chat'
        datasets = []

        try:
            if not datasets_dir.exists():
                return {'error': f'Datasets directory not found: {datasets_dir}', 'datasets': []}

            for d in datasets_dir.iterdir():
                if d.is_dir():
                    train_file = d / 'train.json'
                    test_file = d / 'test.json'
                    if train_file.exists():
                        try:
                            # Count samples efficiently without loading entire file
                            # For JSON arrays, count top-level elements
                            train_samples = self._count_json_samples(
                                train_file)
                            test_samples = 0
                            if test_file.exists():
                                test_samples = self._count_json_samples(
                                    test_file)

                            datasets.append({
                                'name': d.name,
                                'path': str(d.relative_to(root_dir)),
                                'train_samples': train_samples,
                                'test_samples': test_samples
                            })
                        except Exception as e:
                            print(
                                f"Warning: Error processing {train_file}: {e}")
                            continue
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'error': str(e), 'datasets': []}

        return {'datasets': datasets}

    def _count_json_samples(self, file_path: Path) -> int:
        """Count samples in a JSON file efficiently.

        For JSONL files: counts lines.
        For JSON arrays: counts top-level array elements.
        Falls back to loading full file if needed.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_char = f.read(1)
                f.seek(0)

                if first_char == '[':
                    # JSON array - need to parse it
                    data = json.load(f)
                    return len(data) if isinstance(data, list) else 1
                elif first_char == '{':
                    # JSONL format - count lines efficiently
                    return sum(1 for line in f if line.strip())
                else:
                    # Unknown format, try to parse
                    data = json.load(f)
                    return len(data) if isinstance(data, list) else 1
        except Exception:
            # Fallback: try loading as JSON
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return len(data) if isinstance(data, list) else 1
            except Exception:
                return 0

    def get_models(self):
        # Use the root_dir set by main()
        root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)
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
        # Use the root_dir set by main()
        root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)
        configs = []

        try:
            for yaml_file in root_dir.glob('autotrain*.yaml'):
                if 'autogen' not in yaml_file.name:
                    with open(yaml_file) as f:
                        config = yaml.safe_load(f)

                    jobs = config.get('jobs', [])
                    total_epochs = sum(j.get('epochs', 0) for j in jobs)

                    # Estimate time based on previous runs
                    estimated_minutes = len(jobs) * 3  # Rough estimate
                    est_time = f"{estimated_minutes}m" if estimated_minutes < 60 else f"{estimated_minutes//60}h {estimated_minutes % 60}m"

                    configs.append({
                        'name': yaml_file.stem,
                        'path': yaml_file.name,
                        'jobs': len(jobs),
                        'total_epochs': total_epochs,
                        'estimated_time': est_time,
                        'modified': yaml_file.stat().st_mtime
                    })

            # Sort by modification time
            configs.sort(key=lambda x: x.get('modified', 0), reverse=True)
        except Exception as e:
            return {'error': str(e), 'configs': []}

        return {'configs': configs}

    def get_job_details(self, job_name):
        # Use the root_dir set by main()
        root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)
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
                            job['output_files'] = [
                                f.name for f in output_path.rglob('*') if f.is_file()]
                    return {'job': job}

            return {'error': 'Job not found'}
        except Exception as e:
            return {'error': str(e)}

    def get_job_logs(self, job_name):
        # Use the root_dir set by main()
        root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)
        status_file = root_dir / 'data_out' / 'autotrain' / 'status.json'

        try:
            with open(status_file) as f:
                data = json.load(f)

            for job in data.get('jobs', []):
                if job.get('name') == job_name and 'log' in job:
                    log_file = Path(job['log'])
                    if log_file.exists():
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            # Efficiently tail last 500 lines without loading entire file
                            lines = []
                            for line in f:
                                lines.append(line)
                                if len(lines) > 500:
                                    lines.pop(0)  # Keep only last 500
                            return {'logs': ''.join(lines)}

            return {'logs': 'No logs available'}
        except Exception as e:
            return {'error': str(e), 'logs': ''}

    def start_training(self, params):
        """Create and queue a new training job"""
        # Use the root_dir set by main()
        root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)

        try:
            # Accept both legacy and new parameter names
            job_name = params.get('job_name') or params.get('name')
            model = params.get('model') or 'microsoft/Phi-3.5-mini-instruct'
            dataset = params.get('dataset')
            epochs = params.get('epochs', 3)
            max_samples = params.get(
                'max_train_samples', params.get('max_samples', 1000))
            learning_rate = params.get('learning_rate', '2e-4')
            batch_size = params.get('batch_size', 4)
            lora_rank = params.get('lora_rank', 16)
            lora_alpha = params.get('lora_alpha', 32)

            if not job_name or not dataset:
                return {'success': False, 'error': 'Missing required parameters'}

            # Create a custom config YAML
            config_data = {
                'jobs': [{
                    'name': job_name,
                    'runner': 'hf',
                    'category': 'custom',
                    'model': model,
                    'dataset': f'datasets/chat/{dataset}',
                    'epochs': epochs,
                    'max_train_samples': max_samples,
                    'learning_rate': float(learning_rate),
                    'batch_size': batch_size,
                    'lora_rank': lora_rank,
                    'lora_alpha': lora_alpha,
                    'device': 'auto'
                }]
            }

            # Save config
            config_file = root_dir / f'autotrain_custom_{job_name}.yaml'
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)

            # Launch training in background
            cmd = [
                'python',
                str(root_dir / 'scripts' / 'autotrain.py'),
                '--config',
                str(config_file),
                '--resume'
            ]

            subprocess.Popen(
                cmd,
                cwd=str(root_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(
                    subprocess, 'CREATE_NO_WINDOW') else 0
            )

            return {
                'success': True,
                'message': f'Training job {job_name} started',
                'job_name': job_name,
                'job_id': job_name,
                'config_file': config_file.name
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def control_job(self, job_id, action='pause'):
        """Stub to control a job (pause/stop) via flag files"""
        try:
            root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)
            control_dir = root_dir / 'data_out' / 'control'
            control_dir.mkdir(parents=True, exist_ok=True)
            flag_file = control_dir / f'{job_id}.{action}'
            with open(flag_file, 'w') as f:
                f.write(datetime.now().isoformat())
            return {'success': True, 'message': f'Job {action} signal sent', 'job_id': job_id}
        except Exception as e:
            return {'success': False, 'error': str(e), 'job_id': job_id}

    def run_benchmark(self, model_ids):
        """Run a simple synthetic benchmark for models"""
        results = []
        for mid in model_ids:
            try:
                # Synthetic metrics
                inference_time = random.uniform(100, 1200)  # ms
                memory_mb = random.uniform(200, 2000)
                throughput = random.uniform(20, 300)  # tokens/sec
                # Score: lower time & memory, higher throughput
                speed_score = max(0, min(100, (1200 - inference_time) / 12))
                memory_score = max(0, min(100, (2000 - memory_mb) / 20))
                throughput_score = max(0, min(100, throughput / 3))
                score = round(
                    (speed_score + memory_score + throughput_score) / 3, 2)
                results.append({
                    'model_id': mid,
                    'model_name': mid,
                    'inference_time': round(inference_time, 1),
                    'memory_mb': round(memory_mb, 1),
                    'throughput': round(throughput, 1),
                    'score': score
                })
            except Exception as e:
                results.append({'model_id': mid, 'error': str(e)})
        return results

    def get_training_history(self):
        """Get historical training data for charts"""
        # Use the root_dir set by main()
        root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)
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

    def get_system_health(self):
        """Comprehensive system health check"""
        root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)

        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }

        try:
            # Check datasets directory
            datasets_dir = root_dir / 'datasets' / 'chat'
            health['checks']['datasets'] = {
                'exists': datasets_dir.exists(),
                'count': len(list(datasets_dir.glob('*/train.json'))) if datasets_dir.exists() else 0
            }

            # Check output directory
            output_dir = root_dir / 'data_out'
            health['checks']['output'] = {
                'exists': output_dir.exists(),
                'writable': os.access(output_dir, os.W_OK) if output_dir.exists() else False
            }

            # Check GPU availability
            gpu_info = get_gpu_info()
            health['checks']['gpu'] = {
                'available': len(gpu_info.get('gpus', [])) > 0,
                'count': len(gpu_info.get('gpus', []))
            }

            # Check virtual environments
            health['checks']['venvs'] = {
                'quantum_ai': (root_dir / 'ai-projects' / 'quantum-ml' / 'venv').exists(),
                'talk_to_ai': (root_dir / 'ai-projects' / 'chat-cli' / 'venv').exists(),
                'lora_training': (root_dir / 'AI' / 'microsoft_phi-silica-3.6_v1' / 'venv').exists()
            }

            # Overall health
            all_checks = [
                health['checks']['datasets']['exists'],
                health['checks']['output']['exists'],
                any(health['checks']['venvs'].values())
            ]
            health['status'] = 'healthy' if all(all_checks) else 'degraded'

        except Exception as e:
            health['status'] = 'error'
            health['error'] = str(e)

        return health

    def get_quick_stats(self):
        """Quick summary statistics"""
        root_dir = getattr(self.__class__, 'root_dir', REPO_ROOT)

        stats = {
            'training_jobs': 0,
            'datasets': 0,
            'models': 0,
            'gpu_usage': 0,
            'active_processes': 0
        }

        try:
            # Training jobs
            status_file = root_dir / 'data_out' / 'autotrain' / 'status.json'
            if status_file.exists():
                with open(status_file) as f:
                    data = json.load(f)
                stats['training_jobs'] = len(data.get('jobs', []))

            # Datasets
            datasets_dir = root_dir / 'datasets' / 'chat'
            if datasets_dir.exists():
                stats['datasets'] = len(
                    [d for d in datasets_dir.iterdir() if d.is_dir()])

            # Models
            models_dir = root_dir / 'data_out' / 'lora_training' / 'marathon'
            if models_dir.exists():
                stats['models'] = len(
                    [m for m in models_dir.iterdir() if m.is_dir()])

            # GPU usage
            gpu_info = get_gpu_info()
            if gpu_info.get('gpus'):
                stats['gpu_usage'] = gpu_info['gpus'][0].get(
                    'utilization_gpu', 0)

            # Active processes
            processes = get_gpu_processes()
            stats['active_processes'] = len(processes)

        except Exception as e:
            stats['error'] = str(e)

        return stats

    def get_active_processes(self):
        """Get active Python processes"""
        import psutil

        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['name'] and 'python' in pinfo['name'].lower():
                        cmdline = ' '.join(pinfo['cmdline'] or [])
                        if any(keyword in cmdline for keyword in ['train', 'autotrain', 'quantum', 'chat', 'serve']):
                            processes.append({
                                'pid': pinfo['pid'],
                                'name': pinfo['name'],
                                'command': cmdline[:100] + '...' if len(cmdline) > 100 else cmdline,
                                'memory_mb': round(pinfo['memory_info'].rss / 1024 / 1024, 1),
                                'cpu_percent': pinfo['cpu_percent']
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            return {'error': str(e), 'processes': []}

        return {'processes': processes, 'count': len(processes)}

    def get_job_queue_status(self):
        """Get job queue status from job_queue.py"""
        try:
            queue_file = Path('data_out/job_queue.json')
            if not queue_file.exists():
                return {
                    'total_jobs': 0,
                    'pending': 0,
                    'running': 0,
                    'completed': 0,
                    'failed': 0,
                    'blocked': 0,
                    'cancelled': 0,
                    'queue_length': 0,
                    'estimated_total_time': 0,
                    'message': 'Job queue not initialized'
                }

            with open(queue_file, 'r') as f:
                queue_data = json.load(f)

            jobs = queue_data.get('jobs', [])

            # Single-pass aggregation to avoid multiple iterations (optimized)
            status_counts = {'pending': 0, 'running': 0,
                             'completed': 0, 'failed': 0, 'blocked': 0, 'cancelled': 0}
            queue_jobs = []
            estimated_total = 0

            for job in jobs:
                status = job.get('status')
                if status in status_counts:
                    status_counts[status] += 1
                if status in {'pending', 'blocked'}:
                    queue_jobs.append(job)
                    estimated_total += job.get('estimated_duration', 0)

            return {
                'total_jobs': len(jobs),
                'pending': status_counts['pending'],
                'running': status_counts['running'],
                'completed': status_counts['completed'],
                'failed': status_counts['failed'],
                'blocked': status_counts['blocked'],
                'cancelled': status_counts['cancelled'],
                'queue_length': len(queue_jobs),
                'estimated_total_time': estimated_total,
                'updated_at': queue_data.get('updated_at')
            }
        except Exception as e:
            return {'error': str(e), 'total_jobs': 0}

    def end_headers(self):
        # Enable CORS for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header(
            'Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()


def main():
    # Use repository root for all API file lookups.
    root_dir = REPO_ROOT

    # Make root_dir available to handler
    MyHTTPRequestHandler.root_dir = root_dir

    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"🚀 QAI Training Dashboard")
        print(f"=" * 50)
        print(f"Server running at: {url}")
        print(f"Root directory: {root_dir}")
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
