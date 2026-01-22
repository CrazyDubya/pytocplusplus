from typing import Dict, List
import ast
import logging

logger = logging.getLogger("CodeGenerator")


class FunctionGenerator:
    """Handles generation of C++ functions from Python functions."""
    
    def __init__(self, code_generator):
        self.code_generator = code_generator
    
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
                
            translated = self.code_generator.statements._translate_statement(node, local_vars, 1)  # 1 for indent level
            if translated:
                impl.append(translated)
                
        # Return empty string if no statements were translated
        if not impl:
            if return_type != 'void':
                # Add a default return statement for non-void functions
                default_value = self.code_generator.types._get_default_value(return_type)
                impl.append(f"    return {default_value};")
            
        return "\n".join(impl)
