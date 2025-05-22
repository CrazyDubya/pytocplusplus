from typing import List, Dict, Any, Type
import ast
from .base_rule import ConversionRule

class RuleManager:
    """Manages the registration and application of conversion rules."""
    
    def __init__(self):
        self.rules: List[ConversionRule] = []
        self.context: Dict[str, Any] = {}
    
    def register_rule(self, rule: ConversionRule) -> None:
        """Register a new conversion rule."""
        self.rules.append(rule)
        # Sort rules by priority (higher priority first)
        self.rules.sort(key=lambda r: r.get_priority(), reverse=True)
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """Set the context for all rules."""
        self.context = context
        for rule in self.rules:
            rule.set_context(context)
    
    def get_matching_rule(self, node: ast.AST) -> ConversionRule:
        """Get the first rule that matches the given AST node."""
        for rule in self.rules:
            if rule.matches(node):
                return rule
        raise ValueError(f"No matching rule found for node type: {type(node)}")
    
    def convert_node(self, node: ast.AST) -> str:
        """Convert an AST node to C++ code using the appropriate rule."""
        rule = self.get_matching_rule(node)
        return rule.convert(node)
    
    def get_required_headers(self) -> List[str]:
        """Get all required C++ headers from registered rules."""
        headers = set()
        for rule in self.rules:
            headers.update(rule.get_required_headers())
        return sorted(list(headers))
    
    def get_required_libraries(self) -> List[str]:
        """Get all required C++ libraries from registered rules."""
        libraries = set()
        for rule in self.rules:
            libraries.update(rule.get_required_libraries())
        return sorted(list(libraries)) 