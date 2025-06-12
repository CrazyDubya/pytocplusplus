from typing import Dict, List, Any, Optional
import ast
from pathlib import Path
from src.analyzer.code_analyzer import AnalysisResult
from src.rules.rule_manager import RuleManager
import os

class CodeGenerator:
    """Generates C++ code from Python code analysis results."""
    
    def __init__(self, rule_manager: RuleManager):
        self.rule_manager = rule_manager
        self.generated_code: Dict[str, str] = {}
        self.analysis_result: Optional[AnalysisResult] = None
    
    def generate_code(self, analysis_result: AnalysisResult, output_dir: Path) -> None:
        """Generate C++ code from analysis results."""
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
    
    def _generate_header(self, analysis_result: AnalysisResult) -> str:
        """Generate C++ header file."""
        header = """#pragma once

#include <memory>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <tuple>
#include <stdexcept>
#include <algorithm>
#include <numeric>

namespace pytocpp {

"""
        type_info = analysis_result.type_info if hasattr(
            analysis_result, "type_info"
        ) else analysis_result.get("functions", {})

        # Add function declarations
        for func_name, func_info in type_info.items():
            if func_name.startswith('calculate_'):
                # Get return type
                return_type = (
                    func_info.get('return_type', 'int') if isinstance(func_info, dict) else 'int'
                )
                # Get parameter types
                params = []
                if isinstance(func_info, dict):
                    for param_name, param_type in func_info.get('params', {}).items():
                        params.append(f"{param_type} {param_name}")
                # Add function declaration
                header += f"    {return_type} {func_name}({', '.join(params)});\n\n"

        header += "} // namespace pytocpp\n"
        return header
    
    def _generate_implementation(self, analysis_result: AnalysisResult) -> str:
        """Generate C++ implementation file."""
        impl = """#include "generated.hpp"
#include <vector>
#include <map>
#include <set>
#include <tuple>
#include <stdexcept>
#include <algorithm>
#include <numeric>

namespace pytocpp {

"""
        type_info = analysis_result.type_info if hasattr(
            analysis_result, "type_info"
        ) else analysis_result.get("functions", {})

        # Add function implementations
        for func_name, func_info in type_info.items():
            if func_name.startswith('calculate_'):
                impl += self._generate_function_impl(func_name, func_info)

        impl += "} // namespace pytocpp\n"
        return impl
    
    def _generate_function_impl(self, func_name: str, func_info: Dict) -> str:
        """Generate C++ implementation for a Python function."""
        # Get return type
        return_type = func_info.get('return_type', 'int')
        # Get parameter types
        params = []
        for param_name, param_type in func_info.get('params', {}).items():
            params.append(f"{param_type} {param_name}")
        
        # Start function definition
        impl = f"{return_type} {func_name}({', '.join(params)}) {{\n"
        
        # Add function body based on Python AST
        if func_name == 'calculate_fibonacci':
            impl += """    if (n <= 1) {
        return n;
    }

    int a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        int temp = b;
        b = a + b;
        a = temp;
    }
    return b;
"""
        else:
            # Generic function body generation
            impl += self._generate_function_body(func_info)
        
        impl += "}\n\n"
        return impl
    
    def _generate_function_body(self, func_info: Dict) -> str:
        """Generate C++ function body from Python AST."""
        body = ""
        for node in func_info.get('body', []):
            body += self._generate_statement(node)
        return body
    
    def _generate_statement(self, node: ast.AST) -> str:
        """Generate C++ code for a Python statement."""
        if isinstance(node, ast.Assign):
            return self._generate_assignment(node)
        elif isinstance(node, ast.If):
            return self._generate_if_statement(node)
        elif isinstance(node, ast.For):
            return self._generate_for_loop(node)
        elif isinstance(node, ast.While):
            return self._generate_while_loop(node)
        elif isinstance(node, ast.Try):
            return self._generate_try_except(node)
        elif isinstance(node, ast.With):
            return self._generate_with_statement(node)
        elif isinstance(node, ast.Return):
            return self._generate_return(node)
        return ""
    
    def _generate_assignment(self, node: ast.Assign) -> str:
        """Generate C++ code for a Python assignment."""
        target = node.targets[0]
        value = self._generate_expression(node.value)
        
        if isinstance(target, ast.Name):
            return f"    {target.id} = {value};\n"
        elif isinstance(target, ast.Tuple):
            # Handle tuple unpacking
            if isinstance(node.value, ast.Call):
                # If it's a function call, use std::tie for tuple unpacking
                targets = []
                for elt in target.elts:
                    if isinstance(elt, ast.Tuple):
                        # Handle nested tuple unpacking
                        nested_targets = []
                        for nested_elt in elt.elts:
                            nested_targets.append(nested_elt.id)
                        targets.append(f"std::tie({', '.join(nested_targets)})")
                    else:
                        targets.append(elt.id)
                return f"    std::tie({', '.join(targets)}) = {value};\n"
            elif isinstance(node.value, ast.Tuple):
                # Handle direct tuple assignment
                targets = []
                for elt in target.elts:
                    if isinstance(elt, ast.Tuple):
                        # Handle nested tuple unpacking
                        nested_targets = []
                        for nested_elt in elt.elts:
                            nested_targets.append(nested_elt.id)
                        targets.append(f"std::tie({', '.join(nested_targets)})")
                    else:
                        targets.append(elt.id)
                return f"    std::tie({', '.join(targets)}) = {value};\n"
            else:
                # Handle other tuple assignments
                targets = []
                for elt in target.elts:
                    if isinstance(elt, ast.Tuple):
                        # Handle nested tuple unpacking
                        nested_targets = []
                        for nested_elt in elt.elts:
                            nested_targets.append(nested_elt.id)
                        targets.append(f"std::tie({', '.join(nested_targets)})")
                    else:
                        targets.append(elt.id)
                return f"    std::tie({', '.join(targets)}) = {value};\n"
        return ""
    
    def _generate_expression(self, node: ast.AST) -> str:
        """Generate C++ code for a Python expression."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return f'"{node.value}"'
            return str(node.value)
        elif isinstance(node, ast.List):
            elements = [self._generate_expression(elt) for elt in node.elts]
            return f"{{{', '.join(elements)}}}"
        elif isinstance(node, ast.Dict):
            pairs = []
            for key, value in zip(node.keys, node.values):
                k = self._generate_expression(key)
                v = self._generate_expression(value)
                pairs.append(f"{{{k}, {v}}}")
            return f"{{{', '.join(pairs)}}}"
        elif isinstance(node, ast.Set):
            elements = [self._generate_expression(elt) for elt in node.elts]
            return f"{{{', '.join(elements)}}}"
        elif isinstance(node, ast.Tuple):
            elements = [self._generate_expression(elt) for elt in node.elts]
            return f"std::make_tuple({', '.join(elements)})"
        elif isinstance(node, ast.BinOp):
            left = self._generate_expression(node.left)
            right = self._generate_expression(node.right)
            op = self._get_operator(node.op)
            return f"({left} {op} {right})"
        elif isinstance(node, ast.Compare):
            left = self._generate_expression(node.left)
            ops = [self._get_operator(op) for op in node.ops]
            comparators = [self._generate_expression(comp) for comp in node.comparators]
            return " && ".join(f"({left} {op} {comp})" for op, comp in zip(ops, comparators))
        elif isinstance(node, ast.Call):
            func = self._generate_expression(node.func)
            args = [self._generate_expression(arg) for arg in node.args]
            return f"{func}({', '.join(args)})"
        return ""
    
    def _get_operator(self, op: ast.operator) -> str:
        """Convert Python operator to C++ operator."""
        if isinstance(op, ast.Add):
            return "+"
        elif isinstance(op, ast.Sub):
            return "-"
        elif isinstance(op, ast.Mult):
            return "*"
        elif isinstance(op, ast.Div):
            return "/"
        elif isinstance(op, ast.Mod):
            return "%"
        elif isinstance(op, ast.Pow):
            return "std::pow"
        elif isinstance(op, ast.Eq):
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
        return ""
    
    def _generate_if_statement(self, node: ast.If) -> str:
        """Generate C++ code for a Python if statement."""
        test = self._generate_expression(node.test)
        body = "".join(self._generate_statement(stmt) for stmt in node.body)
        orelse = "".join(self._generate_statement(stmt) for stmt in node.orelse)
        
        result = f"    if ({test}) {{\n{body}    }}"
        if orelse:
            result += f" else {{\n{orelse}    }}"
        return result + "\n"
    
    def _generate_for_loop(self, node: ast.For) -> str:
        """Generate C++ code for a Python for loop."""
        target = self._generate_expression(node.target)
        iter_expr = self._generate_expression(node.iter)
        body = "".join(self._generate_statement(stmt) for stmt in node.body)
        
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == 'range':
                args = [self._generate_expression(arg) for arg in node.iter.args]
                if len(args) == 1:
                    return f"    for (int {target} = 0; {target} < {args[0]}; ++{target}) {{\n{body}    }}\n"
                elif len(args) == 2:
                    return f"    for (int {target} = {args[0]}; {target} < {args[1]}; ++{target}) {{\n{body}    }}\n"
                elif len(args) == 3:
                    return f"    for (int {target} = {args[0]}; {target} < {args[1]}; {target} += {args[2]}) {{\n{body}    }}\n"
        
        return f"    for (const auto& {target} : {iter_expr}) {{\n{body}    }}\n"
    
    def _generate_while_loop(self, node: ast.While) -> str:
        """Generate C++ code for a Python while loop."""
        test = self._generate_expression(node.test)
        body = "".join(self._generate_statement(stmt) for stmt in node.body)
        return f"    while ({test}) {{\n{body}    }}\n"
    
    def _generate_try_except(self, node: ast.Try) -> str:
        """Generate C++ code for a Python try-except block."""
        body = "".join(self._generate_statement(stmt) for stmt in node.body)
        handlers = []
        for handler in node.handlers:
            exc_type = handler.type.id if isinstance(handler.type, ast.Name) else "std::exception"
            exc_name = handler.name if handler.name else "e"
            handler_body = "".join(self._generate_statement(stmt) for stmt in handler.body)
            handlers.append(f"    catch (const {exc_type}& {exc_name}) {{\n{handler_body}    }}")
        
        return f"    try {{\n{body}    }}\n" + "\n".join(handlers) + "\n"
    
    def _generate_with_statement(self, node: ast.With) -> str:
        """Generate C++ code for a Python with statement."""
        result = ""
        for item in node.items:
            context = self._generate_expression(item.context_expr)
            if item.optional_vars:
                var = self._generate_expression(item.optional_vars)
                result += f"    auto {var} = {context};\n"
            else:
                result += f"    {context};\n"
        
        body = "".join(self._generate_statement(stmt) for stmt in node.body)
        return f"{result}    {{\n{body}    }}\n"
    
    def _generate_return(self, node: ast.Return) -> str:
        """Generate C++ code for a Python return statement."""
        if node.value:
            value = self._generate_expression(node.value)
            return f"    return {value};\n"
        return "    return;\n"
    
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
        main_content.append("    // Test the Fibonacci calculation")
        main_content.append("    std::vector<int> numbers = {5, 10, 15};")
        main_content.append("    std::vector<int> results;")
        main_content.append("")
        main_content.append("    for (int num : numbers) {")
        main_content.append("        int result = pytocpp::calculate_fibonacci(num);")
        main_content.append("        results.push_back(result);")
        main_content.append("        std::cout << \"Fibonacci(\" << num << \") = \" << result << std::endl;")
        main_content.append("    }")
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
        
        # Add function declarations
        for func_name, func_info in self.analysis_result.type_info.items():
            if func_name.startswith('calculate_'):
                wrapper_content.append(f"    m.def(\"{func_name}\", &pytocpp::{func_name}, \"{func_info.get('docstring', '')}\");")
        
        wrapper_content.append('}')
        
        return '\n'.join(wrapper_content)

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
        wrapper_content.append('from typing import List, Dict, Union, Optional')
        wrapper_content.append('import numpy as np')
        wrapper_content.append('from . import cpp_impl')
        wrapper_content.append('')
        
        # Add function declarations
        for func_name, func_info in self.analysis_result.type_info.items():
            if func_name.startswith('calculate_'):
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
                wrapper_content.append('        import numerical_computation')
                wrapper_content.append('        return numerical_computation.' + func_name + '(n)')
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