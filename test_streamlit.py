#!/usr/bin/env python3
"""
Test script for the Streamlit UI functionality.

This script tests the Streamlit UI components and API connectivity.
"""

import requests
import time
import subprocess
import sys

def test_api_connectivity():
    """Test if the FastAPI service is running."""
    print("🔍 Testing API Connectivity...")
    
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI service is running")
            return True
        else:
            print(f"❌ FastAPI service returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FastAPI service not accessible: {e}")
        return False

def test_streamlit_ui():
    """Test if the Streamlit UI is running."""
    print("🔍 Testing Streamlit UI...")
    
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit UI is running")
            return True
        else:
            print(f"❌ Streamlit UI returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Streamlit UI not accessible: {e}")
        return False

def test_api_endpoints():
    """Test the main API endpoints."""
    print("🔍 Testing API Endpoints...")
    
    endpoints = [
        ("GET", "/health", "Health Check"),
        ("POST", "/api/v1/build-index", "Build Index"),
        ("GET", "/api/v1/index-composition?date=2024-12-16", "Index Composition"),
        ("GET", "/api/v1/index-performance?start_date=2024-12-16&end_date=2024-12-16", "Index Performance"),
        ("GET", "/api/v1/composition-changes?start_date=2024-12-16&end_date=2024-12-16", "Composition Changes"),
        ("POST", "/api/v1/export-data", "Export Data")
    ]
    
    base_url = "http://localhost:8001"
    results = []
    
    for method, endpoint, name in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            else:
                # For POST endpoints, send minimal data
                data = {}
                if "build-index" in endpoint:
                    data = {"start_date": "2024-12-16", "end_date": "2024-12-16", "top_n": 2}
                elif "export-data" in endpoint:
                    data = {"start_date": "2024-12-16", "end_date": "2024-12-16"}
                
                response = requests.post(f"{base_url}{endpoint}", json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                print(f"✅ {name}: OK")
                results.append(True)
            else:
                print(f"⚠️ {name}: Status {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            results.append(False)
    
    return results

def main():
    """Run all tests."""
    print("🧪 Streamlit UI Test Suite")
    print("=" * 50)
    
    # Test 1: API Connectivity
    api_ok = test_api_connectivity()
    
    # Test 2: Streamlit UI
    streamlit_ok = test_streamlit_ui()
    
    # Test 3: API Endpoints (only if API is running)
    endpoint_results = []
    if api_ok:
        endpoint_results = test_api_endpoints()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    print(f"FastAPI Service: {'✅ Running' if api_ok else '❌ Not Running'}")
    print(f"Streamlit UI: {'✅ Running' if streamlit_ok else '❌ Not Running'}")
    
    if endpoint_results:
        passed = sum(endpoint_results)
        total = len(endpoint_results)
        print(f"API Endpoints: {passed}/{total} passed")
    
    print("\n🌐 Access URLs:")
    if api_ok:
        print("🔗 FastAPI: http://localhost:8001")
        print("📚 API Docs: http://localhost:8001/docs")
    if streamlit_ok:
        print("🎨 Streamlit UI: http://localhost:8501")
    
    print("\n💡 Instructions:")
    if not api_ok:
        print("1. Start FastAPI service: uvicorn app.backend.main:app --host 0.0.0.0 --port 8001")
    if not streamlit_ok:
        print("2. Start Streamlit UI: streamlit run streamlit_app.py")
    if api_ok and streamlit_ok:
        print("🎉 Both services are running! Open http://localhost:8501 in your browser.")

if __name__ == "__main__":
    main() 