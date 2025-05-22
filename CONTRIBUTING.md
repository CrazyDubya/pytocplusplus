# Contributing to PyToC++

Thank you for your interest in contributing to PyToC++! This document provides guidelines for contributing to the project.

## Current Status

PyToC++ has recently completed major milestones:
- ✅ Class and inheritance support
- ✅ Union type support with std::variant
- ✅ Advanced f-string handling  
- ✅ Python-C++ interoperability via pybind11

## How to Contribute

### Reporting Issues

1. Check existing [issues](../../issues) to avoid duplicates
2. Use clear, descriptive titles
3. Include:
   - Python code that fails to convert
   - Expected C++ output
   - Actual output/error messages
   - Python and system version info

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/[username]/pytocplusplus.git
   cd pytocplusplus
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run tests**:
   ```bash
   pytest tests/
   ```

4. **Test with examples**:
   ```bash
   python -m src.main examples/class_example.py
   ```

### Priority Areas for Contribution

Based on our current roadmap, we're looking for help with:

#### High Priority
- **Exception handling translation**: Improve try/except C++ code generation
- **Generic type support**: Add template-based generic types
- **Container comprehensions**: List and dict comprehensions
- **Standard library mapping**: Python standard library to C++ equivalents

#### Medium Priority  
- **Regular expression translation**: Python regex to C++ regex
- **File I/O operations**: Python file operations to C++ equivalents
- **Advanced control flow**: match/case statements
- **Decorator support**: Basic decorator translation

#### Advanced Features
- **Generator functions**: Python generators to C++ equivalents
- **Context managers**: Resource management translation
- **Multiple inheritance**: Beyond current single inheritance support

### Code Style Guidelines

1. **Python Code**:
   - Follow PEP 8
   - Use type hints where appropriate
   - Add docstrings to all public functions/classes
   - Maximum line length: 88 characters (Black formatter)

2. **Generated C++ Code**:
   - Follow modern C++ best practices (C++17/20)
   - Use RAII patterns
   - Prefer `std::` containers over raw arrays
   - Use `const` correctness

3. **Testing**:
   - Add tests for new functionality
   - Include both unit tests and integration tests
   - Test with realistic Python examples
   - Verify generated C++ compiles and runs correctly

### Submitting Changes

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Add/update tests**
5. **Update documentation** if needed
6. **Run tests** to ensure everything works
7. **Commit with clear messages**:
   ```bash
   git commit -m "Add support for list comprehensions
   
   - Implement basic list comprehension translation
   - Add tests for simple comprehension cases
   - Update documentation with new feature"
   ```
8. **Push to your fork**
9. **Create a Pull Request**

### Pull Request Guidelines

- **Title**: Clear, descriptive summary
- **Description**: 
  - What changes were made
  - Why the changes were needed
  - How to test the changes
  - Any breaking changes
- **Testing**: Include test results
- **Documentation**: Update relevant docs

### Code Review Process

1. Automated tests must pass
2. Code review by maintainers
3. Documentation review if applicable
4. Final approval and merge

## Development Workflow

### Working with the Analyzer

The `CodeAnalyzer` (`src/analyzer/code_analyzer_fixed.py`) handles Python AST analysis:
- Add new node type handlers in `_visit_*` methods
- Update type inference in `_infer_type`
- Extend class analysis in `_analyze_class_definition`

### Working with the Generator  

The `CodeGenerator` (`src/converter/code_generator_fixed.py`) handles C++ generation:
- Add new statement translation in `_translate_statement`
- Extend expression handling in `_translate_expression`
- Add new C++ patterns in helper methods

### Testing Strategy

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test full conversion process
3. **Example Tests**: Verify realistic Python code conversion
4. **Performance Tests**: Ensure C++ code is actually faster

## Resources

- [Project Roadmap](docs/roadmap.md)
- [Implementation Gaps Report](docs/implementation_gaps_report.md)
- [Enhancement Sprint Plan](docs/enhancement_sprint_plan.md)

## Questions?

- Open an [issue](../../issues) for questions
- Check existing documentation in the `docs/` directory
- Look at `examples/` for usage patterns

## Recognition

Contributors will be acknowledged in:
- README.md contributor section
- Release notes for significant contributions
- Code comments for major features

Thank you for helping make PyToC++ better! 🚀