#!/usr/bin/env python3
"""Run the Tests suite and write a JSON summary."""

import json
import os
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
CODEBASE_DIR = TESTS_DIR.parent / "Codebase"
if str(CODEBASE_DIR) not in sys.path:
    sys.path.insert(0, str(CODEBASE_DIR))


def build_summary(result):
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "total_tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
        "was_successful": result.wasSuccessful(),
        "failure_details": [{"test": str(test), "traceback": traceback} for test, traceback in result.failures],
        "error_details": [{"test": str(test), "traceback": traceback} for test, traceback in result.errors],
    }


def main():
    print("=" * 72)
    print("CV Creation Using LLM - Test Execution")
    print("=" * 72)
    print(f"Tests directory: {TESTS_DIR}")
    print(f"Codebase directory: {CODEBASE_DIR}")
    print()

    loader = unittest.TestLoader()
    suite = loader.discover(str(TESTS_DIR), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    summary = build_summary(result)
    summary_path = TESTS_DIR / "test_results.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print()
    print("-" * 72)
    print(f"Total:   {summary['total_tests']}")
    print(f"Passed:  {summary['passed']}")
    print(f"Failed:  {summary['failures']}")
    print(f"Errors:  {summary['errors']}")
    print(f"Skipped: {summary['skipped']}")
    print(f"Summary JSON: {summary_path}")
    print("-" * 72)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())