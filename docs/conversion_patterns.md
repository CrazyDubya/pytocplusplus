# Python to C++ Conversion Patterns

This document outlines the standard patterns for converting Python constructs to idiomatic C++ equivalents. These patterns will guide the implementation of the code generator to ensure consistent, maintainable, and optimized C++ output.

## Basic Types

| Python | C++ | Notes |
|--------|-----|-------|
| `int` | `int` | Use `int64_t` for guaranteed 64-bit size |
| `float` | `double` | Python's float is double-precision |
| `str` | `std::string` | Use `std::string_view` for read-only references |
| `bool` | `bool` | Direct mapping |
| `None` | `nullptr`, `std::nullopt`, `std::optional<T>()` | Context-dependent |
| `bytes` | `std::vector<uint8_t>` | For binary data |

## Container Types

| Python | C++ | Notes |
|--------|-----|-------|
| `list[T]` | `std::vector<T>` | Most common mapping |
| `tuple[T1, T2, ...]` | `std::tuple<T1, T2, ...>` | Fixed-size heterogeneous |
| `dict[K, V]` | `std::unordered_map<K, V>` | For general dictionaries |
| `dict[K, V]` | `std::map<K, V>` | When ordering matters |
| `set[T]` | `std::unordered_set<T>` | For general sets |
| `set[T]` | `std::set<T>` | When ordering matters |
| `frozenset[T]` | `const std::set<T>` | Immutable set |

## Complex Types

| Python | Notes | C++ | Notes |
|--------|-------|-----|-------|
| `Union[T1, T2]` | Type could be T1 or T2 | `std::variant<T1, T2>` | Tagged union |
| `Optional[T]` | Value or None | `std::optional<T>` | Nullable type |
| `Callable[[Args], R]` | Function type | `std::function<R(Args...)>` | Function object |
| `Any` | Any type | `std::any` | Type-erased container |
| `TypeVar` | Generic type | Templates | Use template parameters |

## Control Flow

### Conditionals

```python
# Python
if condition:
    statement1
elif other_condition:
    statement2
else:
    statement3
```

```cpp
// C++
if (condition) {
    statement1;
} else if (other_condition) {
    statement2;
} else {
    statement3;
}
```

### Loops

```python
# Python - for with range
for i in range(start, end, step):
    body
```

```cpp
// C++
for (int i = start; i < end; i += step) {
    body;
}
```

```python
# Python - for over container
for item in container:
    body
```

```cpp
// C++
for (const auto& item : container) {
    body;
}
```

```python
# Python - while loop
while condition:
    body
```

```cpp
// C++
while (condition) {
    body;
}
```

### Exceptions

```python
# Python
try:
    risky_operation()
except SpecificError as e:
    handle_specific(e)
except Exception as e:
    handle_generic(e)
finally:
    cleanup()
```

```cpp
// C++
try {
    risky_operation();
} catch (const SpecificError& e) {
    handle_specific(e);
} catch (const std::exception& e) {
    handle_generic(e);
} catch (...) {
    // Handle unknown exceptions
}
// Finally block becomes:
cleanup();
```

## Functions

### Basic Function

```python
# Python
def function_name(param1: type1, param2: type2 = default) -> return_type:
    """Docstring."""
    body
    return result
```

```cpp
// C++
/**
 * Docstring.
 */
return_type function_name(type1 param1, type2 param2 = default) {
    body;
    return result;
}
```

### Lambda Functions

```python
# Python
lambda x, y: x + y
```

```cpp
// C++
[](auto x, auto y) { return x + y; }
```

## Classes

### Basic Class

```python
# Python
class ClassName:
    def __init__(self, param1, param2):
        self.attribute1 = param1
        self.attribute2 = param2
        
    def method(self, param):
        return self.attribute1 + param
```

```cpp
// C++
class ClassName {
public:
    ClassName(Type1 param1, Type2 param2)
        : attribute1(param1), attribute2(param2) {}
        
    ReturnType method(ParamType param) {
        return attribute1 + param;
    }
    
private:
    Type1 attribute1;
    Type2 attribute2;
};
```

### Inheritance

