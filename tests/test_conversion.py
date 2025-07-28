import pytest
from pathlib import Path
from src.analyzer.code_analyzer_fixed import CodeAnalyzer
from src.rules.rule_manager import RuleManager
from src.rules.basic_rules import (
    VariableDeclarationRule,
    FunctionDefinitionRule,
    ClassDefinitionRule
)
from src.converter.code_generator_fixed import CodeGenerator

def test_fibonacci_conversion(tmp_path):
    # Setup
    analyzer = CodeAnalyzer()
    rule_manager = RuleManager()
    
    # Register rules
    rule_manager.register_rule(VariableDeclarationRule())
    rule_manager.register_rule(FunctionDefinitionRule())
    rule_manager.register_rule(ClassDefinitionRule())
    
    # Create code generator
    generator = CodeGenerator(rule_manager)
    
    # Analyze example file
    example_file = Path("examples/simple_example.py")
    analysis_result = analyzer.analyze_file(example_file)
    
    # Set context
    rule_manager.set_context({
        'type_info': analysis_result.type_info,
        'performance_bottlenecks': analysis_result.performance_bottlenecks,
        'memory_usage': analysis_result.memory_usage,
        'hot_paths': analysis_result.hot_paths
    })
    
    # Generate C++ code
    output_dir = tmp_path / "generated"
    generator.generate_code(analysis_result, output_dir)
    
    # Verify generated files
    assert (output_dir / "generated.hpp").exists()
    assert (output_dir / "generated.cpp").exists()
    assert (output_dir / "CMakeLists.txt").exists()
    
    # Verify header content
    header_content = (output_dir / "generated.hpp").read_text()
    assert "#pragma once" in header_content
    assert "namespace pytocpp" in header_content
    
    # Verify implementation content
    impl_content = (output_dir / "generated.cpp").read_text()
    assert '#include "generated.hpp"' in impl_content
    assert "namespace pytocpp" in impl_content
    
    # Verify CMake content
    cmake_content = (output_dir / "CMakeLists.txt").read_text()
    assert "cmake_minimum_required" in cmake_content
    assert "project(pytocpp_generated)" in cmake_content 