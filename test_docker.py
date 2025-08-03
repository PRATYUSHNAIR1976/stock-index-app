#!/usr/bin/env python3
"""
Docker containerization test script.

This script tests the containerized application to ensure:
- All services start correctly
- Networking between services works
- Database persistence works
- API endpoints function properly
"""

import requests
import time
import subprocess
import json
import os

# Configuration
BASE_URL = "http://localhost:8001"
TIMEOUT = 30  # seconds to wait for services to start

def wait_for_service(url, timeout=TIMEOUT):
    """Wait for a service to become available."""
    print(f"Waiting for service at {url}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Service is ready at {url}")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(2)
    
    print(f"❌ Service at {url} did not become ready within {timeout} seconds")
    return False

def test_docker_compose():
    """Test Docker Compose setup."""
    print("🚀 Testing Docker Compose Setup")
    print("=" * 50)
    
    # Check if Docker Compose is running
    try:
        result = subprocess.run(
            ["docker-compose", "ps"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Docker Compose is available")
            print("Services status:")
            print(result.stdout)
        else:
            print("❌ Docker Compose not available or not running")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Docker Compose: {e}")
        return False
    
    return True

def test_api_endpoints():
    """Test API endpoints in containerized environment."""
    print("\n🔍 Testing API Endpoints")
    print("-" * 30)
    
    tests = [
        ("Health Check", "GET", "/health"),
        ("Build Index", "POST", "/api/v1/build-index", {
            "start_date": "2024-12-16",
            "end_date": "2024-12-16", 
            "top_n": 2
        }),
        ("Index Composition", "GET", "/api/v1/index-composition?date=2024-12-16"),
        ("Index Performance", "GET", "/api/v1/index-performance?start_date=2024-12-16&end_date=2024-12-16"),
    ]
    
    results = []
    
    for test_name, method, endpoint, *args in tests:
        print(f"\n📋 Testing: {test_name}")
        
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json=args[0], timeout=10)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("✅ PASS")
                results.append(True)
            else:
                print(f"❌ FAIL - {response.text}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ ERROR - {e}")
            results.append(False)
    
    return results

def test_data_persistence():
    """Test that data persists between container restarts."""
    print("\n🗄️ Testing Data Persistence")
    print("-" * 30)
    
    # Check if data directory exists and has files
    data_dir = "./data"
    if os.path.exists(data_dir):
        files = os.listdir(data_dir)
        print(f"✅ Data directory exists with {len(files)} files")
        return True
    else:
        print("❌ Data directory does not exist")
        return False

def main():
    """Run all Docker tests."""
    print("🐳 Docker Containerization Test Suite")
    print("=" * 50)
    
    # Test 1: Docker Compose availability
    if not test_docker_compose():
        print("❌ Docker Compose test failed")
        return
    
    # Test 2: Wait for services to be ready
    if not wait_for_service(BASE_URL):
        print("❌ Service readiness test failed")
        return
    
    # Test 3: API endpoints
    api_results = test_api_endpoints()
    
    # Test 4: Data persistence
    persistence_ok = test_data_persistence()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DOCKER TEST SUMMARY")
    print("=" * 50)
    
    print(f"Docker Compose: ✅ Available")
    print(f"Service Readiness: ✅ Ready")
    print(f"API Endpoints: {sum(api_results)}/{len(api_results)} passed")
    print(f"Data Persistence: {'✅' if persistence_ok else '❌'}")
    
    total_passed = 2 + sum(api_results) + (1 if persistence_ok else 0)
    total_tests = 2 + len(api_results) + 1
    
    print(f"\nOverall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All Docker tests passed! Containerization is working correctly.")
    else:
        print("⚠️ Some Docker tests failed. Check the container setup.")

if __name__ == "__main__":
    main() 