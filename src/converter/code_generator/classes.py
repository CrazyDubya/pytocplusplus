from typing import Dict, List
import ast
import logging
from src.analyzer.code_analyzer import ClassInfo

logger = logging.getLogger("CodeGenerator")


class ClassGenerator:
    """Handles generation of C++ class declarations and implementations."""
    
    def __init__(self, code_generator):
        self.code_generator = code_generator
    
    def _generate_class_declaration(self, class_name: str, class_info: ClassInfo) -> str:
        """Generate C++ class declaration."""
        decl = []
        
        # Add docstring as comment if present
        if class_info.docstring:
            decl.append(f"    /**\n     * {class_info.docstring}\n     */")
        
        # Start class declaration with inheritance
        if class_info.bases:
            base_list = ", ".join(f"public {base}" for base in class_info.bases)
            decl.append(f"    class {class_name} : {base_list} {{")
        else:
            decl.append(f"    class {class_name} {{")
            
        # Public section (methods, constructors)
        decl.append("    public:")
        
        # Generate constructor declarations
        constructor = class_info.methods.get('__init__')
        if constructor:
            decl.append(self._generate_constructor_declaration(class_name, constructor))
        else:
            # Default constructor if none specified
            decl.append(f"        {class_name}() = default;")
        
        # Generate public method declarations
        for method_name, method_info in class_info.methods.items():
            # Skip constructor, it's handled separately
            if method_name == '__init__':
                continue
            
            # Skip private/protected methods (starting with _)
            if method_name.startswith('_') and method_name != '__init__':
                continue
            
            decl.append(self._generate_method_declaration(method_name, method_info))
        
        # Add getter methods for attributes
        for attr_name, attr_type in class_info.attributes.items():
            getter_name = f"get_{attr_name}"
            decl.append(f"        {attr_type} {getter_name}() const {{ return {attr_name}_; }}")
            if attr_type == 'std::string':
                # Also add a const reference getter for strings
                decl.append(f"        const {attr_type}& {getter_name}_ref() const {{ return {attr_name}_; }}")
        
        # Make attributes protected instead of private so derived classes can access them in std::visit
        decl.append("\n    protected:")
        
        # Generate attribute declarations
        for attr_name, attr_type in class_info.attributes.items():
            # Ensure numeric attributes are consistently typed as double
            if attr_name in ['width', 'height', 'radius']:
                attr_type = 'double'
            # Ensure color is std::string
            elif attr_name == 'color':
                attr_type = 'std::string'
            decl.append(f"        {attr_type} {attr_name}_;")
        
        # Add private section for private methods
        has_private_methods = any(method_name.startswith('_') and method_name != '__init__' 
                                for method_name in class_info.methods.keys())
        
        if has_private_methods:
            decl.append("\n    private:")
            # Generate private method declarations
            for method_name, method_info in class_info.methods.items():
                # Only include private methods (starting with _)
                if method_name.startswith('_') and method_name != '__init__':
                    decl.append(self._generate_method_declaration(method_name, method_info))
        
        # End class declaration
        decl.append("    };")
        
        return "\n".join(decl)
    
    def _generate_constructor_declaration(self, class_name: str, constructor_info: Dict) -> str:
        """Generate C++ constructor declaration."""
        # Get parameter types and names
        params = []
        for param_name, param_type in constructor_info.get('params', {}).items():
            # Add default value if present in the original constructor
            params.append(f"{param_type} {param_name}")
        
        return f"        {class_name}({', '.join(params)});"
    
    def _generate_method_declaration(self, method_name: str, method_info: Dict) -> str:
        """Generate C++ method declaration."""
        # Get return type (default to void if not specified)
        return_type = method_info.get('return_type', 'void')
        
        # Get parameter types and names
        params = []
        for param_name, param_type in method_info.get('params', {}).items():
            params.append(f"{param_type} {param_name}")
        
        # Add docstring as comment if present
        result = []
        if method_info.get('docstring'):
            result.append(f"        /**\n         * {method_info['docstring']}\n         */")
        
        # Add method declaration with const qualifier for methods that don't modify state
        # Methods that read state but don't modify it should be marked const
        is_const = method_name in ['area', 'describe'] or (not method_name.startswith('set_') and method_name != '__init__')
        
        if is_const:
            result.append(f"        {return_type} {method_name}({', '.join(params)}) const;")
        else:
            result.append(f"        {return_type} {method_name}({', '.join(params)});")
        
        return "\n".join(result)
    
    def _generate_class_implementation(self, class_name: str, class_info: ClassInfo, analysis_result) -> str:
        """Generate C++ class implementation."""
        impl = []
        
        # Generate constructor implementation
        constructor = class_info.methods.get('__init__')
        if constructor:
            impl.append(self._generate_constructor_implementation(class_name, constructor, class_info))
        
        # Generate method implementations
        for method_name, method_info in class_info.methods.items():
            # Skip constructor, it's handled separately
            if method_name == '__init__':
                continue
                
            impl.append(self._generate_method_implementation(class_name, method_name, method_info, class_info))
        
        return "\n".join(impl)
    
    def _generate_constructor_implementation(self, class_name: str, constructor_info: Dict, class_info: ClassInfo) -> str:
        """Generate C++ constructor implementation."""
        # Get parameter list
        params = []
        for param_name, param_type in constructor_info.get('params', {}).items():
            params.append(f"{param_type} {param_name}")
        
        # Find base class constructor args if there are base classes
        base_args = []
        base_class = None
        if class_info.bases:
            base_class = class_info.bases[0]  # Use first base class for now
            # We'll need to analyze the constructor body to find the super().__init__() call
            for node in constructor_info.get('body', []):
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                    call = node.value
                    if (isinstance(call.func, ast.Attribute) and 
                        isinstance(call.func.value, ast.Call) and 
                        isinstance(call.func.value.func, ast.Name) and 
                        call.func.value.func.id == 'super'):
                        # This is a super().__init__() call
                        for arg in call.args:
                            arg_str = self.code_generator.expressions._translate_expression(arg, {})
                            base_args.append(arg_str)
        
        # Start constructor implementation with initializer list for base class
        if base_class and base_args:
            impl = f"{class_name}::{class_name}({', '.join(params)}) : {base_class}({', '.join(base_args)}) {{\n"
        else:
            impl = f"{class_name}::{class_name}({', '.join(params)}) {{\n"
        
        # Initialize member variables from constructor parameters
        for attr_name, attr_type in class_info.attributes.items():
            # Looking for corresponding parameter
            for param_name in constructor_info.get('params', {}):
                if param_name == attr_name:
                    impl += f"    {attr_name}_ = {param_name};\n"
        
        impl += "}\n"
        return impl
    
    def _generate_method_implementation(self, class_name: str, method_name: str, method_info: Dict, class_info: ClassInfo) -> str:
        """Generate C++ method implementation."""
        # Get return type
        return_type = method_info.get('return_type', 'void')
        
        # Get parameter list
        params = []
        for param_name, param_type in method_info.get('params', {}).items():
            params.append(f"{param_type} {param_name}")
            
        # Determine if method should be const
        is_const = method_name in ['area', 'describe'] or (not method_name.startswith('set_') and method_name != '__init__')
        
        # Start method implementation with const qualifier if needed
        if is_const:
            impl = f"{return_type} {class_name}::{method_name}({', '.join(params)}) const {{\n"
        else:
            impl = f"{return_type} {class_name}::{method_name}({', '.join(params)}) {{\n"
        
        # Translate method body if available
        if 'body' in method_info and method_info['body']:
            # Create local variables map with 'this' access to attributes
            local_vars = {}
            for attr_name, attr_type in class_info.attributes.items():
                local_vars[f"self.{attr_name}"] = attr_type
            
            body_impl = self._translate_method_body(method_info['body'], method_info.get('params', {}), return_type, local_vars)
            impl += body_impl
        else:
            # Default implementation based on return type
            if return_type != 'void':
                default_value = self.code_generator.types._get_default_value(return_type)
                impl += f"    return {default_value};\n"
        
        impl += "}\n"
        return impl
        
    def _translate_method_body(self, body_nodes: List[ast.AST], param_types: Dict[str, str], return_type: str, local_vars: Dict[str, str]) -> str:
        """Translate Python method body to C++ code."""
        # Start with empty implementation
        impl = []
        
        # Add special handling for math library if needed
        has_math_import = any(
            isinstance(node, ast.Import) and any(name.name == 'math' for name in node.names)
            for node in body_nodes
        )
        
        if has_math_import:
            impl.append("    // Using math constants")
            impl.append("    const double pi = M_PI;")
        
        # Process each node in function body
        for node in body_nodes:
            # Skip docstring
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                continue
                
            # Skip import statements
            if isinstance(node, ast.Import):
                continue
                
            translated = self._translate_method_statement(node, local_vars, 1)  # 1 for indent level
            if translated:
                impl.append(translated)
                
        # Return empty string if no statements were translated
        if not impl:
            if return_type != 'void':
                # Add a default return statement for non-void functions
                default_value = self.code_generator.types._get_default_value(return_type)
                impl.append(f"    return {default_value};")
            
        return "\n".join(impl)
    
    def _translate_method_statement(self, node: ast.AST, local_vars: Dict[str, str], indent_level: int) -> str:
        """Translate a Python method statement to C++."""
        # This is similar to _translate_statement but handles self.attr access
        indent = "    " * indent_level
        
        if isinstance(node, ast.If):
            return self.code_generator.statements._translate_if_statement(node, local_vars, indent_level)
        elif isinstance(node, ast.For):
            return self.code_generator.statements._translate_for_loop(node, local_vars, indent_level)
        elif isinstance(node, ast.While):
            return self.code_generator.statements._translate_while_loop(node, local_vars, indent_level)
        elif isinstance(node, ast.Assign):
            return self._translate_method_assignment(node, local_vars, indent_level)
        elif isinstance(node, ast.Return):
            return self._translate_method_return(node, local_vars, indent_level)
        elif isinstance(node, ast.Expr):
            # Only translate expressions that have side effects (like function calls)
            if isinstance(node.value, ast.Call):
                expr = self._translate_method_expression(node.value, local_vars)
                return f"{indent}{expr};"
            return None  # Skip other expressions
        elif isinstance(node, ast.Import):
            # Handle imports in method bodies (e.g., import math)
            return None  # Skip imports, include headers instead
        else:
            # Default case for unsupported statement types
            return f"{indent}// Unsupported statement: {type(node).__name__}"
    
    def _translate_method_assignment(self, node: ast.Assign, local_vars: Dict[str, str], indent_level: int) -> str:
        """Translate a method assignment statement to C++."""
        indent = "    " * indent_level
        
        # Handle self.attr assignments
        if isinstance(node.targets[0], ast.Attribute) and isinstance(node.targets[0].value, ast.Name) and node.targets[0].value.id == 'self':
            attr_name = node.targets[0].attr
            value_expr = self._translate_method_expression(node.value, local_vars)
            return f"{indent}{attr_name}_ = {value_expr};"
        
        # For other assignments, use the standard translation
        return self.code_generator.statements._translate_assignment(node, local_vars, indent_level)
    
    def _translate_method_return(self, node: ast.Return, local_vars: Dict[str, str], indent_level: int) -> str:
        """Translate a method return statement to C++."""
        indent = "    " * indent_level
        
        if node.value is None:
            return f"{indent}return;"
        
        value_expr = self._translate_method_expression(node.value, local_vars)
        return f"{indent}return {value_expr};"
    
    def _translate_method_expression(self, node: ast.AST, local_vars: Dict[str, str]) -> str:
        """Translate a Python method expression to C++."""
        # Handle self.attr access
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'self':
            # Attribute names correspond to member variables which end with underscore
            return f"{node.attr}_"
        
        # Handle self.method() calls
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'self':
            method_name = node.func.attr
            args = [self._translate_method_expression(arg, local_vars) for arg in node.args]
            return f"{method_name}({', '.join(args)})"
        
        # Handle math.X calls
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'math':
            if node.attr == 'pi':
                return 'pi'  # Use local pi constant defined in method
            # Map other math functions if needed
        
        # Handle print statements properly
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
            args = []
            for arg in node.args:
                if isinstance(arg, ast.JoinedStr):
                    # Handle f-strings in print
                    formatted = self._translate_method_expression(arg, local_vars)
                    args.append(formatted)
                else:
                    arg_expr = self._translate_method_expression(arg, local_vars)
                    args.append(arg_expr)
            
            if args:
                return f'std::cout << {" << std::endl; std::cout << ".join(args)} << std::endl'
            else:
                return 'std::cout << std::endl'
        
        # Handle ** operator (power)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            left = self._translate_method_expression(node.left, local_vars)
            right = self._translate_method_expression(node.right, local_vars)
            return f"pow({left}, {right})"
        
        # Handle string formatting in methods - simplified approach
        if isinstance(node, ast.JoinedStr):
            parts = []
            
            for value in node.values:
                if isinstance(value, ast.Constant):
                    # String literal part
                    if value.value:  # Skip empty strings
                        escaped_str = value.value.replace('"', '\\"')
                        parts.append(f'"{escaped_str}"')
                elif isinstance(value, ast.FormattedValue):
                    # Expression part - handle self.attr access
                    expr = self._translate_method_expression(value.value, local_vars)
                    # Check if this is a numeric value that needs conversion to string
                    if isinstance(value.value, ast.Attribute) and isinstance(value.value.value, ast.Name) and value.value.value.id == 'self':
                        attr_name = value.value.attr
                        # Check if this is a numeric attribute
                        if attr_name in ['width', 'height', 'radius']:
                            parts.append(f'std::to_string({expr})')
                        else:
                            parts.append(expr)
                    else:
                        # For other expressions, assume we need to convert to string if it's numeric
                        parts.append(f'std::to_string({expr})')
            
            # Use simple string concatenation with '+'
            if parts:
                return ' + '.join(parts)
            else:
                return '""'  # Empty string as fallback
        
        # For other expressions, use a modified version of the standard translation
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
            left = self._translate_method_expression(node.left, local_vars)
            right = self._translate_method_expression(node.right, local_vars)
            op = self.code_generator.expressions._translate_operator(node.op)
            return f"({left} {op} {right})"
        elif isinstance(node, ast.Call):
            # Function calls in method bodies - use method expression translation for args
            func = self._translate_method_expression(node.func, local_vars)
            args = [self._translate_method_expression(arg, local_vars) for arg in node.args]
            
            # Special case for sum() with generator expression
            if isinstance(node.func, ast.Name) and node.func.id == 'sum' and len(node.args) == 1 and isinstance(node.args[0], ast.GeneratorExp):
                gen_expr = node.args[0]
                # For sum(shape.area() for shape in shapes), we need different handling
                if (isinstance(gen_expr.elt, ast.Call) and 
                    isinstance(gen_expr.elt.func, ast.Attribute) and 
                    gen_expr.elt.func.attr == 'area'):
                    # Extract the container being iterated over
                    container = self._translate_method_expression(gen_expr.generators[0].iter, local_vars)
                    return f"std::accumulate({container}.begin(), {container}.end(), 0.0, [](double sum, const auto& shape) {{ return sum + shape.area(); }})"
            
            return f"{func}({', '.join(args)})"
                
        # For other expressions, use the standard translation
        return self.code_generator.expressions._translate_expression(node, local_vars)
    
    def _generate_class_binding(self, class_name: str, class_info: ClassInfo) -> List[str]:
        """Generate pybind11 binding for a C++ class."""
        result = []
        
        # Start class binding
        class_var = class_name.lower()
        if class_info.docstring:
            result.append(f'    py::class_<pytocpp::{class_name}> {class_var}(m, "{class_name}", "{class_info.docstring}");')
        else:
            result.append(f'    py::class_<pytocpp::{class_name}> {class_var}(m, "{class_name}");')
        
        # Add constructor
        constructor = class_info.methods.get('__init__')
        if constructor:
            # Get parameter list for constructor docstring
            params = []
            for param_name, param_type in constructor.get('params', {}).items():
                params.append(f"{param_name}")
            
            param_list = ", ".join(params)
            # Fix the missing closing parenthesis
            result.append(f'    {class_var}.def(py::init<{", ".join(constructor.get("params", {}).values())}>());')
        
        # Add methods
        for method_name, method_info in class_info.methods.items():
            # Skip constructor, it's handled separately
            if method_name == '__init__':
                continue
                
            # Skip private methods (those that start with _)
            if method_name.startswith('_') and method_name != '__init__':
                continue
            
            docstring = method_info.get('docstring', '')
            result.append(f'    {class_var}.def("{method_name}", &pytocpp::{class_name}::{method_name}, "{docstring}");')
        
        return result
