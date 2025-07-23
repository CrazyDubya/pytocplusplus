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
            temp.write("""
x = 42
y = 3.14
s = "hello"
b = True
none_var = None
empty_list = []
int_list = [1, 2, 3]
mixed_list = [1, "string", 3.14]  # Should default to most permissive type
""".encode('utf-8'))
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
            assert result.type_info['none_var'] == 'std::nullptr_t'
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
            temp.write("""
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
""".encode('utf-8'))
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
            temp.write("""
def simple_function(x: int, y: float) -> str:
    return str(x + y)

def complex_function(data: list[int], options: dict[str, bool] = None) -> tuple[int, float]:
    result = sum(data)
    return result, result / len(data)

def infer_return_type_function(x):
    if x > 0:
        return True
    return False
""".encode('utf-8'))
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
            
            # Check return type inference for function without annotations
            assert 'infer_return_type_function' in result.type_info
            assert result.type_info['infer_return_type_function']['return_type'] == 'bool'
        finally:
            os.unlink(temp_path)
    
    def test_container_types(self):
        """Test handling of container types."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
            temp.write("""
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
""".encode('utf-8'))
            temp_path = temp.name
        
        try:
            # Analyze the file
            analyzer = CodeAnalyzer()
            result = analyzer.analyze_file(Path(temp_path))
            
            # Check container types
            assert result.type_info['int_list'] == 'std::vector<int>'
            assert result.type_info['str_list'] == 'std::vector<std::string>'
            
            assert result.type_info['simple_dict'] == 'std::unordered_map<std::string, int>'
            # complex_dict mapping depends on implementation quality
            
            assert result.type_info['int_set'] == 'std::set<int>'
            assert result.type_info['str_set'] == 'std::set<std::string>'
            
            assert result.type_info['simple_tuple'] == 'std::tuple<int, int, int>'
            # mixed_tuple and nested_tuple depend on implementation quality
        finally:
            os.unlink(temp_path)
    
    def test_performance_analysis(self):
        """Test performance bottleneck detection."""
        # Create a temporary test file with potential performance issues
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
            temp.write("""
def inefficient_function():
    # O(n²) nested loop
    result = []
    for i in range(100):
        for j in range(100):
            result.append(i * j)
    
    # Expensive function call
    sorted_result = sorted(result)
    
    return sorted_result

def append_in_loop():
    items = []
    for i in range(1000):
        items.append(i)  # Inefficient repeated append
    return items
""".encode('utf-8'))
            temp_path = temp.name
        
        try:
            # Analyze the file
            analyzer = CodeAnalyzer()
            result = analyzer.analyze_file(Path(temp_path))
            
            # Check that performance bottlenecks were detected
            assert len(result.performance_bottlenecks) > 0
            
            # Check for specific bottleneck types
            nested_loop_detected = False
            append_detected = False
            
            for bottleneck in result.performance_bottlenecks:
                if bottleneck.get('description', '').startswith('Nested loop'):
                    nested_loop_detected = True
                elif bottleneck.get('description', '').startswith('Container modification'):
                    append_detected = True
            
            assert nested_loop_detected, "Nested loop bottleneck not detected"
            assert append_detected, "Container modification bottleneck not detected"
        finally:
            os.unlink(temp_path)
    
    def test_complexity_analysis(self):
        """Test cyclomatic complexity calculation."""
        # Create a temporary test file with varying complexity
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
            temp.write("""
def simple_function(x):
    return x + 1  # Complexity 1

def complex_function(x):
    if x > 10:  # +1
        if x > 20:  # +1
            return "large"
        else:
            return "medium"
    elif x > 5:  # +1
        return "small"
    else:
        for i in range(x):  # +1
            if i % 2 == 0:  # +1
                print(i)
        return "tiny"
""".encode('utf-8'))
            temp_path = temp.name
        
        try:
            # Analyze the file
            analyzer = CodeAnalyzer()
            result = analyzer.analyze_file(Path(temp_path))
            
            # Check that complexity metrics were calculated
            assert 'simple_function' in result.complexity
            assert 'complex_function' in result.complexity
            
            # Simple function should have complexity 1
            assert result.complexity['simple_function'] == 1
            
            # Complex function should have complexity > 1
            assert result.complexity['complex_function'] >= 5
        finally:
            os.unlink(temp_path)
    
    def test_inference_expressions(self):
        """Test type inference for various expressions."""
        analyzer = CodeAnalyzer()
        
        # Test various expression types
        assert analyzer.type_analyzer._infer_expression_type(ast.Constant(value=42)) == 'int'
        assert analyzer.type_analyzer._infer_expression_type(ast.Constant(value=3.14)) == 'double'
        assert analyzer.type_analyzer._infer_expression_type(ast.Constant(value="hello")) == 'std::string'
        assert analyzer.type_analyzer._infer_expression_type(ast.Constant(value=True)) == 'bool'
        assert analyzer.type_analyzer._infer_expression_type(ast.Constant(value=None)) == 'std::nullptr_t'
        
        # Test binary operations
        bin_op = ast.BinOp(
            left=ast.Constant(value=1),
            op=ast.Add(),
            right=ast.Constant(value=2)
        )
        assert analyzer.type_analyzer._infer_expression_type(bin_op) == 'int'
        
        # Test comparisons
        compare = ast.Compare(
            left=ast.Constant(value=1),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=2)]
        )
        assert analyzer.type_analyzer._infer_expression_type(compare) == 'bool'
        
        # Test boolean operations
        bool_op = ast.BoolOp(
            op=ast.And(),
            values=[ast.Constant(value=True), ast.Constant(value=False)]
        )
        assert analyzer.type_analyzer._infer_expression_type(bool_op) == 'bool'
    
    def test_type_annotation_handling(self):
        """Test handling of Python type annotations."""
        analyzer = CodeAnalyzer()
        
        # Test basic type annotations
        assert analyzer._get_type_name(ast.Name(id='int')) == 'int'
        assert analyzer._get_type_name(ast.Name(id='float')) == 'double'
        assert analyzer._get_type_name(ast.Name(id='str')) == 'std::string'
        assert analyzer._get_type_name(ast.Name(id='bool')) == 'bool'
        
        # Test container type annotations - would be more complex in reality
        # but this is a simplified test for the basic mechanism
        list_annotation = ast.Subscript(
            value=ast.Name(id='list'),
            slice=ast.Name(id='int')
        )
        assert analyzer._get_type_name(list_annotation) == 'std::vector<int>'
        
        # Test optional type
        optional_annotation = ast.Subscript(
            value=ast.Name(id='Optional'),
            slice=ast.Name(id='int')
        )
        assert analyzer._get_type_name(optional_annotation) == 'std::optional<int>'