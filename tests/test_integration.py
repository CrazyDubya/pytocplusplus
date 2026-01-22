"""Integration tests for end-to-end Python to C++ conversion workflow."""

import pytest
import tempfile
import subprocess
import sys
from pathlib import Path
from src.analyzer.code_analyzer import CodeAnalyzer
from src.rules.rule_manager import RuleManager
from src.rules.basic_rules import (
    VariableDeclarationRule,
    FunctionDefinitionRule,
    ClassDefinitionRule
)
from src.converter.code_generator import CodeGenerator


class TestEndToEndConversion:
    """Integration tests for complete conversion workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CodeAnalyzer()
        self.rule_manager = RuleManager()
        self.rule_manager.register_rule(VariableDeclarationRule())
        self.rule_manager.register_rule(FunctionDefinitionRule())
        self.rule_manager.register_rule(ClassDefinitionRule())
        self.generator = CodeGenerator(self.rule_manager)
    
    def test_simple_example_end_to_end(self, tmp_path):
        """Test complete workflow with simple example."""
        # Analyze
        example_file = Path("examples/simple_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        # Set context
        self.rule_manager.set_context({
            'type_info': analysis_result.type_info,
            'performance_bottlenecks': analysis_result.performance_bottlenecks,
            'memory_usage': analysis_result.memory_usage,
            'hot_paths': analysis_result.hot_paths
        })
        
        # Generate
        output_dir = tmp_path / "simple_output"
        self.generator.generate_code(analysis_result, output_dir)
        
        # Verify all expected files exist
        assert (output_dir / "generated.hpp").exists()
        assert (output_dir / "generated.cpp").exists()
        assert (output_dir / "main.cpp").exists()
        assert (output_dir / "wrapper.cpp").exists()
        assert (output_dir / "CMakeLists.txt").exists()
        assert (output_dir / "setup.py").exists()
        assert (output_dir / "python_wrapper" / "__init__.py").exists()
        
        # Verify content quality
        header = (output_dir / "generated.hpp").read_text()
        assert "#pragma once" in header
        assert "namespace pytocpp" in header
        assert len(header) > 100
        
        impl = (output_dir / "generated.cpp").read_text()
        assert '#include "generated.hpp"' in impl
        assert "namespace pytocpp" in impl
        assert len(impl) > 100
    
    def test_class_example_end_to_end(self, tmp_path):
        """Test complete workflow with class example."""
        example_file = Path("examples/class_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        self.rule_manager.set_context({
            'type_info': analysis_result.type_info,
            'performance_bottlenecks': analysis_result.performance_bottlenecks,
            'memory_usage': analysis_result.memory_usage,
            'hot_paths': analysis_result.hot_paths
        })
        
        output_dir = tmp_path / "class_output"
        self.generator.generate_code(analysis_result, output_dir)
        
        # Verify files exist
        assert (output_dir / "generated.hpp").exists()
        assert (output_dir / "generated.cpp").exists()
        
        # Verify class definitions in header
        header = (output_dir / "generated.hpp").read_text()
        assert "class" in header
        # Should have access specifiers
        assert "public:" in header or "private:" in header
    
    def test_complex_example_end_to_end(self, tmp_path):
        """Test complete workflow with complex example."""
        example_file = Path("examples/complex_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        self.rule_manager.set_context({
            'type_info': analysis_result.type_info,
            'performance_bottlenecks': analysis_result.performance_bottlenecks,
            'memory_usage': analysis_result.memory_usage,
            'hot_paths': analysis_result.hot_paths
        })
        
        output_dir = tmp_path / "complex_output"
        self.generator.generate_code(analysis_result, output_dir)
        
        # Verify all files generated
        assert (output_dir / "generated.hpp").exists()
        assert (output_dir / "generated.cpp").exists()
        assert (output_dir / "CMakeLists.txt").exists()
        
        # Verify CMake configuration
        cmake = (output_dir / "CMakeLists.txt").read_text()
        assert "cmake_minimum_required" in cmake
        assert "project(" in cmake
    
    def test_multiple_examples_consistency(self, tmp_path):
        """Test that processing multiple examples maintains consistency."""
        examples = [
            "examples/simple_example.py",
            "examples/class_example.py",
        ]
        
        outputs = []
        for i, example_path in enumerate(examples):
            example_file = Path(example_path)
            analysis_result = self.analyzer.analyze_file(example_file)
            
            self.rule_manager.set_context({
                'type_info': analysis_result.type_info,
                'performance_bottlenecks': analysis_result.performance_bottlenecks,
                'memory_usage': analysis_result.memory_usage,
                'hot_paths': analysis_result.hot_paths
            })
            
            output_dir = tmp_path / f"output_{i}"
            self.generator.generate_code(analysis_result, output_dir)
            outputs.append(output_dir)
        
        # Verify all outputs have consistent structure
        for output_dir in outputs:
            assert (output_dir / "generated.hpp").exists()
            assert (output_dir / "generated.cpp").exists()
            assert (output_dir / "CMakeLists.txt").exists()
            
            # All should have #pragma once
            header = (output_dir / "generated.hpp").read_text()
            assert "#pragma once" in header
    
    def test_analysis_to_generation_data_flow(self, tmp_path):
        """Test that analysis data flows correctly to generation."""
        example_file = Path("examples/simple_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        # Verify analysis found something
        assert analysis_result.type_info
        assert len(analysis_result.type_info) > 0
        
        # Set context with analysis results
        self.rule_manager.set_context({
            'type_info': analysis_result.type_info,
            'performance_bottlenecks': analysis_result.performance_bottlenecks,
            'memory_usage': analysis_result.memory_usage,
            'hot_paths': analysis_result.hot_paths
        })
        
        # Generate code
        output_dir = tmp_path / "dataflow_test"
        self.generator.generate_code(analysis_result, output_dir)
        
        # Verify generated code uses analysis information
        impl = (output_dir / "generated.cpp").read_text()
        
        # Should have some function implementations
        assert "(" in impl and ")" in impl
        # Should have namespace from analysis
        assert "pytocpp" in impl


class TestGeneratedCodeStructure:
    """Tests for the structure and quality of generated code."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CodeAnalyzer()
        self.rule_manager = RuleManager()
        self.rule_manager.register_rule(VariableDeclarationRule())
        self.rule_manager.register_rule(FunctionDefinitionRule())
        self.rule_manager.register_rule(ClassDefinitionRule())
        self.generator = CodeGenerator(self.rule_manager)
    
    def test_header_guard_style(self, tmp_path):
        """Test that headers use #pragma once."""
        example_file = Path("examples/simple_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "header_test"
        self.generator.generate_code(analysis_result, output_dir)
        
        header = (output_dir / "generated.hpp").read_text()
        lines = header.split('\n')
        
        # #pragma once should be near the top
        assert "#pragma once" in lines[0:5]
    
    def test_implementation_includes_header(self, tmp_path):
        """Test that implementation includes its header."""
        example_file = Path("examples/simple_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "include_test"
        self.generator.generate_code(analysis_result, output_dir)
        
        impl = (output_dir / "generated.cpp").read_text()
        lines = impl.split('\n')
        
        # Should include the header early in the file
        found_include = False
        for line in lines[0:20]:
            if '#include "generated.hpp"' in line:
                found_include = True
                break
        
        assert found_include
    
    def test_namespace_usage(self, tmp_path):
        """Test consistent namespace usage."""
        example_file = Path("examples/simple_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "namespace_test"
        self.generator.generate_code(analysis_result, output_dir)
        
        header = (output_dir / "generated.hpp").read_text()
        impl = (output_dir / "generated.cpp").read_text()
        
        # Both should use the same namespace
        assert "namespace pytocpp" in header
        assert "namespace pytocpp" in impl
    
    def test_cmake_build_configuration(self, tmp_path):
        """Test CMake configuration is valid."""
        example_file = Path("examples/simple_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "cmake_test"
        self.generator.generate_code(analysis_result, output_dir)
        
        cmake = (output_dir / "CMakeLists.txt").read_text()
        
        # Should have required CMake elements
        assert "cmake_minimum_required" in cmake
        assert "project(" in cmake
        assert "add_executable" in cmake or "add_library" in cmake
        
        # Should reference generated files
        assert "generated.cpp" in cmake or "generated.hpp" in cmake
    
    def test_python_wrapper_structure(self, tmp_path):
        """Test Python wrapper has correct structure."""
        example_file = Path("examples/simple_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "wrapper_test"
        self.generator.generate_code(analysis_result, output_dir)
        
        wrapper_init = output_dir / "python_wrapper" / "__init__.py"
        assert wrapper_init.exists()
        
        wrapper_content = wrapper_init.read_text()
        # Should have some Python code
        assert len(wrapper_content) > 0


class TestErrorHandling:
    """Tests for error handling in integration scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CodeAnalyzer()
        self.rule_manager = RuleManager()
        self.rule_manager.register_rule(VariableDeclarationRule())
        self.rule_manager.register_rule(FunctionDefinitionRule())
        self.rule_manager.register_rule(ClassDefinitionRule())
        self.generator = CodeGenerator(self.rule_manager)
    
    def test_invalid_python_file(self):
        """Test handling of invalid Python file."""
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
            f.write("def broken(:\n")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(SyntaxError):
                self.analyzer.analyze_file(temp_path)
        finally:
            temp_path.unlink()
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        fake_path = Path("/tmp/nonexistent_file_12345.py")
        
        with pytest.raises(FileNotFoundError):
            self.analyzer.analyze_file(fake_path)
    
    def test_empty_python_file(self, tmp_path):
        """Test handling of empty Python file."""
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")
        
        # Should handle gracefully
        analysis_result = self.analyzer.analyze_file(empty_file)
        
        # Should still generate code (even if minimal)
        output_dir = tmp_path / "empty_output"
        self.generator.generate_code(analysis_result, output_dir)
        
        # Basic files should still be created
        assert (output_dir / "generated.hpp").exists()
        assert (output_dir / "generated.cpp").exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
