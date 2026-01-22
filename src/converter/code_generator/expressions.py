from typing import Dict, List
import ast
import logging

logger = logging.getLogger("CodeGenerator")


class ExpressionTranslator:
    """Handles translation of Python expressions to C++."""
    
    def __init__(self, code_generator):
        self.code_generator = code_generator
    
    def _translate_expression(self, node: ast.AST, local_vars: Dict[str, str]) -> str:
        """Translate a Python expression to C++."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return 'true' if node.value else 'false'
            elif isinstance(node.value, str):
                # Escape quotes in strings
                escaped_str = node.value.replace('"', '\\"')
                return f'"{escaped_str}"'
            elif node.value is None:
                return 'nullptr'
            else:
                return str(node.value)
        elif isinstance(node, ast.BinOp):
            left = self._translate_expression(node.left, local_vars)
            right = self._translate_expression(node.right, local_vars)
            op = self._translate_operator(node.op)
            return f"({left} {op} {right})"
        elif isinstance(node, ast.UnaryOp):
            operand = self._translate_expression(node.operand, local_vars)
            op = self._translate_unary_operator(node.op)
            return f"{op}({operand})"
        elif isinstance(node, ast.Compare):
            # Handle comparisons like a < b, a <= b, etc.
            left = self._translate_expression(node.left, local_vars)
            comparisons = []
            
            for op, right in zip(node.ops, node.comparators):
                right_expr = self._translate_expression(right, local_vars)
                op_str = self._translate_compare_operator(op)
                comparisons.append(f"{left} {op_str} {right_expr}")
                left = right_expr  # For chained comparisons like a < b < c
            
            # Join multiple comparisons with && (a < b < c becomes (a < b) && (b < c))
            if len(comparisons) > 1:
                return " && ".join(f"({comp})" for comp in comparisons)
            else:
                return comparisons[0]
        elif isinstance(node, ast.Call):
            # Handle function calls
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                # Handle built-in functions
                if func_name == 'print':
                    args = [self._translate_expression(arg, local_vars) for arg in node.args]
                    args_str = ' << " " << '.join(args)
                    return f"std::cout << {args_str} << std::endl"
                elif func_name == 'len':
                    if len(node.args) == 1:
                        container = self._translate_expression(node.args[0], local_vars)
                        return f"{container}.size()"
                elif func_name == 'range':
                    # range() is handled by the for loop translation
                    return f"range({', '.join(self._translate_expression(arg, local_vars) for arg in node.args)})"
                elif func_name == 'append' and isinstance(node.func.value, ast.Attribute):
                    # Convert list.append to vector.push_back
                    obj = self._translate_expression(node.func.value.value, local_vars)
                    args = [self._translate_expression(arg, local_vars) for arg in node.args]
                    return f"{obj}.push_back({', '.join(args)})"
                elif func_name in ['sqrt', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'exp', 'log', 'log10', 'floor', 'ceil', 'fabs']:
                    # Handle direct imports from math module (e.g., from math import sqrt)
                    args = [self._translate_expression(arg, local_vars) for arg in node.args]
                    return f"std::{func_name}({', '.join(args)})"
                else:
                    # Regular function call
                    args = [self._translate_expression(arg, local_vars) for arg in node.args]
                    return f"{func_name}({', '.join(args)})"
            elif isinstance(node.func, ast.Attribute):
                # Handle method calls like obj.method()
                obj = self._translate_expression(node.func.value, local_vars)
                method = node.func.attr
                
                # Handle math module functions
                if obj == 'math':
                    if method in ['sqrt', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'exp', 'log', 'log10', 'pow', 'floor', 'ceil', 'fabs']:
                        args = [self._translate_expression(arg, local_vars) for arg in node.args]
                        return f"std::{method}({', '.join(args)})"
                    else:
                        # Handle other math functions that may need special mapping
                        args = [self._translate_expression(arg, local_vars) for arg in node.args]
                        return f"std::{method}({', '.join(args)})"
                
                # Map Python methods to C++ equivalents
                if method == 'append':
                    method = 'push_back'  # std::vector uses push_back, not append
                
                args = [self._translate_expression(arg, local_vars) for arg in node.args]
                return f"{obj}.{method}({', '.join(args)})"
            else:
                # Fallback for other callable expressions
                func = self._translate_expression(node.func, local_vars)
                args = [self._translate_expression(arg, local_vars) for arg in node.args]
                return f"{func}({', '.join(args)})"
        elif isinstance(node, ast.Attribute):
            # Handle attribute access like obj.attr
            obj = self._translate_expression(node.value, local_vars)
            return f"{obj}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            # Handle subscripting like a[b]
            value = self._translate_expression(node.value, local_vars)
            if isinstance(node.slice, ast.Index):  # Python 3.8 and earlier
                index = self._translate_expression(node.slice.value, local_vars)
            else:  # Python 3.9+
                index = self._translate_expression(node.slice, local_vars)
            return f"{value}[{index}]"
        elif isinstance(node, ast.List):
            # Handle list literals
            elements = [self._translate_expression(elt, local_vars) for elt in node.elts]
            element_type = "int"  # Default element type
            
            # Try to infer element type from the first element if available
            if node.elts:
                element_type = self.code_generator.types._infer_cpp_type(node.elts[0], local_vars)
                
            return f"std::vector<{element_type}>{{{', '.join(elements)}}}"
        elif isinstance(node, ast.Dict):
            # Handle dict literals
            if not node.keys:
                return "std::map<std::string, int>()"
                
            pairs = []
            for k, v in zip(node.keys, node.values):
                key = self._translate_expression(k, local_vars)
                value = self._translate_expression(v, local_vars)
                pairs.append(f"{{{key}, {value}}}")
                
            # Infer types from first key-value pair
            key_type = "std::string"
            value_type = "int"
            if node.keys:
                key_type = self.code_generator.types._infer_cpp_type(node.keys[0], local_vars)
                value_type = self.code_generator.types._infer_cpp_type(node.values[0], local_vars)
                
            return f"std::map<{key_type}, {value_type}>{{{', '.join(pairs)}}}"
        elif isinstance(node, ast.Tuple):
            # Handle tuple literals
            elements = [self._translate_expression(elt, local_vars) for elt in node.elts]
            
            # For empty tuples
            if not elements:
                return "std::make_tuple()"
                
            return f"std::make_tuple({', '.join(elements)})"
        elif isinstance(node, ast.ListComp):
            # Handle list comprehensions: [expr for item in iterable]
            return self._translate_list_comprehension(node, local_vars)
        elif isinstance(node, ast.DictComp):
            # Handle dictionary comprehensions: {key: value for item in iterable}
            return self._translate_dict_comprehension(node, local_vars)
        elif isinstance(node, ast.BoolOp):
            # Handle boolean operations like and, or
            op_str = "&&" if isinstance(node.op, ast.And) else "||"
            values = [f"({self._translate_expression(val, local_vars)})" for val in node.values]
            return f" {op_str} ".join(values)
        elif isinstance(node, ast.JoinedStr):
            # Handle f-strings - simplified approach
            parts = []
            
            for value in node.values:
                if isinstance(value, ast.Constant):
                    # String literal part
                    if value.value:  # Skip empty strings
                        escaped_str = value.value.replace('"', '\\"')
                        parts.append(f'"{escaped_str}"')
                elif isinstance(value, ast.FormattedValue):
                    # Expression part
                    expr = self._translate_expression(value.value, local_vars)
                    # Check if we need to convert to string for numeric types
                    if isinstance(value.value, ast.Name) and value.value.id in local_vars:
                        var_type = local_vars[value.value.id]
                        if var_type in ['int', 'double', 'float']:
                            parts.append(f'std::to_string({expr})')
                        else:
                            parts.append(expr)
                    else:
                        # For unknown types, try to convert to string
                        parts.append(f'std::to_string({expr})')
            
            # Use simple string concatenation with '+'
            if parts:
                return ' + '.join(parts)
            else:
                return '""'  # Empty string as fallback
        else:
            # Fallback for unsupported expression types
            return f"/* Unsupported expression: {type(node).__name__} */"
    
    def _translate_operator(self, op: ast.operator) -> str:
        """Translate a Python binary operator to C++."""
        if isinstance(op, ast.Add):
            return "+"
        elif isinstance(op, ast.Sub):
            return "-"
        elif isinstance(op, ast.Mult):
            return "*"
        elif isinstance(op, ast.Div):
            return "/"
        elif isinstance(op, ast.FloorDiv):
            return "/"  # In C++, use int division or std::floor
        elif isinstance(op, ast.Mod):
            return "%"
        elif isinstance(op, ast.Pow):
            return "**"  # Replace with std::pow in post-processing
        elif isinstance(op, ast.LShift):
            return "<<"
        elif isinstance(op, ast.RShift):
            return ">>"
        elif isinstance(op, ast.BitOr):
            return "|"
        elif isinstance(op, ast.BitXor):
            return "^"
        elif isinstance(op, ast.BitAnd):
            return "&"
        elif isinstance(op, ast.MatMult):
            return "*"  # Replace with matrix multiplication in post-processing
        else:
            return "?"
    
    def _translate_unary_operator(self, op: ast.unaryop) -> str:
        """Translate a Python unary operator to C++."""
        if isinstance(op, ast.Invert):
            return "~"
        elif isinstance(op, ast.Not):
            return "!"
        elif isinstance(op, ast.UAdd):
            return "+"
        elif isinstance(op, ast.USub):
            return "-"
        else:
            return "?"
    
    def _translate_compare_operator(self, op: ast.cmpop) -> str:
        """Translate a Python comparison operator to C++."""
        if isinstance(op, ast.Eq):
            return "=="
        elif isinstance(op, ast.NotEq):
            return "!="
        elif isinstance(op, ast.Lt):
            return "<"
        elif isinstance(op, ast.LtE):
            return "<="
        elif isinstance(op, ast.Gt):
            return ">"
        elif isinstance(op, ast.GtE):
            return ">="
        elif isinstance(op, ast.Is):
            return "=="  # In C++, use == for is (may need to be replaced depending on types)
        elif isinstance(op, ast.IsNot):
            return "!="  # In C++, use != for is not (may need to be replaced depending on types)
        elif isinstance(op, ast.In):
            return "in"  # Replace with std::find or similar in post-processing
        elif isinstance(op, ast.NotIn):
            return "not in"  # Replace with !std::find or similar in post-processing
        else:
            return "?"
    
    def _translate_list_comprehension(self, node: ast.ListComp, local_vars: Dict[str, str]) -> str:
        """Translate list comprehension to C++ lambda with performance optimizations."""
        # Get the comprehension parts
        element_expr = node.elt
        generator = node.generators[0]  # For simplicity, handle only one generator
        target = generator.target
        iter_expr = generator.iter
        
        # Translate components
        iter_str = self._translate_expression(iter_expr, local_vars)
        target_name = target.id if isinstance(target, ast.Name) else "item"
        element_str = self._translate_expression(element_expr, local_vars)
        
        # Handle conditional comprehensions (if clauses)
        condition_str = ""
        if generator.ifs:
            conditions = []
            for if_clause in generator.ifs:
                condition = self._translate_expression(if_clause, local_vars)
                conditions.append(condition)
            condition_str = f" if ({' && '.join(conditions)})"
        
        # Create lambda expression for the comprehension with performance optimizations
        # [expr for item in iterable] becomes:
        # [&]() { 
        #   std::vector<auto> result; 
        #   result.reserve(iterable.size());  // Performance optimization
        #   for (auto item : iterable) { 
        #     if (condition) {  // Only if conditions exist
        #       result.push_back(expr); 
        #     }
        #   } 
        #   return result; 
        # }()
        
        if condition_str:
            comprehension_code = f"""[&]() {{
    std::vector<auto> result;
    result.reserve({iter_str}.size());
    for (auto {target_name} : {iter_str}) {{
        if ({' && '.join(self._translate_expression(if_clause, local_vars) for if_clause in generator.ifs)}) {{
            result.push_back({element_str});
        }}
    }}
    return result;
}}()"""
        else:
            comprehension_code = f"""[&]() {{
    std::vector<auto> result;
    result.reserve({iter_str}.size());
    for (auto {target_name} : {iter_str}) {{
        result.push_back({element_str});
    }}
    return result;
}}()"""
        
        return comprehension_code
    
    def _translate_dict_comprehension(self, node: ast.DictComp, local_vars: Dict[str, str]) -> str:
        """Translate dictionary comprehension to C++ lambda with performance optimizations."""
        # Get the comprehension parts
        key_expr = node.key
        value_expr = node.value
        generator = node.generators[0]  # For simplicity, handle only one generator
        target = generator.target
        iter_expr = generator.iter
        
        # Translate components
        iter_str = self._translate_expression(iter_expr, local_vars)
        target_name = target.id if isinstance(target, ast.Name) else "item"
        key_str = self._translate_expression(key_expr, local_vars)
        value_str = self._translate_expression(value_expr, local_vars)
        
        # Handle conditional comprehensions (if clauses)
        condition_str = ""
        if generator.ifs:
            conditions = []
            for if_clause in generator.ifs:
                condition = self._translate_expression(if_clause, local_vars)
                conditions.append(condition)
            condition_str = f" if ({' && '.join(conditions)})"
        
        # Create lambda expression for the dictionary comprehension with performance optimizations
        # Use std::unordered_map instead of std::map for O(1) vs O(log n) performance
        # {key: value for item in iterable} becomes:
        # [&]() { 
        #   std::unordered_map<auto, auto> result; 
        #   for (auto item : iterable) { 
        #     if (condition) {  # Only if conditions exist
        #       result[key] = value; 
        #     }
        #   } 
        #   return result; 
        # }()
        
        if condition_str:
            comprehension_code = f"""[&]() {{
    std::unordered_map<auto, auto> result;
    for (auto {target_name} : {iter_str}) {{
        if ({' && '.join(self._translate_expression(if_clause, local_vars) for if_clause in generator.ifs)}) {{
            result[{key_str}] = {value_str};
        }}
    }}
    return result;
}}()"""
        else:
            comprehension_code = f"""[&]() {{
    std::unordered_map<auto, auto> result;
    for (auto {target_name} : {iter_str}) {{
        result[{key_str}] = {value_str};
    }}
    return result;
}}()"""
        
        return comprehension_code
    
    def _expression_uses_variables(self, expr: ast.AST, variable_names: List[str]) -> bool:
        """Check if an expression uses any of the given variable names."""
        for node in ast.walk(expr):
            if isinstance(node, ast.Name) and node.id in variable_names:
                return True
        return False
