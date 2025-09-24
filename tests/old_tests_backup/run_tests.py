"""
Simplified Test Runner for SAMi Backend

Runs all tests with basic reporting.
Essential functionality only - no over-engineering.
"""

import subprocess
import sys
import time
from datetime import datetime


def run_test_category(test_file, category_name):
    """Run a specific test category and return results."""
    print(f"\n{'='*60}")
    print(f"Running {category_name}")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        # Run pytest on specific file
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            f"tests/{test_file}",
            "-v",
            "--tb=short"
        ], capture_output=True, text=True, cwd=".")

        end_time = time.time()
        duration = end_time - start_time

        # Parse pytest output for pass/fail counts
        output_lines = result.stdout.split('\n')
        summary_line = [line for line in output_lines if 'passed' in line or 'failed' in line or 'error' in line]

        if result.returncode == 0:
            status = "PASSED"
            print(f"✅ {category_name}: PASSED ({duration:.1f}s)")
        else:
            status = "FAILED"
            print(f"❌ {category_name}: FAILED ({duration:.1f}s)")

        # Show summary if available
        if summary_line:
            print(f"   {summary_line[-1]}")

        # Show failures if any
        if result.returncode != 0 and result.stdout:
            print(f"\n📋 Output for {category_name}:")
            print(result.stdout[-500:])  # Show last 500 chars to avoid spam

        return {
            "name": category_name,
            "status": status,
            "duration": duration,
            "return_code": result.returncode,
            "output": result.stdout
        }

    except Exception as e:
        print(f"❌ Error running {category_name}: {e}")
        return {
            "name": category_name,
            "status": "ERROR",
            "duration": 0,
            "return_code": -1,
            "output": str(e)
        }


def main():
    """Main test runner function."""
    print("🚀 SAMi Backend Test Suite")
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Target: Complete execution under 5 minutes")

    overall_start = time.time()

    # Define test categories
    test_categories = [
        ("test_rest_apis.py", "REST API Tests"),
        ("test_ai_integration.py", "AI Integration Tests"),
        ("test_basic_flows.py", "Basic Flow Tests")
    ]

    results = []

    # Run each test category
    for test_file, category_name in test_categories:
        result = run_test_category(test_file, category_name)
        results.append(result)

    overall_end = time.time()
    total_duration = overall_end - overall_start

    # Generate summary report
    print(f"\n{'='*80}")
    print("📊 TEST EXECUTION SUMMARY")
    print(f"{'='*80}")

    passed_count = sum(1 for r in results if r["status"] == "PASSED")
    failed_count = sum(1 for r in results if r["status"] == "FAILED")
    error_count = sum(1 for r in results if r["status"] == "ERROR")
    total_count = len(results)

    print(f"📈 Overall Results:")
    print(f"   Total Categories: {total_count}")
    print(f"   Passed: {passed_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Errors: {error_count}")
    print(f"   Success Rate: {(passed_count/total_count*100):.1f}%")
    print(f"   Total Time: {total_duration:.1f}s")

    # Performance check
    if total_duration < 300:  # 5 minutes
        print(f"✅ Performance: Under 5 minutes target ({total_duration:.1f}s)")
    else:
        print(f"⚠️  Performance: Over 5 minutes target ({total_duration:.1f}s)")

    print(f"\n📋 Category Breakdown:")
    for result in results:
        icon = "✅" if result["status"] == "PASSED" else "❌"
        print(f"   {icon} {result['name']}: {result['status']} ({result['duration']:.1f}s)")

    # Show failures
    failed_categories = [r for r in results if r["status"] in ["FAILED", "ERROR"]]
    if failed_categories:
        print(f"\n🔍 Failed Categories:")
        for result in failed_categories:
            print(f"\n📁 {result['name']}:")
            print("   Check the detailed output above for specific test failures")

    print(f"\n🏁 Test run completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Exit with appropriate code
    if failed_count > 0 or error_count > 0:
        print("❌ Some tests failed - check output above")
        sys.exit(1)
    else:
        print("✅ All tests passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()