import pytest
from pathlib import Path
import ast
import tempfile
import os
from src.analyzer.code_analyzer import CodeAnalyzer, AnalysisResult

class TestCodeAnalyzer:
    
    def test_analyze_file_simple_example(self):
        """Test analyzing the simple example file."""
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_file(Path("examples/simple_example.py"))
        
        # Verify result is correct type
        assert isinstance(result, AnalysisResult)
        
        # Verify function was detected
        assert 'calculate_fibonacci' in result.type_info
        
        # Verify parameter and return types
        func_info = result.type_info['calculate_fibonacci']
        assert func_info['params']['n'] == 'int'
        assert func_info['return_type'] == 'int'
    
    def test_variable_type_inference(self):
        """Test that variable types are correctly inferred."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
            temp.write(b"""
x = 42
y = 3.14
s = "hello"
b = True
empty_list = []
int_list = [1, 2, 3]
mixed_list = [1, "string", 3.14]  # Should default to most permissive type
""")
            temp_path = temp.name
        
        try:
            # Analyze the file
            analyzer = CodeAnalyzer()
            result = analyzer.analyze_file(Path(temp_path))
            
            # Check inferred types
            assert result.type_info['x'] == 'int'
            assert result.type_info['y'] == 'double'
            assert result.type_info['s'] == 'std::string'
            assert result.type_info['b'] == 'bool'
            assert result.type_info['empty_list'] == 'std::vector<int>'  # Default
            assert result.type_info['int_list'] == 'std::vector<int>'
            # Todo: Ideally mixed_list would be std::vector<std::variant<int, std::string, double>>
            # but current implementation doesn't support that
        finally:
            os.unlink(temp_path)
    
    def test_tuple_unpacking(self):
        """Test handling of tuple unpacking assignments."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
            temp.write(b"""
# Simple tuple unpacking
a, b = 1, 2

# Multiple assignment with tuple unpacking
x, y, z = 10, 20, 30

# Nested tuple unpacking
(p, q), r = (1, 2), 3

# Function return unpacking (would require function analysis first)
def get_coordinates():
    return 5, 10

cx, cy = get_coordinates()
""")
            temp_path = temp.name
        
        try:
            # Analyze the file
            analyzer = CodeAnalyzer()
            result = analyzer.analyze_file(Path(temp_path))
            
            # Check that variables are in type_info
            assert 'a' in result.type_info
            assert 'b' in result.type_info
            assert 'x' in result.type_info
            assert 'y' in result.type_info
            assert 'z' in result.type_info
            assert 'p' in result.type_info
            assert 'q' in result.type_info
            assert 'r' in result.type_info
            
            # Nested function will be analyzed, but function call analysis is limited
            assert 'get_coordinates' in result.type_info
            
            # Due to limited call analysis, cx and cy might default to int
            assert 'cx' in result.type_info
            assert 'cy' in result.type_info
        finally:
            os.unlink(temp_path)
    
    def test_function_analysis(self):
        """Test analysis of function definitions with type annotations."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
            temp.write(b"""
def simple_function(x: int, y: float) -> str:
    return str(x + y)

def complex_function(data: list[int], options: dict[str, bool] = None) -> tuple[int, float]:
    result = sum(data)
    return result, result / len(data)
""")
            temp_path = temp.name
        
        try:
            # Analyze the file
            analyzer = CodeAnalyzer()
            result = analyzer.analyze_file(Path(temp_path))
            
            # Check function info
            assert 'simple_function' in result.type_info
            assert result.type_info['simple_function']['params']['x'] == 'int'
            assert result.type_info['simple_function']['params']['y'] == 'double'
            assert result.type_info['simple_function']['return_type'] == 'std::string'
            
            assert 'complex_function' in result.type_info
            assert result.type_info['complex_function']['params']['data'] == 'std::vector<int>'
            # Note: options param type handling depends on the implementation
            assert result.type_info['complex_function']['return_type'] == 'std::tuple<int, double>'
        finally:
            os.unlink(temp_path)
    
    def test_container_types(self):
        """Test handling of container types."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
            temp.write(b"""
# Lists
int_list = [1, 2, 3]
str_list = ["a", "b", "c"]

# Dictionaries
simple_dict = {"a": 1, "b": 2}
complex_dict = {1: [1, 2], 2: [3, 4]}

# Sets
int_set = {1, 2, 3}
str_set = {"a", "b", "c"}

# Tuples
simple_tuple = (1, 2, 3)
mixed_tuple = (1, "a", 3.14)
nested_tuple = ((1, 2), (3, 4))
""")
            temp_path = temp.name
        
        try:
            # Analyze the file
            analyzer = CodeAnalyzer()
            result = analyzer.analyze_file(Path(temp_path))
            
            # Check container types
            assert result.type_info['int_list'] == 'std::vector<int>'
            assert result.type_info['str_list'] == 'std::vector<std::string>'
            
            assert result.type_info['simple_dict'] == 'std::map<std::string, int>'
            # complex_dict depends on implementation quality
            
            assert result.type_info['int_set'] == 'std::set<int>'
            assert result.type_info['str_set'] == 'std::set<std::string>'
            
            assert result.type_info['simple_tuple'] == 'std::tuple<int, int, int>'
            # mixed_tuple and nested_tuple depend on implementation
        finally:
            os.unlink(temp_path)
    
    def test_ast_directly(self):
        """Test analyzer by directly passing AST nodes."""
        # This allows testing without file I/O
        analyzer = CodeAnalyzer()
        
        # Test variable assignment
        assign_node = ast.parse("x = 42").body[0]
        analyzer._infer_variable_type(assign_node)
        assert analyzer.type_info['x'] == 'int'
        
        # Test tuple unpacking
        tuple_node = ast.parse("a, b = 1, 2").body[0]
        analyzer._infer_variable_type(tuple_node)
        assert 'a' in analyzer.type_info
        assert 'b' in analyzer.type_info
        
        # Test function definition
        func_node = ast.parse("def test(x: int) -> str: pass").body[0]
        analyzer._infer_function_types(func_node)
        assert analyzer.type_info['test']['params']['x'] == 'int'
        assert analyzer.type_info['test']['return_type'] == 'std::string'