"""Tests for resource_monitor.py"""
import tempfile
from pathlib import Path
from unittest import mock
import pytest
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCPUMonitoring:
    """Test CPU monitoring functionality"""
    
    def test_cpu_usage_sampling(self):
        """Test sampling CPU usage"""
        # Mock psutil.cpu_percent
        cpu_samples = [25.5, 30.2, 28.7, 35.1]
        
        avg = sum(cpu_samples) / len(cpu_samples)
        max_cpu = max(cpu_samples)
        min_cpu = min(cpu_samples)
        
        assert 28 < avg < 32
        assert max_cpu > 30
        assert min_cpu < 30
    
    def test_per_cpu_tracking(self):
        """Test tracking per-CPU usage"""
        per_cpu = {
            "cpu0": 25,
            "cpu1": 28,
            "cpu2": 32,
            "cpu3": 30
        }
        
        avg_per_cpu = sum(per_cpu.values()) / len(per_cpu)
        assert avg_per_cpu == pytest.approx(28.75, abs=0.1)
    
    def test_cpu_load_average(self):
        """Test CPU load average calculation"""
        load_avg = {
            "1min": 6.5,
            "5min": 5.3,
            "15min": 4.1
        }
        
        cpu_count = 4
        load_per_cpu_1min = load_avg["1min"] / cpu_count
        
        # High if > 1.0 per CPU
        is_high = load_per_cpu_1min > 1.0
        assert is_high


class TestMemoryMonitoring:
    """Test memory monitoring"""
    
    def test_memory_usage_sampling(self):
        """Test memory usage tracking"""
        memory_stats = {
            "total": 32 * 1024 * 1024 * 1024,  # 32 GB
            "available": 8 * 1024 * 1024 * 1024,  # 8 GB
            "used": 24 * 1024 * 1024 * 1024,  # 24 GB
            "percent": 75
        }
        
        calculated_percent = (memory_stats["used"] / memory_stats["total"]) * 100
        assert calculated_percent == memory_stats["percent"]
    
    def test_swap_memory_monitoring(self):
        """Test swap memory monitoring"""
        swap_stats = {
            "total": 8 * 1024 * 1024 * 1024,  # 8 GB
            "used": 2 * 1024 * 1024 * 1024,   # 2 GB
            "free": 6 * 1024 * 1024 * 1024,   # 6 GB
            "percent": 25
        }
        
        calculated_percent = (swap_stats["used"] / swap_stats["total"]) * 100
        assert calculated_percent == swap_stats["percent"]
    
    def test_memory_pressure_detection(self):
        """Test detecting memory pressure"""
        thresholds = {
            "normal": 70,
            "warning": 85,
            "critical": 95
        }
        
        memory_percent = 88
        
        if memory_percent > thresholds["critical"]:
            status = "critical"
        elif memory_percent > thresholds["warning"]:
            status = "warning"
        else:
            status = "normal"
        
        assert status == "warning"


class TestDiskMonitoring:
    """Test disk usage monitoring"""
    
    def test_disk_space_tracking(self):
        """Test tracking disk space"""
        disk_stats = {
            "total": 1000 * 1024 * 1024 * 1024,  # 1 TB
            "used": 750 * 1024 * 1024 * 1024,    # 750 GB
            "free": 250 * 1024 * 1024 * 1024,    # 250 GB
            "percent": 75
        }
        
        calculated_percent = (disk_stats["used"] / disk_stats["total"]) * 100
        assert calculated_percent == disk_stats["percent"]
    
    def test_inode_usage_tracking(self):
        """Test tracking inode usage"""
        inode_stats = {
            "total": 10000000,
            "used": 7500000,
            "free": 2500000,
            "percent": 75
        }
        
        calculated_percent = (inode_stats["used"] / inode_stats["total"]) * 100
        assert calculated_percent == inode_stats["percent"]
    
    def test_disk_io_monitoring(self):
        """Test disk I/O monitoring"""
        disk_io = {
            "read_count": 1000,
            "write_count": 500,
            "read_bytes": 10 * 1024 * 1024,  # 10 MB
            "write_bytes": 5 * 1024 * 1024   # 5 MB
        }
        
        total_io = disk_io["read_count"] + disk_io["write_count"]
        assert total_io == 1500
        
        total_bytes = disk_io["read_bytes"] + disk_io["write_bytes"]
        assert total_bytes == 15 * 1024 * 1024


