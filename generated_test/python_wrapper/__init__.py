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
