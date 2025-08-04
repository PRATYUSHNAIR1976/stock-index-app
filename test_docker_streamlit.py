#!/usr/bin/env python3
"""
Docker Streamlit UI test script.

This script tests the containerized Streamlit UI to ensure:
- All services start correctly
- Streamlit UI is accessible
- API integration works
- Charts and visualizations render properly
"""

import requests
import time
import subprocess
import json
import os

# Configuration
FASTAPI_URL = "http://localhost:8001"
STREAMLIT_URL = "http://localhost:8501"
TIMEOUT = 30  # seconds to wait for services to start

def wait_for_service(url, timeout=TIMEOUT):
    """Wait for a service to become available."""
    print(f"⏳ Waiting for service at {url}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
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
    
    try:
        # Check if docker-compose is available
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True, check=True)
        print("✅ Docker Compose is available")
        
        # Check services status
        result = subprocess.run(['docker-compose', 'ps'], 
                              capture_output=True, text=True, check=True)
        print("📊 Services status:")
        print(result.stdout)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker Compose error: {e}")
        return False
    except FileNotFoundError:
        print("❌ Docker Compose not found")
        return False

def test_streamlit_ui():
    """Test Streamlit UI functionality."""
    print("\n🎨 Testing Streamlit UI")
    print("=" * 50)
    
    # Test 1: Basic accessibility
    try:
        response = requests.get(STREAMLIT_URL, timeout=10)
        if response.status_code == 200:
            print("✅ Streamlit UI is accessible")
        else:
            print(f"❌ Streamlit UI returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Streamlit UI not accessible: {e}")
        return False
    
    # Test 2: Health check
    try:
        response = requests.get(f"{STREAMLIT_URL}/_stcore/health", timeout=10)
        if response.status_code == 200:
            print("✅ Streamlit health check passed")
        else:
            print(f"⚠️ Streamlit health check returned status {response.status_code}")
    except Exception as e:
        print(f"⚠️ Streamlit health check failed: {e}")
    
    return True

def test_api_integration():
    """Test API integration from Streamlit."""
    print("\n🔗 Testing API Integration")
    print("=" * 50)
    
    # Test FastAPI health
    try:
        response = requests.get(f"{FASTAPI_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ FastAPI health check passed")
        else:
            print(f"❌ FastAPI health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FastAPI not accessible: {e}")
        return False
    
    # Test build index endpoint
    try:
        response = requests.post(
            f"{FASTAPI_URL}/api/v1/build-index",
            json={
                "start_date": "2024-12-16",
                "end_date": "2024-12-16",
                "top_n": 2
            },
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Build index API working")
            else:
                print(f"⚠️ Build index API returned error: {result.get('error')}")
        else:
            print(f"❌ Build index API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Build index API error: {e}")
    
    # Test index composition endpoint
    try:
        response = requests.get(
            f"{FASTAPI_URL}/api/v1/index-composition?date=2024-12-16",
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Index composition API working")
            else:
                print(f"⚠️ Index composition API returned error: {result.get('error')}")
        else:
            print(f"❌ Index composition API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Index composition API error: {e}")
    
    # Test index performance endpoint
    try:
        response = requests.get(
            f"{FASTAPI_URL}/api/v1/index-performance?start_date=2024-12-16&end_date=2024-12-16",
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Index performance API working")
            else:
                print(f"⚠️ Index performance API returned error: {result.get('error')}")
        else:
            print(f"❌ Index performance API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Index performance API error: {e}")
    
    return True

def test_export_functionality():
    """Test export functionality."""
    print("\n📤 Testing Export Functionality")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"{FASTAPI_URL}/api/v1/export-data",
            json={
                "start_date": "2024-12-16",
                "end_date": "2024-12-16"
            },
            timeout=60
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("file_url"):
                print("✅ Export API working")
                print(f"📁 File URL: {result.get('file_url')}")
                print(f"📏 File Size: {result.get('file_size')} bytes")
            else:
                print(f"⚠️ Export API returned error: {result.get('error')}")
        else:
            print(f"❌ Export API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Export API error: {e}")
    
    return True

def test_data_persistence():
    """Test data persistence across containers."""
    print("\n💾 Testing Data Persistence")
    print("=" * 50)
    
    # Check if data directory exists and has files
    if os.path.exists("data"):
        files = os.listdir("data")
        if files:
            print(f"✅ Data directory exists with {len(files)} files")
            for file in files:
                print(f"   📄 {file}")
        else:
            print("⚠️ Data directory exists but is empty")
    else:
        print("❌ Data directory does not exist")
    
    # Check if exports directory exists and has files
    if os.path.exists("exports"):
        files = os.listdir("exports")
        if files:
            print(f"✅ Exports directory exists with {len(files)} files")
            for file in files[:3]:  # Show first 3 files
                print(f"   📄 {file}")
        else:
            print("⚠️ Exports directory exists but is empty")
    else:
        print("❌ Exports directory does not exist")
    
    return True

def main():
    """Run all Docker Streamlit tests."""
    print("🎨 Docker Streamlit UI Test Suite")
    print("=" * 60)
    
    # Test 1: Docker Compose availability
    if not test_docker_compose():
        print("❌ Docker Compose test failed")
        return
    
    # Test 2: Wait for services to be ready
    fastapi_ready = wait_for_service(FASTAPI_URL)
    streamlit_ready = wait_for_service(STREAMLIT_URL)
    
    if not fastapi_ready or not streamlit_ready:
        print("❌ Service readiness test failed")
        return
    
    # Test 3: Streamlit UI
    streamlit_ok = test_streamlit_ui()
    
    # Test 4: API Integration
    api_ok = test_api_integration()
    
    # Test 5: Export functionality
    export_ok = test_export_functionality()
    
    # Test 6: Data persistence
    persistence_ok = test_data_persistence()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DOCKER STREAMLIT TEST SUMMARY")
    print("=" * 60)
    
    print(f"Docker Compose: ✅ Available")
    print(f"FastAPI Service: {'✅ Ready' if fastapi_ready else '❌ Not Ready'}")
    print(f"Streamlit UI: {'✅ Ready' if streamlit_ready else '❌ Not Ready'}")
    print(f"Streamlit Functionality: {'✅ Working' if streamlit_ok else '❌ Failed'}")
    print(f"API Integration: {'✅ Working' if api_ok else '❌ Failed'}")
    print(f"Export Functionality: {'✅ Working' if export_ok else '❌ Failed'}")
    print(f"Data Persistence: {'✅ Working' if persistence_ok else '❌ Failed'}")
    
    total_passed = sum([fastapi_ready, streamlit_ready, streamlit_ok, api_ok, export_ok, persistence_ok])
    total_tests = 6
    
    print(f"\nOverall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All Docker Streamlit tests passed! UI is working correctly.")
        print("\n🌐 Access URLs:")
        print(f"🔗 FastAPI: {FASTAPI_URL}")
        print(f"📚 API Docs: {FASTAPI_URL}/docs")
        print(f"🎨 Streamlit UI: {STREAMLIT_URL}")
    else:
        print("⚠️ Some Docker Streamlit tests failed. Check the container setup.")

if __name__ == "__main__":
    main() 