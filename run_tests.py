#!/usr/bin/env python3
"""
Automatic test runner for all API endpoints
Usage: python run_tests.py
"""
import subprocess
import sys
import os

def check_dependencies():
    """Check if pytest is installed"""
    try:
        import pytest
        return True
    except ImportError:
        print("ERROR: pytest is not installed.")
        print("Install it with: pip install pytest")
        return False

def check_api_running():
    """Check if API server is running"""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    print("="*60)
    print("Payment Gateway API - Automatic Test Suite")
    print("="*60)
    
    # Check dependencies
    print("\n[1/3] Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("  ✓ pytest is installed")
    
    # Check API is running
    print("\n[2/3] Checking API server...")
    if not check_api_running():
        print("  ✗ API server is not running")
        print("\n  Please start the API server first:")
        print("    cd backend")
        print("    uvicorn app.main:app --reload")
        sys.exit(1)
    print("  ✓ API server is running")
    
    # Run tests
    print("\n[3/3] Running automatic tests...")
    print("="*60)
    
    # Run pytest with verbose output
    result = subprocess.run(
        ["pytest", "tests/", "-v", "--tb=short", "--color=yes"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print("\n" + "="*60)
    if result.returncode == 0:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
        print("\nRun with more details: pytest tests/ -v")
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
