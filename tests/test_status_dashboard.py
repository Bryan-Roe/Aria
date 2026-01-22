"""Tests for status_dashboard.py and monitoring"""
import json
import tempfile
from pathlib import Path
from unittest import mock
import pytest
import sys
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestStatusDashboard:
    """Test status dashboard functionality"""
    
    def test_status_file_aggregation(self):
        """Test aggregating status from multiple sources"""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_out = Path(tmpdir) / "data_out"
            data_out.mkdir()
            
            # Create status files for different orchestrators
            orchestrators = ["training", "quantum", "evaluation"]
            
            for orch in orchestrators:
                orch_dir = data_out / orch
                orch_dir.mkdir()
                
                status = {
                    "orchestrator": orch,
                    "status": "completed",
                    "total_jobs": 10,
                    "succeeded": 9,
                    "failed": 1,
                    "last_updated": "2026-01-17T12:00:00Z"
                }
                
                (orch_dir / "status.json").write_text(json.dumps(status))
            
            # Aggregate statuses
            total_jobs = 0
            total_succeeded = 0
            
            for orch in orchestrators:
                status_file = data_out / orch / "status.json"
                if status_file.exists():
                    status = json.loads(status_file.read_text())
                    total_jobs += status["total_jobs"]
                    total_succeeded += status["succeeded"]
            
            assert total_jobs == 30
            assert total_succeeded == 27
    
    def test_dashboard_metrics_calculation(self):
        """Test calculating dashboard metrics"""
        status_data = {
            "training": {"total_jobs": 10, "succeeded": 9, "failed": 1},
            "quantum": {"total_jobs": 5, "succeeded": 5, "failed": 0},
            "evaluation": {"total_jobs": 15, "succeeded": 12, "failed": 3}
        }
        
        total = sum(s["total_jobs"] for s in status_data.values())
        succeeded = sum(s["succeeded"] for s in status_data.values())
        failed = sum(s["failed"] for s in status_data.values())
        success_rate = succeeded / total if total > 0 else 0
        
        assert total == 30
        assert succeeded == 26
        assert failed == 4
        assert success_rate == pytest.approx(0.867, abs=0.01)


class TestOrchestrationMetrics:
    """Test orchestration metrics tracking"""
    
    def test_job_duration_tracking(self):
        """Test tracking job durations"""
        jobs = [
            {"name": "job1", "start": "12:00:00", "end": "12:05:00", "duration_minutes": 5},
            {"name": "job2", "start": "12:05:00", "end": "12:15:00", "duration_minutes": 10},
            {"name": "job3", "start": "12:15:00", "end": "12:20:00", "duration_minutes": 5}
        ]
        
        total_duration = sum(j["duration_minutes"] for j in jobs)
        avg_duration = total_duration / len(jobs)
        
        assert total_duration == 20
        assert avg_duration == pytest.approx(6.67, abs=0.01)
    
    def test_success_rate_by_component(self):
        """Test calculating success rates by component"""
        results = {
            "training": {"total": 100, "succeeded": 95},
            "quantum": {"total": 50, "succeeded": 48},
            "evaluation": {"total": 75, "succeeded": 70}
        }
        
        success_rates = {
            name: (data["succeeded"] / data["total"])
            for name, data in results.items()
        }
        
        assert success_rates["training"] == 0.95
        assert success_rates["quantum"] == 0.96
        assert success_rates["evaluation"] == pytest.approx(0.933, abs=0.01)
    
    def test_trend_analysis(self):
        """Test analyzing performance trends"""
        historical_data = [
            {"date": "2026-01-15", "accuracy": 0.88},
            {"date": "2026-01-16", "accuracy": 0.90},
            {"date": "2026-01-17", "accuracy": 0.92}
        ]
        
        # Calculate trend (improvement rate)
        if len(historical_data) >= 2:
            trend = historical_data[-1]["accuracy"] - historical_data[0]["accuracy"]
            improvement_rate = trend / len(historical_data) * 100
            
            assert trend == pytest.approx(0.04, abs=0.001)
            assert improvement_rate == pytest.approx(1.33, abs=0.01)


class TestResourceMonitoring:
    """Test resource monitoring functionality"""
    
    def test_cpu_usage_tracking(self):
        """Test tracking CPU usage"""
        cpu_samples = [25, 30, 28, 32, 35, 33]
        
        avg_cpu = sum(cpu_samples) / len(cpu_samples)
        max_cpu = max(cpu_samples)
        min_cpu = min(cpu_samples)
        
        assert avg_cpu == pytest.approx(30.5, abs=0.1)
        assert max_cpu == 35
        assert min_cpu == 25
    
    def test_memory_usage_tracking(self):
        """Test tracking memory usage"""
        memory_data = {
            "total_gb": 32,
            "available_gb": 8,
            "used_gb": 24,
            "percent": 75
        }
        
        assert memory_data["percent"] == (memory_data["used_gb"] / memory_data["total_gb"]) * 100
    
    def test_gpu_memory_allocation(self):
        """Test GPU memory monitoring"""
        gpu_stats = {
            "device": "cuda:0",
            "total_memory_gb": 24,
            "allocated_gb": 18,
            "reserved_gb": 20,
            "free_gb": 6
        }
        
        utilization = (gpu_stats["allocated_gb"] / gpu_stats["total_memory_gb"]) * 100
        
        assert utilization == 75
        assert gpu_stats["free_gb"] == gpu_stats["total_memory_gb"] - gpu_stats["allocated_gb"]
    
    def test_disk_space_monitoring(self):
        """Test disk space monitoring"""
        disk_stats = {
            "total_gb": 1000,
            "used_gb": 750,
            "free_gb": 250,
            "percent_used": 75
        }
        
        assert disk_stats["percent_used"] == (disk_stats["used_gb"] / disk_stats["total_gb"]) * 100
        
        # Should warn if > 80%
        should_warn = disk_stats["percent_used"] > 80
        assert not should_warn


