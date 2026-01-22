import ast
import sys
from pathlib import Path
from typing import Any

def print_ast_node(node: ast.AST, indent: int = 0) -> None:
    """Print an AST node with indentation."""
    node_type = type(node).__name__
    print(' ' * indent + f"{node_type}", end='')
    
    if isinstance(node, ast.Name):
        print(f"(id={node.id})", end='')
    elif isinstance(node, ast.Constant):
        print(f"(value={node.value}, kind={getattr(node, 'kind', None)})", end='')
    elif isinstance(node, ast.arg):
        print(f"(arg={node.arg})", end='')
    
    print()
    
    # Recursively print child nodes
    for field_name, field_value in ast.iter_fields(node):
        if isinstance(field_value, list):
            for i, item in enumerate(field_value):
                if isinstance(item, ast.AST):
                    print(' ' * (indent + 2) + f"{field_name}[{i}]:")
                    print_ast_node(item, indent + 4)
        elif isinstance(field_value, ast.AST):
            print(' ' * (indent + 2) + f"{field_name}:")
            print_ast_node(field_value, indent + 4)

def analyze_file(file_path: str) -> None:
    """Analyze a Python file's AST."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    # Find classes and functions
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            print(f"Class: {node.name}")
            print("=" * 40)
            print_ast_node(node)
            print("\n")
        elif isinstance(node, ast.FunctionDef) and node.name != 'main':
            print(f"Function: {node.name}")
            print("=" * 40)
            print_ast_node(node)
            print("\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "examples/simple_example.py"
    
    analyze_file(file_path)