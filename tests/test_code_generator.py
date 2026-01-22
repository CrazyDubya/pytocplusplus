"""Comprehensive tests for the code generator modules."""

import pytest
import ast
import tempfile
from pathlib import Path
from src.analyzer.code_analyzer import CodeAnalyzer, AnalysisResult
from src.rules.rule_manager import RuleManager
from src.rules.basic_rules import (
    VariableDeclarationRule,
    FunctionDefinitionRule,
    ClassDefinitionRule
)
from src.converter.code_generator import CodeGenerator
from src.converter.code_generator.base import CodeGenerator as BaseCodeGenerator
from src.converter.code_generator.types import TypeHandler
from src.converter.code_generator.expressions import ExpressionTranslator
from src.converter.code_generator.statements import StatementTranslator
from src.converter.code_generator.functions import FunctionGenerator
from src.converter.code_generator.classes import ClassGenerator
from src.converter.code_generator.output import OutputGenerator


class TestCodeGeneratorIntegration:
    """Integration tests for the complete code generation workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CodeAnalyzer()
        self.rule_manager = RuleManager()
        self.rule_manager.register_rule(VariableDeclarationRule())
        self.rule_manager.register_rule(FunctionDefinitionRule())
        self.rule_manager.register_rule(ClassDefinitionRule())
        self.generator = CodeGenerator(self.rule_manager)
    
    def test_simple_function_conversion(self, tmp_path):
        """Test conversion of simple function."""
        example_file = Path("examples/simple_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "generated"
        self.generator.generate_code(analysis_result, output_dir)
        
        # Verify all expected files are generated
        assert (output_dir / "generated.hpp").exists()
        assert (output_dir / "generated.cpp").exists()
        assert (output_dir / "main.cpp").exists()
        assert (output_dir / "wrapper.cpp").exists()
        assert (output_dir / "CMakeLists.txt").exists()
        assert (output_dir / "setup.py").exists()
        assert (output_dir / "python_wrapper" / "__init__.py").exists()
    
    def test_class_conversion(self, tmp_path):
        """Test conversion of class with methods."""
        example_file = Path("examples/class_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "generated_class"
        self.generator.generate_code(analysis_result, output_dir)
        
        # Verify files exist
        assert (output_dir / "generated.hpp").exists()
        assert (output_dir / "generated.cpp").exists()
        
        # Verify header contains class definitions
        header_content = (output_dir / "generated.hpp").read_text()
        assert "class" in header_content
        assert "public:" in header_content or "private:" in header_content
    
    def test_complex_example_conversion(self, tmp_path):
        """Test conversion of complex example with multiple constructs."""
        example_file = Path("examples/complex_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "generated_complex"
        self.generator.generate_code(analysis_result, output_dir)
        
        # Verify all files generated
        assert (output_dir / "generated.hpp").exists()
        assert (output_dir / "generated.cpp").exists()
        
        # Verify implementation has content
        impl_content = (output_dir / "generated.cpp").read_text()
        assert len(impl_content) > 100
        assert "namespace pytocpp" in impl_content
    
    def test_header_includes_pragma_once(self, tmp_path):
        """Test that generated header includes #pragma once."""
        example_file = Path("examples/simple_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "test_header"
        self.generator.generate_code(analysis_result, output_dir)
        
        header_content = (output_dir / "generated.hpp").read_text()
        assert "#pragma once" in header_content
    
    def test_implementation_includes_header(self, tmp_path):
        """Test that implementation includes the header file."""
        example_file = Path("examples/simple_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "test_impl"
        self.generator.generate_code(analysis_result, output_dir)
        
        impl_content = (output_dir / "generated.cpp").read_text()
        assert '#include "generated.hpp"' in impl_content
    
    def test_cmake_file_structure(self, tmp_path):
        """Test that CMake file has correct structure."""
        example_file = Path("examples/simple_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "test_cmake"
        self.generator.generate_code(analysis_result, output_dir)
        
        cmake_content = (output_dir / "CMakeLists.txt").read_text()
        assert "cmake_minimum_required" in cmake_content
        assert "project(" in cmake_content
        assert "add_executable" in cmake_content or "add_library" in cmake_content
    
    def test_pybind_wrapper_generation(self, tmp_path):
        """Test that pybind11 wrapper is generated."""
        example_file = Path("examples/simple_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "test_pybind"
        self.generator.generate_code(analysis_result, output_dir)
        
        wrapper_content = (output_dir / "wrapper.cpp").read_text()
        assert "pybind11" in wrapper_content or "PYBIND11_MODULE" in wrapper_content
    
    def test_python_wrapper_generation(self, tmp_path):
        """Test that Python wrapper module is generated."""
        example_file = Path("examples/simple_example.py")
        analysis_result = self.analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "test_py_wrapper"
        self.generator.generate_code(analysis_result, output_dir)
        
        wrapper_file = output_dir / "python_wrapper" / "__init__.py"
        assert wrapper_file.exists()
        
        wrapper_content = wrapper_file.read_text()
        assert len(wrapper_content) > 0


class TestTypeHandler:
    """Tests for TypeHandler module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule_manager = RuleManager()
        self.generator = CodeGenerator(self.rule_manager)
        self.type_handler = TypeHandler(self.generator)
    
    def test_infer_int_type(self):
        """Test inference of int type."""
        code = "x = 42"
        tree = ast.parse(code)
        node = tree.body[0].value
        
        result = self.type_handler._infer_cpp_type(node, {})
        assert result in ['int', 'auto']
    
    def test_infer_float_type(self):
        """Test inference of float/double type."""
        code = "x = 3.14"
        tree = ast.parse(code)
        node = tree.body[0].value
        
        result = self.type_handler._infer_cpp_type(node, {})
        assert result in ['double', 'float', 'auto']
    
    def test_infer_string_type(self):
        """Test inference of string type."""
        code = 's = "hello"'
        tree = ast.parse(code)
        node = tree.body[0].value
        
        result = self.type_handler._infer_cpp_type(node, {})
        assert result in ['std::string', 'auto']
    
    def test_infer_bool_type(self):
        """Test inference of bool type."""
        code = "b = True"
        tree = ast.parse(code)
        node = tree.body[0].value
        
        result = self.type_handler._infer_cpp_type(node, {})
        assert result in ['bool', 'auto']
    
    def test_get_default_value_int(self):
        """Test getting default value for int type."""
        result = self.type_handler._get_default_value('int')
        assert result == '0'
    
    def test_get_default_value_double(self):
        """Test getting default value for double type."""
        result = self.type_handler._get_default_value('double')
        assert result == '0.0'
    
    def test_get_default_value_string(self):
        """Test getting default value for string type."""
        result = self.type_handler._get_default_value('std::string')
        assert result == '""'
    
    def test_get_default_value_bool(self):
        """Test getting default value for bool type."""
        result = self.type_handler._get_default_value('bool')
        assert result == 'false'


class TestExpressionTranslator:
    """Tests for ExpressionTranslator module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule_manager = RuleManager()
        self.generator = CodeGenerator(self.rule_manager)
        self.expr_translator = ExpressionTranslator(self.generator)
    
    def test_translate_binary_addition(self):
        """Test translation of binary addition."""
        code = "x + y"
        tree = ast.parse(code, mode='eval')
        
        result = self.expr_translator._translate_expression(tree.body, {'x': 'int', 'y': 'int'})
        assert 'x' in result
        assert 'y' in result
        assert '+' in result
    
    def test_translate_binary_multiplication(self):
        """Test translation of binary multiplication."""
        code = "a * b"
        tree = ast.parse(code, mode='eval')
        
        result = self.expr_translator._translate_expression(tree.body, {'a': 'int', 'b': 'int'})
        assert 'a' in result
        assert 'b' in result
        assert '*' in result
    
    def test_translate_comparison(self):
        """Test translation of comparison."""
        code = "x > 5"
        tree = ast.parse(code, mode='eval')
        
        result = self.expr_translator._translate_expression(tree.body, {'x': 'int'})
        assert 'x' in result
        assert '5' in result
        assert '>' in result
    
    def test_translate_function_call(self):
        """Test translation of function call."""
        code = "len(my_list)"
        tree = ast.parse(code, mode='eval')
        
        result = self.expr_translator._translate_expression(tree.body, {'my_list': 'std::vector<int>'})
        # Should handle the function call somehow
        assert isinstance(result, str)
        assert len(result) > 0


class TestStatementTranslator:
    """Tests for StatementTranslator module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule_manager = RuleManager()
        self.generator = CodeGenerator(self.rule_manager)
        self.stmt_translator = StatementTranslator(self.generator)
    
    def test_translate_assignment(self):
        """Test translation of assignment statement."""
        code = "x = 42"
        tree = ast.parse(code)
        node = tree.body[0]
        
        result = self.stmt_translator._translate_statement(node, {}, 0)
        assert isinstance(result, str)
        assert 'x' in result or 'auto' in result
    
    def test_translate_return_statement(self):
        """Test translation of return statement."""
        code = "return x + 1"
        tree = ast.parse(code)
        node = tree.body[0]
        
        result = self.stmt_translator._translate_statement(node, {'x': 'int'}, 0)
        assert 'return' in result
    
    def test_translate_if_statement(self):
        """Test translation of if statement."""
        code = """
if x > 0:
    y = 1
else:
    y = 0
"""
        tree = ast.parse(code)
        node = tree.body[0]
        
        result = self.stmt_translator._translate_statement(node, {'x': 'int'}, 0)
        assert 'if' in result
        assert '{' in result or 'if' in result


class TestFunctionGenerator:
    """Tests for FunctionGenerator module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule_manager = RuleManager()
        self.generator = CodeGenerator(self.rule_manager)
        self.func_generator = FunctionGenerator(self.generator)
    
    def test_generate_simple_function(self):
        """Test generation of simple function implementation."""
        func_info = {
            'params': {'n': 'int'},
            'return_type': 'int',
            'body': [],
            'decorators': []
        }
        
        result = self.func_generator._generate_function_impl('calculate', func_info)
        assert 'int calculate' in result
        assert 'int n' in result


class TestOutputGenerator:
    """Tests for OutputGenerator module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule_manager = RuleManager()
        self.generator = CodeGenerator(self.rule_manager)
        # Analyze a simple example to get real analysis results
        self.analyzer = CodeAnalyzer()
        example_file = Path("examples/simple_example.py")
        self.analysis_result = self.analyzer.analyze_file(example_file)
        self.generator.analysis_result = self.analysis_result
        self.output_generator = OutputGenerator(self.generator)
    
    def test_generate_header_structure(self):
        """Test that header has correct structure."""
        header = self.output_generator._generate_header(self.analysis_result)
        
        assert '#pragma once' in header
        assert '#include' in header
        assert 'namespace' in header
    
    def test_generate_implementation_structure(self):
        """Test that implementation has correct structure."""
        impl = self.output_generator._generate_implementation(self.analysis_result)
        
        assert '#include "generated.hpp"' in impl
        assert 'namespace' in impl
    
    def test_generate_main_cpp(self):
        """Test generation of main.cpp file."""
        main = self.output_generator._generate_main_cpp()
        
        assert 'int main' in main
        assert 'return 0' in main
    
    def test_generate_cmake(self):
        """Test generation of CMakeLists.txt."""
        cmake = self.output_generator._generate_cmake()
        
        assert 'cmake_minimum_required' in cmake
        assert 'project(' in cmake
    
    def test_generate_python_wrapper(self):
        """Test generation of Python wrapper."""
        wrapper = self.output_generator._generate_python_wrapper()
        
        assert isinstance(wrapper, str)
        assert len(wrapper) > 0


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility after refactoring."""
    
    def test_import_code_generator(self):
        """Test that CodeGenerator can still be imported from old location."""
        from src.converter.code_generator import CodeGenerator
        
        rule_manager = RuleManager()
        generator = CodeGenerator(rule_manager)
        
        assert generator is not None
        assert hasattr(generator, 'generate_code')
    
    def test_old_workflow_still_works(self, tmp_path):
        """Test that the old workflow still works after refactoring."""
        # This is the workflow from the old test_conversion.py
        analyzer = CodeAnalyzer()
        rule_manager = RuleManager()
        rule_manager.register_rule(VariableDeclarationRule())
        rule_manager.register_rule(FunctionDefinitionRule())
        rule_manager.register_rule(ClassDefinitionRule())
        
        generator = CodeGenerator(rule_manager)
        
        example_file = Path("examples/simple_example.py")
        analysis_result = analyzer.analyze_file(example_file)
        
        output_dir = tmp_path / "backward_compat"
        generator.generate_code(analysis_result, output_dir)
        
        # Verify files were generated
        assert (output_dir / "generated.hpp").exists()
        assert (output_dir / "generated.cpp").exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
