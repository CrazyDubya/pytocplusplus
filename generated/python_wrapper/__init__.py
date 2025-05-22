"""
Python wrapper for optimized C++ implementations.
This module provides both pure Python and C++ implementations,
allowing you to choose based on your needs.
"""

from typing import List, Dict, Union, Optional, Type, TypeVar, Any
import numpy as np
from . import cpp_impl

# Import C++ classes
from .cpp_impl import Shape, Rectangle, Circle

def calculate_total_area(
    shapes: List[Shape], use_cpp: bool = True) -> float:
    """
    Calculate the total area of a list of shapes.
    
    Args:
        shapes: List of Shape objects
        use_cpp: Whether to use C++ implementation (default: True)
    
    Returns:
        Total area of all shapes
    """
    if use_cpp:
        return cpp_impl.calculate_total_area(shapes)
    else:
        # Use original Python implementation
        import examples.class_example
        return examples.class_example.calculate_total_area(shapes)

def get_shape_info(
    shape: Union[Rectangle, Circle], use_cpp: bool = True) -> Dict[str, Union[float, str]]:
    """
    Get information about a shape.
    
    Args:
        shape: A Rectangle or Circle object
        use_cpp: Whether to use C++ implementation (default: True)
    
    Returns:
        Dictionary with shape information
    """
    if use_cpp:
        return cpp_impl.get_shape_info(shape)
    else:
        # Use original Python implementation
        import examples.class_example
        return examples.class_example.get_shape_info(shape)
