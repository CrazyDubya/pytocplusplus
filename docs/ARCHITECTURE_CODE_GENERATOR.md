# Code Generator Architecture

## Overview

The Code Generator module is responsible for converting Python code analysis results into equivalent C++ code, including headers, implementations, bindings, and build files.

## Modular Structure

The code generator has been refactored from a single 1,763-line file into a modular architecture with 7 specialized modules, each handling a specific aspect of code generation.

```
src/converter/code_generator/
├── __init__.py          # Module exports and backward compatibility
├── base.py              # Main CodeGenerator orchestration
├── types.py             # Type inference and conversion
├── expressions.py       # Expression translation
├── statements.py        # Statement translation  
├── functions.py         # Function code generation
├── classes.py           # Class code generation
└── output.py            # Output file generation
```

## Module Responsibilities

### base.py - Core Orchestration
**Class:** `CodeGenerator`

Main entry point that orchestrates the entire code generation process.

**Key Methods:**
- `generate_code(analysis_result, output_dir)` - Main workflow coordinator
- Delegation methods for backward compatibility

**Responsibilities:**
- Initializes all submodules
- Coordinates the generation workflow
- Manages generated code storage
- Handles file I/O operations
- Provides backward-compatible API

### types.py - Type System
**Class:** `TypeHandler`

Handles C++ type inference from Python AST nodes and type conversions.

**Key Methods:**
- `_infer_cpp_type(node, local_vars)` - Infers C++ type from Python expression
- `_get_default_value(type_str)` - Returns default value for C++ type

**Responsibilities:**
- Python to C++ type mapping
- Type inference from literals and expressions
- Default value generation
- Container type handling (vector, map, set, tuple)

### expressions.py - Expression Translation
**Class:** `ExpressionTranslator`

Translates Python expressions to C++ equivalents.

**Key Methods:**
- `_translate_expression(node, local_vars)` - Main expression translator
- `_translate_operator(op)` - Binary operator translation
- `_translate_unary_operator(op)` - Unary operator translation
- `_translate_compare_operator(op)` - Comparison operator translation
- `_translate_list_comprehension(node, local_vars)` - List comprehension translation
- `_translate_dict_comprehension(node, local_vars)` - Dictionary comprehension translation
- `_expression_uses_variables(expr, variable_names)` - Variable usage analysis

**Responsibilities:**
- Name, constant, and literal translation
- Operator translation
- Function call translation
- Attribute access translation
- Subscript operation translation
- Comprehension translation (with optimization)
- F-string translation

### statements.py - Statement Translation
**Class:** `StatementTranslator`

Translates Python control flow and statements to C++.

**Key Methods:**
- `_translate_statement(node, local_vars, indent_level)` - Main statement dispatcher
- `_translate_if_statement(node, local_vars, indent_level)` - If/elif/else translation
- `_translate_for_loop(node, local_vars, indent_level)` - For loop translation
- `_translate_while_loop(node, local_vars, indent_level)` - While loop translation
- `_translate_assignment(node, local_vars, indent_level)` - Assignment translation
- `_translate_return(node, local_vars, indent_level)` - Return statement translation

**Responsibilities:**
- Control flow translation (if, for, while)
- Assignment handling (including tuple unpacking)
- Return statement translation
- Variable declaration inference
- Range-based for loop conversion
- Iterator type inference

### functions.py - Function Generation
**Class:** `FunctionGenerator`

Generates C++ function implementations from Python functions.

**Key Methods:**
- `_generate_function_impl(func_name, func_info)` - Generate function implementation
- `_translate_function_body(body_nodes, param_types, return_type)` - Translate function body

**Responsibilities:**
- Function signature generation
- Parameter handling
- Return type handling
- Function body translation
- Special case handling (e.g., variant parameters)

### classes.py - Class Generation
**Class:** `ClassGenerator`

Generates C++ class declarations and implementations from Python classes.

**Key Methods:**
- `_generate_class_declaration(class_name, class_info)` - Generate class header
- `_generate_class_implementation(class_name, class_info, analysis_result)` - Generate class implementation
- `_generate_constructor_declaration(class_name, constructor_info)` - Generate constructor header
- `_generate_constructor_implementation(class_name, constructor_info, class_info)` - Generate constructor implementation
- `_generate_method_declaration(method_name, method_info)` - Generate method header
- `_generate_method_implementation(class_name, method_name, method_info, class_info)` - Generate method implementation
- `_translate_method_body(body_nodes, param_types, return_type, local_vars)` - Translate method body
- `_translate_method_statement(node, local_vars, indent_level)` - Translate method statement
- `_translate_method_assignment(node, local_vars, indent_level)` - Translate self.attr assignments
- `_translate_method_return(node, local_vars, indent_level)` - Translate method return
- `_translate_method_expression(node, local_vars)` - Translate method expressions (handles self.attr)
- `_generate_class_binding(class_name, class_info)` - Generate pybind11 binding

