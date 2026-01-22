"""Performance benchmarking suite for PyToCPlusPlus conversion."""

import time
import tempfile
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
import statistics

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzer.code_analyzer import CodeAnalyzer
from src.rules.rule_manager import RuleManager
from src.rules.basic_rules import (
    VariableDeclarationRule,
    FunctionDefinitionRule,
    ClassDefinitionRule
)
from src.converter.code_generator import CodeGenerator


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    name: str
    file_size_lines: int
    analysis_time: float
    generation_time: float
    total_time: float
    output_size_lines: int


class PerformanceBenchmark:
    """Benchmark suite for measuring conversion performance."""
    
    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.rule_manager = RuleManager()
        self.rule_manager.register_rule(VariableDeclarationRule())
        self.rule_manager.register_rule(FunctionDefinitionRule())
        self.rule_manager.register_rule(ClassDefinitionRule())
        self.generator = CodeGenerator(self.rule_manager)
        self.results: List[BenchmarkResult] = []
    
    def benchmark_file(self, file_path: Path, name: str = None) -> BenchmarkResult:
        """Benchmark conversion of a single file."""
        if name is None:
            name = file_path.name
        
        # Count input lines
        with open(file_path, 'r') as f:
            input_lines = len(f.readlines())
        
        # Benchmark analysis
        start_time = time.perf_counter()
        analysis_result = self.analyzer.analyze_file(file_path)
        analysis_time = time.perf_counter() - start_time
        
        # Set context
        self.rule_manager.set_context({
            'type_info': analysis_result.type_info,
            'performance_bottlenecks': analysis_result.performance_bottlenecks,
            'memory_usage': analysis_result.memory_usage,
            'hot_paths': analysis_result.hot_paths
        })
        
        # Benchmark generation
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            start_time = time.perf_counter()
            self.generator.generate_code(analysis_result, output_dir)
            generation_time = time.perf_counter() - start_time
            
            # Count output lines
            output_lines = 0
            if (output_dir / "generated.hpp").exists():
                with open(output_dir / "generated.hpp", 'r') as f:
                    output_lines += len(f.readlines())
            if (output_dir / "generated.cpp").exists():
                with open(output_dir / "generated.cpp", 'r') as f:
                    output_lines += len(f.readlines())
        
        total_time = analysis_time + generation_time
        
        result = BenchmarkResult(
            name=name,
            file_size_lines=input_lines,
            analysis_time=analysis_time,
            generation_time=generation_time,
            total_time=total_time,
            output_size_lines=output_lines
        )
        
        self.results.append(result)
        return result
    
    def benchmark_all_examples(self) -> List[BenchmarkResult]:
        """Benchmark all example files."""
        examples_dir = Path("examples")
        example_files = [
            examples_dir / "simple_example.py",
            examples_dir / "class_example.py",
            examples_dir / "complex_example.py",
        ]
        
        results = []
        for example_file in example_files:
            if example_file.exists():
                result = self.benchmark_file(example_file)
                results.append(result)
        
        return results
    
    def print_results(self, results: List[BenchmarkResult] = None):
        """Print benchmark results in a formatted table."""
        if results is None:
            results = self.results
        
        if not results:
            print("No benchmark results available.")
            return
        
        print("\n" + "=" * 80)
        print("PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)
        print()
        print(f"{'File':<25} {'Lines':<8} {'Analysis':<12} {'Generation':<12} {'Total':<12} {'Output':<8}")
        print(f"{'Name':<25} {'(in)':<8} {'Time (s)':<12} {'Time (s)':<12} {'Time (s)':<12} {'Lines':<8}")
        print("-" * 80)
        
        for result in results:
            print(f"{result.name:<25} {result.file_size_lines:<8} "
                  f"{result.analysis_time:<12.4f} {result.generation_time:<12.4f} "
                  f"{result.total_time:<12.4f} {result.output_size_lines:<8}")
        
        print("-" * 80)
        
        # Calculate statistics
        if len(results) > 1:
            total_times = [r.total_time for r in results]
            analysis_times = [r.analysis_time for r in results]
            generation_times = [r.generation_time for r in results]
            
            print()
            print("Statistics:")
            print(f"  Average total time:      {statistics.mean(total_times):.4f} s")
            print(f"  Median total time:       {statistics.median(total_times):.4f} s")
            print(f"  Avg analysis time:       {statistics.mean(analysis_times):.4f} s")
            print(f"  Avg generation time:     {statistics.mean(generation_times):.4f} s")
            
            # Calculate throughput
            total_input_lines = sum(r.file_size_lines for r in results)
            total_time_sum = sum(r.total_time for r in results)
            throughput = total_input_lines / total_time_sum if total_time_sum > 0 else 0
            
            print(f"  Throughput:              {throughput:.1f} lines/s")
        
        print("=" * 80)
        print()
    
    def run_multiple_iterations(self, file_path: Path, iterations: int = 5) -> Dict:
        """Run multiple iterations to get stable performance metrics."""
        results = []
        
        for i in range(iterations):
            result = self.benchmark_file(file_path, name=f"{file_path.name}_iter{i+1}")
            results.append(result)
        
        # Calculate statistics
        total_times = [r.total_time for r in results]
        analysis_times = [r.analysis_time for r in results]
        generation_times = [r.generation_time for r in results]
        
        stats = {
            'file': file_path.name,
            'iterations': iterations,
            'total_time_mean': statistics.mean(total_times),
            'total_time_median': statistics.median(total_times),
            'total_time_stdev': statistics.stdev(total_times) if len(total_times) > 1 else 0,
            'analysis_time_mean': statistics.mean(analysis_times),
            'generation_time_mean': statistics.mean(generation_times),
        }
        
        return stats
    
    def print_iteration_stats(self, stats: Dict):
        """Print statistics from multiple iterations."""
        print("\n" + "=" * 80)
        print(f"PERFORMANCE BENCHMARK - {stats['file']} ({stats['iterations']} iterations)")
        print("=" * 80)
        print()
        print(f"Total Time:")
        print(f"  Mean:      {stats['total_time_mean']:.4f} s")
        print(f"  Median:    {stats['total_time_median']:.4f} s")
        print(f"  Std Dev:   {stats['total_time_stdev']:.4f} s")
        print()
        print(f"Component Breakdown:")
        print(f"  Analysis:   {stats['analysis_time_mean']:.4f} s ({stats['analysis_time_mean']/stats['total_time_mean']*100:.1f}%)")
        print(f"  Generation: {stats['generation_time_mean']:.4f} s ({stats['generation_time_mean']/stats['total_time_mean']*100:.1f}%)")
        print("=" * 80)
        print()


def run_benchmarks():
    """Run all performance benchmarks."""
    benchmark = PerformanceBenchmark()
    
    print("\n🚀 Running Performance Benchmarks...")
    print()
    
    # Benchmark all examples
    print("Benchmarking example files...")
    results = benchmark.benchmark_all_examples()
    benchmark.print_results(results)
    
    # Run multiple iterations on simple example for stability
    print("Running stability test (5 iterations on simple example)...")
    simple_example = Path("examples/simple_example.py")
    if simple_example.exists():
        stats = benchmark.run_multiple_iterations(simple_example, iterations=5)
        benchmark.print_iteration_stats(stats)
    
    print("✅ Benchmarks complete!")


if __name__ == "__main__":
    run_benchmarks()
