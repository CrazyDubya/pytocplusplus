from typing import Dict, List
import logging
from src.analyzer.code_analyzer import AnalysisResult, ClassInfo

logger = logging.getLogger("CodeGenerator")


class OutputGenerator:
    """Generates output files (headers, implementations, wrappers, etc.) from code generation results."""
    
    def __init__(self, code_generator):
        """Initialize the output generator with a reference to the main code generator.
        
        Args:
            code_generator: Reference to the main CodeGenerator instance
        """
        self.code_generator = code_generator
    
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
            header += self.code_generator._generate_class_declaration(class_name, class_info)
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
                    # Clean up function name (remove "function_" prefix if present)
                    clean_func_name = func_name.replace('function_', '') if func_name.startswith('function_') else func_name
                    
                    # Get return type
                    return_type = func_info.get('return_type', 'int')
                    
                    # Get parameter types
                    params = []
                    for param_name, param_type in func_info.get('params', {}).items():
                        params.append(f"{param_type} {param_name}")
                    
                    # Add function declaration
                    header += f"    {return_type} {clean_func_name}({', '.join(params)});\n\n"

        header += "} // namespace pytocpp\n"
        return header
    
    def _generate_implementation(self, analysis_result: AnalysisResult) -> str:
        """Generate C++ implementation file."""
        impl = """#include "generated.hpp"
#include <vector>
#include <map>
#include <unordered_map>
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
            impl += self.code_generator._generate_class_implementation(class_name, class_info, analysis_result)
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
                    # Clean up function name (remove "function_" prefix if present)
                    clean_func_name = func_name.replace('function_', '') if func_name.startswith('function_') else func_name
                    impl += self.code_generator._generate_function_impl(clean_func_name, func_info)

        impl += "} // namespace pytocpp\n"
        return impl
    
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
        for func_name, func_info in self.code_generator.analysis_result.type_info.items():
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
        for class_name, class_info in self.code_generator.analysis_result.class_info.items():
            wrapper_content.extend(self.code_generator._generate_class_binding(class_name, class_info))
        
        if self.code_generator.analysis_result.class_info:
            wrapper_content.append('')
        
        # Add function declarations (skip class methods to avoid duplicates)
        for func_name, func_info in self.code_generator.analysis_result.type_info.items():
            # Only process actual functions, not variables or classes or class methods
            if (isinstance(func_info, dict) and 'params' in func_info and 'return_type' in func_info and 
                func_info.get('type', '') != 'class' and not func_name.startswith('__')):
                # Skip methods that belong to classes
                is_class_method = False
                for class_name, class_info in self.code_generator.analysis_result.class_info.items():
                    if func_name in class_info.methods:
                        is_class_method = True
                        break
                
                if not is_class_method:
                    docstring = func_info.get('docstring', '')
                    wrapper_content.append(f'    m.def("{func_name}", &pytocpp::{func_name}, "{docstring}");')
                
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
        wrapper_content.append('from typing import List, Dict, Union, Optional, Type, TypeVar, Any')
        wrapper_content.append('import numpy as np')
        wrapper_content.append('from . import cpp_impl')
        wrapper_content.append('')
        
        # Import classes from C++ implementation
        if self.code_generator.analysis_result.class_info:
            imports = []
            for class_name in self.code_generator.analysis_result.class_info.keys():
                imports.append(class_name)
            
            if imports:
                wrapper_content.append(f"# Import C++ classes")
                wrapper_content.append(f"from .cpp_impl import {', '.join(imports)}")
                wrapper_content.append('')
        
        # Add function declarations for supported functions
        for func_name, func_info in self.code_generator.analysis_result.type_info.items():
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