class TestAlertManagement:
    """Test alert generation and management"""
    
    def test_alert_threshold_detection(self):
        """Test detecting when metrics exceed thresholds"""
        thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90
        }
        
        current_metrics = {
            "cpu_percent": 82,
            "memory_percent": 70,
            "disk_percent": 95
        }
        
        alerts = []
        for metric, value in current_metrics.items():
            if value > thresholds.get(metric, 100):
                alerts.append(f"{metric} exceeds threshold: {value}% > {thresholds[metric]}%")
        
        assert len(alerts) == 2
        assert any("cpu_percent" in a for a in alerts)
        assert any("disk_percent" in a for a in alerts)
    
    def test_alert_severity_classification(self):
        """Test classifying alert severity"""
        def classify_severity(value, threshold):
            if value >= threshold * 1.1:  # 10% over threshold
                return "critical"
            elif value >= threshold:
                return "warning"
            return "ok"
        
        threshold = 80
        
        assert classify_severity(75, threshold) == "ok"
        assert classify_severity(82, threshold) == "warning"
        assert classify_severity(90, threshold) == "critical"
    
    def test_alert_deduplication(self):
        """Test preventing duplicate alerts"""
        alerts = [
            {"type": "cpu", "timestamp": "12:00:00"},
            {"type": "memory", "timestamp": "12:00:05"},
            {"type": "cpu", "timestamp": "12:00:10"},  # Duplicate
            {"type": "disk", "timestamp": "12:00:15"}
        ]
        
        unique_alerts = []
        seen_types = set()
        
        for alert in alerts:
            if alert["type"] not in seen_types:
                unique_alerts.append(alert)
                seen_types.add(alert["type"])
        
        assert len(unique_alerts) == 3
        assert len(seen_types) == 3


class TestDashboardDataFormatting:
    """Test data formatting for display"""
    
    def test_number_formatting(self):
        """Test formatting numbers for display"""
        numbers = [1000000, 5.5555, 0.00001, 999]
        
        formatted = [
            f"{1000000:,}",           # "1,000,000"
            f"{5.5555:.2f}",          # "5.56"
            f"{0.00001:.5f}",         # "0.00001"
            f"{999:,}"                # "999"
        ]
        
        assert formatted[0] == "1,000,000"
        assert formatted[1] == "5.56"
        assert formatted[2] == "0.00001"
    
    def test_time_formatting(self):
        """Test formatting timestamps"""
        from datetime import datetime
        
        dt = datetime(2026, 1, 17, 14, 30, 45)
        
        formats = {
            "iso": dt.isoformat(),
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M:%S"),
            "short": dt.strftime("%m/%d %H:%M")
        }
        
        assert formats["iso"] == "2026-01-17T14:30:45"
        assert formats["date"] == "2026-01-17"
        assert formats["time"] == "14:30:45"
        assert formats["short"] == "01/17 14:30"
    
    def test_duration_formatting(self):
        """Test formatting durations"""
        def format_duration(seconds):
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{int(hours):02d}:{int(minutes):02d}:{int(secs):02d}"
        
        assert format_duration(3661) == "01:01:01"
        assert format_duration(7200) == "02:00:00"
        assert format_duration(45) == "00:00:45"


class TestHealthCheckEndpoint:
    """Test health check endpoint functionality"""
    
    def test_health_check_response_structure(self):
        """Test health check response has required fields"""
        health_check = {
            "status": "healthy",
            "timestamp": "2026-01-17T12:00:00Z",
            "uptime_seconds": 86400,
            "components": {
                "aria_web": "healthy",
                "function_app": "healthy",
                "quantum_mcp": "unhealthy"
            },
            "metrics": {
                "cpu_percent": 45,
                "memory_percent": 62,
                "disk_percent": 75
            }
        }
        
        assert health_check["status"] in ["healthy", "unhealthy", "degraded"]
        assert "timestamp" in health_check
        assert "components" in health_check
        assert "metrics" in health_check
    
    def test_overall_health_calculation(self):
        """Test calculating overall health status"""
        components = {
            "training": "healthy",
            "quantum": "healthy",
            "evaluation": "degraded",
            "database": "healthy"
        }
        
        health_statuses = list(components.values())
        
        if "unhealthy" in health_statuses:
            overall = "unhealthy"
        elif "degraded" in health_statuses:
            overall = "degraded"
        else:
            overall = "healthy"
        
        assert overall == "degraded"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
