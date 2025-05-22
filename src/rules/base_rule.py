from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import ast

class ConversionRule(ABC):
    """Base class for all Python to C++ conversion rules."""
    
    def __init__(self, priority: int = 0):
        self.priority = priority
        self.context: Dict[str, Any] = {}
    
    @abstractmethod
    def matches(self, node: ast.AST) -> bool:
        """Check if this rule applies to the given AST node."""
        pass
    
    @abstractmethod
    def convert(self, node: ast.AST) -> str:
        """Convert the Python AST node to C++ code."""
        pass
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """Set the context for this rule."""
        self.context = context
    
    def get_priority(self) -> int:
        """Get the priority of this rule."""
        return self.priority
    
    def get_required_headers(self) -> List[str]:
        """Get the C++ headers required for this conversion."""
        return []
    
    def get_required_libraries(self) -> List[str]:
        """Get the C++ libraries required for this conversion."""
        return [] 