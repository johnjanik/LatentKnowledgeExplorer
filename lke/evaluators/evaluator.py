"""
Evaluation module for benchmarking extracted models.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..core.models import StructuredModel, Concept, Relationship


@dataclass
class BenchmarkResult:
    """Result of running a benchmark test."""
    benchmark_name: str
    passed: bool
    score: float
    expected: Any
    actual: Any
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "benchmark_name": self.benchmark_name,
            "passed": self.passed,
            "score": self.score,
            "expected": self.expected,
            "actual": self.actual,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


@dataclass
class EvaluationReport:
    """Report of evaluation results."""
    model_name: str
    total_benchmarks: int
    passed: int
    failed: int
    average_score: float
    results: List[BenchmarkResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_name": self.model_name,
            "total_benchmarks": self.total_benchmarks,
            "passed": self.passed,
            "failed": self.failed,
            "average_score": self.average_score,
            "results": [r.to_dict() for r in self.results],
            "metadata": self.metadata
        }


class Evaluator:
    """
    Evaluator for testing extracted models against benchmarks.

    This is a minimal implementation that can be extended with
    more sophisticated evaluation methods.
    """

    def __init__(self, model: Optional[StructuredModel] = None):
        """
        Initialize evaluator.

        Args:
            model: StructuredModel to evaluate
        """
        self.model = model

    def evaluate(self, benchmarks: List[Dict[str, Any]],
                model: Optional[StructuredModel] = None) -> EvaluationReport:
        """
        Evaluate a model against a set of benchmarks.

        Args:
            benchmarks: List of benchmark specifications
            model: Model to evaluate (uses self.model if not provided)

        Returns:
            EvaluationReport with results
        """
        if model is None:
            model = self.model

        if model is None:
            raise ValueError("No model provided for evaluation")

        results = []

        for benchmark in benchmarks:
            result = self._run_benchmark(benchmark, model)
            results.append(result)

        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        avg_score = sum(r.score for r in results) / len(results) if results else 0.0

        return EvaluationReport(
            model_name=model.domain_name,
            total_benchmarks=len(benchmarks),
            passed=passed,
            failed=failed,
            average_score=avg_score,
            results=results
        )

    def _run_benchmark(self, benchmark: Dict[str, Any],
                      model: StructuredModel) -> BenchmarkResult:
        """
        Run a single benchmark test.

        Args:
            benchmark: Benchmark specification
            model: Model to test

        Returns:
            BenchmarkResult
        """
        benchmark_type = benchmark.get("type", "unknown")

        try:
            if benchmark_type == "concept_exists":
                return self._test_concept_exists(benchmark, model)
            elif benchmark_type == "relationship_exists":
                return self._test_relationship_exists(benchmark, model)
            elif benchmark_type == "concept_count":
                return self._test_concept_count(benchmark, model)
            else:
                return BenchmarkResult(
                    benchmark_name=benchmark.get("name", "unknown"),
                    passed=False,
                    score=0.0,
                    expected=None,
                    actual=None,
                    error_message=f"Unknown benchmark type: {benchmark_type}"
                )
        except Exception as e:
            return BenchmarkResult(
                benchmark_name=benchmark.get("name", "unknown"),
                passed=False,
                score=0.0,
                expected=None,
                actual=None,
                error_message=str(e)
            )

    def _test_concept_exists(self, benchmark: Dict[str, Any],
                           model: StructuredModel) -> BenchmarkResult:
        """Test if a concept exists in the model."""
        expected_name = benchmark.get("expected_concept", "")

        # Search for concept
        found = any(
            c.name.lower() == expected_name.lower()
            for c in model.concepts
        )

        return BenchmarkResult(
            benchmark_name=benchmark.get("name", "concept_exists"),
            passed=found,
            score=1.0 if found else 0.0,
            expected=expected_name,
            actual=[c.name for c in model.concepts]
        )

    def _test_relationship_exists(self, benchmark: Dict[str, Any],
                                 model: StructuredModel) -> BenchmarkResult:
        """Test if a relationship exists in the model."""
        source_name = benchmark.get("source", "")
        target_name = benchmark.get("target", "")

        # Find concepts
        source_concept = next(
            (c for c in model.concepts if c.name.lower() == source_name.lower()),
            None
        )
        target_concept = next(
            (c for c in model.concepts if c.name.lower() == target_name.lower()),
            None
        )

        if not source_concept or not target_concept:
            return BenchmarkResult(
                benchmark_name=benchmark.get("name", "relationship_exists"),
                passed=False,
                score=0.0,
                expected=f"{source_name} -> {target_name}",
                actual="Concepts not found"
            )

        # Check for relationship
        found = any(
            r.source == source_concept.id and r.target == target_concept.id
            for r in model.relationships
        )

        return BenchmarkResult(
            benchmark_name=benchmark.get("name", "relationship_exists"),
            passed=found,
            score=1.0 if found else 0.0,
            expected=f"{source_name} -> {target_name}",
            actual="Found" if found else "Not found"
        )

    def _test_concept_count(self, benchmark: Dict[str, Any],
                          model: StructuredModel) -> BenchmarkResult:
        """Test if the model has the expected number of concepts."""
        expected_count = benchmark.get("expected_count", 0)
        actual_count = len(model.concepts)

        tolerance = benchmark.get("tolerance", 0)
        passed = abs(actual_count - expected_count) <= tolerance

        # Calculate score based on how close we are
        if expected_count == 0:
            score = 1.0 if actual_count == 0 else 0.0
        else:
            score = max(0.0, 1.0 - abs(actual_count - expected_count) / expected_count)

        return BenchmarkResult(
            benchmark_name=benchmark.get("name", "concept_count"),
            passed=passed,
            score=score,
            expected=expected_count,
            actual=actual_count
        )

    def get_model_quality_score(self, model: Optional[StructuredModel] = None) -> Dict[str, float]:
        """
        Calculate quality metrics for a model.

        Args:
            model: Model to evaluate (uses self.model if not provided)

        Returns:
            Dictionary of quality metrics
        """
        if model is None:
            model = self.model

        if model is None:
            raise ValueError("No model provided for evaluation")

        metrics = {}

        # Concept coverage
        metrics["concept_count"] = len(model.concepts)

        # Relationship density
        if model.concepts:
            metrics["relationship_density"] = len(model.relationships) / len(model.concepts)
        else:
            metrics["relationship_density"] = 0.0

        # Axiom coverage
        metrics["axiom_count"] = len(model.axioms)

        # Average concept confidence
        if model.concepts:
            metrics["avg_concept_confidence"] = sum(c.confidence for c in model.concepts) / len(model.concepts)
        else:
            metrics["avg_concept_confidence"] = 0.0

        # Connectedness (percentage of concepts with at least one relationship)
        connected_concepts = set()
        for rel in model.relationships:
            connected_concepts.add(rel.source)
            connected_concepts.add(rel.target)

        if model.concepts:
            metrics["concept_connectedness"] = len(connected_concepts) / len(model.concepts)
        else:
            metrics["concept_connectedness"] = 0.0

        return metrics
