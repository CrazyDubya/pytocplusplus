"""Type inference analyzer for Python to C++ conversion."""

from typing import Dict, List, Any, Optional, Union, Set
import ast
import logging

logger = logging.getLogger("TypeInference")

class TypeInferenceAnalyzer:
    """Specialized analyzer for type inference."""
    
    def __init__(self):
        self.type_info: Dict[str, Any] = {}
        # Add expression type cache
        self.expression_cache: Dict[str, str] = {}
    
    def analyze_types(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze types in the AST and return type information."""
        self.type_info.clear()
        # Clear cache at the start of analysis
        self.expression_cache.clear()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                self._infer_variable_type(node)
            elif isinstance(node, ast.FunctionDef):
                self._analyze_function_types(node)
            elif isinstance(node, ast.AnnAssign):
                self._handle_annotated_assignment(node)
        
        return self.type_info.copy()
    
    def _store_type_for_target(self, target: ast.AST, type_str: str) -> None:
        """Helper method to safely store type information for a target."""
        if isinstance(target, ast.Name):
            self.type_info[target.id] = type_str
        elif isinstance(target, ast.Attribute):
            # For attribute access like obj.attr, store as obj.attr
            if isinstance(target.value, ast.Name):
                self.type_info[f"{target.value.id}.{target.attr}"] = type_str
        elif isinstance(target, ast.Tuple):
            # For tuple unpacking, we need to handle each element
            for i, elt in enumerate(target.elts):
                if isinstance(elt, ast.Name):
                    # Assign a generic type for now, could be improved
                    self.type_info[elt.id] = 'auto'
    
    def _infer_variable_type(self, node: ast.Assign) -> None:
        """Infer the type of a variable assignment."""
        if not node.targets:
            return
            
        target = node.targets[0]
        
        # Handle tuple unpacking separately
        if isinstance(target, ast.Tuple):
            self._handle_tuple_target_assignment(node)
            return
        
        # Handle regular assignments
        type_str = self._infer_expression_type(node.value)
        if type_str:
            self._store_type_for_target(target, type_str)
    
    def _handle_tuple_target_assignment(self, node: ast.Assign) -> None:
        """Handle tuple unpacking in assignments."""
        target_tuple = node.targets[0]
        
        if isinstance(node.value, ast.Tuple):
            # Direct tuple assignment: a, b = 1, 2
            for target_elt, value_elt in zip(target_tuple.elts, node.value.elts):
                type_str = self._infer_expression_type(value_elt)
                self._store_type_for_target(target_elt, type_str)
        elif isinstance(node.value, ast.Call):
            # Function call returning tuple: a, b = func()
            # For now, assign 'auto' - could be improved with function analysis
            for target_elt in target_tuple.elts:
                self._store_type_for_target(target_elt, 'auto')
        else:
            # Other cases, assign 'auto'
            for target_elt in target_tuple.elts:
                self._store_type_for_target(target_elt, 'auto')
    
    def _handle_annotated_assignment(self, node: ast.AnnAssign) -> None:
        """Handle type-annotated assignments."""
        if isinstance(node.target, ast.Name):
            type_str = self._annotation_to_cpp_type(node.annotation)
            if type_str:
                self.type_info[node.target.id] = type_str
    
    def _annotation_to_cpp_type(self, annotation: ast.AST) -> Optional[str]:
        """Convert Python type annotation to C++ type."""
        if isinstance(annotation, ast.Name):
            type_map = {
                'int': 'int',
                'float': 'double',
                'str': 'std::string',
                'bool': 'bool',
                'bytes': 'std::vector<uint8_t>',
            }
            return type_map.get(annotation.id)
        elif isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                if annotation.value.id in ['List', 'list']:
                    element_type = self._annotation_to_cpp_type(annotation.slice)
                    return f'std::vector<{element_type or "int"}>'
                elif annotation.value.id in ['Dict', 'dict']:
                    if isinstance(annotation.slice, ast.Tuple) and len(annotation.slice.elts) == 2:
                        key_type = self._annotation_to_cpp_type(annotation.slice.elts[0])
                        value_type = self._annotation_to_cpp_type(annotation.slice.elts[1])
                        return f'std::unordered_map<{key_type or "std::string"}, {value_type or "int"}>'
                elif annotation.value.id in ['Tuple', 'tuple']:
                    if isinstance(annotation.slice, ast.Tuple):
                        types = []
                        for elt in annotation.slice.elts:
                            cpp_type = self._annotation_to_cpp_type(elt)
                            if cpp_type:
                                types.append(cpp_type)
                        if types:
                            return f'std::tuple<{", ".join(types)}>'
                elif annotation.value.id == 'Optional':
                    inner_type = self._annotation_to_cpp_type(annotation.slice)
                    return f'std::optional<{inner_type or "int"}>'
                elif annotation.value.id == 'Union':
                    # Handle Union types
                    if isinstance(annotation.slice, ast.Tuple):
                        types = []
                        for elt in annotation.slice.elts:
                            cpp_type = self._annotation_to_cpp_type(elt)
                            if cpp_type:
                                types.append(cpp_type)
                        if types:
                            return f'std::variant<{", ".join(types)}>'
        return None
    
    def _infer_expression_type(self, expr: ast.AST) -> Optional[str]:
        """Infer the type of an expression with caching."""
        # Create a cache key based on the AST dump
        cache_key = ast.dump(expr)
        
        # Check if we already cached this expression's type
        if cache_key in self.expression_cache:
            return self.expression_cache[cache_key]
        
        # Infer the type
        result = None
        if isinstance(expr, ast.Constant):
            # Check bool first since bool is a subclass of int in Python
            if isinstance(expr.value, bool):
                result = 'bool'
            elif isinstance(expr.value, int):
                result = 'int'
            elif isinstance(expr.value, float):
                result = 'double'
            elif isinstance(expr.value, str):
                result = 'std::string'
            elif expr.value is None:
                result = 'std::nullptr_t'
        elif isinstance(expr, ast.List):
            if expr.elts:
                element_type = self._infer_expression_type(expr.elts[0])
                result = f'std::vector<{element_type or "int"}>'
            else:
                result = 'std::vector<int>'
        elif isinstance(expr, ast.Dict):
            if expr.keys and expr.values:
                key_type = self._infer_expression_type(expr.keys[0]) 
                value_type = self._infer_expression_type(expr.values[0])
                # Use std::unordered_map for better performance (O(1) vs O(log n))
                result = f'std::unordered_map<{key_type or "std::string"}, {value_type or "int"}>'
            else:
                result = 'std::unordered_map<std::string, int>'
        elif isinstance(expr, ast.Set):
            if expr.elts:
                element_type = self._infer_expression_type(expr.elts[0])
                result = f'std::set<{element_type or "int"}>'
            else:
                result = 'std::set<int>'
        elif isinstance(expr, ast.Tuple):
            if expr.elts:
                types = []
                for elt in expr.elts:
                    elt_type = self._infer_expression_type(elt)
                    types.append(elt_type or "auto")
                result = f'std::tuple<{", ".join(types)}>'
            else:
                result = 'std::tuple<>'
        elif isinstance(expr, ast.Name):
            # Look up the variable type if we know it
            result = self.type_info.get(expr.id, 'auto')
        elif isinstance(expr, ast.Call):
            # Function call - could be improved with function analysis
            result = 'auto'
        elif isinstance(expr, ast.BinOp):
            # Binary operation - infer from operands
            left_type = self._infer_expression_type(expr.left)
            right_type = self._infer_expression_type(expr.right)
            if left_type == 'double' or right_type == 'double':
                result = 'double'
            elif left_type == 'int' and right_type == 'int':
                result = 'int'
            else:
                result = 'auto'
        elif isinstance(expr, ast.ListComp):
            # List comprehension - infer from element type
            element_type = self._infer_expression_type(expr.elt)
            result = f'std::vector<{element_type or "auto"}>'
        elif isinstance(expr, ast.DictComp):
            # Dictionary comprehension - infer from key and value types
            key_type = self._infer_expression_type(expr.key)
            value_type = self._infer_expression_type(expr.value)
            result = f'std::unordered_map<{key_type or "auto"}, {value_type or "auto"}>'
        elif isinstance(expr, ast.Compare):
            # Comparison operations return boolean
            result = 'bool'
        elif isinstance(expr, ast.BoolOp):
            # Boolean operations (and, or) return boolean
            result = 'bool'
        
        # Cache the result if we found one
        if result is not None:
            self.expression_cache[cache_key] = result
        
        return result
    
    def _analyze_function_types(self, node: ast.FunctionDef) -> None:
        """Analyze function parameter and return types."""
        # Store function signature information
        func_info = {
            'params': {},
            'return_type': 'void',
            'body': node.body  # Store the AST body for code generation
        }
        
        # Analyze parameters
        for arg in node.args.args:
            if arg.annotation:
                param_type = self._annotation_to_cpp_type(arg.annotation)
                if param_type:
                    func_info['params'][arg.arg] = param_type
                    self.type_info[arg.arg] = param_type
            else:
                func_info['params'][arg.arg] = 'auto'
                self.type_info[arg.arg] = 'auto'
        
        # Analyze return type
        if node.returns:
            return_type = self._annotation_to_cpp_type(node.returns)
            if return_type:
                func_info['return_type'] = return_type
        else:
            # Try to infer return type from return statements
            inferred_return_type = self._infer_return_type_from_body(node.body)
            if inferred_return_type:
                func_info['return_type'] = inferred_return_type
        
        self.type_info[node.name] = func_info
    
    def _infer_return_type_from_body(self, body: List[ast.AST]) -> Optional[str]:
        """Infer return type from return statements in function body."""
        return_types = set()
        
        for node in ast.walk(ast.Module(body=body)):
            if isinstance(node, ast.Return) and node.value:
                ret_type = self._infer_expression_type(node.value)
                if ret_type:
                    return_types.add(ret_type)
        
        # If all return statements have the same type, use that
        if len(return_types) == 1:
            return return_types.pop()
        elif len(return_types) > 1:
            # Multiple different return types - use auto for now
            return 'auto'
        
        return None  # No return statements found