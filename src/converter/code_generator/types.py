from typing import Dict
import ast
import logging

logger = logging.getLogger("CodeGenerator")


class TypeHandler:
    """Handles type inference and conversion for C++ code generation."""
    
    def __init__(self, code_generator):
        self.code_generator = code_generator
    
    def _infer_cpp_type(self, node: ast.AST, local_vars: Dict[str, str]) -> str:
        """Infer C++ type from a Python expression."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return "bool"
            elif isinstance(node.value, int):
                return "int"
            elif isinstance(node.value, float):
                return "double"
            elif isinstance(node.value, str):
                return "std::string"
            elif node.value is None:
                return "std::nullptr_t"
            else:
                return "auto"
        elif isinstance(node, ast.Name):
            if node.id in local_vars:
                return local_vars[node.id]
            elif node.id == 'True' or node.id == 'False':
                return "bool"
            elif node.id == 'None':
                return "std::nullptr_t"
            else:
                return "auto"
        elif isinstance(node, ast.List):
            if node.elts:
                element_type = self._infer_cpp_type(node.elts[0], local_vars)
                return f"std::vector<{element_type}>"
            else:
                return "std::vector<int>"
        elif isinstance(node, ast.Dict):
            if node.keys and node.values:
                key_type = self._infer_cpp_type(node.keys[0], local_vars)
                value_type = self._infer_cpp_type(node.values[0], local_vars)
                return f"std::map<{key_type}, {value_type}>"
            else:
                return "std::map<std::string, int>"
        elif isinstance(node, ast.Tuple):
            if node.elts:
                element_types = [self._infer_cpp_type(elt, local_vars) for elt in node.elts]
                return f"std::tuple<{', '.join(element_types)}>"
            else:
                return "std::tuple<>"
        elif isinstance(node, ast.BinOp):
            # Infer type based on operands
            left_type = self._infer_cpp_type(node.left, local_vars)
            right_type = self._infer_cpp_type(node.right, local_vars)
            
            # Type precedence rules (simplified)
            if left_type == "double" or right_type == "double":
                return "double"
            elif left_type == "std::string" and right_type == "std::string":
                return "std::string"
            else:
                return "int"
        elif isinstance(node, ast.Compare):
            return "bool"
        elif isinstance(node, ast.BoolOp):
            return "bool"
        elif isinstance(node, ast.Call):
            # For function calls, we'd need the function's return type
            # For now, use a simplistic approach
            if isinstance(node.func, ast.Name):
                if self.code_generator.analysis_result and node.func.id in self.code_generator.analysis_result.type_info:
                    func_info = self.code_generator.analysis_result.type_info[node.func.id]
                    if isinstance(func_info, dict) and 'return_type' in func_info:
                        return func_info['return_type']
                
                # Common built-ins
                if node.func.id == 'int':
                    return "int"
                elif node.func.id == 'float':
                    return "double"
                elif node.func.id == 'str':
                    return "std::string"
                elif node.func.id == 'bool':
                    return "bool"
                elif node.func.id == 'list':
                    return "std::vector<int>"
                elif node.func.id == 'dict':
                    return "std::map<std::string, int>"
                elif node.func.id == 'set':
                    return "std::set<int>"
                elif node.func.id == 'tuple':
                    return "std::tuple<int>"
            
            return "auto"
        else:
            return "auto"
    
    def _get_default_value(self, type_str: str) -> str:
        """Get a default value for a C++ type."""
        if type_str == 'int':
            return '0'
        elif type_str == 'double':
            return '0.0'
        elif type_str == 'bool':
            return 'false'
        elif type_str == 'std::string':
            return '""'
        elif type_str == 'std::nullptr_t':
            return 'nullptr'
        elif type_str.startswith('std::vector<'):
            return f"{type_str}()"
        elif type_str.startswith('std::map<'):
            return f"{type_str}()"
        elif type_str.startswith('std::set<'):
            return f"{type_str}()"
        elif type_str.startswith('std::tuple<'):
            return f"{type_str}()"
        else:
            return "{}"