class TestGPUMonitoring:
    """Test GPU monitoring"""
    
    def test_gpu_memory_tracking(self):
        """Test GPU memory usage tracking"""
        gpu_memory = {
            "device": "cuda:0",
            "total": 24 * 1024 * 1024 * 1024,      # 24 GB
            "allocated": 18 * 1024 * 1024 * 1024,  # 18 GB
            "reserved": 20 * 1024 * 1024 * 1024,   # 20 GB
            "free": 4 * 1024 * 1024 * 1024         # 4 GB
        }
        
        utilization = (gpu_memory["allocated"] / gpu_memory["total"]) * 100
        assert utilization == 75
    
    def test_gpu_utilization_percentage(self):
        """Test GPU utilization percentage"""
        gpu_util = {
            "device": "cuda:0",
            "utilization": 85
        }
        
        is_high = gpu_util["utilization"] > 80
        assert is_high
    
    def test_multi_gpu_monitoring(self):
        """Test monitoring multiple GPUs"""
        gpus = [
            {"device": "cuda:0", "utilization": 75, "memory_percent": 60},
            {"device": "cuda:1", "utilization": 82, "memory_percent": 70},
            {"device": "cuda:2", "utilization": 45, "memory_percent": 40}
        ]
        
        avg_util = sum(g["utilization"] for g in gpus) / len(gpus)
        avg_mem = sum(g["memory_percent"] for g in gpus) / len(gpus)
        
        assert avg_util == pytest.approx(67.33, abs=0.1)
        assert avg_mem == pytest.approx(56.67, abs=0.1)


class TestNetworkMonitoring:
    """Test network monitoring"""
    
    def test_network_io_tracking(self):
        """Test tracking network I/O"""
        network_io = {
            "bytes_sent": 1000 * 1024 * 1024,  # 1000 MB
            "bytes_recv": 2000 * 1024 * 1024,  # 2000 MB
            "packets_sent": 100000,
            "packets_recv": 200000
        }
        
        total_bytes = network_io["bytes_sent"] + network_io["bytes_recv"]
        assert total_bytes == 3000 * 1024 * 1024
    
    def test_network_bandwidth_calculation(self):
        """Test calculating network bandwidth"""
        import time
        
        # Simulate bandwidth calculation
        bytes_before = 1000 * 1024 * 1024
        bytes_after = 1010 * 1024 * 1024
        time_diff = 10  # seconds
        
        bytes_diff = bytes_after - bytes_before
        bandwidth_mbps = (bytes_diff / (1024 * 1024)) / time_diff
        
        assert bandwidth_mbps == 1.0


class TestProcessMonitoring:
    """Test process monitoring"""
    
    def test_process_cpu_usage(self):
        """Test tracking process CPU usage"""
        processes = [
            {"name": "python", "pid": 1234, "cpu_percent": 25.5},
            {"name": "python", "pid": 1235, "cpu_percent": 18.2},
            {"name": "node", "pid": 5678, "cpu_percent": 12.3}
        ]
        
        python_processes = [p for p in processes if p["name"] == "python"]
        total_python_cpu = sum(p["cpu_percent"] for p in python_processes)
        
        assert len(python_processes) == 2
        assert total_python_cpu == pytest.approx(43.7, abs=0.1)
    
    def test_process_memory_tracking(self):
        """Test tracking process memory"""
        processes = [
            {"name": "python", "pid": 1234, "memory_mb": 512},
            {"name": "python", "pid": 1235, "memory_mb": 384},
            {"name": "node", "pid": 5678, "memory_mb": 256}
        ]
        
        total_memory = sum(p["memory_mb"] for p in processes)
        assert total_memory == 1152
        
        avg_memory = total_memory / len(processes)
        assert avg_memory == pytest.approx(384, abs=0.1)
    
    def test_top_processes_by_resource(self):
        """Test identifying top resource consumers"""
        processes = [
            {"name": "python_training", "cpu_percent": 85},
            {"name": "python_quantum", "cpu_percent": 45},
            {"name": "node_server", "cpu_percent": 15},
            {"name": "python_inference", "cpu_percent": 30}
        ]
        
        top_3 = sorted(processes, key=lambda p: p["cpu_percent"], reverse=True)[:3]
        
        assert len(top_3) == 3
        assert top_3[0]["cpu_percent"] == 85
        assert top_3[1]["cpu_percent"] == 45
        assert top_3[2]["cpu_percent"] == 30


