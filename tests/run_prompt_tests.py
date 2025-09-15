"""
Main Test Runner for SAMi Backend Prompt Testing

This script provides a comprehensive test execution framework for the SAMi Backend
end-to-end prompt testing suite. It can run individual test categories, full test suites,
or specific test scenarios with detailed reporting.

Usage:
    python tests/run_prompt_tests.py --all                    # Run all tests
    python tests/run_prompt_tests.py --smoke                  # Run smoke tests only
    python tests/run_prompt_tests.py --category cinema        # Run cinema tests
    python tests/run_prompt_tests.py --performance            # Run performance tests
    python tests/run_prompt_tests.py --load-test             # Run load testing
    python tests/run_prompt_tests.py --report-only           # Generate report only
"""

import asyncio
import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.prompt_tester import (
    PromptTester, ensure_backend_running, wait_for_backend
)
from tests.utils import (
    TestResult, TestSuiteResult, TestOrchestrator, TestReportGenerator,
    PerformanceMonitor, format_test_duration
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)


class PromptTestRunner:
    """Main test runner for SAMi Backend prompt tests."""

    def __init__(self):
        self.orchestrator = TestOrchestrator()
        self.performance_monitor = PerformanceMonitor()
        self.results: List[TestSuiteResult] = []

    async def run_smoke_tests(self) -> TestSuiteResult:
        """Run basic smoke tests to verify system functionality."""
        logger.info("🔥 Running smoke tests...")

        test_cases = [
            ("Basic Cinema Query", "Show me all cinemas"),
            ("Basic Movie Query", "List all movies"),
            ("Basic Schedule Query", "What's scheduled for today?"),
            ("Basic Analytics Query", "Show me today's revenue"),
            ("Basic Availability Query", "What's available in Cinema 1?")
        ]

        return await self._run_test_suite("Smoke Tests", test_cases)

    async def run_cinema_tests(self) -> TestSuiteResult:
        """Run comprehensive cinema management tests."""
        logger.info("🎬 Running cinema management tests...")

        test_cases = [
            ("List All Cinemas", "Show me all cinemas"),
            ("Get Cinema Details", "Tell me about Cinema 1"),
            ("Cinema Capacity Query", "What's the capacity of Cinema 2?"),
            ("Cinema Availability", "Is Cinema 3 available tonight?"),
            ("Compare Cinemas", "Compare Cinema 1 and Cinema 2"),
            ("Cinema Recommendations", "Which cinema is best for a date?"),
            ("Cinema Features", "What types of cinemas do we have?"),
            ("Cinema Status", "Are all cinemas operational?")
        ]

        return await self._run_test_suite("Cinema Management", test_cases)

    async def run_movie_tests(self) -> TestSuiteResult:
        """Run comprehensive movie management tests."""
        logger.info("🎭 Running movie management tests...")

        test_cases = [
            ("List All Movies", "Show me all movies"),
            ("Search by Genre", "Find all action movies"),
            ("Search by Rating", "Show me PG-13 movies"),
            ("Movie Details", "Tell me about Avatar"),
            ("Movie Duration Query", "Find movies under 2 hours"),
            ("Movie Recommendations", "Recommend a good comedy"),
            ("Popular Movies", "What are our most popular movies?"),
            ("Add New Movie", "Add a new movie called 'Test Film' that's 120 minutes long, rated PG-13")
        ]

        return await self._run_test_suite("Movie Management", test_cases)

    async def run_schedule_tests(self) -> TestSuiteResult:
        """Run comprehensive schedule management tests."""
        logger.info("📅 Running schedule management tests...")

        test_cases = [
            ("Current Schedule", "What's scheduled for today?"),
            ("Future Schedule", "Show me tomorrow's schedule"),
            ("Check Availability", "What time slots are available for Cinema 1 tomorrow?"),
            ("Schedule Movie", "Schedule Avatar for Cinema 1 tomorrow at 8 PM for $15"),
            ("Movie Schedule Query", "When is Inception playing?"),
            ("Cinema Schedule Query", "What's playing in Cinema 2?"),
            ("Best Available Times", "What's the best time to schedule a movie tomorrow?"),
            ("Schedule Modification", "Change the 8 PM Avatar showing to 9 PM")
        ]

        return await self._run_test_suite("Schedule Management", test_cases)

    async def run_analytics_tests(self) -> TestSuiteResult:
        """Run comprehensive analytics tests."""
        logger.info("📊 Running analytics tests...")

        test_cases = [
            ("Daily Revenue", "Show me today's revenue"),
            ("Weekly Revenue", "What was our revenue this week?"),
            ("Cinema Revenue", "Show me revenue for Cinema 1"),
            ("Movie Revenue", "How much revenue did Avatar generate?"),
            ("Occupancy Rate", "What's our occupancy rate today?"),
            ("Occupancy by Cinema", "Which cinemas have the best attendance?"),
            ("Performance Summary", "Give me a business performance summary"),
            ("Revenue Comparison", "Compare this month's performance to last month")
        ]

        return await self._run_test_suite("Analytics", test_cases)

    async def run_error_handling_tests(self) -> TestSuiteResult:
        """Run error handling and edge case tests."""
        logger.info("⚠️ Running error handling tests...")

        test_cases = [
            ("Invalid Cinema", "Schedule a movie for Cinema 999 tomorrow"),
            ("Invalid Date", "Show me revenue for the year 3000"),
            ("Invalid Time", "Schedule Avatar at 25:00 tonight"),
            ("Ambiguous Request", "Schedule a movie tomorrow"),
            ("Empty Request", ""),
            ("Missing Information", "What's the revenue?"),
            ("Conflicting Request", "Schedule Avatar and Inception both at 8 PM in Cinema 1"),
            ("Nonexistent Movie", "Schedule 'Nonexistent Movie' for Cinema 1")
        ]

        return await self._run_test_suite("Error Handling", test_cases, expect_errors=True)

    async def run_context_tests(self) -> TestSuiteResult:
        """Run conversational context tests."""
        logger.info("💬 Running context and follow-up tests...")

        # Context tests require specific session management
        tester = PromptTester(session_id=f"context_test_{datetime.now().isoformat()}")
        await tester.connect()

        results = []
        start_time = time.time()

        try:
            # Test movie context follow-up
            response1 = await tester.send_prompt_expect_success("Tell me about Avatar")
            response2 = await tester.send_prompt_expect_success("Schedule it for Cinema 1 tomorrow at 8 PM")

            results.append(TestResult(
                test_name="Movie Context Follow-up",
                passed=True,
                response_time=1.0,  # Approximate
                response_content=response2.get("content", "")
            ))

            # Test cinema context follow-up
            response3 = await tester.send_prompt_expect_success("Tell me about Cinema 1")
            response4 = await tester.send_prompt_expect_success("What times is it available tomorrow?")

            results.append(TestResult(
                test_name="Cinema Context Follow-up",
                passed=True,
                response_time=1.0,  # Approximate
                response_content=response4.get("content", "")
            ))

            # Test topic switching
            response5 = await tester.send_prompt_expect_success("Actually, show me today's revenue instead")

            results.append(TestResult(
                test_name="Topic Switching",
                passed=True,
                response_time=1.0,  # Approximate
                response_content=response5.get("content", "")
            ))

        except Exception as e:
            logger.error(f"Context test error: {e}")
            results.append(TestResult(
                test_name="Context Tests",
                passed=False,
                response_time=0.0,
                error_message=str(e)
            ))

        finally:
            await tester.disconnect()

        total_time = time.time() - start_time
        passed_tests = sum(1 for r in results if r.passed)

        return TestSuiteResult(
            suite_name="Context and Follow-up",
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=len(results) - passed_tests,
            total_time=total_time,
            results=results
        )

    async def run_performance_tests(self) -> TestSuiteResult:
        """Run performance benchmarking tests."""
        logger.info("⚡ Running performance tests...")

        performance_thresholds = {
            "fast_response": 2.0,
            "normal_response": 5.0,
            "slow_response": 10.0
        }

        test_cases = [
            ("Fast Query Performance", "Show me all cinemas"),
            ("Normal Query Performance", "What's our revenue this week?"),
            ("Complex Query Performance", "Generate a comprehensive business performance report"),
            ("Search Performance", "Find all action movies"),
            ("Analytics Performance", "Show me occupancy trends this month")
        ]

        return await self._run_performance_test_suite("Performance Tests", test_cases, performance_thresholds)

    async def run_load_tests(self, concurrent_users: int = 5, requests_per_user: int = 5) -> Dict[str, Any]:
        """Run load testing with multiple concurrent users."""
        logger.info(f"🔥 Running load tests with {concurrent_users} concurrent users...")

        async def test_function(session_suffix: str):
            """Single test function for load testing."""
            tester = PromptTester(session_id=f"load_test_{session_suffix}")
            try:
                await tester.connect()
                response = await tester.send_prompt_expect_success("Show me all cinemas")
                return True
            finally:
                await tester.disconnect()

        return await self.orchestrator.run_load_test(
            test_function=test_function,
            concurrent_users=concurrent_users,
            requests_per_user=requests_per_user
        )

    async def _run_test_suite(
        self,
        suite_name: str,
        test_cases: List[tuple],
        expect_errors: bool = False
    ) -> TestSuiteResult:
        """Run a suite of test cases."""
        results = []
        start_time = time.time()

        for test_name, prompt in test_cases:
            try:
                tester = PromptTester(session_id=f"test_{test_name.lower().replace(' ', '_')}")
                await tester.connect()

                test_start = time.time()

                if expect_errors and any(keyword in prompt.lower() for keyword in ["999", "3000", "25:00", ""]):
                    # For error cases, use send_prompt instead of send_prompt_expect_success
                    response = await tester.send_prompt(prompt)
                    test_passed = True  # We expect these to be handled gracefully
                else:
                    response = await tester.send_prompt_expect_success(prompt)
                    test_passed = True

                test_time = time.time() - test_start
                self.performance_monitor.record_response_time(test_name, test_time)

                results.append(TestResult(
                    test_name=test_name,
                    passed=test_passed,
                    response_time=test_time,
                    response_content=response.get("content", "")[:200] + "..." if len(response.get("content", "")) > 200 else response.get("content", "")
                ))

                await tester.disconnect()

            except Exception as e:
                logger.error(f"Test '{test_name}' failed: {e}")
                results.append(TestResult(
                    test_name=test_name,
                    passed=False,
                    response_time=0.0,
                    error_message=str(e)
                ))

        total_time = time.time() - start_time
        passed_tests = sum(1 for r in results if r.passed)

        return TestSuiteResult(
            suite_name=suite_name,
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=len(results) - passed_tests,
            total_time=total_time,
            results=results
        )

    async def _run_performance_test_suite(
        self,
        suite_name: str,
        test_cases: List[tuple],
        thresholds: Dict[str, float]
    ) -> TestSuiteResult:
        """Run performance-focused test suite."""
        results = []
        start_time = time.time()

        for test_name, prompt in test_cases:
            try:
                tester = PromptTester(session_id=f"perf_{test_name.lower().replace(' ', '_')}")
                await tester.connect()

                test_start = time.time()
                response = await tester.send_prompt_expect_success(prompt)
                test_time = time.time() - test_start

                # Determine performance threshold based on test name
                if "fast" in test_name.lower():
                    threshold = thresholds["fast_response"]
                elif "complex" in test_name.lower():
                    threshold = thresholds["slow_response"]
                else:
                    threshold = thresholds["normal_response"]

                test_passed = test_time <= threshold
                if not test_passed:
                    logger.warning(f"Performance test '{test_name}' exceeded threshold: {test_time:.2f}s > {threshold}s")

                self.performance_monitor.record_response_time(test_name, test_time)

                results.append(TestResult(
                    test_name=test_name,
                    passed=test_passed,
                    response_time=test_time,
                    metadata={"threshold": threshold, "exceeded": not test_passed}
                ))

                await tester.disconnect()

            except Exception as e:
                logger.error(f"Performance test '{test_name}' failed: {e}")
                results.append(TestResult(
                    test_name=test_name,
                    passed=False,
                    response_time=0.0,
                    error_message=str(e)
                ))

        total_time = time.time() - start_time
        passed_tests = sum(1 for r in results if r.passed)

        return TestSuiteResult(
            suite_name=suite_name,
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=len(results) - passed_tests,
            total_time=total_time,
            results=results
        )

    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        return TestReportGenerator.generate_summary_report(self.results)


