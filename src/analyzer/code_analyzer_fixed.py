from typing import Dict, List, Any, Optional, Union, Set, Tuple
import ast
import networkx as nx
from dataclasses import dataclass, field
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CodeAnalyzer")

@dataclass
class ClassInfo:
    """Information about a class definition."""
    name: str
    docstring: Optional[str] = None
    bases: List[str] = field(default_factory=list)
    attributes: Dict[str, str] = field(default_factory=dict)  # attr_name -> type
    methods: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # method_name -> info

@dataclass
class AnalysisResult:
    """Container for code analysis results."""
    type_info: Dict[str, Any]
    class_info: Dict[str, ClassInfo]  # class_name -> ClassInfo
    performance_bottlenecks: List[Dict[str, Any]]
    memory_usage: Dict[str, int]
    hot_paths: List[List[str]]
    dependencies: nx.DiGraph
    complexity: Dict[str, int]

class CodeAnalyzer:
    """Analyzes Python code for conversion to C++."""
    
    def __init__(self):
        self.type_info: Dict[str, Any] = {}
        self.class_info: Dict[str, ClassInfo] = {}
        self.current_class: Optional[str] = None
        self.performance_bottlenecks: List[Dict[str, Any]] = []
        self.memory_usage: Dict[str, int] = {}
        self.hot_paths: List[List[str]] = []
        self.dependencies = nx.DiGraph()
        self.complexity: Dict[str, int] = {}
        # Cache mapping id(node) -> inferred C++ type
        self._expr_type_cache: Dict[int, str] = {}
    
    def analyze_file(self, file_path: Path) -> AnalysisResult:
        """Analyze a Python file and return the results."""
        logger.info(f"Analyzing Python code: {file_path}")
        try:
            # Clear expression type cache for a fresh analysis run
            self._expr_type_cache.clear()
            with open(file_path, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Perform various analyses
            self._analyze_classes(tree)  # Analyze classes first to detect inheritance
            self._analyze_types(tree)
            self._analyze_performance(tree)
            self._analyze_memory_usage(tree)
            self._analyze_hot_paths(tree)
            self._analyze_dependencies(tree)
            self._analyze_complexity(tree)
            
            return AnalysisResult(
                type_info=self.type_info,
                class_info=self.class_info,
                performance_bottlenecks=self.performance_bottlenecks,
                memory_usage=self.memory_usage,
                hot_paths=self.hot_paths,
                dependencies=self.dependencies,
                complexity=self.complexity
            )
        except Exception as e:
            logger.error(f"Error analyzing file: {e}")
            raise
    
    def _analyze_classes(self, tree: ast.AST) -> None:
        """Analyze class definitions in the code."""
        # First pass: collect all class names and inheritance
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Get class docstring
                docstring = ast.get_docstring(node)
                
                # Get base classes
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    # Handle more complex base expressions if needed
                
                # Create ClassInfo
                class_info = ClassInfo(
                    name=node.name,
                    docstring=docstring,
                    bases=bases
                )
                
                # Store class info
                self.class_info[node.name] = class_info
                
                # Add class to type_info for type checking
                self.type_info[node.name] = {
                    'type': 'class',
                    'bases': bases,
                    'methods': {},
                    'attributes': {}
                }
                
        # Second pass: analyze class bodies
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self.current_class = node.name
                
                # Analyze class body
                self._analyze_class_body(node)
                
                self.current_class = None
    
    def _analyze_class_body(self, node: ast.ClassDef) -> None:
        """Analyze the body of a class definition."""
        class_info = self.class_info[node.name]
        
        for item in node.body:
            # Skip docstring
            if isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                continue
                
            # Analyze class methods
            if isinstance(item, ast.FunctionDef):
                self._analyze_class_method(node.name, item)
    
    def _analyze_class_method(self, class_name: str, node: ast.FunctionDef) -> None:
        """Analyze a class method."""
        # Get method docstring
        docstring = ast.get_docstring(node)
        
        # Create method info
        method_info = {
            'docstring': docstring,
            'params': {},
            'return_type': None,
            'body': node.body
        }
        
        # Get return type from type hints
        if hasattr(node, 'returns') and node.returns:
            method_info['return_type'] = self._get_type_name(node.returns)
        
        # Get parameter types from type hints (skip self)
        for arg in node.args.args:
            if arg.arg != 'self':  # Skip self parameter
                if hasattr(arg, 'annotation') and arg.annotation:
                    method_info['params'][arg.arg] = self._get_type_name(arg.annotation)
                else:
                    method_info['params'][arg.arg] = 'int'  # Default
        
        # Store method info
        self.class_info[class_name].methods[node.name] = method_info
        
        # Store in type_info as well for type checking
        if class_name in self.type_info and 'methods' in self.type_info[class_name]:
            self.type_info[class_name]['methods'][node.name] = method_info
        
        # Analyze method body to detect attribute assignments
        self._analyze_method_attributes(class_name, node)
    
    def _analyze_method_attributes(self, class_name: str, node: ast.FunctionDef) -> None:
        """Analyze a method body to detect attribute assignments."""
        # Also check method parameters for type hints
        if node.name == '__init__':
            for arg in node.args.args:
                if arg.arg != 'self' and hasattr(arg, 'annotation') and arg.annotation:
                    param_type = self._get_type_name(arg.annotation)
                    self.class_info[class_name].attributes[arg.arg] = param_type
        
        for sub_node in ast.walk(node):
            # Look for assignments to self attributes (self.attr = value)
            if isinstance(sub_node, ast.Assign):
                for target in sub_node.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                        # This is a self attribute assignment
                        attr_name = target.attr
                        attr_type = self._infer_expression_type(sub_node.value)
                        
                        # For string values, ensure type is std::string
                        if isinstance(sub_node.value, ast.Constant) and isinstance(sub_node.value.value, str):
                            attr_type = 'std::string'
                        # For name references, check if it's a parameter with known type
                        elif isinstance(sub_node.value, ast.Name):
                            param_name = sub_node.value.id
                            # Check if this is a constructor parameter with type annotation
                            if node.name == '__init__':
                                for arg in node.args.args:
                                    if arg.arg == param_name and hasattr(arg, 'annotation') and arg.annotation:
                                        attr_type = self._get_type_name(arg.annotation)
                                        break
                        
                        # Store attribute type
                        self.class_info[class_name].attributes[attr_name] = attr_type
                        
                        # Also store in type_info
                        if class_name in self.type_info and 'attributes' in self.type_info[class_name]:
                            self.type_info[class_name]['attributes'][attr_name] = attr_type
    
    def _analyze_types(self, tree: ast.AST) -> None:
        """Analyze and infer types in the code."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                self._infer_variable_type(node)
            elif isinstance(node, ast.FunctionDef) and not self.current_class:
                # Only analyze standalone functions here, class methods are handled separately
                self._infer_function_types(node)
    
    def _analyze_performance(self, tree: ast.AST) -> None:
        """Identify performance bottlenecks."""
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                self._check_loop_performance(node)
            elif isinstance(node, ast.Call):
                self._check_function_call_performance(node)
    
    def _analyze_memory_usage(self, tree: ast.AST) -> None:
        """Analyze memory usage patterns."""
        for node in ast.walk(tree):
            if isinstance(node, ast.List):
                self._analyze_list_memory(node)
            elif isinstance(node, ast.Dict):
                self._analyze_dict_memory(node)
    
    def _analyze_hot_paths(self, tree: ast.AST) -> None:
        """Identify frequently executed code paths."""
        # Basic implementation that marks loops and conditionals
        hot_paths = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                if hasattr(node, 'body') and node.body:
                    path = [self._get_node_location(stmt) for stmt in node.body]
                    hot_paths.append(path)
        self.hot_paths = hot_paths
    
    def _get_node_location(self, node: ast.AST) -> str:
        """Get a string representation of a node's location."""
        if hasattr(node, 'lineno'):
            return f"line_{node.lineno}"
        return "unknown_location"
    
    def _analyze_dependencies(self, tree: ast.AST) -> None:
        """Build dependency graph of the code."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self._add_import_dependency(node)
            elif isinstance(node, ast.ImportFrom):
                self._add_import_from_dependency(node)
    
    def _analyze_complexity(self, tree: ast.AST) -> None:
        """Calculate code complexity metrics."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._calculate_function_complexity(node)

    def _store_type_for_target(self, target: ast.AST, type_str: str) -> None:
        """Helper method to safely store type information for a target."""
        if isinstance(target, ast.Name):
            self.type_info[target.id] = type_str
        elif isinstance(target, ast.Attribute):
            # For attribute access like obj.attr, store as obj.attr
            if isinstance(target.value, ast.Name):
                self.type_info[f"{target.value.id}.{target.attr}"] = type_str
        # For other target types, we don't store type information
    
    def _infer_variable_type(self, node: ast.Assign) -> None:
        """Infer the type of a variable assignment."""
        # Handle tuple targets (unpacking assignments)
        if isinstance(node.targets[0], ast.Tuple):
            self._handle_tuple_target_assignment(node)
            return
        
        # Basic type inference implementation
        if isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, bool):  # Check bool first (bool is a subclass of int)
                self._store_type_for_target(node.targets[0], 'bool')
            elif isinstance(node.value.value, (int, float)):
                type_str = 'int' if isinstance(node.value.value, int) else 'double'
                self._store_type_for_target(node.targets[0], type_str)
            elif isinstance(node.value.value, str):
                self._store_type_for_target(node.targets[0], 'std::string')
            elif node.value.value is None:
                self._store_type_for_target(node.targets[0], 'std::nullptr_t')
        elif isinstance(node.value, ast.List):
            # Try to infer list element type
            if node.value.elts:
                elt_type = self._infer_expression_type(node.value.elts[0])
                self._store_type_for_target(node.targets[0], f'std::vector<{elt_type}>')
            else:
                self._store_type_for_target(node.targets[0], 'std::vector<int>')  # Default to int
        elif isinstance(node.value, ast.Dict):
            # Try to infer key and value types
            if node.value.keys and node.value.values:
                key_type = self._infer_expression_type(node.value.keys[0])
                value_type = self._infer_expression_type(node.value.values[0])
                self._store_type_for_target(node.targets[0], f'std::map<{key_type}, {value_type}>')
            else:
                self._store_type_for_target(node.targets[0], 'std::map<std::string, int>')  # Default
        elif isinstance(node.value, ast.Set):
            # Try to infer set element type
            if node.value.elts:
                elt_type = self._infer_expression_type(node.value.elts[0])
                self._store_type_for_target(node.targets[0], f'std::set<{elt_type}>')
            else:
                self._store_type_for_target(node.targets[0], 'std::set<int>')  # Default
        elif isinstance(node.value, ast.Tuple):
            # For tuples, we'll use std::tuple
            if node.value.elts:
                elt_types = []
                for elt in node.value.elts:
                    if isinstance(elt, ast.Name):
                        elt_types.append(self._get_type_name(elt))
                    elif isinstance(elt, ast.Subscript):
                        elt_types.append(self._get_type_name(elt))
                    elif isinstance(elt, ast.Tuple):
                        # Handle nested tuples
                        nested_types = []
                        for nested_elt in elt.elts:
                            nested_types.append(self._infer_expression_type(nested_elt))
                        elt_types.append(f'std::tuple<{", ".join(nested_types)}>')
                    else:
                        elt_types.append(self._infer_expression_type(elt))
                self._store_type_for_target(node.targets[0], f'std::tuple<{", ".join(elt_types)}>')
            else:
                self._store_type_for_target(node.targets[0], 'std::tuple<>')
        elif isinstance(node.value, ast.Call):
            # Try to infer type from function call
            if isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id
                if func_name in self.type_info:
                    func_info = self.type_info[func_name]
                    if isinstance(func_info, dict) and 'return_type' in func_info:
                        return_type = func_info['return_type']
                        self._store_type_for_target(node.targets[0], return_type)
                    else:
                        self._store_type_for_target(node.targets[0], 'int')  # Default
                else:
                    # Try to infer type from common built-in functions
                    if func_name == 'int':
                        self._store_type_for_target(node.targets[0], 'int')
                    elif func_name == 'float':
                        self._store_type_for_target(node.targets[0], 'double')
                    elif func_name == 'str':
                        self._store_type_for_target(node.targets[0], 'std::string')
                    elif func_name == 'bool':
                        self._store_type_for_target(node.targets[0], 'bool')
                    elif func_name == 'list':
                        self._store_type_for_target(node.targets[0], 'std::vector<int>')
                    elif func_name == 'dict':
                        self._store_type_for_target(node.targets[0], 'std::map<std::string, int>')
                    elif func_name == 'set':
                        self._store_type_for_target(node.targets[0], 'std::set<int>')
                    else:
                        self._store_type_for_target(node.targets[0], 'int')  # Default
            else:
                self._store_type_for_target(node.targets[0], 'int')  # Default

    def _handle_tuple_target_assignment(self, node: ast.Assign) -> None:
        """Handle tuple unpacking in assignments."""
        target_tuple = node.targets[0]
        
        if isinstance(node.value, ast.Call):
            # If it's a function call, try to get the return type
            if isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id
                if func_name in self.type_info:
                    func_info = self.type_info[func_name]
                    if isinstance(func_info, dict) and 'return_type' in func_info:
                        return_type = func_info['return_type']
                        if return_type and isinstance(return_type, str) and return_type.startswith('std::tuple<'):
                            # Extract the types from the tuple
                            types = return_type[11:-1].split(', ')
                            for i, target in enumerate(target_tuple.elts):
                                if i < len(types):
                                    if isinstance(target, ast.Tuple):
                                        # Handle nested tuple unpacking
                                        if types[i].startswith('std::tuple<'):
                                            nested_types = types[i][11:-1].split(', ')  # Remove std::tuple<>
                                            for j, nested_target in enumerate(target.elts):
                                                if j < len(nested_types) and isinstance(nested_target, ast.Name):
                                                    self.type_info[nested_target.id] = nested_types[j]
                                                elif isinstance(nested_target, ast.Name):
                                                    self.type_info[nested_target.id] = 'int'  # Default
                                        else:
                                            # If not a tuple type, use the same type for all nested elements
                                            for nested_target in target.elts:
                                                if isinstance(nested_target, ast.Name):
                                                    self.type_info[nested_target.id] = 'int'  # Default
                                    elif isinstance(target, ast.Name):
                                        self.type_info[target.id] = types[i]
                                elif isinstance(target, ast.Name):
                                    self.type_info[target.id] = 'int'  # Default
                        else:
                            # Default to int for all targets if return type is not a tuple
                            self._assign_default_types_to_tuple(target_tuple)
                    else:
                        # Default to int for all targets
                        self._assign_default_types_to_tuple(target_tuple)
                else:
                    # Default to int for all targets
                    self._assign_default_types_to_tuple(target_tuple)
            else:
                # Default to int for all targets
                self._assign_default_types_to_tuple(target_tuple)
        elif isinstance(node.value, ast.Tuple):
            # Handle direct tuple assignment
            for i, (target, value) in enumerate(zip(target_tuple.elts, node.value.elts)):
                if isinstance(target, ast.Tuple):
                    # Handle nested tuple unpacking
                    if isinstance(value, ast.Tuple):
                        for j, (nested_target, nested_value) in enumerate(zip(target.elts, value.elts)):
                            if isinstance(nested_target, ast.Name):
                                self.type_info[nested_target.id] = self._infer_expression_type(nested_value)
                    else:
                        # Default to int for nested targets
                        for nested_target in target.elts:
                            if isinstance(nested_target, ast.Name):
                                self.type_info[nested_target.id] = 'int'
                elif isinstance(target, ast.Name):
                    self.type_info[target.id] = self._infer_expression_type(value)
        else:
            # Default to int for all targets
            self._assign_default_types_to_tuple(target_tuple)

    def _assign_default_types_to_tuple(self, target_tuple: ast.Tuple) -> None:
        """Assign default types to all elements in a tuple unpacking."""
        for target in target_tuple.elts:
            if isinstance(target, ast.Tuple):
                for nested_target in target.elts:
                    if isinstance(nested_target, ast.Name):
                        self.type_info[nested_target.id] = 'int'
            elif isinstance(target, ast.Name):
                self.type_info[target.id] = 'int'

    def _infer_expression_type(self, node: ast.AST) -> str:
        """Infer the type of an expression."""
        cache_key = id(node) if hasattr(node, 'lineno') else None
        if cache_key is not None and cache_key in self._expr_type_cache:
            return self._expr_type_cache[cache_key]

        result: str = 'int'

        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):  # Check bool first (bool is a subclass of int)
                result = 'bool'
            elif isinstance(node.value, int):
                result = 'int'
            elif isinstance(node.value, float):
                result = 'double'
            elif isinstance(node.value, str):
                result = 'std::string'
            elif node.value is None:
                result = 'std::nullptr_t'
        elif isinstance(node, ast.Name):
            # Check if we already know the type of this variable
            if node.id in self.type_info:
                type_info = self.type_info[node.id]
                if isinstance(type_info, str):
                    result = type_info
                else:
                    result = 'int'
            else:
                # Otherwise infer from common names
                if node.id == 'int':
                    result = 'int'
                elif node.id == 'float':
                    result = 'double'
                elif node.id == 'str':
                    result = 'std::string'
                elif node.id == 'bool':
                    result = 'bool'
                elif node.id == 'None':
                    result = 'std::nullptr_t'
                else:
                    result = 'int'
        elif isinstance(node, ast.List):
            if node.elts:
                elt_type = self._infer_expression_type(node.elts[0])
                result = f'std::vector<{elt_type}>'
            else:
                result = 'std::vector<int>'
        elif isinstance(node, ast.Dict):
            if node.keys and node.values:
                key_type = self._infer_expression_type(node.keys[0])
                value_type = self._infer_expression_type(node.values[0])
                result = f'std::map<{key_type}, {value_type}>'
            else:
                result = 'std::map<std::string, int>'
        elif isinstance(node, ast.Set):
            if node.elts:
                elt_type = self._infer_expression_type(node.elts[0])
                result = f'std::set<{elt_type}>'
            else:
                result = 'std::set<int>'
        elif isinstance(node, ast.Tuple):
            if node.elts:
                elt_types = []
                for elt in node.elts:
                    if isinstance(elt, ast.Name):
                        elt_types.append(self._get_type_name(elt))
                    elif isinstance(elt, ast.Subscript):
                        elt_types.append(self._get_type_name(elt))
                    else:
                        elt_types.append(self._infer_expression_type(elt))
                result = f'std::tuple<{", ".join(elt_types)}>'
            else:
                result = 'std::tuple<>'
        elif isinstance(node, ast.BinOp):
            # For binary operations, infer type based on operands
            left_type = self._infer_expression_type(node.left)
            right_type = self._infer_expression_type(node.right)
            # If either operand is double, result is double
            if 'double' in (left_type, right_type):
                result = 'double'
            # If string + string, result is string
            elif left_type == 'std::string' and right_type == 'std::string':
                result = 'std::string'
            # If string + string, result is string
            else:
                result = 'int'
        elif isinstance(node, ast.UnaryOp):
            # Infer type based on operand
            operand_type = self._infer_expression_type(node.operand)
            # For not operator, result is bool
            if isinstance(node.op, ast.Not):
                result = 'bool'
            else:
                result = operand_type
        elif isinstance(node, ast.Compare):
            # Compare always returns bool
            result = 'bool'
        elif isinstance(node, ast.BoolOp):
            # Boolean operations always return bool
            result = 'bool'
        elif isinstance(node, ast.Call):
            # Try to infer return type from function
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in self.type_info:
                    func_info = self.type_info[func_name]
                    if isinstance(func_info, dict) and 'return_type' in func_info:
                        result = func_info['return_type']
                    else:
                        result = 'int'
                else:
                    # Common built-in functions
                    if func_name == 'int':
                        result = 'int'
                    elif func_name == 'float':
                        result = 'double'
                    elif func_name == 'str':
                        result = 'std::string'
                    elif func_name == 'bool':
                        result = 'bool'
                    elif func_name == 'list':
                        result = 'std::vector<int>'
                    elif func_name == 'dict':
                        result = 'std::map<std::string, int>'
                    elif func_name == 'set':
                        result = 'std::set<int>'
                    elif func_name == 'tuple':
                        result = 'std::tuple<int>'
                    elif func_name == 'sum':
                        result = 'int'
                    elif func_name == 'len':
                        result = 'int'
                    elif func_name == 'min' or func_name == 'max':
                        if node.args:
                            result = self._infer_expression_type(node.args[0])
                        else:
                            result = 'int'
                    else:
                        result = 'int'
            else:
                result = 'int'
        elif isinstance(node, ast.Subscript):
            # Handle container access
            if isinstance(node.value, ast.Name):
                value_name = node.value.id
                if value_name in self.type_info:
                    type_info = self.type_info[value_name]
                    # Extract inner type from container types
                    if isinstance(type_info, str):
                        if type_info.startswith('std::vector<'):
                            result = type_info[12:-1]
                            self._expr_type_cache[id(node)] = result
                            return result
                        elif type_info.startswith('std::map<'):
                            parts = type_info[9:-1].split(', ')
                            if len(parts) > 1:
                                result = parts[1]
                                self._expr_type_cache[id(node)] = result
                                return result
                        elif type_info.startswith('std::tuple<'):
                            parts = type_info[11:-1].split(', ')
                            if parts:
                                result = parts[0]
                                self._expr_type_cache[id(node)] = result
                                return result
            # Try to infer from value type
            value_type = self._infer_expression_type(node.value)
            if value_type.startswith('std::vector<'):
                result = value_type[12:-1]
            elif value_type.startswith('std::map<'):
                parts = value_type[9:-1].split(', ')
                if len(parts) > 1:
                    result = parts[1]
                else:
                    result = 'int'
            else:
                result = 'int'
        else:
            result = 'int'

        if cache_key is not None:
            self._expr_type_cache[cache_key] = result
        return result

    def _infer_function_types(self, node: ast.FunctionDef) -> None:
        """Infer function parameter and return types."""
        # Store function information
        func_info = {
            'docstring': ast.get_docstring(node),
            'params': {},
            'return_type': None,
            'body': node.body
        }
        
        # Get return type from type hints
        if hasattr(node, 'returns') and node.returns:
            func_info['return_type'] = self._get_type_name(node.returns)
        
        # Get parameter types from type hints
        for arg in node.args.args:
            if hasattr(arg, 'annotation') and arg.annotation:
                func_info['params'][arg.arg] = self._get_type_name(arg.annotation)
            else:
                func_info['params'][arg.arg] = 'int'  # Default
        
        # Store function info
        self.type_info[node.name] = func_info
        
        # If no return type hint, try to infer from return statements
        if not func_info['return_type']:
            return_type = self._infer_return_type(node)
            if return_type:
                func_info['return_type'] = return_type
            else:
                func_info['return_type'] = 'void'  # Default if no returns found

    def _infer_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        """Infer the return type of a function from its return statements."""
        return_types = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value:
                return_types.append(self._infer_expression_type(child.value))
        
        if not return_types:
            return None
        
        # If all return types are the same, use that
        if all(t == return_types[0] for t in return_types):
            return return_types[0]
        
        # If multiple return types, consider using a variant or the most common
        # For now, just use the first one as a default
        return return_types[0]

    def _get_type_name(self, node: ast.AST) -> str:
        """Get C++ type name from Python type annotation."""
        if isinstance(node, ast.Name):
            # Basic types
            if node.id == 'int':
                return 'int'
            elif node.id == 'float':
                return 'double'
            elif node.id == 'str':
                return 'std::string'
            elif node.id == 'bool':
                return 'bool'
            elif node.id == 'None' or node.id == 'NoneType':
                return 'std::nullptr_t'
                
            # Check if it's a class type we know about
            if node.id in self.class_info:
                # It's a class we've analyzed, use the class name
                return node.id
                
            # Return the name for other user-defined types
            return node.id
        elif isinstance(node, ast.Tuple):
            # Handle tuple type annotations directly
            elt_types = []
            for e in node.elts:
                if isinstance(e, ast.Name):
                    elt_types.append(self._get_type_name(e))
                elif isinstance(e, ast.Subscript):
                    elt_types.append(self._get_type_name(e))
                else:
                    elt_types.append('int')  # Default type
            return f'std::tuple<{", ".join(elt_types)}>'
        elif isinstance(node, ast.Subscript):
            # Handle generic types like List[int], Dict[str, int], etc.
            if isinstance(node.value, ast.Name):
                base_type = node.value.id
                
                # Get the slice/index - depends on Python version
                if isinstance(node.slice, ast.Index):  # Python 3.8 and earlier
                    elt = node.slice.value
                else:  # Python 3.9 and later
                    elt = node.slice
                
                # Handle different collection types
                if base_type == 'list' or base_type == 'List':
                    inner_type = self._get_type_name(elt)
                    return f'std::vector<{inner_type}>'
                elif base_type == 'dict' or base_type == 'Dict':
                    # Dict takes two type parameters
                    if isinstance(elt, ast.Tuple) and len(elt.elts) >= 2:
                        key_type = self._get_type_name(elt.elts[0])
                        value_type = self._get_type_name(elt.elts[1])
                        return f'std::map<{key_type}, {value_type}>'
                    else:
                        # Default if not a proper tuple
                        return 'std::map<std::string, int>'
                elif base_type == 'set' or base_type == 'Set':
                    inner_type = self._get_type_name(elt)
                    return f'std::set<{inner_type}>'
                elif base_type == 'tuple' or base_type == 'Tuple':
                    # Tuple can take multiple type parameters
                    if isinstance(elt, ast.Tuple):
                        elt_types = [self._get_type_name(e) for e in elt.elts]
                        return f'std::tuple<{", ".join(elt_types)}>'
                    else:
                        # Single type parameter
                        inner_type = self._get_type_name(elt)
                        return f'std::tuple<{inner_type}>'
                elif base_type == 'Optional':
                    # Handle Optional[T] -> std::optional<T>
                    inner_type = self._get_type_name(elt)
                    return f'std::optional<{inner_type}>'
                elif base_type == 'Union':
                    # Handle Union[T1, T2, ...] -> std::variant<T1, T2, ...>
                    if isinstance(elt, ast.Tuple):
                        variant_types = [self._get_type_name(e) for e in elt.elts]
                        return f'std::variant<{", ".join(variant_types)}>'
                    else:
                        # Single type in union (not very useful)
                        inner_type = self._get_type_name(elt)
                        return f'std::variant<{inner_type}>'
                else:
                    # Check if it's a class type with a template parameter
                    if base_type in self.class_info:
                        inner_type = self._get_type_name(elt)
                        return f'{base_type}<{inner_type}>'
                        
                    # Unknown generic type - return as is
                    inner_type = self._get_type_name(elt)
                    return f'{base_type}<{inner_type}>'
            return 'int'  # Default
        elif isinstance(node, ast.Constant):
            # Handle literal types
            if isinstance(node.value, bool):
                return 'bool'
            elif isinstance(node.value, str):
                return 'std::string'
            elif isinstance(node.value, int):
                return 'int'
            elif isinstance(node.value, float):
                return 'double'
            elif node.value is None:
                return 'std::nullptr_t'
            return 'int'  # Default type
        return 'int'  # Default type for unknown annotations
    
    def _check_loop_performance(self, node: ast.For) -> None:
        """Check for performance issues in loops."""
        # Basic loop performance analysis
        bottleneck = {
            'type': 'loop',
            'location': f"line_{node.lineno}",
            'description': "Potential loop optimization opportunity"
        }
        
        # Check for nested loops (O(n²) or worse)
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)) and child != node:
                bottleneck['severity'] = 'high'
                bottleneck['description'] = "Nested loop detected - potential O(n²) operation"
                self.performance_bottlenecks.append(bottleneck)
                return
        
        # Check for container modifications inside loop
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                if child.func.attr in ('append', 'extend', 'insert'):
                    bottleneck['severity'] = 'medium'
                    bottleneck['description'] = "Container modification inside loop - consider pre-allocation"
                    self.performance_bottlenecks.append(bottleneck)
                    return
        
        # Add as a low-severity bottleneck for general loops
        bottleneck['severity'] = 'low'
        self.performance_bottlenecks.append(bottleneck)
    
    def _check_function_call_performance(self, node: ast.Call) -> None:
        """Check for performance issues in function calls."""
        # Basic function call performance analysis
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            # Check for known expensive functions
            if func_name in ('sorted', 'filter', 'map', 'reduce'):
                bottleneck = {
                    'type': 'function_call',
                    'location': f"line_{node.lineno}",
                    'description': f"Potentially expensive call to {func_name}",
                    'severity': 'medium'
                }
                self.performance_bottlenecks.append(bottleneck)
    
    def _analyze_list_memory(self, node: ast.List) -> None:
        """Analyze memory usage of list operations."""
        # Basic list memory analysis
        list_id = f"list_{id(node)}"
        
        # Estimate number of elements
        num_elements = len(node.elts)
        
        # Estimate bytes per element (assuming int by default)
        bytes_per_element = 8  # 64-bit (8 bytes) per int
        
        # Calculate estimated memory usage
        memory_usage = num_elements * bytes_per_element
        
        # Store memory usage information
        self.memory_usage[list_id] = memory_usage
    
    def _analyze_dict_memory(self, node: ast.Dict) -> None:
        """Analyze memory usage of dictionary operations."""
        # Basic dictionary memory analysis
        dict_id = f"dict_{id(node)}"
        
        # Estimate number of key-value pairs
        num_elements = len(node.keys)
        
        # Estimate bytes per element (key + value + overhead)
        bytes_per_element = 32  # Rough estimate for key-value pair
        
        # Calculate estimated memory usage
        memory_usage = num_elements * bytes_per_element
        
        # Store memory usage information
        self.memory_usage[dict_id] = memory_usage
    
    def _add_import_dependency(self, node: ast.Import) -> None:
        """Add import dependencies to the graph."""
        for name in node.names:
            self.dependencies.add_edge('current_module', name.name)
    
    def _add_import_from_dependency(self, node: ast.ImportFrom) -> None:
        """Add import from dependencies to the graph."""
        for name in node.names:
            self.dependencies.add_edge(node.module, name.name)
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> None:
        """Calculate cyclomatic complexity of a function."""
        # Base complexity
        complexity = 1
        
        # Count branching statements
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        # Store complexity
        self.complexity[node.name] = complexity