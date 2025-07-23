"""Optimized C++ code generator with enhanced function body translation."""

from typing import Dict, List, Any, Optional, Union, Set
import ast
import logging

logger = logging.getLogger("OptimizedTranslator")

class OptimizedFunctionTranslator:
    """Enhanced function body translator for better C++ code generation."""
    
    def __init__(self):
        self.local_vars: Dict[str, str] = {}
        self.param_types: Dict[str, str] = {}
    
    def translate_function(self, func_node: ast.FunctionDef, type_info: Dict[str, Any]) -> str:
        """Translate a complete function to optimized C++."""
        # Extract function info
        func_name = func_node.name
        return_type = self._get_return_type(func_node, type_info)
        
        # Process parameters
        params = []
        self.param_types.clear()
        for arg in func_node.args.args:
            param_type = self._get_parameter_type(arg, type_info)
            self.param_types[arg.arg] = param_type
            params.append(f"{param_type} {arg.arg}")
        
        # Translate function body
        body = self._translate_function_body(func_node.body, return_type)
        
        # Generate function signature and body
        signature = f"{return_type} {func_name}({', '.join(params)})"
        return f"{signature} {{\n{body}\n}}\n"
    
    def _get_return_type(self, func_node: ast.FunctionDef, type_info: Dict[str, Any]) -> str:
        """Determine function return type."""
        # Check type annotation first
        if func_node.returns:
            return self._ast_to_cpp_type(func_node.returns)
        
        # Try to infer from type_info
        func_key = f"function_{func_node.name}"
        if func_key in type_info:
            func_info = type_info[func_key]
            if isinstance(func_info, dict) and 'return_type' in func_info:
                return func_info['return_type']
        
        # Analyze return statements
        return_type = self._infer_return_type_from_body(func_node.body)
        return return_type or 'void'
    
    def _get_parameter_type(self, arg: ast.arg, type_info: Dict[str, Any]) -> str:
        """Get parameter type from annotation or type_info."""
        if arg.annotation:
            return self._ast_to_cpp_type(arg.annotation)
        
        # Check type_info
        if arg.arg in type_info:
            type_val = type_info[arg.arg]
            if isinstance(type_val, str):
                return type_val
        
        return 'auto'  # Default
    
    def _ast_to_cpp_type(self, node: ast.AST) -> str:
        """Convert AST type annotation to C++ type."""
        if isinstance(node, ast.Name):
            type_map = {
                'int': 'int',
                'float': 'double', 
                'str': 'std::string',
                'bool': 'bool',
                'None': 'void'
            }
            return type_map.get(node.id, node.id)
        elif isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name):
                base = node.value.id
                if base == 'List':
                    inner = self._ast_to_cpp_type(node.slice)
                    return f'std::vector<{inner}>'
                elif base == 'Dict':
                    if isinstance(node.slice, ast.Tuple) and len(node.slice.elts) == 2:
                        key_type = self._ast_to_cpp_type(node.slice.elts[0])
                        val_type = self._ast_to_cpp_type(node.slice.elts[1])
                        return f'std::map<{key_type}, {val_type}>'
                elif base == 'Optional':
                    inner = self._ast_to_cpp_type(node.slice)
                    return f'std::optional<{inner}>'
        return 'auto'
    
    def _translate_function_body(self, body_nodes: List[ast.AST], return_type: str) -> str:
        """Translate function body with optimizations."""
        self.local_vars.clear()
        self.local_vars.update(self.param_types)
        
        statements = []
        
        for node in body_nodes:
            # Skip docstrings
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                continue
            
            stmt = self._translate_statement(node, 1)
            if stmt:
                statements.append(stmt)
        
        # Add default return if needed
        if not statements and return_type != 'void':
            statements.append(f"    return {self._get_default_value(return_type)};")
        
        return '\n'.join(statements)
    
    def _translate_statement(self, node: ast.AST, indent_level: int) -> Optional[str]:
        """Translate a statement to optimized C++."""
        indent = "    " * indent_level
        
        if isinstance(node, ast.If):
            return self._translate_if(node, indent_level)
        elif isinstance(node, ast.For):
            return self._translate_for_loop(node, indent_level)
        elif isinstance(node, ast.While):
            return self._translate_while_loop(node, indent_level)
        elif isinstance(node, ast.Assign):
            return self._translate_assignment(node, indent_level)
        elif isinstance(node, ast.AugAssign):
            return self._translate_aug_assignment(node, indent_level)
        elif isinstance(node, ast.Return):
            return self._translate_return(node, indent_level)
        elif isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Call):
                expr = self._translate_expression(node.value)
                return f"{indent}{expr};"
        
        return None
    
    def _translate_if(self, node: ast.If, indent_level: int) -> str:
        """Translate if statement with optimized conditions."""
        indent = "    " * indent_level
        condition = self._translate_expression(node.test)
        
        result = f"{indent}if ({condition}) {{\n"
        
        # Translate body
        for stmt in node.body:
            translated = self._translate_statement(stmt, indent_level + 1)
            if translated:
                result += translated + "\n"
        
        result += f"{indent}}}"
        
        # Handle else/elif
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                # elif case
                result += " else " + self._translate_if(node.orelse[0], 0).lstrip()
            else:
                # else case
                result += " else {\n"
                for stmt in node.orelse:
                    translated = self._translate_statement(stmt, indent_level + 1)
                    if translated:
                        result += translated + "\n"
                result += f"{indent}}}"
        
        return result
    
    def _translate_for_loop(self, node: ast.For, indent_level: int) -> str:
        """Translate for loop with range optimization."""
        indent = "    " * indent_level
        
        # Handle range-based loops specially for optimization
        if (isinstance(node.iter, ast.Call) and 
            isinstance(node.func, ast.Name) and 
            node.func.id == 'range' and
            isinstance(node.target, ast.Name)):
            
            var_name = node.target.id
            self.local_vars[var_name] = 'int'
            
            # Optimize range() calls
            if len(node.iter.args) == 1:
                # range(n) -> for (int i = 0; i < n; ++i)
                end = self._translate_expression(node.iter.args[0])
                result = f"{indent}for (int {var_name} = 0; {var_name} < {end}; ++{var_name}) {{\n"
            elif len(node.iter.args) == 2:
                # range(start, end)
                start = self._translate_expression(node.iter.args[0])
                end = self._translate_expression(node.iter.args[1])
                result = f"{indent}for (int {var_name} = {start}; {var_name} < {end}; ++{var_name}) {{\n"
            elif len(node.iter.args) == 3:
                # range(start, end, step)
                start = self._translate_expression(node.iter.args[0])
                end = self._translate_expression(node.iter.args[1])
                step = self._translate_expression(node.iter.args[2])
                result = f"{indent}for (int {var_name} = {start}; {var_name} < {end}; {var_name} += {step}) {{\n"
            else:
                # Fallback
                result = f"{indent}// Complex range loop\n"
        else:
            # Range-based for loop
            if isinstance(node.target, ast.Name):
                var_name = node.target.id
                iterable = self._translate_expression(node.iter)
                result = f"{indent}for (const auto& {var_name} : {iterable}) {{\n"
        
        # Translate body
        for stmt in node.body:
            translated = self._translate_statement(stmt, indent_level + 1)
            if translated:
                result += translated + "\n"
        
        result += f"{indent}}}"
        return result
    
    def _translate_assignment(self, node: ast.Assign, indent_level: int) -> str:
        """Translate assignment with type inference."""
        indent = "    " * indent_level
        
        # Handle tuple unpacking
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
            return self._translate_tuple_assignment(node, indent_level)
        
        # Regular assignment
        target = node.targets[0]
        if isinstance(target, ast.Name):
            var_name = target.id
            value_expr = self._translate_expression(node.value)
            
            # Type inference for new variables
            if var_name not in self.local_vars:
                var_type = self._infer_expression_type(node.value)
                self.local_vars[var_name] = var_type
                return f"{indent}{var_type} {var_name} = {value_expr};"
            else:
                return f"{indent}{var_name} = {value_expr};"
        
        return f"{indent}// Assignment not translated"
    
    def _translate_tuple_assignment(self, node: ast.Assign, indent_level: int) -> str:
        """Translate tuple unpacking assignment."""
        indent = "    " * indent_level
        target_tuple = node.targets[0]
        
        if isinstance(node.value, ast.Tuple):
            # Direct tuple assignment: a, b = 1, 2
            result = []
            for target_elt, value_elt in zip(target_tuple.elts, node.value.elts):
                if isinstance(target_elt, ast.Name):
                    var_name = target_elt.id
                    value_expr = self._translate_expression(value_elt)
                    var_type = self._infer_expression_type(value_elt)
                    self.local_vars[var_name] = var_type
                    result.append(f"{indent}{var_type} {var_name} = {value_expr};")
            return '\n'.join(result)
        else:
            # Function call or other expression
            # Use std::tie for unpacking
            vars_list = []
            for target_elt in target_tuple.elts:
                if isinstance(target_elt, ast.Name):
                    var_name = target_elt.id
                    if var_name not in self.local_vars:
                        self.local_vars[var_name] = 'auto'
                    vars_list.append(var_name)
            
            value_expr = self._translate_expression(node.value)
            return f"{indent}std::tie({', '.join(vars_list)}) = {value_expr};"
    
    def _translate_return(self, node: ast.Return, indent_level: int) -> str:
        """Translate return statement."""
        indent = "    " * indent_level
        if node.value:
            value_expr = self._translate_expression(node.value)
            return f"{indent}return {value_expr};"
        else:
            return f"{indent}return;"
    
    def _translate_expression(self, node: ast.AST) -> str:
        """Translate expression with optimizations."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return 'true' if node.value else 'false'
            elif isinstance(node.value, str):
                return f'"{node.value}"'
            elif node.value is None:
                return 'nullptr'
            else:
                return str(node.value)
        elif isinstance(node, ast.BinOp):
            left = self._translate_expression(node.left)
            right = self._translate_expression(node.right)
            op = self._translate_binary_op(node.op)
            return f"({left} {op} {right})"
        elif isinstance(node, ast.Compare):
            left = self._translate_expression(node.left)
            comparisons = []
            for op, comparator in zip(node.ops, node.comparators):
                op_str = self._translate_comparison_op(op)
                right = self._translate_expression(comparator)
                comparisons.append(f"{left} {op_str} {right}")
                left = right  # For chained comparisons
            return ' && '.join(comparisons)
        elif isinstance(node, ast.Call):
            return self._translate_function_call(node)
        elif isinstance(node, ast.List):
            elements = [self._translate_expression(elt) for elt in node.elts]
            element_type = self._infer_expression_type(node.elts[0]) if node.elts else 'int'
            return f"std::vector<{element_type}>{{{', '.join(elements)}}}"
        elif isinstance(node, ast.Subscript):
            value = self._translate_expression(node.value)
            index = self._translate_expression(node.slice)
            return f"{value}[{index}]"
        
        return "/* expression not translated */"
    
    def _translate_function_call(self, node: ast.Call) -> str:
        """Translate function calls with optimizations."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            args = [self._translate_expression(arg) for arg in node.args]
            
            # Special case optimizations
            if func_name == 'print':
                if args:
                    return f'std::cout << {" << \" \" << ".join(args)} << std::endl'
                else:
                    return 'std::cout << std::endl'
            elif func_name == 'len':
                return f'{args[0]}.size()'
            elif func_name == 'range':
                # This should be handled in for loop translation
                return f'/* range call */'
            elif func_name == 'sum':
                # Use std::accumulate for better performance
                if args:
                    return f'std::accumulate({args[0]}.begin(), {args[0]}.end(), 0)'
            
            return f"{func_name}({', '.join(args)})"
        elif isinstance(node.func, ast.Attribute):
            # Method calls
            obj = self._translate_expression(node.func.value)
            method = node.func.attr
            args = [self._translate_expression(arg) for arg in node.args]
            
            # Special method translations
            if method == 'append':
                return f'{obj}.push_back({args[0]})'
            elif method == 'extend':
                return f'{obj}.insert({obj}.end(), {args[0]}.begin(), {args[0]}.end())'
            
            return f"{obj}.{method}({', '.join(args)})"
        
        return "/* function call not translated */"
    
    def _translate_binary_op(self, op: ast.AST) -> str:
        """Translate binary operators."""
        op_map = {
            ast.Add: '+',
            ast.Sub: '-', 
            ast.Mult: '*',
            ast.Div: '/',
            ast.Mod: '%',
            ast.Pow: '**',  # Will need special handling
            ast.LShift: '<<',
            ast.RShift: '>>',
            ast.BitOr: '|',
            ast.BitXor: '^',
            ast.BitAnd: '&'
        }
        return op_map.get(type(op), '?')
    
    def _translate_comparison_op(self, op: ast.AST) -> str:
        """Translate comparison operators."""
        op_map = {
            ast.Eq: '==',
            ast.NotEq: '!=',
            ast.Lt: '<',
            ast.LtE: '<=',
            ast.Gt: '>',
            ast.GtE: '>=',
            ast.Is: '==',
            ast.IsNot: '!='
        }
        return op_map.get(type(op), '?')
    
    def _infer_expression_type(self, node: ast.AST) -> str:
        """Infer C++ type from expression."""
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
            return self.local_vars.get(node.id, 'auto')
        elif isinstance(node, ast.List):
            if node.elts:
                element_type = self._infer_expression_type(node.elts[0])
                return f'std::vector<{element_type}>'
            return 'std::vector<int>'
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in ['len', 'sum']:
                    return 'int'
                elif func_name == 'str':
                    return 'std::string'
        
        return 'auto'
    
    def _infer_return_type_from_body(self, body_nodes: List[ast.AST]) -> Optional[str]:
        """Infer return type by analyzing return statements."""
        for node in ast.walk(ast.Module(body=body_nodes, type_ignores=[])):
            if isinstance(node, ast.Return) and node.value:
                return self._infer_expression_type(node.value)
        return None
    
    def _get_default_value(self, type_str: str) -> str:
        """Get default value for C++ type."""
        defaults = {
            'int': '0',
            'double': '0.0',
            'bool': 'false', 
            'std::string': '""',
            'void': '',
        }
        if type_str.startswith('std::vector'):
            return f'{type_str}()'
        elif type_str.startswith('std::map'):
            return f'{type_str}()'
        return defaults.get(type_str, '{}')