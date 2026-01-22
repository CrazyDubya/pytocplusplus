import argparse
import sys
import logging
from pathlib import Path
from typing import Tuple

# Fix imports to work with both module and script execution
try:
    # When run as a script
    from analyzer.code_analyzer import CodeAnalyzer
    from rules.rule_manager import RuleManager
    from rules.basic_rules import (
        VariableDeclarationRule,
        FunctionDefinitionRule,
        ClassDefinitionRule
    )
    from converter.code_generator import CodeGenerator
    from testing.benchmark_runner import BenchmarkRunner
    from utils.error_handling import get_enhanced_logger, ValidationHelper
except ImportError:
    # When run as a module
    from src.analyzer.code_analyzer import CodeAnalyzer
    from src.rules.rule_manager import RuleManager
    from src.rules.basic_rules import (
        VariableDeclarationRule,
        FunctionDefinitionRule,
        ClassDefinitionRule
    )
    from src.converter.code_generator import CodeGenerator
    from src.testing.benchmark_runner import BenchmarkRunner
    from src.utils.error_handling import get_enhanced_logger, ValidationHelper

# Set up enhanced logging
logger = get_enhanced_logger("PyToC++")

def setup_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert Python code to optimized C++")
    parser.add_argument("input_file", type=str, help="Input Python file to convert")
    parser.add_argument("--output-dir", type=str, default="generated",
                      help="Output directory for generated C++ files")
    parser.add_argument("--skip-benchmarks", action="store_true",
                      help="Skip running benchmarks")
    parser.add_argument("--verbose", "-v", action="store_true",
                      help="Enable verbose output")
    return parser

def initialize_components() -> Tuple:
    """Initialize and return all necessary components."""
    try:
        analyzer = CodeAnalyzer()
        rule_manager = RuleManager()
        
        # Register rules
        rule_manager.register_rule(VariableDeclarationRule())
        rule_manager.register_rule(FunctionDefinitionRule())
        rule_manager.register_rule(ClassDefinitionRule())
        
        return analyzer, rule_manager
    except Exception as e:
        logger.error(f"Error initializing components: {e}")
        sys.exit(1)

def analyze_python_code(analyzer, input_path: Path):
    """Analyze Python code and return results."""
    try:
        logger.info(f"Analyzing Python code: {input_path}")
        # Validate input file first
        ValidationHelper.validate_python_file(input_path)
        
        return analyzer.analyze_file(input_path)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except SyntaxError as e:
        logger.error(f"Python syntax error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error analyzing Python code: {e}")
        sys.exit(1)

def generate_cpp_code(generator, analysis_result, output_dir: Path) -> None:
    """Generate C++ code from analysis results."""
    try:
        logger.info(f"Generating C++ code in: {output_dir}")
        # Validate output directory
        ValidationHelper.validate_output_directory(output_dir)
        
        generator.generate_code(analysis_result, output_dir)
        logger.success("C++ code generation successful")
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating C++ code: {e}")
        sys.exit(1)

def main() -> None:
    # Parse arguments
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Convert paths to Path objects
    input_path = Path(args.input_file)
    output_dir = Path(args.output_dir)
    
    # Validate input file
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    if not input_path.suffix == '.py':
        logger.error(f"Input file must be a Python file (.py): {input_path}")
        sys.exit(1)
    
    # Initialize components
    analyzer, rule_manager = initialize_components()
    generator = CodeGenerator(rule_manager)
    
    # Analyze Python code
    analysis_result = analyze_python_code(analyzer, input_path)
    
    # Set context for rules
    rule_manager.set_context({
        'type_info': analysis_result.type_info,
        'performance_bottlenecks': analysis_result.performance_bottlenecks,
        'memory_usage': analysis_result.memory_usage,
        'hot_paths': analysis_result.hot_paths
    })
    
    # Generate C++ code
    generate_cpp_code(generator, analysis_result, output_dir)
    
    # Run benchmarks if not skipped
    if not args.skip_benchmarks:
        # Try to find benchmark script
        # First try in the same directory as input file
        benchmark_script = input_path.parent / "benchmark.py"
        
        # If not found, check examples directory
        if not benchmark_script.exists():
            examples_dir = Path.cwd() / "examples"
            benchmark_script = examples_dir / "benchmark.py"
            
        if not benchmark_script.exists():
            logger.warning("Benchmark script not found, skipping benchmarks")
            return
            
        logger.info(f"Using benchmark script: {benchmark_script}")
        
        # Run benchmarks
        logger.info("Running benchmarks...")
        runner = BenchmarkRunner(Path.cwd())
        report = runner.run_benchmarks(output_dir, benchmark_script)
        print(report)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)