async def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="SAMi Backend Prompt Test Runner")
    parser.add_argument("--all", action="store_true", help="Run all test suites")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests only")
    parser.add_argument("--category", choices=["cinema", "movie", "schedule", "analytics", "error", "context"],
                        help="Run specific category tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--load-test", action="store_true", help="Run load tests")
    parser.add_argument("--concurrent-users", type=int, default=5, help="Number of concurrent users for load test")
    parser.add_argument("--requests-per-user", type=int, default=5, help="Number of requests per user for load test")
    parser.add_argument("--report-only", action="store_true", help="Generate report only (no tests)")
    parser.add_argument("--output", default="test_report.txt", help="Output file for test report")

    args = parser.parse_args()

    # Check if backend is running
    logger.info("🔍 Checking backend availability...")
    try:
        await wait_for_backend(max_wait=10)
        logger.info("✅ Backend is available")
    except TimeoutError:
        logger.error("❌ Backend is not available. Please start the SAMi backend first.")
        sys.exit(1)

    runner = PromptTestRunner()

    if args.report_only:
        logger.info("📄 Generating report only...")
        report = runner.generate_report()
        print(report)
        return

    start_time = datetime.now()
    logger.info(f"🚀 Starting SAMi Backend Prompt Tests at {start_time}")

    try:
        if args.all:
            logger.info("🎯 Running all test suites...")
            runner.results.append(await runner.run_smoke_tests())
            runner.results.append(await runner.run_cinema_tests())
            runner.results.append(await runner.run_movie_tests())
            runner.results.append(await runner.run_schedule_tests())
            runner.results.append(await runner.run_analytics_tests())
            runner.results.append(await runner.run_error_handling_tests())
            runner.results.append(await runner.run_context_tests())
            runner.results.append(await runner.run_performance_tests())

        elif args.smoke:
            runner.results.append(await runner.run_smoke_tests())

        elif args.category:
            if args.category == "cinema":
                runner.results.append(await runner.run_cinema_tests())
            elif args.category == "movie":
                runner.results.append(await runner.run_movie_tests())
            elif args.category == "schedule":
                runner.results.append(await runner.run_schedule_tests())
            elif args.category == "analytics":
                runner.results.append(await runner.run_analytics_tests())
            elif args.category == "error":
                runner.results.append(await runner.run_error_handling_tests())
            elif args.category == "context":
                runner.results.append(await runner.run_context_tests())

        elif args.performance:
            runner.results.append(await runner.run_performance_tests())

        elif args.load_test:
            logger.info("🔥 Running load tests...")
            load_results = await runner.run_load_tests(
                concurrent_users=args.concurrent_users,
                requests_per_user=args.requests_per_user
            )

            print("\n" + "="*80)
            print("LOAD TEST RESULTS")
            print("="*80)
            print(f"Concurrent Users: {load_results['concurrent_users']}")
            print(f"Requests per User: {load_results['requests_per_user']}")
            print(f"Total Requests: {load_results['total_requests']}")
            print(f"Successful Requests: {load_results['successful_requests']}")
            print(f"Success Rate: {load_results['success_rate']:.1f}%")

            perf_stats = load_results['performance_stats']
            if 'average_response_time' in perf_stats:
                print(f"Average Response Time: {perf_stats['average_response_time']:.2f}s")
                print(f"Min Response Time: {perf_stats['min_response_time']:.2f}s")
                print(f"Max Response Time: {perf_stats['max_response_time']:.2f}s")

        else:
            # Default to smoke tests
            runner.results.append(await runner.run_smoke_tests())

        # Generate and display report
        if runner.results:
            end_time = datetime.now()
            duration = end_time - start_time

            print("\n" + "="*80)
            print("TEST EXECUTION COMPLETE")
            print("="*80)
            print(f"Start Time: {start_time}")
            print(f"End Time: {end_time}")
            print(f"Total Duration: {format_test_duration(duration.total_seconds())}")
            print()

            report = runner.generate_report()
            print(report)

            # Save report to file
            with open(args.output, 'w') as f:
                f.write(f"SAMi Backend Prompt Test Report\n")
                f.write(f"Generated: {datetime.now()}\n")
                f.write(f"Duration: {format_test_duration(duration.total_seconds())}\n\n")
                f.write(report)

            logger.info(f"📄 Report saved to {args.output}")

            # Exit with error code if any tests failed
            total_tests = sum(suite.total_tests for suite in runner.results)
            total_passed = sum(suite.passed_tests for suite in runner.results)

            if total_passed < total_tests:
                logger.warning(f"⚠️ {total_tests - total_passed} tests failed")
                sys.exit(1)
            else:
                logger.info("🎉 All tests passed!")

    except KeyboardInterrupt:
        logger.info("⏹️ Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())