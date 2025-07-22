#!/usr/bin/env python3
"""
Simple test runner for GPTree CLI tool.
This script runs all tests and provides a summary.
"""

import subprocess
import sys
import os

def run_tests():
    """Run all tests using pytest."""
    print("Running GPTree CLI Tool Tests...")
    print("=" * 50)
    
    # Change to the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Check if pytest-cov is available
    try:
        import pytest_cov
        coverage_available = True
        print("📊 Coverage reporting enabled")
    except ImportError:
        coverage_available = False
        print("ℹ️  Coverage reporting disabled (install pytest-cov for coverage)")
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
    
    if coverage_available:
        cmd.extend([
            "--cov=cli_tool_gptree",
            "--cov-report=term-missing", 
            "--cov-report=html:htmlcov"
        ])
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print("\n" + "=" * 50)
            print("✅ All tests passed!")
            if coverage_available:
                print("📊 Coverage report generated in htmlcov/")
        else:
            print("\n" + "=" * 50)
            print("❌ Some tests failed!")
            return False
            
    except FileNotFoundError:
        print("❌ pytest not found. Install it with:")
        print("   pip install pytest")
        print("   pip install pytest-cov  # Optional, for coverage reporting")
        return False
    
    return result.returncode == 0

def run_tests_simple():
    """Run all tests using pytest (no coverage)."""
    print("Running GPTree CLI Tool Tests (Simple Mode)...")
    print("=" * 50)
    
    # Change to the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Simple pytest command
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print("\n" + "=" * 50)
            print("✅ All tests passed!")
        else:
            print("\n" + "=" * 50)
            print("❌ Some tests failed!")
            return False
            
    except FileNotFoundError:
        print("❌ pytest not found. Install it with:")
        print("   pip install pytest")
        return False
    
    return result.returncode == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 