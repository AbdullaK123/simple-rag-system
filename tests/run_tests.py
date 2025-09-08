#!/usr/bin/env python3
"""
Test runner script for the DocumentService tests.
Provides convenient commands to run different test categories.
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 run_tests.py [command]")
        print("\nAvailable commands:")
        print("  all          - Run all tests")
        print("  unit         - Run only unit tests")
        print("  integration  - Run only integration tests")  
        print("  fast         - Run all tests except slow ones")
        print("  coverage     - Run tests with coverage report")
        print("  docs         - Run specific test by name")
        print("\nExamples:")
        print("  python3 run_tests.py all")
        print("  python3 run_tests.py unit")
        print("  python3 run_tests.py coverage")
        return 1

    command = sys.argv[1].lower()
    
    if command == "all":
        return run_command([
            "python3", "-m", "pytest", 
            "tests/test_document_service.py", 
            "-v"
        ])
    
    elif command == "unit":
        return run_command([
            "python3", "-m", "pytest", 
            "tests/test_document_service.py::TestDocumentService",
            "-v"
        ])
    
    elif command == "integration":
        return run_command([
            "python3", "-m", "pytest", 
            "tests/test_document_service.py::TestDocumentServiceIntegration",
            "-v"
        ])
    
    elif command == "fast":
        return run_command([
            "python3", "-m", "pytest", 
            "tests/test_document_service.py",
            "-m", "not slow",
            "-v"
        ])
    
    elif command == "coverage":
        return run_command([
            "python3", "-m", "pytest", 
            "tests/test_document_service.py",
            "--cov=app.services.documents",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "-v"
        ])
    
    elif command == "docs":
        return run_command([
            "python3", "-m", "pytest", 
            "tests/test_document_service.py",
            "-k", "document",
            "-v"
        ])
    
    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
