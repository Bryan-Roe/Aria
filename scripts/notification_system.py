"""Desktop Notification System for QAI Training Events"""
import os
import platform
import subprocess  # nosec B404 - subprocess used safely with list arguments, no shell=True
from datetime import datetime
from typing import Optional
from pathlib import Path

class NotificationManager:
    """Cross-platform desktop notifications for training events"""
    
    def __init__(self):
        self.system = platform.system()
        self.enabled = self._check_notification_support()
        
    def _check_notification_support(self) -> bool:
        """Check if notifications are supported on this platform"""
        if self.system == "Windows":
            try:
                from win10toast import ToastNotifier
                self.toaster = ToastNotifier()
                return True
            except ImportError:
                print("Warning: win10toast not installed. Install with: pip install win10toast")
                return False
        elif self.system == "Darwin":  # macOS
            return True  # Uses osascript
        elif self.system == "Linux":
            return True  # Uses notify-send
        return False
    
    def send_notification(
        self,
        title: str,
        message: str,
        icon: str = "info",
        duration: int = 10
    ):
        """Send cross-platform desktop notification"""
        if not self.enabled:
            print(f"[Notification] {title}: {message}")
            return
        
        try:
            if self.system == "Windows":
                self._send_windows(title, message, icon, duration)
            elif self.system == "Darwin":
                self._send_macos(title, message)
            elif self.system == "Linux":
                self._send_linux(title, message, icon)
        except Exception as e:
            print(f"Notification error: {e}")
    
    def _send_windows(self, title: str, message: str, icon: str, duration: int):
        """Send Windows 10 toast notification"""
        icon_path = None
        if icon == "success":
            # Use default Windows icon or provide custom path
            pass
        
        self.toaster.show_toast(
            title=title,
            msg=message,
            icon_path=icon_path,
            duration=duration,
            threaded=True
        )
    
    def _send_macos(self, title: str, message: str):
        """Send macOS notification using osascript"""
        # For AppleScript strings, we need to escape backslashes and double quotes
        # Also replace newlines with spaces to prevent script injection
        safe_title = title.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
        safe_message = message.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
        
        script = f'display notification "{safe_message}" with title "{safe_title}"'
        try:
            # Using subprocess with list arguments prevents shell injection
            # The script is passed as a single argument to osascript -e
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                print(f"macOS notification warning: osascript returned {result.returncode}, stderr: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("macOS notification error: osascript timed out")
        except FileNotFoundError:
            print("macOS notification error: osascript not found")
        except OSError as e:
            print(f"macOS notification error: {e}")
    
    def _send_linux(self, title: str, message: str, icon: str):
        """Send Linux notification using notify-send"""
        icon_name = {
            "info": "dialog-information",
            "success": "dialog-ok",
            "warning": "dialog-warning",
            "error": "dialog-error"
        }.get(icon, "dialog-information")
        
        # Use subprocess with list arguments to prevent command injection
        try:
            result = subprocess.run(['notify-send', '-i', icon_name, title, message], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                print(f"Linux notification warning: notify-send returned {result.returncode}, stderr: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("Linux notification error: notify-send timed out")
        except FileNotFoundError:
            print("Linux notification error: notify-send not found")
        except OSError as e:
            print(f"Linux notification error: {e}")
    
    def notify_job_started(self, job_name: str):
        """Notify when training job starts"""
        self.send_notification(
            title="🚀 Training Started",
            message=f"Job '{job_name}' has begun training",
            icon="info"
        )
    
    def notify_job_completed(self, job_name: str, duration_min: int, final_loss: float):
        """Notify when training job completes successfully"""
        self.send_notification(
            title="✅ Training Complete",
            message=f"Job '{job_name}' finished in {duration_min}min with loss {final_loss:.4f}",
            icon="success",
            duration=15
        )
    
    def notify_job_failed(self, job_name: str, error: str):
        """Notify when training job fails"""
        self.send_notification(
            title="❌ Training Failed",
            message=f"Job '{job_name}' failed: {error[:100]}",
            icon="error",
            duration=20
        )
    
    def notify_milestone(self, job_name: str, milestone: str, value: float):
        """Notify when training reaches a milestone"""
        self.send_notification(
            title=f"🎯 Milestone Reached",
            message=f"Job '{job_name}': {milestone} = {value:.4f}",
            icon="success"
        )
    
    def notify_gpu_alert(self, gpu_util: int, memory_used: int):
        """Notify about GPU resource alerts"""
        if gpu_util > 95:
            self.send_notification(
                title="⚠️ GPU Alert",
                message=f"GPU utilization at {gpu_util}% (Memory: {memory_used}MB)",
                icon="warning"
            )
    
    def notify_backup_complete(self, backup_name: str, size_mb: float):
        """Notify when backup completes"""
        self.send_notification(
            title="💾 Backup Complete",
            message=f"Created backup '{backup_name}' ({size_mb:.2f} MB)",
            icon="success"
        )
    
    def notify_evaluation_complete(self, model_name: str, perplexity: float):
        """Notify when model evaluation completes"""
        self.send_notification(
            title="📊 Evaluation Complete",
            message=f"Model '{model_name}' - Perplexity: {perplexity:.2f}",
            icon="info"
        )

# Integration with training orchestrators
class TrainingNotifier:
    """Wrapper for training-specific notifications"""
    
    def __init__(self):
        self.notifier = NotificationManager()
        self.milestones = {
            'loss_threshold': 0.5,  # Notify when loss drops below this
            'epoch_interval': 5      # Notify every N epochs
        }
    
    def monitor_training(self, job_name: str, status_file: Path):
        """Monitor training progress and send notifications"""
        import json
        import time
        
        last_epoch = 0
        job_started = False
        
        while True:
            if not status_file.exists():
                time.sleep(5)
                continue
            
            try:
                with open(status_file, 'r') as f:
                    status = json.load(f)
                
                if not job_started and status.get('status') == 'running':
                    self.notifier.notify_job_started(job_name)
                    job_started = True
                
                # Check for milestones
                current_loss = status.get('current_loss', float('inf'))
                current_epoch = status.get('current_epoch', 0)
                
                if current_loss < self.milestones['loss_threshold'] and last_epoch == 0:
                    self.notifier.notify_milestone(
                        job_name,
                        f"Loss below {self.milestones['loss_threshold']}",
                        current_loss
                    )
                
                if current_epoch > 0 and current_epoch % self.milestones['epoch_interval'] == 0:
                    if current_epoch != last_epoch:
                        self.notifier.notify_milestone(
                            job_name,
                            f"Epoch {current_epoch} complete",
                            current_loss
                        )
                        last_epoch = current_epoch
                
                # Check if completed
                if status.get('status') == 'completed':
                    duration_min = status.get('duration_sec', 0) // 60
                    final_loss = status.get('final_loss', 0)
                    self.notifier.notify_job_completed(job_name, duration_min, final_loss)
                    break
                
                elif status.get('status') == 'failed':
                    error = status.get('error', 'Unknown error')
                    self.notifier.notify_job_failed(job_name, error)
                    break
                
            except Exception as e:
                print(f"Error monitoring training: {e}")
            
            time.sleep(10)  # Check every 10 seconds

# CLI for testing notifications
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="QAI Notification System")
    parser.add_argument('--test', action='store_true', help='Send test notification')
    parser.add_argument('--monitor', help='Monitor job status file')
    parser.add_argument('--job-name', default='Test Job', help='Job name for monitoring')
    
    args = parser.parse_args()
    
    notifier = NotificationManager()
    
    if args.test:
        print("Sending test notifications...")
        notifier.send_notification(
            title="🧪 QAI Test Notification",
            message="Notification system is working correctly!",
            icon="success"
        )
        print("✅ Test notification sent")
    
    elif args.monitor:
        print(f"Monitoring job: {args.job_name}")
        print(f"Status file: {args.monitor}")
        
        monitor = TrainingNotifier()
        monitor.monitor_training(args.job_name, Path(args.monitor))
    
    else:
        print("QAI Notification System")
        print(f"Platform: {notifier.system}")
        print(f"Enabled: {notifier.enabled}")
        print("\nExamples:")
        print("  Test notification: python notification_system.py --test")
        print("  Monitor training: python notification_system.py --monitor data_out/autotrain/status.json --job-name my_job")
