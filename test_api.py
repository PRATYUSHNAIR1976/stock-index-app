#!/usr/bin/env python3
"""
Simple API test script for the Stock Index Service.

This script tests the main API endpoints to ensure they are working correctly.
Run this after starting the FastAPI server to verify functionality.
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8001"

def test_health():
    """Test the health check endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_build_index():
    """Test the build index endpoint."""
    print("\n🔍 Testing build index endpoint...")
    payload = {
        "start_date": "2024-12-16",
        "end_date": "2024-12-16",
        "top_n": 2
    }
    try:
        response = requests.post(f"{BASE_URL}/api/v1/build-index", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_index_composition():
    """Test the index composition endpoint."""
    print("\n🔍 Testing index composition endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/index-composition?date=2024-12-16")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Date: {data.get('date')}")
            print(f"Total stocks: {data.get('total_stocks')}")
            print(f"Equal weight: {data.get('equal_weight')}")
        else:
            print(f"Response: {response.json()}")
        return response.status_code in [200, 404]
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_index_performance():
    """Test the index performance endpoint."""
    print("\n🔍 Testing index performance endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/index-performance?start_date=2024-12-16&end_date=2024-12-16")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total return: {data.get('total_return')}")
            print(f"Daily returns count: {len(data.get('daily_returns', []))}")
        else:
            print(f"Response: {response.json()}")
        return response.status_code in [200, 404]
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all API tests."""
    print("🚀 Testing Stock Index API")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Build Index", test_build_index),
        ("Index Composition", test_index_composition),
        ("Index Performance", test_index_performance),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status}: {test_name}")
        except Exception as e:
            print(f"❌ ERROR: {test_name} - {e}")
            results.append((test_name, False))
        
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the API implementation.")

if __name__ == "__main__":
    main() 