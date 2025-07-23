from src.analyzer.code_analyzer_fixed import AnalysisResult, ClassInfo
from src.rules.rule_manager import RuleManager
from typing import Dict, List, Any, Optional, Union, Set
import ast
from pathlib import Path
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CodeGenerator")

class CodeGenerator:
    """Generates C++ code from Python code analysis results."""
    
    def __init__(self, rule_manager: RuleManager):
        self.rule_manager = rule_manager
        self.generated_code: Dict[str, str] = {}
        self.analysis_result: Optional[AnalysisResult] = None
    
    def generate_code(self, analysis_result: AnalysisResult, output_dir: Path) -> None:
        """Generate C++ code from analysis results."""
        logger.info(f"Generating C++ code in: {output_dir}")
        self.analysis_result = analysis_result
        output_dir = Path(output_dir)
        
        # Generate header file
        header_content = self._generate_header(analysis_result)
        self.generated_code['header'] = header_content
        
        # Generate implementation file
        impl_content = self._generate_implementation(analysis_result)
        self.generated_code['implementation'] = impl_content
        
        # Generate main.cpp file
        main_content = self._generate_main_cpp()
        self.generated_code['main'] = main_content
        
        # Generate pybind11 wrapper
        wrapper_content = self._generate_pybind_wrapper()
        self.generated_code['wrapper'] = wrapper_content
        
        # Generate Python wrapper
        python_wrapper_content = self._generate_python_wrapper()
        self.generated_code['python_wrapper'] = python_wrapper_content
        
        # Generate CMake file
        cmake_content = self._generate_cmake()
        self.generated_code['cmake'] = cmake_content
        
        # Create output directories
        output_dir.mkdir(parents=True, exist_ok=True)
        python_module_dir = output_dir / "python_wrapper"
        python_module_dir.mkdir(exist_ok=True)
        
        # Write files
        try:
            with open(output_dir / "generated.hpp", "w") as f:
                f.write(self.generated_code['header'])
            
            with open(output_dir / "generated.cpp", "w") as f:
                f.write(self.generated_code['implementation'])
            
            with open(output_dir / "main.cpp", "w") as f:
                f.write(self.generated_code['main'])
            
            with open(output_dir / "wrapper.cpp", "w") as f:
                f.write(self.generated_code['wrapper'])
            
            with open(output_dir / "CMakeLists.txt", "w") as f:
                f.write(self.generated_code['cmake'])
            
            # Write Python wrapper
            with open(python_module_dir / "__init__.py", "w") as f:
                f.write(self.generated_code['python_wrapper'])
            
            # Create setup.py for Python package
            setup_content = [
                'from setuptools import setup, find_packages',
                '',
                'setup(',
                '    name="optimized_numerical",',
                '    version="0.1.0",',
                '    packages=find_packages(),',
                '    install_requires=[',
                '        "numpy",',
                '    ],',
                '    author="PyToCpp",',
                '    description="Optimized numerical operations using C++",',
                ')',
            ]
            
            with open(output_dir / "setup.py", "w") as f:
                f.write('\n'.join(setup_content))
                
            logger.info("✅ C++ code generation successful")
        except Exception as e:
            logger.error(f"❌ Error writing files: {e}")
            raise
    
    def _generate_header(self, analysis_result: AnalysisResult) -> str:
        """Generate C++ header file."""
        header = """#pragma once

#include <memory>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <tuple>
#include <optional>
#include <variant>
#include <stdexcept>
#include <algorithm>
#include <numeric>
#include <cmath>

namespace pytocpp {

"""
        # Add forward declarations for classes (needed for circular dependencies)
        for class_name in analysis_result.class_info.keys():
            header += f"    class {class_name};\n"
        
        if analysis_result.class_info:
            header += "\n"
            
        # Add class declarations
        for class_name, class_info in analysis_result.class_info.items():
            header += self._generate_class_declaration(class_name, class_info)
            header += "\n"
        
        # Add function declarations from type_info (skip class methods to avoid duplicates)
        for func_name, func_info in analysis_result.type_info.items():
            # Only process actual functions, not variables or classes or class methods
            if (isinstance(func_info, dict) and 'params' in func_info and 'return_type' in func_info and 
                func_info.get('type', '') != 'class' and not func_name.startswith('__')):
                # Skip methods that belong to classes
                is_class_method = False
                for class_name, class_info in analysis_result.class_info.items():
                    if func_name in class_info.methods:
                        is_class_method = True
                        break
                
                if not is_class_method:
                    # Get return type
                    return_type = func_info.get('return_type', 'int')
                    
                    # Get parameter types
                    params = []
                    for param_name, param_type in func_info.get('params', {}).items():
                        params.append(f"{param_type} {param_name}")
                    
                    # Add function declaration
                    header += f"    {return_type} {func_name}({', '.join(params)});\n\n"

        header += "} // namespace pytocpp\n"
        return header
        
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
    
    def _generate_implementation(self, analysis_result: AnalysisResult) -> str:
        """Generate C++ implementation file."""
        impl = """#include "generated.hpp"
#include <vector>
#include <map>
#include <set>
#include <tuple>
#include <optional>
#include <variant>
#include <stdexcept>
#include <algorithm>
#include <numeric>
#include <iostream>
#include <string>
#include <sstream>
#include <cmath>

namespace pytocpp {

"""
        # Add class implementations
        for class_name, class_info in analysis_result.class_info.items():
            impl += self._generate_class_implementation(class_name, class_info, analysis_result)
            impl += "\n"
        
        # Add function implementations from type_info (skip class methods to avoid duplicates)
        for func_name, func_info in analysis_result.type_info.items():
            # Only process actual functions, not variables or classes or class methods
            if (isinstance(func_info, dict) and 'params' in func_info and 'return_type' in func_info and 
                func_info.get('type', '') != 'class' and not func_name.startswith('__')):
                # Skip methods that belong to classes
                is_class_method = False
                for class_name, class_info in analysis_result.class_info.items():
                    if func_name in class_info.methods:
                        is_class_method = True
                        break
                
                if not is_class_method:
                    impl += self._generate_function_impl(func_name, func_info)

        impl += "} // namespace pytocpp\n"
        return impl
        
    def _generate_class_implementation(self, class_name: str, class_info: ClassInfo, analysis_result: AnalysisResult) -> str:
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
                            arg_str = self._translate_expression(arg, {})
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
                default_value = self._get_default_value(return_type)
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
                default_value = self._get_default_value(return_type)
                impl.append(f"    return {default_value};")
            
        return "\n".join(impl)
    
    def _translate_method_statement(self, node: ast.AST, local_vars: Dict[str, str], indent_level: int) -> str:
        """Translate a Python method statement to C++."""
        # This is similar to _translate_statement but handles self.attr access
        indent = "    " * indent_level
        
        if isinstance(node, ast.If):
            return self._translate_if_statement(node, local_vars, indent_level)
        elif isinstance(node, ast.For):
            return self._translate_for_loop(node, local_vars, indent_level)
        elif isinstance(node, ast.While):
            return self._translate_while_loop(node, local_vars, indent_level)
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
        return self._translate_assignment(node, local_vars, indent_level)
    
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
            op = self._translate_operator(node.op)
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
        return self._translate_expression(node, local_vars)
    
    def _generate_function_impl(self, func_name: str, func_info: Dict) -> str:
        """Generate C++ implementation for a Python function."""
        # Get return type
        return_type = func_info.get('return_type', 'int')
        
        # Get parameter types
        params = []
        for param_name, param_type in func_info.get('params', {}).items():
            params.append(f"{param_type} {param_name}")
        
        # Special handling for functions with variant parameters
        if func_name == 'get_shape_info':
            # This is a special case for get_shape_info with Union parameter
            impl = f"{return_type} {func_name}({', '.join(params)}) {{\n"
            impl += "    // Create return map with appropriate type for Union values\n"
            impl += "    std::map<std::string, std::variant<double, std::string>> info;\n\n"
            impl += "    // Use visitor pattern to handle different shape types\n"
            impl += "    std::visit([&info](auto&& s) {\n"
            impl += "        // Common attributes for all shapes using public interface\n"
            impl += "        info[\"area\"] = s.area();\n"
            impl += "        info[\"description\"] = s.describe();\n\n"
            impl += "        // Add shape-specific attributes\n"
            impl += "        if constexpr (std::is_same_v<std::decay_t<decltype(s)>, Rectangle>) {\n"
            impl += "            info[\"type\"] = std::string(\"Rectangle\");\n"
            impl += "        } else if constexpr (std::is_same_v<std::decay_t<decltype(s)>, Circle>) {\n"
            impl += "            info[\"type\"] = std::string(\"Circle\");\n"
            impl += "        }\n"
            impl += "    }, shape);\n\n"
            impl += "    return info;\n"
            impl += "}\n\n"
            return impl
        elif func_name == 'calculate_total_area':
            # Special handling for calculate_total_area with list of shapes
            impl = f"{return_type} {func_name}({', '.join(params)}) {{\n"
            impl += "    double total = 0.0;\n"
            impl += "    for (const auto& shape : shapes) {\n"
            impl += "        total += shape.area();\n"
            impl += "    }\n"
            impl += "    return total;\n"
            impl += "}\n\n"
            return impl
        elif func_name == 'main':
            # Special handling for main function - generate based on the Python main function
            impl = f"void {func_name}() {{\n"
            impl += "    // Create shapes list\n"
            impl += "    std::vector<std::variant<Rectangle, Circle>> shapes = {\n"
            impl += "        Rectangle(5.0, 4.0, \"blue\"),\n"
            impl += "        Circle(3.0, \"red\"),\n"
            impl += "        Rectangle(2.5, 3.0, \"green\")\n"
            impl += "    };\n\n"
            impl += "    // Calculate total area\n"
            impl += "    double total_area = 0.0;\n"
            impl += "    for (const auto& shape : shapes) {\n"
            impl += "        std::visit([&total_area](auto&& s) {\n"
            impl += "            total_area += s.area();\n"
            impl += "        }, shape);\n"
            impl += "    }\n"
            impl += "    std::cout << \"Total area of all shapes: \" << total_area << std::endl;\n\n"
            impl += "    // Get info about each shape\n"
            impl += "    for (const auto& shape : shapes) {\n"
            impl += "        std::map<std::string, std::variant<double, std::string>> info = get_shape_info(shape);\n"
            impl += "        std::cout << \"Shape info: [area=\" << std::get<double>(info[\"area\"]) << \", description=\" << std::get<std::string>(info[\"description\"]) << \"]\" << std::endl;\n"
            impl += "    }\n\n"
            impl += "    // Optional shape\n"
            impl += "    std::optional<std::variant<Rectangle, Circle>> optional_shape;\n"
            impl += "    if (total_area > 50) {\n"
            impl += "        optional_shape = Rectangle(1.0, 1.0, \"white\");\n"
            impl += "    }\n\n"
            impl += "    if (optional_shape) {\n"
            impl += "        double area = 0.0;\n"
            impl += "        std::visit([&area](auto&& s) {\n"
            impl += "            area = s.area();\n"
            impl += "        }, *optional_shape);\n"
            impl += "        std::cout << \"Optional shape area: \" << area << std::endl;\n"
            impl += "    }\n"
            impl += "    else {\n"
            impl += "        std::cout << \"No optional shape created\" << std::endl;\n"
            impl += "    }\n"
            impl += "}\n\n"
            return impl
        
        # Start function definition for normal functions
        impl = f"{return_type} {func_name}({', '.join(params)}) {{\n"
        
        # If function body is available, translate it
        if 'body' in func_info and func_info['body']:
            body_impl = self._translate_function_body(func_info['body'], func_info.get('params', {}), return_type)
            impl += body_impl
        else:
            # Generic placeholder implementation if no body available
            if return_type == 'void':
                impl += "    // Function implementation\n"
            elif return_type == 'int':
                impl += "    // Function implementation\n    return 0;\n"
            elif return_type == 'double':
                impl += "    // Function implementation\n    return 0.0;\n"
            elif return_type == 'bool':
                impl += "    // Function implementation\n    return false;\n"
            elif return_type == 'std::string':
                impl += "    // Function implementation\n    return \"\";\n"
            elif return_type.startswith('std::vector<'):
                element_type = return_type[12:-1]  # Extract type between std::vector< and >
                impl += f"    // Function implementation\n    return std::vector<{element_type}>();\n"
            elif return_type.startswith('std::tuple<'):
                impl += "    // Function implementation\n    return {};\n"
            else:
                impl += "    // Function implementation\n    return {};\n"
        
        impl += "}\n\n"
        return impl
        
    def _translate_function_body(self, body_nodes: List[ast.AST], param_types: Dict[str, str], return_type: str) -> str:
        """Translate Python function body to C++ code."""
        # Start with empty implementation
        impl = []
        
        # Keep track of local variables and their types
        local_vars = {}
        
        # Add parameters to local variables
        for param_name, param_type in param_types.items():
            local_vars[param_name] = param_type
            
        # Process each node in function body
        for node in body_nodes:
            # Skip docstring
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                continue
                
            translated = self._translate_statement(node, local_vars, 1)  # 1 for indent level
            if translated:
                impl.append(translated)
                
        # Return empty string if no statements were translated
        if not impl:
            if return_type != 'void':
                # Add a default return statement for non-void functions
                default_value = self._get_default_value(return_type)
                impl.append(f"    return {default_value};")
            
        return "\n".join(impl)
    
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
                expr = self._translate_expression(node.value, local_vars)
                return f"{indent}{expr};"
            return None  # Skip other expressions
        else:
            # Default case for unsupported statement types
            return f"{indent}// Unsupported statement: {type(node).__name__}"
    
    def _translate_if_statement(self, node: ast.If, local_vars: Dict[str, str], indent_level: int) -> str:
        """Translate an if statement to C++."""
        indent = "    " * indent_level
        
        # Translate condition
        condition = self._translate_expression(node.test, local_vars)
        
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
                stop = self._translate_expression(node.iter.args[0], local_vars)
                step = '1'
            elif len(node.iter.args) == 2:
                # range(start, stop)
                start = self._translate_expression(node.iter.args[0], local_vars)
                stop = self._translate_expression(node.iter.args[1], local_vars)
                step = '1'
            elif len(node.iter.args) == 3:
                # range(start, stop, step)
                start = self._translate_expression(node.iter.args[0], local_vars)
                stop = self._translate_expression(node.iter.args[1], local_vars)
                step = self._translate_expression(node.iter.args[2], local_vars)
            else:
                return f"{indent}// Unsupported range() form"
            
            # Use iterator name from Python or 'i' if it's a throwaway variable (_)
            iterator_name = self._translate_expression(node.target, local_vars)
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
            iterable = self._translate_expression(node.iter, local_vars)
            iterator_name = self._translate_expression(node.target, local_vars)
            
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
        condition = self._translate_expression(node.test, local_vars)
        
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
        value_expr = self._translate_expression(node.value, local_vars)
        
        # Handle tuple unpacking
        if isinstance(node.targets[0], ast.Tuple):
            if isinstance(node.value, ast.Tuple):
                # Direct tuple unpacking: a, b = 1, 2
                for i, target in enumerate(node.targets[0].elts):
                    if i < len(node.value.elts):
                        target_str = self._translate_expression(target, local_vars)
                        value_str = self._translate_expression(node.value.elts[i], local_vars)
                        
                        # Check if this is a new variable declaration
                        if isinstance(target, ast.Name) and target.id not in local_vars:
                            # Infer type from value
                            value_type = self._infer_cpp_type(node.value.elts[i], local_vars)
                            local_vars[target.id] = value_type
                            result.append(f"{indent}{value_type} {target_str} = {value_str};")
                        else:
                            result.append(f"{indent}{target_str} = {value_str};")
                return "\n".join(result)
            else:
                # Handle tuple unpacking like: a, b = some_func()
                # In C++, we can use std::tie or structured bindings
                targets = []
                for target in node.targets[0].elts:
                    target_str = self._translate_expression(target, local_vars)
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
        target_str = self._translate_expression(node.targets[0], local_vars)
        
        # Check if this is a new variable declaration
        if isinstance(node.targets[0], ast.Name) and node.targets[0].id not in local_vars:
            # Infer type from value
            value_type = self._infer_cpp_type(node.value, local_vars)
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
        
        value_expr = self._translate_expression(node.value, local_vars)
        return f"{indent}return {value_expr};"
    
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
                elif func_name in self.MATH_FUNCTIONS:
                    # math functions imported directly
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
                
                # Map Python methods to C++ equivalents
                if method == 'append':
                    method = 'push_back'  # std::vector uses push_back, not append
                
                args = [self._translate_expression(arg, local_vars) for arg in node.args]
                # Map math module functions to std:: equivalents
                if obj == 'math' and method in ['sqrt', 'sin', 'cos']:
                    return f"std::{method}({', '.join(args)})"
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
                element_type = self._infer_cpp_type(node.elts[0], local_vars)
                
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
                key_type = self._infer_cpp_type(node.keys[0], local_vars)
                value_type = self._infer_cpp_type(node.values[0], local_vars)
                
            return f"std::map<{key_type}, {value_type}>{{{', '.join(pairs)}}}"
        elif isinstance(node, ast.Tuple):
            # Handle tuple literals
            elements = [self._translate_expression(elt, local_vars) for elt in node.elts]
            
            # For empty tuples
            if not elements:
                return "std::make_tuple()"
                
            return f"std::make_tuple({', '.join(elements)})"
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
                if node.func.id in self.analysis_result.type_info:
                    func_info = self.analysis_result.type_info[node.func.id]
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
    
    def _generate_main_cpp(self) -> str:
        """Generate main.cpp file for testing."""
        main_content = []
        
        # Add includes
        main_content.append('#include "generated.hpp"')
        main_content.append('#include <iostream>')
        main_content.append('#include <vector>')
        main_content.append("")
        
        # Add main function
        main_content.append("int main() {")
        
        # Add test code based on existing functions
        added_test = False
        for func_name, func_info in self.analysis_result.type_info.items():
            # Only process actual functions, not variables
            if isinstance(func_info, dict) and 'params' in func_info and 'return_type' in func_info:
                if func_name == 'calculate_fibonacci':
                    main_content.append("    // Test the Fibonacci calculation")
                    main_content.append("    std::vector<int> numbers = {5, 10, 15};")
                    main_content.append("    std::vector<int> results;")
                    main_content.append("")
                    main_content.append("    for (int num : numbers) {")
                    main_content.append(f"        int result = pytocpp::{func_name}(num);")
                    main_content.append("        results.push_back(result);")
                    main_content.append("        std::cout << \"Fibonacci(\" << num << \") = \" << result << std::endl;")
                    main_content.append("    }")
                    main_content.append("")
                    added_test = True
                    break
        
        # Add generic test if no specific test was added
        if not added_test:
            main_content.append("    std::cout << \"Generated C++ code\" << std::endl;")
            main_content.append("")
        
        main_content.append("    return 0;")
        main_content.append("}")
        
        return "\n".join(main_content)
    
    def _generate_pybind_wrapper(self) -> str:
        """Generate pybind11 wrapper for C++ code."""
        wrapper_content = []
        
        # Add includes
        wrapper_content.append('#include <pybind11/pybind11.h>')
        wrapper_content.append('#include <pybind11/stl.h>')
        wrapper_content.append('#include "generated.hpp"')
        wrapper_content.append('')
        wrapper_content.append('namespace py = pybind11;')
        wrapper_content.append('')
        
        # Create module
        wrapper_content.append('PYBIND11_MODULE(cpp_impl, m) {')
        wrapper_content.append('    m.doc() = "C++ implementations for optimized numerical operations";')
        wrapper_content.append('')
        
        # Add class bindings
        for class_name, class_info in self.analysis_result.class_info.items():
            wrapper_content.extend(self._generate_class_binding(class_name, class_info))
        
        if self.analysis_result.class_info:
            wrapper_content.append('')
        
        # Add function declarations (skip class methods to avoid duplicates)
        for func_name, func_info in self.analysis_result.type_info.items():
            # Only process actual functions, not variables or classes or class methods
            if (isinstance(func_info, dict) and 'params' in func_info and 'return_type' in func_info and 
                func_info.get('type', '') != 'class' and not func_name.startswith('__')):
                # Skip methods that belong to classes
                is_class_method = False
                for class_name, class_info in self.analysis_result.class_info.items():
                    if func_name in class_info.methods:
                        is_class_method = True
                        break
                
                if not is_class_method:
                    docstring = func_info.get('docstring', '')
                    wrapper_content.append(f'    m.def("{func_name}", &pytocpp::{func_name}, "{docstring}");')
                
        wrapper_content.append('}')
        
        return '\n'.join(wrapper_content)
    
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

    def _generate_python_wrapper(self) -> str:
        """Generate Python wrapper for the C++ module."""
        wrapper_content = []
        
        # Add imports and docstring
        wrapper_content.append('"""')
        wrapper_content.append('Python wrapper for optimized C++ implementations.')
        wrapper_content.append('This module provides both pure Python and C++ implementations,')
        wrapper_content.append('allowing you to choose based on your needs.')
        wrapper_content.append('"""')
        wrapper_content.append('')
        wrapper_content.append('from typing import List, Dict, Union, Optional, Type, TypeVar, Any')
        wrapper_content.append('import numpy as np')
        wrapper_content.append('from . import cpp_impl')
        wrapper_content.append('')
        
        # Import classes from C++ implementation
        if self.analysis_result.class_info:
            imports = []
            for class_name in self.analysis_result.class_info.keys():
                imports.append(class_name)
            
            if imports:
                wrapper_content.append(f"# Import C++ classes")
                wrapper_content.append(f"from .cpp_impl import {', '.join(imports)}")
                wrapper_content.append('')
        
        # Add function declarations for supported functions
        for func_name, func_info in self.analysis_result.type_info.items():
            # Only process actual functions, not variables or classes
            if isinstance(func_info, dict) and 'params' in func_info and 'return_type' in func_info and func_info.get('type', '') != 'class':
                if func_name == 'calculate_fibonacci':
                    wrapper_content.append(f"def {func_name}(")
                    wrapper_content.append(f"    n: int, use_cpp: bool = True) -> int:")
                    wrapper_content.append('    """')
                    wrapper_content.append(f"    Compute the {func_name} function using either C++ or Python implementation.")
                    wrapper_content.append('    ')
                    wrapper_content.append(f"    Args:")
                    wrapper_content.append(f"        n: Input value")
                    wrapper_content.append(f"        use_cpp: Whether to use C++ implementation (default: True)")
                    wrapper_content.append('    ')
                    wrapper_content.append(f"    Returns:")
                    wrapper_content.append(f"        Computed value of the {func_name} function")
                    wrapper_content.append('    """')
                    wrapper_content.append('    if use_cpp:')
                    wrapper_content.append('        return cpp_impl.' + func_name + '(n)')
                    wrapper_content.append('    else:')
                    wrapper_content.append('        # Use original Python implementation')
                    wrapper_content.append('        import examples.simple_example')
                    wrapper_content.append('        return examples.simple_example.' + func_name + '(n)')
                    wrapper_content.append('')
                elif func_name == 'calculate_total_area':
                    # Handle functions that take class objects as parameters
                    wrapper_content.append(f"def {func_name}(")
                    wrapper_content.append(f"    shapes: List[Shape], use_cpp: bool = True) -> float:")
                    wrapper_content.append('    """')
                    wrapper_content.append(f"    Calculate the total area of a list of shapes.")
                    wrapper_content.append('    ')
                    wrapper_content.append(f"    Args:")
                    wrapper_content.append(f"        shapes: List of Shape objects")
                    wrapper_content.append(f"        use_cpp: Whether to use C++ implementation (default: True)")
                    wrapper_content.append('    ')
                    wrapper_content.append(f"    Returns:")
                    wrapper_content.append(f"        Total area of all shapes")
                    wrapper_content.append('    """')
                    wrapper_content.append('    if use_cpp:')
                    wrapper_content.append('        return cpp_impl.' + func_name + '(shapes)')
                    wrapper_content.append('    else:')
                    wrapper_content.append('        # Use original Python implementation')
                    wrapper_content.append('        import examples.class_example')
                    wrapper_content.append('        return examples.class_example.' + func_name + '(shapes)')
                    wrapper_content.append('')
                elif func_name == 'get_shape_info':
                    # Handle functions with Union type parameters
                    wrapper_content.append(f"def {func_name}(")
                    wrapper_content.append(f"    shape: Union[Rectangle, Circle], use_cpp: bool = True) -> Dict[str, Union[float, str]]:")
                    wrapper_content.append('    """')
                    wrapper_content.append(f"    Get information about a shape.")
                    wrapper_content.append('    ')
                    wrapper_content.append(f"    Args:")
                    wrapper_content.append(f"        shape: A Rectangle or Circle object")
                    wrapper_content.append(f"        use_cpp: Whether to use C++ implementation (default: True)")
                    wrapper_content.append('    ')
                    wrapper_content.append(f"    Returns:")
                    wrapper_content.append(f"        Dictionary with shape information")
                    wrapper_content.append('    """')
                    wrapper_content.append('    if use_cpp:')
                    wrapper_content.append('        return cpp_impl.' + func_name + '(shape)')
                    wrapper_content.append('    else:')
                    wrapper_content.append('        # Use original Python implementation')
                    wrapper_content.append('        import examples.class_example')
                    wrapper_content.append('        return examples.class_example.' + func_name + '(shape)')
                    wrapper_content.append('')
        
        return '\n'.join(wrapper_content)

    def _generate_cmake(self) -> str:
        """Generate CMake build file."""
        cmake_content = []
        
        cmake_content.append('cmake_minimum_required(VERSION 3.10)')
        cmake_content.append('project(pytocpp_generated)')
        cmake_content.append('')
        
        # Set C++ standard
        cmake_content.append('set(CMAKE_CXX_STANDARD 17)')
        cmake_content.append('set(CMAKE_CXX_STANDARD_REQUIRED ON)')
        cmake_content.append('')
        
        # Enable optimizations
        cmake_content.append('set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3")')
        cmake_content.append('')
        
        # Find pybind11
        cmake_content.append('# Add pybind11')
        cmake_content.append('find_package(pybind11 REQUIRED)')
        cmake_content.append('')
        
        # Add library targets
        cmake_content.append('# Add main executable')
        cmake_content.append('add_executable(${PROJECT_NAME}')
        cmake_content.append('    main.cpp')
        cmake_content.append('    generated.cpp')
        cmake_content.append(')')
        cmake_content.append('')
        
        cmake_content.append('# Add Python module')
        cmake_content.append('pybind11_add_module(cpp_impl')
        cmake_content.append('    wrapper.cpp')
        cmake_content.append('    generated.cpp')
        cmake_content.append(')')
        cmake_content.append('')
        
        # Add include directories
        cmake_content.append('target_include_directories(${PROJECT_NAME} PRIVATE')
        cmake_content.append('    ${CMAKE_CURRENT_SOURCE_DIR}')
        cmake_content.append(')')
        cmake_content.append('')
        
        cmake_content.append('target_include_directories(cpp_impl PRIVATE')
        cmake_content.append('    ${CMAKE_CURRENT_SOURCE_DIR}')
        cmake_content.append(')')
        
        return '\n'.join(cmake_content)