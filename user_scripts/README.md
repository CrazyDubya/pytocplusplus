# User Scripts Directory

This directory is for your Python scripts that you want to convert to C++. 

## How to Use

1. Place your Python scripts in this directory
2. Run the conversion tool:
   ```bash
   python src/main.py user_scripts/your_script.py --output-dir generated/your_script
   ```

## Requirements for Your Scripts

For best results, your Python scripts should:

1. Use type hints (e.g., `def function(x: int) -> str:`)
2. Have clear function and variable names
3. Avoid complex Python-specific features that don't map well to C++
4. Include docstrings for functions and classes

## What Gets Generated

For each script, the tool will generate:

1. A C++ header file (`generated.hpp`)
2. A C++ implementation file (`generated.cpp`)
3. A CMake build file (`CMakeLists.txt`)

## Building the Generated Code

After conversion, you can build the C++ code:

```bash
cd generated/your_script
mkdir build
cd build
cmake ..
make
```

## Example

See the `examples/test_data` directory for sample scripts that demonstrate the conversion capabilities. 