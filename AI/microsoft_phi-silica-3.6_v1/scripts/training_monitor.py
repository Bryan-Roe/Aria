"""
Training Monitor & Dashboard
Real-time training progress monitoring with live metrics
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import threading
import queue


@dataclass
class TrainingMetrics:
    """Training metrics at a point in time"""
    step: int
    epoch: int
    loss: float
    learning_rate: float
    timestamp: str
    grad_norm: Optional[float] = None
    throughput: Optional[float] = None  # tokens/sec
    gpu_memory_mb: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrainingSession:
    """Complete training session information"""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: List[TrainingMetrics] = field(default_factory=list)
    status: str = "running"  # running, completed, failed
    total_steps: int = 0
    best_loss: float = float('inf')
    best_step: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "metrics": [m.to_dict() for m in self.metrics]
        }


class TrainingMonitor:
    """Monitor and track training progress"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or f"training_{int(time.time())}"
        self.session = TrainingSession(
            session_id=self.session_id,
            start_time=datetime.now().isoformat()
        )
        
        self.log_dir = Path("data_out/training_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / f"{self.session_id}.jsonl"
        self.summary_file = self.log_dir / f"{self.session_id}_summary.json"
        
        self.metrics_queue = queue.Queue()
        self.should_stop = threading.Event()
        self.writer_thread = threading.Thread(target=self._write_metrics_worker, daemon=True)
        self.writer_thread.start()
    
    def log_metrics(
        self,
        step: int,
        epoch: int,
        loss: float,
        learning_rate: float,
        **kwargs
    ):
        """Log training metrics"""
        metrics = TrainingMetrics(
            step=step,
            epoch=epoch,
            loss=loss,
            learning_rate=learning_rate,
            timestamp=datetime.now().isoformat(),
            grad_norm=kwargs.get('grad_norm'),
            throughput=kwargs.get('throughput'),
            gpu_memory_mb=kwargs.get('gpu_memory_mb')
        )
        
        self.session.metrics.append(metrics)
        self.session.total_steps = step
        
        # Track best loss
        if loss < self.session.best_loss:
            self.session.best_loss = loss
            self.session.best_step = step
        
        # Queue for async writing
        self.metrics_queue.put(metrics)
    
    def update_config(self, config: Dict[str, Any]):
        """Update training configuration"""
        self.session.config.update(config)
    
    def complete(self, status: str = "completed"):
        """Mark training as complete"""
        self.session.status = status
        self.session.end_time = datetime.now().isoformat()
        self._save_summary()
        
        # Stop writer thread
        self.should_stop.set()
        self.writer_thread.join(timeout=5)
    
    def _write_metrics_worker(self):
        """Background worker to write metrics"""
        while not self.should_stop.is_set():
            try:
                metrics = self.metrics_queue.get(timeout=1)
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(metrics.to_dict()) + '\n')
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error writing metrics: {e}")
    
    def _save_summary(self):
        """Save training summary"""
        with open(self.summary_file, 'w') as f:
            json.dump(self.session.to_dict(), f, indent=2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current training statistics"""
        if not self.session.metrics:
            return {}
        
        recent_losses = [m.loss for m in self.session.metrics[-100:]]
        recent_throughputs = [m.throughput for m in self.session.metrics[-100:] if m.throughput]
        
        return {
            "total_steps": self.session.total_steps,
            "current_loss": self.session.metrics[-1].loss if self.session.metrics else None,
            "best_loss": self.session.best_loss,
            "best_step": self.session.best_step,
            "avg_recent_loss": sum(recent_losses) / len(recent_losses) if recent_losses else None,
            "avg_throughput": sum(recent_throughputs) / len(recent_throughputs) if recent_throughputs else None,
            "duration": self._get_duration()
        }
    
    def _get_duration(self) -> str:
        """Get training duration"""
        start = datetime.fromisoformat(self.session.start_time)
        end = datetime.fromisoformat(self.session.end_time) if self.session.end_time else datetime.now()
        duration = end - start
        
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        seconds = int(duration.total_seconds() % 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def print_progress(self, step: int, total_steps: int):
        """Print training progress"""
        stats = self.get_stats()
        progress = (step / total_steps * 100) if total_steps > 0 else 0
        
        print(f"\rStep {step}/{total_steps} ({progress:.1f}%) | "
              f"Loss: {stats.get('current_loss', 'N/A'):.4f} | "
              f"Best: {stats['best_loss']:.4f} @ {stats['best_step']} | "
              f"Duration: {stats['duration']}", end='')
    
    @staticmethod
    def load_session(session_id: str) -> Optional[TrainingSession]:
        """Load a previous training session"""
        summary_file = Path(f"data_out/training_logs/{session_id}_summary.json")
        
        if not summary_file.exists():
            return None
        
        with open(summary_file) as f:
            data = json.load(f)
        
        # Reconstruct session
        session = TrainingSession(
            session_id=data['session_id'],
            start_time=data['start_time'],
            end_time=data.get('end_time'),
            config=data.get('config', {}),
            status=data.get('status', 'unknown'),
            total_steps=data.get('total_steps', 0),
            best_loss=data.get('best_loss', float('inf')),
            best_step=data.get('best_step', 0)
        )
        
        # Load metrics
        session.metrics = [
            TrainingMetrics(**m) for m in data.get('metrics', [])
        ]
        
        return session
    
    @staticmethod
    def list_sessions() -> List[str]:
        """List all training sessions"""
        log_dir = Path("data_out/training_logs")
        if not log_dir.exists():
            return []
        
        sessions = []
        for file in log_dir.glob("*_summary.json"):
            session_id = file.stem.replace('_summary', '')
            sessions.append(session_id)
        
        return sorted(sessions, reverse=True)


class LiveDashboard:
    """Live training dashboard (terminal-based)"""
    
    def __init__(self, monitor: TrainingMonitor):
        self.monitor = monitor
        self.running = False
        self.dashboard_thread = None
    
    def start(self):
        """Start the dashboard"""
        self.running = True
        self.dashboard_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.dashboard_thread.start()
    
    def stop(self):
        """Stop the dashboard"""
        self.running = False
        if self.dashboard_thread:
            self.dashboard_thread.join(timeout=2)
    
    def _update_loop(self):
        """Update loop for dashboard"""
        while self.running:
            self._render_dashboard()
            time.sleep(5)  # Update every 5 seconds
    
    def _render_dashboard(self):
        """Render the dashboard"""
        stats = self.monitor.get_stats()
        
        # Clear screen (simple version)
        print("\033[2J\033[H")  # ANSI escape codes
        
        print("=" * 80)
        print(f"TRAINING DASHBOARD - Session: {self.monitor.session_id}")
        print("=" * 80)
        
        print(f"\nDuration: {stats.get('duration', 'N/A')}")
        print(f"Status: {self.monitor.session.status.upper()}")
        
        print(f"\n📊 Progress:")
        print(f"  Total Steps: {stats.get('total_steps', 0):,}")
        print(f"  Current Loss: {stats.get('current_loss', 'N/A')}")
        print(f"  Best Loss: {stats.get('best_loss', float('inf')):.4f} (step {stats.get('best_step', 0)})")
        print(f"  Avg Recent Loss: {stats.get('avg_recent_loss', 'N/A')}")
        
        if stats.get('avg_throughput'):
            print(f"\n⚡ Performance:")
            print(f"  Throughput: {stats['avg_throughput']:.1f} tokens/sec")
        
        # Show recent metrics
        recent = self.monitor.session.metrics[-5:]
        if recent:
            print(f"\n📈 Recent Metrics:")
            print(f"  {'Step':<8} {'Loss':<10} {'LR':<12} {'Time':<12}")
            print(f"  {'-'*8} {'-'*10} {'-'*12} {'-'*12}")
            for m in recent:
                timestamp = m.timestamp.split('T')[1][:8]
                print(f"  {m.step:<8} {m.loss:<10.4f} {m.learning_rate:<12.6f} {timestamp:<12}")
        
        print("\n" + "=" * 80)


def main():
    """CLI for training monitor"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Training Monitor")
    parser.add_argument("--list", action="store_true", help="List all sessions")
    parser.add_argument("--session", type=str, help="View specific session")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    if args.list:
        sessions = TrainingMonitor.list_sessions()
        print("Available training sessions:")
        for session_id in sessions:
            print(f"  - {session_id}")
    
    elif args.session:
        session = TrainingMonitor.load_session(args.session)
        if session:
            print(f"\nSession: {session.session_id}")
            print(f"Status: {session.status}")
            print(f"Duration: {session.start_time} to {session.end_time}")
            print(f"Total Steps: {session.total_steps}")
            print(f"Best Loss: {session.best_loss:.4f} @ step {session.best_step}")
            print(f"Total Metrics: {len(session.metrics)}")
        else:
            print(f"Session not found: {args.session}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
