"""Class analyzer for Python class definitions."""

from typing import Dict, List, Any, Optional
import ast
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("ClassAnalyzer")

@dataclass
class ClassInfo:
    """Information about a class definition."""
    name: str
    docstring: Optional[str] = None
    bases: List[str] = field(default_factory=list)
    attributes: Dict[str, str] = field(default_factory=dict)  # attr_name -> type
    methods: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # method_name -> info

class ClassAnalyzer:
    """Specialized analyzer for class definitions."""
    
    def __init__(self):
        self.class_info: Dict[str, ClassInfo] = {}
        self.current_class: Optional[str] = None
    
    def analyze_classes(self, tree: ast.AST) -> Dict[str, ClassInfo]:
        """Analyze class definitions in the AST."""
        self.class_info.clear()
        
        # First pass: collect all class names and inheritance
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._analyze_class_definition(node)
        
        # Second pass: analyze methods and attributes within classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._analyze_class_members(node)
        
        return self.class_info.copy()
    
    def _analyze_class_definition(self, node: ast.ClassDef) -> None:
        """Analyze a single class definition."""
        # Get class docstring
        docstring = ast.get_docstring(node)
        
        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            # Handle more complex base expressions if needed
        
        # Create ClassInfo
        class_info = ClassInfo(
            name=node.name,
            docstring=docstring,
            bases=bases
        )
        
        # Store class info
        self.class_info[node.name] = class_info
        logger.debug(f"Found class: {node.name} with bases: {bases}")
    
    def _analyze_class_members(self, node: ast.ClassDef) -> None:
        """Analyze methods and attributes within a class."""
        class_info = self.class_info[node.name]
        self.current_class = node.name
        
        try:
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    self._analyze_method(item, class_info)
                elif isinstance(item, ast.AnnAssign):
                    self._analyze_class_attribute(item, class_info)
                elif isinstance(item, ast.Assign):
                    self._analyze_class_assignment(item, class_info)
        finally:
            self.current_class = None
    
    def _analyze_method(self, node: ast.FunctionDef, class_info: ClassInfo) -> None:
        """Analyze a method definition."""
        method_info = {
            'name': node.name,
            'is_constructor': node.name == '__init__',
            'is_static': any(isinstance(dec, ast.Name) and dec.id == 'staticmethod' 
                           for dec in node.decorator_list),
            'is_class_method': any(isinstance(dec, ast.Name) and dec.id == 'classmethod' 
                                 for dec in node.decorator_list),
            'parameters': [],
            'return_type': 'void',
            'docstring': ast.get_docstring(node)
        }
        
        # Analyze parameters
        for arg in node.args.args:
            if arg.arg == 'self':  # Skip self parameter
                continue
                
            param_info = {
                'name': arg.arg,
                'type': 'auto',  # Default type
                'has_default': False
            }
            
            # Check for type annotation
            if arg.annotation:
                param_info['type'] = self._annotation_to_string(arg.annotation)
            
            method_info['parameters'].append(param_info)
        
        # Check for return type annotation
        if node.returns:
            method_info['return_type'] = self._annotation_to_string(node.returns)
        
        class_info.methods[node.name] = method_info
        logger.debug(f"Found method: {class_info.name}.{node.name}")
    
    def _analyze_class_attribute(self, node: ast.AnnAssign, class_info: ClassInfo) -> None:
        """Analyze a type-annotated class attribute."""
        if isinstance(node.target, ast.Name):
            attr_name = node.target.id
            attr_type = self._annotation_to_string(node.annotation)
            class_info.attributes[attr_name] = attr_type
            logger.debug(f"Found attribute: {class_info.name}.{attr_name}: {attr_type}")
    
    def _analyze_class_assignment(self, node: ast.Assign, class_info: ClassInfo) -> None:
        """Analyze a class-level assignment."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                attr_name = target.id
                # Try to infer type from value
                attr_type = self._infer_value_type(node.value)
                class_info.attributes[attr_name] = attr_type
                logger.debug(f"Found attribute: {class_info.name}.{attr_name}: {attr_type}")
    
    def _annotation_to_string(self, annotation: ast.AST) -> str:
        """Convert an AST annotation to a string representation."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                base = annotation.value.id
                if isinstance(annotation.slice, ast.Name):
                    param = annotation.slice.id
                    return f"{base}[{param}]"
                elif isinstance(annotation.slice, ast.Tuple):
                    params = [self._annotation_to_string(elt) for elt in annotation.slice.elts]
                    return f"{base}[{', '.join(params)}]"
        elif isinstance(annotation, ast.Attribute):
            if isinstance(annotation.value, ast.Name):
                return f"{annotation.value.id}.{annotation.attr}"
        
        # Fallback: return a generic string representation
        return 'auto'
    
    def _infer_value_type(self, value: ast.AST) -> str:
        """Infer type from a value expression."""
        if isinstance(value, ast.Constant):
            if isinstance(value.value, int):
                return 'int'
            elif isinstance(value.value, float):
                return 'double'
            elif isinstance(value.value, str):
                return 'std::string'
            elif isinstance(value.value, bool):
                return 'bool'
        elif isinstance(value, ast.List):
            return 'std::vector'
        elif isinstance(value, ast.Dict):
            return 'std::map'
        elif isinstance(value, ast.Set):
            return 'std::set'
        
        return 'auto'