```python
# Python
class Derived(Base):
    def __init__(self, param):
        super().__init__(param)
        self.derived_attr = param * 2
```

```cpp
// C++
class Derived : public Base {
public:
    Derived(Type param)
        : Base(param), derived_attr(param * 2) {}
        
private:
    Type derived_attr;
};
```

## Python Idioms

### List Comprehension

```python
# Python
result = [expr for item in iterable if condition]
```

```cpp
// C++
std::vector<ResultType> result;
for (const auto& item : iterable) {
    if (condition) {
        result.push_back(expr);
    }
}
```

### Dictionary Comprehension

```python
# Python
result = {key: value for item in iterable if condition}
```

```cpp
// C++
std::map<KeyType, ValueType> result;
for (const auto& item : iterable) {
    if (condition) {
        result[key] = value;
    }
}
```

### Generator Function

```python
# Python
def generate():
    for i in range(10):
        yield i
```

```cpp
// C++
class Generator {
public:
    Generator() : current(0) {}
    bool next() {
        if (current < 10) {
            current++;
            return true;
        }
        return false;
    }
    int value() const { return current - 1; }
    
private:
    int current;
};
```

### Context Managers

```python
# Python
with open("file.txt") as f:
    content = f.read()
```

```cpp
// C++
{
    std::ifstream f("file.txt");
    std::string content((std::istreambuf_iterator<char>(f)),
                          std::istreambuf_iterator<char>());
}
```

## Standard Library Mappings

| Python | C++ |
|--------|-----|
| `math.sqrt(x)` | `std::sqrt(x)` |
| `math.sin(x)` | `std::sin(x)` |
| `math.cos(x)` | `std::cos(x)` |
| `random.random()` | `std::uniform_real_distribution<double>(0.0, 1.0)(generator)` |
| `len(container)` | `container.size()` |
| `min(a, b)` | `std::min(a, b)` |
| `max(a, b)` | `std::max(a, b)` |
| `sorted(iterable)` | `std::sort(container.begin(), container.end())` |
| `sum(iterable)` | `std::accumulate(container.begin(), container.end(), 0)` |
| `list.append(item)` | `vector.push_back(item)` |
| `dict[key] = value` | `map[key] = value` |
| `key in dict` | `map.find(key) != map.end()` |

## Memory Management Patterns

### Resource Acquisition

```python
# Python - resources automatically cleaned up
resource = acquire_resource()
use_resource(resource)
# Resource released automatically
```

```cpp
// C++ - RAII pattern
{
    auto resource = std::unique_ptr<Resource>(acquire_resource());
    use_resource(resource.get());
}  // Resource released automatically by unique_ptr destructor
```

### Reference vs Value

```python
# Python - objects are references by default
def modify(obj):
    obj.attribute = new_value
```

```cpp
// C++ - explicit references required
void modify(Object& obj) {
    obj.attribute = new_value;
}
```

## Performance Patterns

### Loop Optimization

```python
# Python
result = []
for item in large_list:
    result.append(process(item))
```

```cpp
// C++
std::vector<ResultType> result;
result.reserve(large_list.size());  // Pre-allocate memory
for (const auto& item : large_list) {
    result.push_back(process(item));
}
```

### Parallel Processing

```python
# Python with concurrent.futures
with concurrent.futures.ThreadPoolExecutor() as executor:
    results = list(executor.map(process, items))
```

```cpp
// C++ with std::execution
#include <execution>
std::vector<ResultType> results(items.size());
std::transform(std::execution::par, items.begin(), items.end(),
               results.begin(), process);
```

## Implementation Notes

1. **Type Safety**: Always prioritize type safety in the generated C++ code.
2. **Resource Management**: Use RAII patterns to ensure proper resource cleanup.
3. **Optimization**: Look for optimization opportunities but maintain readability.
4. **Idiomatic Code**: Generate C++ code that follows C++ idioms, not just direct translations.
5. **Modern C++**: Use features from C++17/20 when appropriate for cleaner, more efficient code.
6. **Maintainability**: Add comments explaining non-obvious translations or optimizations.
7. **Error Handling**: Translate Python's exception patterns to C++ exception handling.