"""
Test Utilities and Helpers

Utility functions and helper classes for SAMi Backend testing.
Provides common functionality for test data generation, validation, and test orchestration.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from dataclasses import dataclass
import random
import string
import time
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Container for individual test results."""
    test_name: str
    passed: bool
    response_time: float
    error_message: Optional[str] = None
    response_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TestSuiteResult:
    """Container for test suite results."""
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_time: float
    results: List[TestResult]

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        return (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0.0


@dataclass
class RetryMetrics:
    """Container for retry operation metrics."""
    total_attempts: int = 0
    successful_attempts: int = 0
    rate_limit_hits: int = 0
    total_backoff_time: float = 0.0
    max_delay_used: float = 0.0

    @property
    def retry_rate(self) -> float:
        """Calculate percentage of operations that required retries."""
        return ((self.total_attempts - self.successful_attempts) / self.total_attempts * 100) if self.total_attempts > 0 else 0.0


class RetryHandler:
    """
    Handles exponential backoff retry logic for API rate limits.

    Optimized for 1-minute rate limit windows with configurable backoff strategy.
    """

    def __init__(
        self,
        base_delay: float = 5.0,
        max_delay: float = 65.0,
        max_retries: int = 5,
        exponential_base: float = 2.0,
        jitter_percent: float = 0.25
    ):
        """
        Initialize retry handler.

        Args:
            base_delay: Base delay in seconds (default 5s for 1-minute rate limits)
            max_delay: Maximum delay in seconds (default 65s, just over 1 minute)
            max_retries: Maximum number of retry attempts
            exponential_base: Base for exponential backoff calculation
            jitter_percent: Percentage of jitter to add (0.25 = ±25%)
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.exponential_base = exponential_base
        self.jitter_percent = jitter_percent
        self.metrics = RetryMetrics()

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt with exponential backoff and jitter.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds with jitter applied
        """
        # Calculate exponential delay
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        # Add jitter (±jitter_percent)
        jitter_range = delay * self.jitter_percent
        jitter = random.uniform(-jitter_range, jitter_range)
        final_delay = max(0.1, delay + jitter)  # Minimum 0.1 second delay

        self.metrics.max_delay_used = max(self.metrics.max_delay_used, final_delay)
        return final_delay

    def is_rate_limit_error(self, exception: Exception) -> bool:
        """
        Check if exception indicates a rate limit error.

        Args:
            exception: Exception to check

        Returns:
            True if this is a rate limit related error
        """
        error_str = str(exception).lower()

        # HTTP 429 rate limit
        if "429" in error_str:
            return True

        # Common rate limit messages
        rate_limit_indicators = [
            "rate limit",
            "quota exceeded",
            "too many requests",
            "resource has been exhausted",
            "rate_limit_exceeded",
            "quota_exceeded",
            "api_quota_exceeded"
        ]

        return any(indicator in error_str for indicator in rate_limit_indicators)

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if operation should be retried.

        Args:
            exception: Exception that occurred
            attempt: Current attempt number (0-based)

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.max_retries:
            return False

        # Only retry on rate limit errors
        return self.is_rate_limit_error(exception)

    async def execute_with_retry(
        self,
        operation: Callable,
        *args,
        operation_name: str = "operation",
        **kwargs
    ) -> Any:
        """
        Execute an operation with retry logic.

        Args:
            operation: Async function to execute
            *args: Arguments to pass to operation
            operation_name: Name for logging purposes
            **kwargs: Keyword arguments to pass to operation

        Returns:
            Result of successful operation

        Raises:
            Exception: Last exception if all retries exhausted
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            self.metrics.total_attempts += 1

            try:
                result = await operation(*args, **kwargs)
                if attempt == 0:
                    self.metrics.successful_attempts += 1

                if attempt > 0:
                    logger.info(
                        f"{operation_name} succeeded on attempt {attempt + 1}"
                    )

                return result

            except Exception as e:
                last_exception = e

                if self.is_rate_limit_error(e):
                    self.metrics.rate_limit_hits += 1

                if not self.should_retry(e, attempt):
                    logger.error(
                        f"{operation_name} failed after {attempt + 1} attempts: {e}"
                    )
                    raise e

                # Calculate delay for next attempt
                delay = self.calculate_delay(attempt)
                self.metrics.total_backoff_time += delay

                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}. "
                    f"Retrying in {delay:.1f}s..."
                )

                await asyncio.sleep(delay)

        # This shouldn't be reached, but just in case
        if last_exception:
            raise last_exception


def retry_with_backoff(
    base_delay: float = 5.0,
    max_delay: float = 65.0,
    max_retries: int = 5,
    operation_name: Optional[str] = None
):
    """
    Decorator for adding exponential backoff retry logic to async functions.

    Args:
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        max_retries: Maximum number of retry attempts
        operation_name: Optional name for logging (defaults to function name)

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        retry_handler = RetryHandler(
            base_delay=base_delay,
            max_delay=max_delay,
            max_retries=max_retries
        )

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            name = operation_name or func.__name__
            return await retry_handler.execute_with_retry(
                func, *args, operation_name=name, **kwargs
            )

        # Attach metrics to wrapper for inspection
        wrapper.retry_metrics = retry_handler.metrics  # type: ignore

        return wrapper

    return decorator


class TestDataGenerator:
    """Generates test data for various scenarios."""

    @staticmethod
    def generate_movie_data(count: int = 1) -> List[Dict[str, Any]]:
        """Generate test movie data."""
        genres = ["Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Thriller", "Romance"]
        ratings = ["G", "PG", "PG-13", "R", "NC-17"]

        movies = []
        for i in range(count):
            movie = {
                "title": f"Test Movie {i+1}",
                "genre": random.choice(genres),
                "rating": random.choice(ratings),
                "duration": random.randint(90, 180),
                "description": f"A thrilling {random.choice(genres).lower()} movie for testing."
            }
            movies.append(movie)

        return movies

    @staticmethod
    def generate_cinema_data(count: int = 3) -> List[Dict[str, Any]]:
        """Generate test cinema data."""
        cinemas = []
        for i in range(count):
            cinema = {
                "id": i + 1,
                "name": f"Cinema {i + 1}",
                "capacity": random.choice([100, 150, 200, 250]),
                "type": random.choice(["Standard", "Premium", "IMAX"])
            }
            cinemas.append(cinema)

        return cinemas

    @staticmethod
    def generate_schedule_data(
        movie_count: int = 3,
        cinema_count: int = 3,
        days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """Generate test schedule data."""
        schedules = []
        base_date = datetime.now() + timedelta(days=1)  # Start from tomorrow

        for day in range(days_ahead):
            current_date = base_date + timedelta(days=day)

            for cinema_id in range(1, cinema_count + 1):
                for hour in [14, 17, 20, 23]:  # 2 PM, 5 PM, 8 PM, 11 PM
                    schedule = {
                        "movie_id": random.randint(1, movie_count),
                        "cinema_id": cinema_id,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "time": f"{hour:02d}:00",
                        "price": random.choice([10.0, 12.0, 15.0, 18.0, 20.0])
                    }
                    schedules.append(schedule)

        return schedules

    @staticmethod
    def generate_random_string(length: int = 10) -> str:
        """Generate a random string for testing."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def generate_test_session_id() -> str:
        """Generate a unique test session ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = TestDataGenerator.generate_random_string(6)
        return f"test_{timestamp}_{random_suffix}"


class ResponseValidator:
    """Validates AI responses for various criteria."""

    @staticmethod
    def validate_response_completeness(response: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate that response is complete and well-formed."""
        try:
            # Check required fields
            required_fields = ["type", "content", "timestamp"]
            for field in required_fields:
                if field not in response:
                    return False, f"Missing required field: {field}"

            # Check content is not empty
            if not response.get("content", "").strip():
                return False, "Response content is empty"

            # Check timestamp format
            timestamp = response.get("timestamp", "")
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                return False, f"Invalid timestamp format: {timestamp}"

            return True, "Response is complete and valid"

        except Exception as e:
            return False, f"Response validation error: {str(e)}"

    @staticmethod
    def validate_ai_metadata(response: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate AI-specific metadata."""
        try:
            metadata = response.get("metadata", {})

            # Check AI-powered flag
            if not metadata.get("ai_powered"):
                return False, "Response should be marked as AI-powered"

            # Check function calls tracking
            function_calls = metadata.get("function_calls_made")
            if function_calls is None or not isinstance(function_calls, int):
                return False, "Function calls should be tracked as integer"

            # Check handler information
            if "handler" not in metadata:
                return False, "Handler information should be present"

            return True, "AI metadata is valid"

        except Exception as e:
            return False, f"AI metadata validation error: {str(e)}"

    @staticmethod
    def validate_content_keywords(
        response: Dict[str, Any],
        required_keywords: List[str],
        case_sensitive: bool = False
    ) -> Tuple[bool, str]:
        """Validate that response content contains required keywords."""
        try:
            content = response.get("content", "")
            if not case_sensitive:
                content = content.lower()
                required_keywords = [kw.lower() for kw in required_keywords]

            missing_keywords = []
            for keyword in required_keywords:
                if keyword not in content:
                    missing_keywords.append(keyword)

            if missing_keywords:
                return False, f"Missing required keywords: {missing_keywords}"

            return True, "All required keywords found"

        except Exception as e:
            return False, f"Keyword validation error: {str(e)}"

    @staticmethod
    def validate_response_length(
        response: Dict[str, Any],
        min_length: int = 10,
        max_length: int = 5000
    ) -> Tuple[bool, str]:
        """Validate response content length."""
        try:
            content = response.get("content", "")
            length = len(content)

            if length < min_length:
                return False, f"Response too short: {length} < {min_length}"

            if length > max_length:
                return False, f"Response too long: {length} > {max_length}"

            return True, f"Response length appropriate: {length} characters"

        except Exception as e:
            return False, f"Length validation error: {str(e)}"


class PerformanceMonitor:
    """Monitors and analyzes test performance."""

    def __init__(self):
        self.response_times: List[float] = []
        self.operation_times: Dict[str, List[float]] = {}

    def record_response_time(self, operation: str, response_time: float):
        """Record response time for an operation."""
        self.response_times.append(response_time)

        if operation not in self.operation_times:
            self.operation_times[operation] = []
        self.operation_times[operation].append(response_time)

    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.response_times:
            return {"error": "No response times recorded"}

        stats = {
            "total_requests": len(self.response_times),
            "average_response_time": sum(self.response_times) / len(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "median_response_time": sorted(self.response_times)[len(self.response_times) // 2]
        }

        # Per-operation statistics
        operation_stats = {}
        for operation, times in self.operation_times.items():
            operation_stats[operation] = {
                "count": len(times),
                "average": sum(times) / len(times),
                "min": min(times),
                "max": max(times)
            }

        stats["by_operation"] = operation_stats
        return stats

    def check_performance_thresholds(self, thresholds: Dict[str, float]) -> List[str]:
        """Check if performance meets thresholds."""
        issues = []
        stats = self.get_statistics()

        if "average_response_time" in stats:
            avg_time = stats["average_response_time"]

            if "fast_response" in thresholds and avg_time > thresholds["fast_response"]:
                issues.append(f"Average response time {avg_time:.2f}s exceeds fast threshold {thresholds['fast_response']}s")

            if "normal_response" in thresholds and avg_time > thresholds["normal_response"]:
                issues.append(f"Average response time {avg_time:.2f}s exceeds normal threshold {thresholds['normal_response']}s")

        return issues


class TestReportGenerator:
    """Generates comprehensive test reports."""

    @staticmethod
    def generate_retry_report(retry_metrics: Dict[str, Any]) -> str:
        """Generate a detailed retry metrics report."""
        if not retry_metrics or retry_metrics.get("total_attempts", 0) == 0:
            return "No retry metrics available"

        report = [
            "="*60,
            "Rate Limit Retry Metrics Report",
            "="*60,
            f"Total Operations: {retry_metrics.get('total_attempts', 0)}",
            f"Successful First Attempts: {retry_metrics.get('successful_attempts', 0)}",
            f"Operations Requiring Retries: {retry_metrics.get('total_attempts', 0) - retry_metrics.get('successful_attempts', 0)}",
            f"Rate Limit Hits: {retry_metrics.get('rate_limit_hits', 0)}",
            f"Retry Rate: {retry_metrics.get('retry_rate', 0):.1f}%",
            f"Total Backoff Time: {retry_metrics.get('total_backoff_time', 0):.2f}s",
            f"Max Delay Used: {retry_metrics.get('max_delay_used', 0):.2f}s",
            ""
        ]

        # Add efficiency analysis
        total_attempts = retry_metrics.get('total_attempts', 0)
        successful_attempts = retry_metrics.get('successful_attempts', 0)

        if total_attempts > 0:
            success_rate = (successful_attempts / total_attempts) * 100
            if success_rate >= 90:
                efficiency = "Excellent"
            elif success_rate >= 75:
                efficiency = "Good"
            else:
                efficiency = "Needs Attention"

            report.extend([
                f"First Attempt Success Rate: {success_rate:.1f}% ({efficiency})",
                ""
            ])

        # Add recommendations
        rate_limit_hits = retry_metrics.get('rate_limit_hits', 0)
        if rate_limit_hits > 0:
            report.extend([
                "Recommendations:",
                f"   - {rate_limit_hits} rate limit(s) encountered",
                "   - Consider adding delays between test operations",
                "   - Monitor API quota usage patterns",
                ""
            ])

        return "\n".join(report)

    @staticmethod
    def generate_summary_report(suite_results: List[TestSuiteResult]) -> str:
        """Generate a summary report of all test suites."""
        total_tests = sum(suite.total_tests for suite in suite_results)
        total_passed = sum(suite.passed_tests for suite in suite_results)
        total_time = sum(suite.total_time for suite in suite_results)

        report = [
            "="*80,
            "SAMi Backend Prompt Testing Summary Report",
            "="*80,
            f"Total Test Suites: {len(suite_results)}",
            f"Total Tests: {total_tests}",
            f"Passed: {total_passed}",
            f"Failed: {total_tests - total_passed}",
            f"Success Rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "N/A",
            f"Total Time: {total_time:.2f}s",
            "",
            "Suite Breakdown:",
            "-"*40
        ]

        for suite in suite_results:
            report.extend([
                f"📁 {suite.suite_name}:",
                f"   Tests: {suite.passed_tests}/{suite.total_tests}",
                f"   Success Rate: {suite.success_rate:.1f}%",
                f"   Time: {suite.total_time:.2f}s",
                ""
            ])

        return "\n".join(report)

    @staticmethod
    def generate_detailed_report(suite_result: TestSuiteResult) -> str:
        """Generate a detailed report for a specific test suite."""
        report = [
            "="*80,
            f"Detailed Report: {suite_result.suite_name}",
            "="*80,
            f"Total Tests: {suite_result.total_tests}",
            f"Passed: {suite_result.passed_tests}",
            f"Failed: {suite_result.failed_tests}",
            f"Success Rate: {suite_result.success_rate:.1f}%",
            f"Total Time: {suite_result.total_time:.2f}s",
            "",
            "Individual Test Results:",
            "-"*40
        ]

        for result in suite_result.results:
            status_icon = "✅" if result.passed else "❌"
            report.extend([
                f"{status_icon} {result.test_name}",
                f"   Time: {result.response_time:.2f}s",
            ])

            if not result.passed and result.error_message:
                report.append(f"   Error: {result.error_message}")

            if result.metadata:
                report.append(f"   Metadata: {result.metadata}")

            report.append("")

        return "\n".join(report)

    @staticmethod
    def generate_performance_report(monitor: PerformanceMonitor) -> str:
        """Generate a performance analysis report."""
        stats = monitor.get_statistics()

        if "error" in stats:
            return f"Performance Report: {stats['error']}"

        report = [
            "="*80,
            "Performance Analysis Report",
            "="*80,
            f"Total Requests: {stats['total_requests']}",
            f"Average Response Time: {stats['average_response_time']:.2f}s",
            f"Min Response Time: {stats['min_response_time']:.2f}s",
            f"Max Response Time: {stats['max_response_time']:.2f}s",
            f"Median Response Time: {stats['median_response_time']:.2f}s",
            "",
            "Performance by Operation:",
            "-"*40
        ]

        for operation, op_stats in stats.get("by_operation", {}).items():
            report.extend([
                f"🔧 {operation}:",
                f"   Count: {op_stats['count']}",
                f"   Average: {op_stats['average']:.2f}s",
                f"   Min: {op_stats['min']:.2f}s",
                f"   Max: {op_stats['max']:.2f}s",
                ""
            ])

        return "\n".join(report)


class TestOrchestrator:
    """Orchestrates complex test scenarios and workflows."""

    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.test_results: List[TestSuiteResult] = []
        self.retry_metrics: List[Dict[str, Any]] = []

    async def run_load_test(
        self,
        test_function: Callable,
        concurrent_users: int = 5,
        requests_per_user: int = 10
    ) -> Dict[str, Any]:
        """Run a load test with multiple concurrent users."""

        async def user_session(user_id: int):
            """Simulate a single user session."""
            results = []

            for request_num in range(requests_per_user):
                try:
                    start_time = datetime.now()
                    result = await test_function(f"load_user_{user_id}_{request_num}")
                    end_time = datetime.now()

                    response_time = (end_time - start_time).total_seconds()
                    self.performance_monitor.record_response_time("load_test", response_time)

                    results.append({
                        "user_id": user_id,
                        "request_num": request_num,
                        "success": True,
                        "response_time": response_time
                    })

                except Exception as e:
                    results.append({
                        "user_id": user_id,
                        "request_num": request_num,
                        "success": False,
                        "error": str(e)
                    })

            return results

        # Run concurrent user sessions
        user_tasks = [user_session(i) for i in range(concurrent_users)]
        all_results = await asyncio.gather(*user_tasks)

        # Analyze results
        total_requests = concurrent_users * requests_per_user
        successful_requests = sum(
            1 for user_results in all_results
            for result in user_results
            if result["success"]
        )

        return {
            "concurrent_users": concurrent_users,
            "requests_per_user": requests_per_user,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "performance_stats": self.performance_monitor.get_statistics()
        }

    async def run_stress_test(
        self,
        test_function: Callable,
        max_concurrent_users: int = 10,
        ramp_up_time: int = 30
    ) -> Dict[str, Any]:
        """Run a stress test with gradually increasing load."""

        stress_results = []
        ramp_step = max_concurrent_users // 5  # 5 steps

        for concurrent_users in range(ramp_step, max_concurrent_users + 1, ramp_step):
            logger.info(f"Stress test: {concurrent_users} concurrent users")

            load_result = await self.run_load_test(
                test_function,
                concurrent_users=concurrent_users,
                requests_per_user=5  # Fewer requests per user for stress test
            )

            stress_results.append({
                "concurrent_users": concurrent_users,
                "success_rate": load_result["success_rate"],
                "avg_response_time": load_result["performance_stats"].get("average_response_time", 0)
            })

            # Wait between ramp steps
            await asyncio.sleep(ramp_up_time // 5)

        return {
            "max_concurrent_users": max_concurrent_users,
            "ramp_results": stress_results,
            "final_performance": self.performance_monitor.get_statistics()
        }

    def add_retry_metrics(self, metrics: Dict[str, Any]):
        """Add retry metrics from a test session."""
        if metrics:
            self.retry_metrics.append(metrics)

    def get_aggregated_retry_metrics(self) -> Dict[str, Any]:
        """Aggregate retry metrics from all test sessions."""
        if not self.retry_metrics:
            return {}

        aggregated = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "rate_limit_hits": 0,
            "total_backoff_time": 0.0,
            "max_delay_used": 0.0,
            "session_count": len(self.retry_metrics)
        }

        for metrics in self.retry_metrics:
            aggregated["total_attempts"] += metrics.get("total_attempts", 0)
            aggregated["successful_attempts"] += metrics.get("successful_attempts", 0)
            aggregated["rate_limit_hits"] += metrics.get("rate_limit_hits", 0)
            aggregated["total_backoff_time"] += metrics.get("total_backoff_time", 0.0)
            aggregated["max_delay_used"] = max(
                aggregated["max_delay_used"],
                metrics.get("max_delay_used", 0.0)
            )

        # Calculate retry rate
        total_attempts = aggregated["total_attempts"]
        successful_attempts = aggregated["successful_attempts"]
        if total_attempts > 0:
            aggregated["retry_rate"] = ((total_attempts - successful_attempts) / total_attempts) * 100
        else:
            aggregated["retry_rate"] = 0.0

        return aggregated

    def generate_comprehensive_report(self) -> str:
        """Generate a comprehensive test report."""
        report_parts = []

        # Summary report
        if self.test_results:
            report_parts.append(TestReportGenerator.generate_summary_report(self.test_results))

        # Performance report
        report_parts.append(TestReportGenerator.generate_performance_report(self.performance_monitor))

        # Retry metrics report
        if self.retry_metrics:
            aggregated_metrics = self.get_aggregated_retry_metrics()
            report_parts.append(TestReportGenerator.generate_retry_report(aggregated_metrics))

        return "\n\n".join(report_parts)


# Utility functions for common test operations
def create_test_prompt_variations(base_prompt: str, variations: List[str]) -> List[str]:
    """Create variations of a test prompt."""
    prompts = [base_prompt]
    for variation in variations:
        prompts.append(f"{base_prompt} {variation}")
        prompts.append(f"{variation} {base_prompt}")
    return prompts


def extract_key_metrics_from_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key metrics from a response for analysis."""
    return {
        "type": response.get("type", "unknown"),
        "content_length": len(response.get("content", "")),
        "has_metadata": "metadata" in response,
        "ai_powered": response.get("metadata", {}).get("ai_powered", False),
        "function_calls": response.get("metadata", {}).get("function_calls_made", 0),
        "timestamp": response.get("timestamp", "")
    }


async def wait_with_timeout(coro, timeout: float = 30.0):
    """Execute a coroutine with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation timed out after {timeout} seconds")


def format_test_duration(seconds: float) -> str:
    """Format test duration in human-readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"