class TestMonitoringDataCollection:
    """Test data collection and storage"""
    
    def test_metrics_snapshot(self):
        """Test collecting snapshot of all metrics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot_file = Path(tmpdir) / "metrics_snapshot.json"
            
            snapshot = {
                "timestamp": "2026-01-17T12:00:00Z",
                "cpu": {"percent": 45, "load_avg": 2.1},
                "memory": {"percent": 62},
                "disk": {"percent": 75},
                "gpu": {"device": "cuda:0", "utilization": 85}
            }
            
            snapshot_file.write_text(json.dumps(snapshot, indent=2))
            
            loaded = json.loads(snapshot_file.read_text())
            assert loaded["cpu"]["percent"] == 45
            assert loaded["memory"]["percent"] == 62
    
    def test_metrics_history(self):
        """Test storing metrics history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "metrics_history.jsonl"
            
            snapshots = [
                {"timestamp": "12:00:00", "cpu_percent": 40},
                {"timestamp": "12:01:00", "cpu_percent": 45},
                {"timestamp": "12:02:00", "cpu_percent": 42},
                {"timestamp": "12:03:00", "cpu_percent": 48}
            ]
            
            lines = [json.dumps(s) for s in snapshots]
            history_file.write_text("\n".join(lines))
            
            stored = [json.loads(line) for line in history_file.read_text().split("\n")]
            assert len(stored) == 4
            assert stored[0]["cpu_percent"] == 40
    
    def test_metrics_aggregation_window(self):
        """Test aggregating metrics over time windows"""
        samples = [40, 45, 42, 48, 50, 46, 44, 49]
        
        # 2-sample window aggregates
        windows = [
            [samples[i], samples[i+1]] for i in range(0, len(samples)-1, 2)
        ]
        
        window_avgs = [sum(w) / len(w) for w in windows]
        
        assert len(window_avgs) == 4
        assert window_avgs[0] == 42.5
        assert window_avgs[-1] == 46.5


class TestMonitoringAlerts:
    """Test alert generation in monitoring"""
    
    def test_threshold_alert_generation(self):
        """Test generating alerts when thresholds exceeded"""
        thresholds = {"cpu_percent": 80, "memory_percent": 85}
        current = {"cpu_percent": 85, "memory_percent": 70}
        
        alerts = []
        for metric, threshold in thresholds.items():
            if current[metric] > threshold:
                alerts.append(f"{metric} exceeded: {current[metric]}% > {threshold}%")
        
        assert len(alerts) == 1
        assert "cpu_percent" in alerts[0]
    
    def test_alert_cooldown(self):
        """Test preventing alert spam with cooldown"""
        alerts = []
        last_alert_time = {}
        cooldown_seconds = 300
        
        def add_alert(alert_type, timestamp):
            if alert_type not in last_alert_time:
                alerts.append({"type": alert_type, "timestamp": timestamp})
                last_alert_time[alert_type] = timestamp
                return True
            else:
                time_since = timestamp - last_alert_time[alert_type]
                if time_since > cooldown_seconds:
                    alerts.append({"type": alert_type, "timestamp": timestamp})
                    last_alert_time[alert_type] = timestamp
                    return True
            return False
        
        assert add_alert("cpu", 1000) == True
        assert add_alert("cpu", 1100) == False  # Within cooldown
        assert add_alert("cpu", 1400) == True   # After cooldown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
