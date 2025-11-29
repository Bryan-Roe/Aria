
Comprehensive test suite for the production API.

Usage:
    python test_api.py

Author: Quantum AI System
Date: November 16, 2025
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8080"
# Use timeout for all requests to prevent hanging
REQUEST_TIMEOUT = 30  # seconds

def test_health():
    """Test health endpoint"""
    print("\n" + "="*70)
    print("TEST 1: Health Check")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/health", timeout=REQUEST_TIMEOUT, timeout=REQUEST_TIMEOUT)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
    print("✅ PASSED")

def test_model_info():
    """Test model info endpoint"""
    print("\n" + "="*70)
    print("TEST 2: Model Info")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/model_info", timeout=REQUEST_TIMEOUT)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert 'architecture' in response.json()
    print("✅ PASSED")

def test_single_prediction_genuine():
    """Test single prediction - genuine banknote"""
    print("\n" + "="*70)
    print("TEST 3: Single Prediction (Genuine)")
    print("="*70)
    
    # Example genuine banknote features
    data = {
        "features": [3.6216, 8.6661, -2.8073, -0.44699]
    }
    
    print(f"Input: {json.dumps(data, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/predict",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    result = response.json()
    assert 'prediction' in result
    assert 'confidence' in result
    assert result['confidence'] > 0.5
    print("✅ PASSED")

def test_single_prediction_forged():
    """Test single prediction - forged banknote"""
    print("\n" + "="*70)
    print("TEST 4: Single Prediction (Forged)")
    print("="*70)
    
    # Example forged banknote features
    data = {
        "features": [-4.5459, 8.1674, -2.4586, -1.4621]
    }
    
    print(f"Input: {json.dumps(data, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/predict",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    result = response.json()
    assert 'prediction' in result
    assert 'confidence' in result
    print("✅ PASSED")

def test_batch_prediction():
    """Test batch prediction"""
    print("\n" + "="*70)
    print("TEST 5: Batch Prediction")
    print("="*70)
    
    data = {
        "batch": [
            {"features": [3.6216, 8.6661, -2.8073, -0.44699]},  # Genuine
            {"features": [-4.5459, 8.1674, -2.4586, -1.4621]},  # Forged
            {"features": [2.5, 1.2, -0.8, 0.3]},                # Test
        ]
    }
    
    print(f"Input: {len(data['batch'])} banknotes")
    
    response = requests.post(
        f"{BASE_URL}/api/predict_batch",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    result = response.json()
    assert 'results' in result
    assert 'summary' in result
    assert result['summary']['total_processed'] == 3
    print("✅ PASSED")

def test_invalid_input():
    """Test error handling with invalid input"""
    print("\n" + "="*70)
    print("TEST 6: Invalid Input Handling")
    print("="*70)
    
    # Missing features field
    data = {"wrong_field": [1, 2, 3, 4]}
    
    print(f"Input: {json.dumps(data, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/predict",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 400
    assert 'error' in response.json()
    print("✅ PASSED")

def test_wrong_feature_count():
    """Test error handling with wrong feature count"""
    print("\n" + "="*70)
    print("TEST 7: Wrong Feature Count")
    print("="*70)
    
    # Only 3 features instead of 4
    data = {"features": [1.0, 2.0, 3.0]}
    
    print(f"Input: {json.dumps(data, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/predict",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 400
    assert 'error' in response.json()
    print("✅ PASSED")

def test_performance():
    """Test API performance"""
    print("\n" + "="*70)
    print("TEST 8: Performance Benchmark")
    print("="*70)
    
    data = {"features": [3.6216, 8.6661, -2.8073, -0.44699]}
    
    n_requests = 10
    times = []
    
    print(f"Making {n_requests} requests...")
    
    for i in range(n_requests):
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/predict",
            json=data,
            headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT
        )
        elapsed = time.time() - start
        times.append(elapsed * 1000)  # Convert to ms
        
        assert response.status_code == 200
        print(f"  Request {i+1}/{n_requests}: {elapsed*1000:.2f}ms", end='\r')
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n\nPerformance Results:")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  Min: {min_time:.2f}ms")
    print(f"  Max: {max_time:.2f}ms")
    
    assert avg_time < 200  # Should be under 200ms
    print("✅ PASSED")

def main():
    """Run all tests"""
    print("=" * 70)
    print("  BANKNOTE FRAUD DETECTOR API - TEST SUITE")
    print("=" * 70)
    print(f"\nTarget: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            print("\n❌ API is not responding correctly")
            print("   Make sure the API is running:")
            print("   python banknote_api.py")
            return
    except requests.exceptions.RequestException:
        print("\n❌ Cannot connect to API")
        print("   Make sure the API is running:")
        print("   python banknote_api.py")
        return
    
    # Run tests
    tests = [
        test_health,
        test_model_info,
        test_single_prediction_genuine,
        test_single_prediction_forged,
        test_batch_prediction,
        test_invalid_input,
        test_wrong_feature_count,
        test_performance
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    print(f"\nTotal Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ API is production-ready!")
    else:
        print(f"\n⚠️ {failed} test(s) failed")
        print("   Review the output above for details")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
"""
Test the Banknote Fraud Detector API

Comprehensive test suite for the production API.

Usage:
    python test_api.py

Author: Quantum AI System
Date: November 16, 2025
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8080"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*70)
    print("TEST 1: Health Check")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
    print("✅ PASSED")

def test_model_info():
    """Test model info endpoint"""
    print("\n" + "="*70)
    print("TEST 2: Model Info")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/model_info")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert 'architecture' in response.json()
    print("✅ PASSED")

def test_single_prediction_genuine():
    """Test single prediction - genuine banknote"""
    print("\n" + "="*70)
    print("TEST 3: Single Prediction (Genuine)")
    print("="*70)
    
    # Example genuine banknote features
    data = {
        "features": [3.6216, 8.6661, -2.8073, -0.44699]
    }
    
    print(f"Input: {json.dumps(data, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/predict",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    result = response.json()
    assert 'prediction' in result
    assert 'confidence' in result
    assert result['confidence'] > 0.5
    print("✅ PASSED")

def test_single_prediction_forged():
    """Test single prediction - forged banknote"""
    print("\n" + "="*70)
    print("TEST 4: Single Prediction (Forged)")
    print("="*70)
    
    # Example forged banknote features
    data = {
        "features": [-4.5459, 8.1674, -2.4586, -1.4621]
    }
    
    print(f"Input: {json.dumps(data, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/predict",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    result = response.json()
    assert 'prediction' in result
    assert 'confidence' in result
    print("✅ PASSED")

def test_batch_prediction():
    """Test batch prediction"""
    print("\n" + "="*70)
    print("TEST 5: Batch Prediction")
    print("="*70)
    
    data = {
        "batch": [
            {"features": [3.6216, 8.6661, -2.8073, -0.44699]},  # Genuine
            {"features": [-4.5459, 8.1674, -2.4586, -1.4621]},  # Forged
            {"features": [2.5, 1.2, -0.8, 0.3]},                # Test
        ]
    }
    
    print(f"Input: {len(data['batch'])} banknotes")
    
    response = requests.post(
        f"{BASE_URL}/api/predict_batch",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    result = response.json()
    assert 'results' in result
    assert 'summary' in result
    assert result['summary']['total_processed'] == 3
    print("✅ PASSED")

def test_invalid_input():
    """Test error handling with invalid input"""
    print("\n" + "="*70)
    print("TEST 6: Invalid Input Handling")
    print("="*70)
    
    # Missing features field
    data = {"wrong_field": [1, 2, 3, 4]}
    
    print(f"Input: {json.dumps(data, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/predict",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 400
    assert 'error' in response.json()
    print("✅ PASSED")

def test_wrong_feature_count():
    """Test error handling with wrong feature count"""
    print("\n" + "="*70)
    print("TEST 7: Wrong Feature Count")
    print("="*70)
    
    # Only 3 features instead of 4
    data = {"features": [1.0, 2.0, 3.0]}
    
    print(f"Input: {json.dumps(data, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/predict",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 400
    assert 'error' in response.json()
    print("✅ PASSED")

def test_performance():
    """Test API performance"""
    print("\n" + "="*70)
    print("TEST 8: Performance Benchmark")
    print("="*70)
    
    data = {"features": [3.6216, 8.6661, -2.8073, -0.44699]}
    
    n_requests = 10
    times = []
    
    print(f"Making {n_requests} requests...")
    
    for i in range(n_requests):
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/predict",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        elapsed = time.time() - start
        times.append(elapsed * 1000)  # Convert to ms
        
        assert response.status_code == 200
        print(f"  Request {i+1}/{n_requests}: {elapsed*1000:.2f}ms", end='\r')
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n\nPerformance Results:")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  Min: {min_time:.2f}ms")
    print(f"  Max: {max_time:.2f}ms")
    
    assert avg_time < 200  # Should be under 200ms
    print("✅ PASSED")

def main():
    """Run all tests"""
    print("=" * 70)
    print("  BANKNOTE FRAUD DETECTOR API - TEST SUITE")
    print("=" * 70)
    print(f"\nTarget: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("\n❌ API is not responding correctly")
            print("   Make sure the API is running:")
            print("   python banknote_api.py")
            return
    except requests.exceptions.RequestException:
        print("\n❌ Cannot connect to API")
        print("   Make sure the API is running:")
        print("   python banknote_api.py")
        return
    
    # Run tests
    tests = [
        test_health,
        test_model_info,
        test_single_prediction_genuine,
        test_single_prediction_forged,
        test_batch_prediction,
        test_invalid_input,
        test_wrong_feature_count,
        test_performance
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    print(f"\nTotal Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ API is production-ready!")
    else:
        print(f"\n⚠️ {failed} test(s) failed")
        print("   Review the output above for details")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
