from typing import Dict
import ast
import logging

logger = logging.getLogger("CodeGenerator")


class StatementTranslator:
    """Handles translation of Python statements to C++."""
    
    def __init__(self, code_generator):
        self.code_generator = code_generator
    
    def _translate_statement(self, node: ast.AST, local_vars: Dict[str, str], indent_level: int) -> str:
        """Translate a Python statement to C++."""
        indent = "    " * indent_level
        
        if isinstance(node, ast.If):
            return self._translate_if_statement(node, local_vars, indent_level)
        elif isinstance(node, ast.For):
            return self._translate_for_loop(node, local_vars, indent_level)
        elif isinstance(node, ast.While):
            return self._translate_while_loop(node, local_vars, indent_level)
        elif isinstance(node, ast.Assign):
            return self._translate_assignment(node, local_vars, indent_level)
        elif isinstance(node, ast.Return):
            return self._translate_return(node, local_vars, indent_level)
        elif isinstance(node, ast.Expr):
            # Only translate expressions that have side effects (like function calls)
            if isinstance(node.value, ast.Call):
                expr = self.code_generator.expressions._translate_expression(node.value, local_vars)
                return f"{indent}{expr};"
            return None  # Skip other expressions
        else:
            # Default case for unsupported statement types
            return f"{indent}// Unsupported statement: {type(node).__name__}"
    
    def _translate_if_statement(self, node: ast.If, local_vars: Dict[str, str], indent_level: int) -> str:
        """Translate an if statement to C++."""
        indent = "    " * indent_level
        
        # Translate condition
        condition = self.code_generator.expressions._translate_expression(node.test, local_vars)
        
        result = [f"{indent}if ({condition}) {{"]
        
        # Translate body
        for stmt in node.body:
            translated = self._translate_statement(stmt, local_vars, indent_level + 1)
            if translated:
                result.append(translated)
        
        result.append(f"{indent}}}")
        
        # Translate elif/else branches
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                # This is an elif branch
                elif_branch = self._translate_statement(node.orelse[0], local_vars, indent_level)
                # Replace the first "if" with "else if"
                elif_branch = elif_branch.replace(f"{indent}if", f"{indent}else if", 1)
                result.append(elif_branch)
            else:
                # This is an else branch
                result.append(f"{indent}else {{")
                for stmt in node.orelse:
                    translated = self._translate_statement(stmt, local_vars, indent_level + 1)
                    if translated:
                        result.append(translated)
                result.append(f"{indent}}}")
        
        return "\n".join(result)
    
    def _translate_for_loop(self, node: ast.For, local_vars: Dict[str, str], indent_level: int) -> str:
        """Translate a for loop to C++."""
        indent = "    " * indent_level
        
        # Check if this is a range-based loop
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
            # Handle different range() forms: range(stop), range(start, stop), range(start, stop, step)
            if len(node.iter.args) == 1:
                # range(stop)
                start = '0'
                stop = self.code_generator.expressions._translate_expression(node.iter.args[0], local_vars)
                step = '1'
            elif len(node.iter.args) == 2:
                # range(start, stop)
                start = self.code_generator.expressions._translate_expression(node.iter.args[0], local_vars)
                stop = self.code_generator.expressions._translate_expression(node.iter.args[1], local_vars)
                step = '1'
            elif len(node.iter.args) == 3:
                # range(start, stop, step)
                start = self.code_generator.expressions._translate_expression(node.iter.args[0], local_vars)
                stop = self.code_generator.expressions._translate_expression(node.iter.args[1], local_vars)
                step = self.code_generator.expressions._translate_expression(node.iter.args[2], local_vars)
            else:
                return f"{indent}// Unsupported range() form"
            
            # Use iterator name from Python or 'i' if it's a throwaway variable (_)
            iterator_name = self.code_generator.expressions._translate_expression(node.target, local_vars)
            if iterator_name == '_':
                iterator_name = 'i'
                
            # Create a C++ for loop
            result = [f"{indent}for (int {iterator_name} = {start}; {iterator_name} < {stop}; {iterator_name} += {step}) {{"]
            
            # Translate body
            for stmt in node.body:
                translated = self._translate_statement(stmt, local_vars, indent_level + 1)
                if translated:
                    result.append(translated)
            
            result.append(f"{indent}}}")
            return "\n".join(result)
        else:
            # Handle general iteration over a container
            iterable = self.code_generator.expressions._translate_expression(node.iter, local_vars)
            iterator_name = self.code_generator.expressions._translate_expression(node.target, local_vars)
            
            # Try to determine element type from the iterable
            element_type = 'auto'  # Default to auto if we can't determine
            
            # Create a C++ range-based for loop
            result = [f"{indent}for ({element_type} {iterator_name} : {iterable}) {{"]
            
            # Translate body
            for stmt in node.body:
                translated = self._translate_statement(stmt, local_vars, indent_level + 1)
                if translated:
                    result.append(translated)
            
            result.append(f"{indent}}}")
            return "\n".join(result)
    
    def _translate_while_loop(self, node: ast.While, local_vars: Dict[str, str], indent_level: int) -> str:
        """Translate a while loop to C++."""
        indent = "    " * indent_level
        
        # Translate condition
        condition = self.code_generator.expressions._translate_expression(node.test, local_vars)
        
        result = [f"{indent}while ({condition}) {{"]
        
        # Translate body
        for stmt in node.body:
            translated = self._translate_statement(stmt, local_vars, indent_level + 1)
            if translated:
                result.append(translated)
        
        result.append(f"{indent}}}")
        return "\n".join(result)
    
    def _translate_assignment(self, node: ast.Assign, local_vars: Dict[str, str], indent_level: int) -> str:
        """Translate an assignment to C++."""
        indent = "    " * indent_level
        result = []
        
        # Get the value expression
        value_expr = self.code_generator.expressions._translate_expression(node.value, local_vars)
        
        # Handle tuple unpacking
        if isinstance(node.targets[0], ast.Tuple):
            if isinstance(node.value, ast.Tuple):
                # Direct tuple unpacking: a, b = 1, 2 or a, b = b, a + b
                # For simultaneous assignment, we need to evaluate all values first
                target_vars = []
                value_exprs = []
                temp_vars = []
                
                # First, evaluate all values and store in temp variables if needed
                for i, (target, value) in enumerate(zip(node.targets[0].elts, node.value.elts)):
                    if isinstance(target, ast.Name):
                        target_name = target.id
                        value_expr = self.code_generator.expressions._translate_expression(value, local_vars)
                        
                        # Check if the value expression uses any of the target variables
                        # This handles cases like a, b = b, a + b
                        uses_target_vars = any(
                            isinstance(t, ast.Name) and t.id == target_name 
                            for t in node.targets[0].elts[:i]  # Only check previous targets
                        )
                        
                        # If the value expression refers to variables we're about to change,
                        # we need a temporary variable
                        value_uses_changing_vars = self.code_generator.expressions._expression_uses_variables(
                            value, [t.id for t in node.targets[0].elts if isinstance(t, ast.Name)]
                        )
                        
                        if value_uses_changing_vars and i > 0:
                            # Create a temporary variable
                            temp_var = f"temp_{i}"
                            value_type = self.code_generator.types._infer_cpp_type(value, local_vars)
                            temp_vars.append(f"{indent}{value_type} {temp_var} = {value_expr};")
                            value_exprs.append(temp_var)
                        else:
                            value_exprs.append(value_expr)
                        
                        target_vars.append(target_name)
                
                # Generate temporary variable declarations first
                result.extend(temp_vars)
                
                # Then generate the actual assignments
                for i, (target_name, value_expr) in enumerate(zip(target_vars, value_exprs)):
                    if target_name not in local_vars:
                        # Infer type from value
                        value_type = self.code_generator.types._infer_cpp_type(node.value.elts[i], local_vars)
                        local_vars[target_name] = value_type
                        result.append(f"{indent}{value_type} {target_name} = {value_expr};")
                    else:
                        result.append(f"{indent}{target_name} = {value_expr};")
                
                return "\n".join(result)
            else:
                # Handle tuple unpacking like: a, b = some_func()
                # In C++, we can use std::tie or structured bindings
                targets = []
                for target in node.targets[0].elts:
                    target_str = self.code_generator.expressions._translate_expression(target, local_vars)
                    targets.append(target_str)
                    
                # For simple cases, use structured bindings (C++17)
                all_new_vars = all(isinstance(t, ast.Name) and t.id not in local_vars for t in node.targets[0].elts)
                if all_new_vars:
                    targets_str = ", ".join(targets)
                    return f"{indent}auto [{targets_str}] = {value_expr};"
                else:
                    # Otherwise use std::tie
                    targets_str = ", ".join(targets)
                    return f"{indent}std::tie({targets_str}) = {value_expr};"
        
        # Regular assignment
        target_str = self.code_generator.expressions._translate_expression(node.targets[0], local_vars)
        
        # Check if this is a new variable declaration
        if isinstance(node.targets[0], ast.Name) and node.targets[0].id not in local_vars:
            # Infer type from value
            value_type = self.code_generator.types._infer_cpp_type(node.value, local_vars)
            local_vars[node.targets[0].id] = value_type
            return f"{indent}{value_type} {target_str} = {value_expr};"
        else:
            # Regular assignment to existing variable
            return f"{indent}{target_str} = {value_expr};"
    
    def _translate_return(self, node: ast.Return, local_vars: Dict[str, str], indent_level: int) -> str:
        """Translate a return statement to C++."""
        indent = "    " * indent_level
        
        if node.value is None:
            return f"{indent}return;"
        
        value_expr = self.code_generator.expressions._translate_expression(node.value, local_vars)
        return f"{indent}return {value_expr};"
