"""
Python wrapper for optimized C++ implementations.
This module provides both pure Python and C++ implementations,
allowing you to choose based on your needs.
"""

from typing import List, Dict, Union, Optional, Type, TypeVar, Any
import numpy as np
from . import cpp_impl

def calculate_fibonacci(
    n: int, use_cpp: bool = True) -> int:
    """
    Compute the calculate_fibonacci function using either C++ or Python implementation.
    
    Args:
        n: Input value
        use_cpp: Whether to use C++ implementation (default: True)
    
    Returns:
        Computed value of the calculate_fibonacci function
    """
    if use_cpp:
        return cpp_impl.calculate_fibonacci(n)
    else:
        # Use original Python implementation
        import examples.simple_example
        return examples.simple_example.calculate_fibonacci(n)