**Responsibilities:**
- Class declaration generation
- Constructor generation
- Method generation (public, protected, private)
- Inheritance handling
- Member variable management
- Self/this translation
- Pybind11 binding generation

### output.py - Output Generation
**Class:** `OutputGenerator`

Generates all output files needed for compilation and usage.

**Key Methods:**
- `_generate_header(analysis_result)` - Generate C++ header file (.hpp)
- `_generate_implementation(analysis_result)` - Generate C++ implementation file (.cpp)
- `_generate_main_cpp()` - Generate test main.cpp
- `_generate_pybind_wrapper()` - Generate pybind11 wrapper.cpp
- `_generate_python_wrapper()` - Generate Python wrapper module
- `_generate_cmake()` - Generate CMakeLists.txt build file

**Responsibilities:**
- Header file generation with includes and declarations
- Implementation file generation
- Test harness generation
- Python/C++ binding generation
- Build system configuration
- Python package setup

## Data Flow

```
┌─────────────────┐
│ AnalysisResult  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CodeGenerator  │ (base.py)
│  generate_code  │
└────────┬────────┘
         │
         ├──────────────────┬──────────────────┬──────────────────┐
         ▼                  ▼                  ▼                  ▼
   ┌──────────┐       ┌──────────┐      ┌──────────┐      ┌──────────┐
   │   types  │       │statements│      │functions │      │ classes  │
   │ (types.py)│      │ (.py)    │      │ (.py)    │      │ (.py)    │
   └──────────┘       └──────────┘      └──────────┘      └──────────┘
         │                  │                  │                  │
         └──────────────────┴──────────────────┴──────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ expressions  │
                    │ (.py)        │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    output    │
                    │   (.py)      │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Generated   │
                    │    Files     │
                    └──────────────┘
```

## Cross-Module Communication

Modules communicate through the main `CodeGenerator` instance:

```python
# In base.py
class CodeGenerator:
    def __init__(self, rule_manager):
        self.types = TypeHandler(self)
        self.expressions = ExpressionTranslator(self)
        self.statements = StatementTranslator(self)
        # ... other submodules
        
# In statements.py
class StatementTranslator:
    def __init__(self, code_generator):
        self.code_generator = code_generator
        
    def _translate_assignment(self, node, local_vars, indent_level):
        # Access other modules through code_generator
        value_expr = self.code_generator.expressions._translate_expression(node.value, local_vars)
        value_type = self.code_generator.types._infer_cpp_type(node.value, local_vars)
```

## Backward Compatibility

The refactored architecture maintains full backward compatibility:

```python
# Old usage (still works)
from src.converter.code_generator import CodeGenerator

generator = CodeGenerator(rule_manager)
generator.generate_code(analysis_result, output_dir)

# All original methods still accessible
header = generator._generate_header(analysis_result)
```

Delegation methods in `base.py` forward calls to appropriate submodules.

## Extension Points

To add new functionality:

1. **New Expression Type**: Add to `ExpressionTranslator._translate_expression()`
2. **New Statement Type**: Add to `StatementTranslator._translate_statement()`
3. **New Type Mapping**: Add to `TypeHandler._infer_cpp_type()`
4. **New Output Format**: Add method to `OutputGenerator`

## Testing Strategy

Each module can be tested independently:

```python
# Test type inference
type_handler = TypeHandler(mock_generator)
result = type_handler._infer_cpp_type(ast_node, local_vars)

# Test expression translation
expr_translator = ExpressionTranslator(mock_generator)
cpp_code = expr_translator._translate_expression(ast_node, local_vars)
```

## Performance Considerations

- **Lazy Evaluation**: Submodules are initialized once at CodeGenerator creation
- **In-Memory Processing**: All code generation happens in memory before file I/O
- **Single Pass**: Each AST node is processed exactly once
- **Optimizations**: List comprehensions use `reserve()` for vector preallocation

## Future Improvements

1. **Parallel Processing**: Generate independent classes in parallel
2. **Caching**: Cache type inference results for repeated expressions
3. **Plugin System**: Allow custom translation handlers
4. **Template System**: Use templates for output file generation
5. **Validation**: Add pre-generation validation of generated code

## Summary

The modular architecture provides:
- ✅ Clear separation of concerns
- ✅ Better testability and maintainability  
- ✅ Easier onboarding for new developers
- ✅ Full backward compatibility
- ✅ Foundation for future enhancements
