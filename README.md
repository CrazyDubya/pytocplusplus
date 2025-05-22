# PyToC++

A tool for analyzing Python code and converting it to optimized C++ code.

## Current Status

PyToC++ has reached several major milestones and now supports complex Python constructs:
- ✓ Core analyzer functionality works for basic Python constructs
- ✓ Simple Python functions can be converted to working C++ code
- ✓ Type inference for basic Python types is implemented
- ✓ End-to-end conversion pipeline is functional
- ✓ Generic function body translation implemented
- ✓ Benchmarking system working with performance comparison
- ✓ **Class and inheritance support**: Full Python class translation with proper C++ inheritance
- ✓ **Union type support**: Python Union types converted to std::variant with visitor pattern
- ✓ **Advanced f-string handling**: Proper mixed string/numeric concatenation using std::to_string
- ✓ **Python-C++ interoperability**: Working pybind11 bindings for seamless integration

## Features

- Python code analysis
- Performance bottleneck detection
- Type inference
- Memory usage analysis
- Automatic C++ code generation
- Build system generation

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Conversion

To convert a Python file to C++:

```bash
# For simple functions
python -m src.main examples/simple_example.py --output-dir generated

# For complex classes with inheritance and Union types
python -m src.main examples/class_example.py --output-dir generated
```

This will:
1. Analyze the Python code
2. Infer types for variables and functions
3. Detect performance bottlenecks
4. Generate optimized C++ code
5. Create a CMake build system

### Output Structure

The conversion process generates:
- `generated.hpp` - Header with function declarations
- `generated.cpp` - Implementation file with C++ code
- `main.cpp` - Example program using the generated code
- `CMakeLists.txt` - Build configuration file
- `wrapper.cpp` - Python binding using pybind11
- `python_wrapper/` - Python module calling the C++ implementation

### Building and Running Generated Code

```bash
cd generated
mkdir build && cd build
cmake ..
make
./pytocpp_generated
```

### Benchmarking

PyToC++ includes benchmarking to compare the performance of Python and C++ implementations:

```bash
python -m src.main examples/simple_example.py --output-dir generated
```

This will automatically:
1. Generate C++ code
2. Build the C++ implementation
3. Run benchmarks comparing Python and C++ versions
4. Report performance results with speedup ratios

Example output:
```
Benchmark Results (time per call in microseconds):
----------------------------------------------------------------------
n        Python (μs)     C++ (μs)        Ratio      Speedup   
----------------------------------------------------------------------
5        0.125        0.186        0.67x      
10       0.215        0.164        1.31x      
15       0.309        0.162        1.91x      
20       0.385        0.164        2.34x      
25       0.488        0.167        2.92x      
30       0.599        0.165        3.63x      
35       0.683        0.154        4.42x
```

This shows that the C++ implementation becomes 4.42x faster than Python for larger inputs.

### Class Example Output

When converting `examples/class_example.py` (which includes Shape, Rectangle, and Circle classes with inheritance), the generated C++ application produces:

```
Total area of all shapes: 55.7743
Shape info: [area=20, description=A blue rectangle with width 5.000000 and height 4.000000]
Shape info: [area=28.2743, description=A red circle with radius 3.000000]
Shape info: [area=7.5, description=A green rectangle with width 2.500000 and height 3.000000]
Optional shape area: 1
```

This demonstrates successful translation of:
- Class inheritance (Shape -> Rectangle, Circle)
- Method overriding (area(), describe())
- Union types (std::variant<Rectangle, Circle>)
- F-string formatting with numeric-to-string conversion
- Optional types (std::optional)

## Project Structure

```
pytocplusplus/
├── src/
│   ├── analyzer/           # Python code analysis components
│   │   ├── code_analyzer.py     # Original analyzer with bug
│   │   └── code_analyzer_fixed.py  # Fixed implementation
│   ├── converter/          # C++ conversion components
│   │   ├── code_generator.py    # Original generator
│   │   └── code_generator_fixed.py  # Fixed implementation
│   ├── rules/             # Conversion rules and patterns
│   └── utils/             # Utility functions
├── tests/                 # Test cases
├── examples/             # Example Python code and their C++ conversions
├── docs/                 # Documentation
└── requirements.txt      # Python dependencies
```

## Supported Python Features

Currently, PyToC++ effectively handles:
- Basic variable assignments
- Function definitions with type annotations
- Simple control flow (if/else statements)
- Loop translation (for/while loops)
- Tuple unpacking in assignments
- List operations (creation, append)
- Container operations
- Advanced f-string formatting with mixed types
- Basic numeric operations
- Return statements
- **Class definitions and methods** with inheritance
- **Union types** using std::variant
- **Optional types** using std::optional
- **Method overriding** and polymorphism
- **Constructor translation** with proper initialization

More complex features are under development, including:
- Exception handling
- Standard library mapping
- Container comprehensions
- Generic type support
- Protocol/interface translation

## Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: 
   ```
   pytest tests/test_code_analyzer_fixed.py
   pytest tests/test_conversion_fixed.py
   ```

### Contributing

Contributions are welcome! Check the roadmap and enhancement sprint plan in the docs directory to see current priorities.

**Recent Major Contributions Completed:**
- ✅ Class and inheritance support (Sprint 2)
- ✅ Union type support with std::variant (Sprint 2) 
- ✅ Advanced f-string handling (Sprint 2)
- ✅ Python-C++ interoperability via pybind11 (Sprint 2)

**Next Priority Areas:**
- Exception handling translation
- Generic type support 
- Container comprehensions
- Standard library mapping

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.