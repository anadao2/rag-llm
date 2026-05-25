#!/usr/bin/env python
"""Script para rodar todos os testes do projeto."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_test_file(test_name: str, test_path: str) -> bool:
    """Roda um arquivo de teste em subprocesso isolado."""
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print('='*60)
    
    project_root = Path(__file__).parent.absolute()
    
    # Preparar environment
    env = {
        **subprocess.os.environ,
        'PYTHONPATH': str(project_root),
        'OPENAI_API_KEY': 'test-key',
    }
    
    try:
        result = subprocess.run(
            [sys.executable, test_path],
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"[OK] {test_name} completed successfully")
            return True
        else:
            print(f"[FAIL] {test_name} failed with code {result.returncode}")
            return False
    except subprocess.TimeoutExpired:
        print(f"[FAIL] {test_name} timed out")
        return False
    except Exception as e:
        print(f"[FAIL] {test_name} error: {e}")
        return False


def main():
    """Roda todos os testes."""
    print("\n" + "="*60)
    print("RAG-LLM DDD TEST SUITE")
    print("="*60)
    
    tests = [
        ("Domain Layer Tests", "tests/test_domain.py"),
        ("Application Layer Tests", "tests/test_application.py"),
        ("Infrastructure Layer Tests", "tests/test_infrastructure.py"),
        ("Integration Tests", "tests/test_integration.py"),
        ("End-to-End Tests", "tests/test_e2e.py"),
        ("SOLID Principles Tests", "tests/test_solid.py"),
    ]
    
    results = []
    for name, path in tests:
        success = run_test_file(name, path)
        results.append((name, success))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status}: {name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("ALL TESTS PASSED!")
        print("="*60)
        return 0
    else:
        print("SOME TESTS FAILED")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
