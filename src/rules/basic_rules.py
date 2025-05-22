from typing import Any, Dict, List
import ast
from .base_rule import ConversionRule

class VariableDeclarationRule(ConversionRule):
    """Rule for converting Python variable declarations to C++."""
    
    def __init__(self):
        super().__init__(priority=100)  # High priority for basic declarations
    
    def matches(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Assign)
    
    def convert(self, node: ast.Assign) -> str:
        if not isinstance(node, ast.Assign):
            return ""
        
        # Get type information from context if available
        var_type = self.context.get('type_info', {}).get(node.targets[0].id, 'auto')
        
        # Convert the value
        value = self._convert_value(node.value)
        
        # Generate C++ declaration
        return f"{var_type} {node.targets[0].id} = {value};"
    
    def _convert_value(self, value: ast.AST) -> str:
        if isinstance(value, ast.Num):
            return str(value.n)
        elif isinstance(value, ast.Str):
            return f'"{value.s}"'
        elif isinstance(value, ast.List):
            return f"{{{', '.join(self._convert_value(e) for e in value.elts)}}}"
        return "{}"  # Default empty initialization

class FunctionDefinitionRule(ConversionRule):
    """Rule for converting Python function definitions to C++."""
    
    def __init__(self):
        super().__init__(priority=90)
    
    def matches(self, node: ast.AST) -> bool:
        return isinstance(node, ast.FunctionDef)
    
    def convert(self, node: ast.FunctionDef) -> str:
        if not isinstance(node, ast.FunctionDef):
            return ""
        
        # Get return type from context or default to void
        return_type = self.context.get('return_types', {}).get(node.name, 'void')
        
        # Convert parameters
        params = self._convert_parameters(node.args)
        
        # Convert function body
        body = self._convert_body(node.body)
        
        return f"{return_type} {node.name}({params}) {{\n{body}\n}}"
    
    def _convert_parameters(self, args: ast.arguments) -> str:
        param_list = []
        for arg in args.args:
            param_type = self.context.get('param_types', {}).get(arg.arg, 'auto')
            param_list.append(f"{param_type} {arg.arg}")
        return ", ".join(param_list)
    
    def _convert_body(self, body: List[ast.AST]) -> str:
        # This is a simplified version - would need more complex logic in practice
        return "    // Function body conversion\n    return;"

class ClassDefinitionRule(ConversionRule):
    """Rule for converting Python class definitions to C++."""
    
    def __init__(self):
        super().__init__(priority=80)
    
    def matches(self, node: ast.AST) -> bool:
        return isinstance(node, ast.ClassDef)
    
    def convert(self, node: ast.ClassDef) -> str:
        if not isinstance(node, ast.ClassDef):
            return ""
        
        # Convert class body
        body = self._convert_class_body(node.body)
        
        return f"class {node.name} {{\npublic:\n{body}\n}};"
    
    def _convert_class_body(self, body: List[ast.AST]) -> str:
        # This is a simplified version - would need more complex logic in practice
        return "    // Class body conversion"
    
    def get_required_headers(self) -> List[str]:
        return ["<string>", "<vector>", "<memory>"] 