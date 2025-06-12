from typing import Dict, List, Any, Optional
import ast
import networkx as nx
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AnalysisResult:
    """Container for code analysis results."""
    type_info: Dict[str, str]
    performance_bottlenecks: List[Dict[str, Any]]
    memory_usage: Dict[str, int]
    hot_paths: List[List[str]]
    dependencies: nx.DiGraph
    complexity: Dict[str, int]

class CodeAnalyzer:
    """Analyzes Python code for conversion to C++."""
    
    def __init__(self):
        self.type_info: Dict[str, str] = {}
        self.performance_bottlenecks: List[Dict[str, Any]] = []
        self.memory_usage: Dict[str, int] = {}
        self.hot_paths: List[List[str]] = []
        self.dependencies = nx.DiGraph()
        self.complexity: Dict[str, int] = {}
    
    def analyze_file(self, file_path: Path) -> AnalysisResult:
        """Analyze a Python file and return the results."""
        with open(file_path, 'r') as f:
            content = f.read()

        tree = ast.parse(content)

        # Perform various analyses in a single traversal
        self._traverse_tree(tree)

        return AnalysisResult(
            type_info=self.type_info,
            performance_bottlenecks=self.performance_bottlenecks,
            memory_usage=self.memory_usage,
            hot_paths=self.hot_paths,
            dependencies=self.dependencies,
            complexity=self.complexity
        )

    def _traverse_tree(self, tree: ast.AST) -> None:
        """Walk the AST once and delegate analysis to helper methods."""
        for node in ast.walk(tree):
            self._analyze_types(node)
            self._analyze_performance(node)
            self._analyze_memory_usage(node)
            self._analyze_hot_paths(node)
            self._analyze_dependencies(node)
            self._analyze_complexity(node)

    def _analyze_types(self, node: ast.AST) -> None:
        """Analyze and infer types for a single node."""
        if isinstance(node, ast.Assign):
            self._infer_variable_type(node)
        elif isinstance(node, ast.FunctionDef):
            self._infer_function_types(node)

    def _analyze_performance(self, node: ast.AST) -> None:
        """Identify performance bottlenecks for a single node."""
        if isinstance(node, ast.For):
            self._check_loop_performance(node)
        elif isinstance(node, ast.Call):
            self._check_function_call_performance(node)

    def _analyze_memory_usage(self, node: ast.AST) -> None:
        """Analyze memory usage patterns for a single node."""
        if isinstance(node, ast.List):
            self._analyze_list_memory(node)
        elif isinstance(node, ast.Dict):
            self._analyze_dict_memory(node)

    def _analyze_hot_paths(self, node: ast.AST) -> None:
        """Identify frequently executed code paths."""
        # Implementation will use static analysis and heuristics
        pass

    def _analyze_dependencies(self, node: ast.AST) -> None:
        """Build dependency graph of the code."""
        if isinstance(node, ast.Import):
            self._add_import_dependency(node)
        elif isinstance(node, ast.ImportFrom):
            self._add_import_from_dependency(node)

    def _analyze_complexity(self, node: ast.AST) -> None:
        """Calculate code complexity metrics for a node."""
        if isinstance(node, ast.FunctionDef):
            self._calculate_function_complexity(node)
    
    def _infer_variable_type(self, node: ast.Assign) -> None:
        """Infer the type of a variable assignment."""
        # Handle tuple targets (unpacking assignments) early
        if isinstance(node.targets[0], ast.Tuple):
            # Move existing tuple unpacking logic here
            if isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    func_name = node.value.func.id
                    if func_name in self.type_info:
                        return_type = self.type_info[func_name].get('return_type', 'std::tuple<int, int>')
                        if return_type.startswith('std::tuple<'):
                            types = return_type[11:-1].split(', ')
                            for i, target in enumerate(node.targets[0].elts):
                                if i < len(types):
                                    if isinstance(target, ast.Tuple):
                                        nested_types = types[i][11:-1].split(', ')
                                        for j, nested_target in enumerate(target.elts):
                                            if j < len(nested_types):
                                                self.type_info[nested_target.id] = nested_types[j]
                                            else:
                                                self.type_info[nested_target.id] = 'int'
                                    else:
                                        self.type_info[target.id] = types[i]
                                else:
                                    self.type_info[target.id] = 'int'
                        else:
                            for target in node.targets[0].elts:
                                if isinstance(target, ast.Name):
                                    self.type_info[target.id] = 'int'
                    else:
                        for target in node.targets[0].elts:
                            if isinstance(target, ast.Tuple):
                                for nested_target in target.elts:
                                    self.type_info[nested_target.id] = 'int'
                            elif isinstance(target, ast.Name):
                                self.type_info[target.id] = 'int'
            elif isinstance(node.value, ast.Tuple):
                for i, (target, value) in enumerate(zip(node.targets[0].elts, node.value.elts)):
                    if isinstance(target, ast.Tuple):
                        if isinstance(value, ast.Tuple):
                            for j, (nested_target, nested_value) in enumerate(zip(target.elts, value.elts)):
                                self.type_info[nested_target.id] = self._infer_expression_type(nested_value)
                        else:
                            for nested_target in target.elts:
                                self.type_info[nested_target.id] = 'int'
                    else:
                        self.type_info[target.id] = self._infer_expression_type(value)
            else:
                for target in node.targets[0].elts:
                    if isinstance(target, ast.Tuple):
                        for nested_target in target.elts:
                            self.type_info[nested_target.id] = 'int'
                    else:
                        self.type_info[target.id] = 'int'
            return

        # Basic type inference implementation
        if isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, (int, float)):
                self.type_info[node.targets[0].id] = 'int' if isinstance(node.value.value, int) else 'double'
            elif isinstance(node.value.value, str):
                self.type_info[node.targets[0].id] = 'std::string'
            elif isinstance(node.value.value, bool):
                self.type_info[node.targets[0].id] = 'bool'
        elif isinstance(node.value, ast.List):
            # Try to infer list element type
            if node.value.elts:
                elt_type = self._infer_expression_type(node.value.elts[0])
                self.type_info[node.targets[0].id] = f'std::vector<{elt_type}>'
            else:
                self.type_info[node.targets[0].id] = 'std::vector<int>'  # Default to int
        elif isinstance(node.value, ast.Dict):
            # Try to infer key and value types
            if node.value.keys and node.value.values:
                key_type = self._infer_expression_type(node.value.keys[0])
                value_type = self._infer_expression_type(node.value.values[0])
                self.type_info[node.targets[0].id] = f'std::map<{key_type}, {value_type}>'
            else:
                self.type_info[node.targets[0].id] = 'std::map<std::string, int>'  # Default
        elif isinstance(node.value, ast.Set):
            # Try to infer set element type
            if node.value.elts:
                elt_type = self._infer_expression_type(node.value.elts[0])
                self.type_info[node.targets[0].id] = f'std::set<{elt_type}>'
            else:
                self.type_info[node.targets[0].id] = 'std::set<int>'  # Default
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
                self.type_info[node.targets[0].id] = f'std::tuple<{", ".join(elt_types)}>'
            else:
                self.type_info[node.targets[0].id] = 'std::tuple<>'
        elif isinstance(node.value, ast.Call):
            # Try to infer type from function call
            if isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id
                if func_name in self.type_info:
                    self.type_info[node.targets[0].id] = self.type_info[func_name].get('return_type', 'int')
                else:
                    self.type_info[node.targets[0].id] = 'int'  # Default
            else:
                self.type_info[node.targets[0].id] = 'int'  # Default
        elif isinstance(node.targets[0], ast.Tuple):
            # Handle tuple unpacking
            if isinstance(node.value, ast.Call):
                # If it's a function call, try to get the return type
                if isinstance(node.value.func, ast.Name):
                    func_name = node.value.func.id
                    if func_name in self.type_info:
                        return_type = self.type_info[func_name].get('return_type', 'std::tuple<int, int>')
                        if return_type.startswith('std::tuple<'):
                            # Extract the types from the tuple
                            types = return_type[11:-1].split(', ')
                            for i, target in enumerate(node.targets[0].elts):
                                if i < len(types):
                                    if isinstance(target, ast.Tuple):
                                        # Handle nested tuple unpacking
                                        nested_types = types[i][11:-1].split(', ')  # Remove std::tuple<>
                                        for j, nested_target in enumerate(target.elts):
                                            if j < len(nested_types):
                                                self.type_info[nested_target.id] = nested_types[j]
                                            else:
                                                self.type_info[nested_target.id] = 'int'  # Default
                                    else:
                                        self.type_info[target.id] = types[i]
                                else:
                                    self.type_info[target.id] = 'int'  # Default
                    else:
                        # Default to int for all targets
                        for target in node.targets[0].elts:
                            if isinstance(target, ast.Tuple):
                                for nested_target in target.elts:
                                    self.type_info[nested_target.id] = 'int'
                            else:
                                self.type_info[target.id] = 'int'
            elif isinstance(node.value, ast.Tuple):
                # Handle direct tuple assignment
                for i, (target, value) in enumerate(zip(node.targets[0].elts, node.value.elts)):
                    if isinstance(target, ast.Tuple):
                        # Handle nested tuple unpacking
                        if isinstance(value, ast.Tuple):
                            for j, (nested_target, nested_value) in enumerate(zip(target.elts, value.elts)):
                                self.type_info[nested_target.id] = self._infer_expression_type(nested_value)
                        else:
                            # Default to int for nested targets
                            for nested_target in target.elts:
                                self.type_info[nested_target.id] = 'int'
                    else:
                        self.type_info[target.id] = self._infer_expression_type(value)
            else:
                # Default to int for all targets
                for target in node.targets[0].elts:
                    if isinstance(target, ast.Tuple):
                        for nested_target in target.elts:
                            self.type_info[nested_target.id] = 'int'
                    else:
                        self.type_info[target.id] = 'int'

    def _infer_expression_type(self, node: ast.AST) -> str:
        """Infer the type of an expression."""
        print(f"Inferring expression type for: {type(node)}")
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int):
                return 'int'
            elif isinstance(node.value, float):
                return 'double'
            elif isinstance(node.value, str):
                return 'std::string'
            elif isinstance(node.value, bool):
                return 'bool'
        elif isinstance(node, ast.Name):
            if node.id == 'int':
                return 'int'
            elif node.id == 'float':
                return 'double'
            elif node.id == 'str':
                return 'std::string'
            elif node.id == 'bool':
                return 'bool'
            return node.id
        elif isinstance(node, ast.List):
            if node.elts:
                elt_type = self._infer_expression_type(node.elts[0])
                return f'std::vector<{elt_type}>'
            return 'std::vector<int>'
        elif isinstance(node, ast.Dict):
            if node.keys and node.values:
                key_type = self._infer_expression_type(node.keys[0])
                value_type = self._infer_expression_type(node.values[0])
                return f'std::map<{key_type}, {value_type}>'
            return 'std::map<std::string, int>'
        elif isinstance(node, ast.Set):
            if node.elts:
                elt_type = self._infer_expression_type(node.elts[0])
                return f'std::set<{elt_type}>'
            return 'std::set<int>'
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
                return f'std::tuple<{", ".join(elt_types)}>'
            return 'std::tuple<>'
        elif isinstance(node, ast.BinOp):
            # For binary operations, infer type based on operands
            left_type = self._infer_expression_type(node.left)
            right_type = self._infer_expression_type(node.right)
            # If either operand is double, result is double
            if 'double' in (left_type, right_type):
                return 'double'
            return 'int'
        elif isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name):
                base_type = node.value.id
                if isinstance(node.slice, ast.Index):  # Python 3.8 and earlier
                    elt = node.slice.value
                else:  # Python 3.9 and later
                    elt = node.slice
                
                if base_type == 'list':
                    return f'std::vector<{self._infer_expression_type(elt)}>'
                elif base_type == 'dict':
                    if isinstance(elt, ast.Tuple):
                        key_type = self._infer_expression_type(elt.elts[0])
                        value_type = self._infer_expression_type(elt.elts[1])
                        return f'std::map<{key_type}, {value_type}>'
                    else:
                        return f'std::map<std::string, {self._infer_expression_type(elt)}>'
                elif base_type == 'set':
                    return f'std::set<{self._infer_expression_type(elt)}>'
                elif base_type == 'tuple':
                    if isinstance(elt, ast.Tuple):
                        elt_types = []
                        for e in elt.elts:
                            if isinstance(e, ast.Name):
                                elt_types.append(self._get_type_name(e))
                            elif isinstance(e, ast.Subscript):
                                elt_types.append(self._get_type_name(e))
                            else:
                                elt_types.append(self._infer_expression_type(e))
                        return f'std::tuple<{", ".join(elt_types)}>'
                    else:
                        return f'std::tuple<{self._infer_expression_type(elt)}>'
                else:
                    return base_type
            return 'int'  # Default
        return 'int'  # Default type

    def _analyze_control_flow(self, node: ast.AST) -> None:
        """Analyze control flow structures."""
        if isinstance(node, ast.If):
            self._analyze_if_statement(node)
        elif isinstance(node, ast.For):
            self._analyze_for_loop(node)
        elif isinstance(node, ast.While):
            self._analyze_while_loop(node)
        elif isinstance(node, ast.Try):
            self._analyze_try_except(node)
        elif isinstance(node, ast.With):
            self._analyze_with_statement(node)

    def _analyze_if_statement(self, node: ast.If) -> None:
        """Analyze if statement structure."""
        # Store condition type
        if isinstance(node.test, ast.Compare):
            self._analyze_comparison(node.test)
        elif isinstance(node.test, ast.BoolOp):
            self._analyze_boolean_operation(node.test)

    def _analyze_for_loop(self, node: ast.For) -> None:
        """Analyze for loop structure."""
        # Store iterator type
        if isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Name):
                if node.iter.func.id == 'range':
                    self.type_info[node.target.id] = 'int'
                elif node.iter.func.id in ('list', 'tuple', 'set'):
                    self.type_info[node.target.id] = 'int'  # Default for now
        elif isinstance(node.iter, ast.List):
            elt_type = self._infer_expression_type(node.iter.elts[0]) if node.iter.elts else 'int'
            self.type_info[node.target.id] = elt_type

    def _analyze_while_loop(self, node: ast.While) -> None:
        """Analyze while loop structure."""
        # Store condition type
        if isinstance(node.test, ast.Compare):
            self._analyze_comparison(node.test)
        elif isinstance(node.test, ast.BoolOp):
            self._analyze_boolean_operation(node.test)

    def _analyze_try_except(self, node: ast.Try) -> None:
        """Analyze try-except structure."""
        # Store exception types
        for handler in node.handlers:
            if handler.type:
                if isinstance(handler.type, ast.Name):
                    self.type_info[handler.name] = handler.type.id
                elif isinstance(handler.type, ast.Tuple):
                    for elt in handler.type.elts:
                        if isinstance(elt, ast.Name):
                            self.type_info[handler.name] = elt.id

    def _analyze_with_statement(self, node: ast.With) -> None:
        """Analyze with statement structure."""
        # Store context manager type
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                if isinstance(item.context_expr.func, ast.Name):
                    self.type_info[item.optional_vars.id] = item.context_expr.func.id

    def _analyze_comparison(self, node: ast.Compare) -> None:
        """Analyze comparison operation."""
        # Store operand types
        left_type = self._infer_expression_type(node.left)
        for op, right in zip(node.ops, node.comparators):
            right_type = self._infer_expression_type(right)
            # Store comparison result type (always bool)
            self.type_info[f'comparison_{id(node)}'] = 'bool'

    def _analyze_boolean_operation(self, node: ast.BoolOp) -> None:
        """Analyze boolean operation."""
        # Store operand types
        for value in node.values:
            value_type = self._infer_expression_type(value)
            # Store boolean operation result type (always bool)
            self.type_info[f'bool_op_{id(node)}'] = 'bool'
    
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
        if node.returns:
            func_info['return_type'] = self._get_type_name(node.returns)
        
        # Get parameter types from type hints
        for arg in node.args.args:
            if arg.annotation:
                func_info['params'][arg.arg] = self._get_type_name(arg.annotation)
            else:
                func_info['params'][arg.arg] = 'int'  # Default
        
        # Store function info
        self.type_info[node.name] = func_info

    def _get_type_name(self, node: ast.AST) -> str:
        """Get C++ type name from Python type annotation."""
        print(f"Processing node type: {type(node)}")
        if isinstance(node, ast.Name):
            print(f"Name node: {node.id}")
            if node.id == 'int':
                return 'int'
            elif node.id == 'float':
                return 'double'
            elif node.id == 'str':
                return 'std::string'
            elif node.id == 'bool':
                return 'bool'
            return node.id
        elif isinstance(node, ast.Tuple):
            print("Tuple node")
            # Handle tuple type annotations directly
            elt_types = []
            for e in node.elts:
                print(f"  Processing tuple element type: {type(e)}")
                if isinstance(e, ast.Name):
                    elt_types.append(self._get_type_name(e))
                elif isinstance(e, ast.Subscript):
                    elt_types.append(self._get_type_name(e))
                else:
                    print(f"  Unknown tuple element type: {type(e)}")
                    elt_types.append('int')  # Default type
            return f'std::tuple<{", ".join(elt_types)}>'
        elif isinstance(node, ast.Subscript):
            print("Subscript node")
            if isinstance(node.value, ast.Name):
                base_type = node.value.id
                print(f"  Base type: {base_type}")
                if isinstance(node.slice, ast.Index):  # Python 3.8 and earlier
                    elt = node.slice.value
                else:  # Python 3.9 and later
                    elt = node.slice
                print(f"  Element type: {type(elt)}")
                
                if base_type == 'list':
                    return f'std::vector<{self._get_type_name(elt)}>'
                elif base_type == 'dict':
                    if isinstance(elt, ast.Tuple):
                        key_type = self._get_type_name(elt.elts[0])
                        value_type = self._get_type_name(elt.elts[1])
                        return f'std::map<{key_type}, {value_type}>'
                    else:
                        return f'std::map<std::string, {self._get_type_name(elt)}>'
                elif base_type == 'set':
                    return f'std::set<{self._get_type_name(elt)}>'
                elif base_type == 'tuple':
                    if isinstance(elt, ast.Tuple):
                        elt_types = []
                        for e in elt.elts:
                            print(f"    Processing tuple element type: {type(e)}")
                            if isinstance(e, ast.Name):
                                elt_types.append(self._get_type_name(e))
                            elif isinstance(e, ast.Subscript):
                                elt_types.append(self._get_type_name(e))
                            else:
                                print(f"    Unknown tuple element type: {type(e)}")
                                elt_types.append('int')  # Default type
                        return f'std::tuple<{", ".join(elt_types)}>'
                    else:
                        return f'std::tuple<{self._get_type_name(elt)}>'
                else:
                    return base_type
            elif isinstance(node.value, ast.Tuple):
                # Handle tuple type annotations directly
                elt_types = []
                for e in node.value.elts:
                    print(f"  Processing tuple element type: {type(e)}")
                    if isinstance(e, ast.Name):
                        elt_types.append(self._get_type_name(e))
                    elif isinstance(e, ast.Subscript):
                        elt_types.append(self._get_type_name(e))
                    else:
                        print(f"  Unknown tuple element type: {type(e)}")
                        elt_types.append('int')  # Default type
                return f'std::tuple<{", ".join(elt_types)}>'
            elif isinstance(node.value, ast.Subscript):
                # Handle nested subscripts
                return self._get_type_name(node.value)
            return 'int'  # Default
        elif isinstance(node, ast.Constant):
            print(f"Constant node: {node.value}")
            if isinstance(node.value, str):
                return 'std::string'
            elif isinstance(node.value, int):
                return 'int'
            elif isinstance(node.value, float):
                return 'double'
            elif isinstance(node.value, bool):
                return 'bool'
            return 'int'  # Default type
        print(f"Unknown node type: {type(node)}")
        return 'int'  # Default type
    
    def _check_loop_performance(self, node: ast.For) -> None:
        """Check for performance issues in loops."""
        # Implementation will analyze loop complexity and operations
        pass
    
    def _check_function_call_performance(self, node: ast.Call) -> None:
        """Check for performance issues in function calls."""
        # Implementation will analyze function call patterns
        pass
    
    def _analyze_list_memory(self, node: ast.List) -> None:
        """Analyze memory usage of list operations."""
        # Implementation will estimate memory usage
        pass
    
    def _analyze_dict_memory(self, node: ast.Dict) -> None:
        """Analyze memory usage of dictionary operations."""
        # Implementation will estimate memory usage
        pass
    
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
        # Implementation will count branches and loops
        pass 