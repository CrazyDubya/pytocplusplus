import ast
import sys
from typing import Any

def print_ast(node: ast.AST, level: int = 0) -> None:
    indent = "  " * level
    print(f"{indent}{type(node).__name__}")
    for field, value in ast.iter_fields(node):
        if isinstance(value, list):
            print(f"{indent}  {field}:")
            for item in value:
                if isinstance(item, ast.AST):
                    print_ast(item, level + 2)
                else:
                    print(f"{indent}    {item}")
        elif isinstance(value, ast.AST):
            print(f"{indent}  {field}:")
            print_ast(value, level + 2)
        else:
            print(f"{indent}  {field}: {value}")

def print_type_info(node: ast.AST, level: int = 0) -> None:
    indent = "  " * level
    if isinstance(node, ast.FunctionDef):
        print(f"{indent}Function: {node.name}")
        if node.returns:
            print(f"{indent}  Returns:")
            print_type_info(node.returns, level + 2)
        for arg in node.args.args:
            print(f"{indent}  Argument: {arg.arg}")
            if arg.annotation:
                print(f"{indent}    Annotation:")
                print_type_info(arg.annotation, level + 4)
    elif isinstance(node, ast.Name):
        print(f"{indent}Name: {node.id}")
    elif isinstance(node, ast.Subscript):
        print(f"{indent}Subscript:")
        print(f"{indent}  Value:")
        print_type_info(node.value, level + 2)
        print(f"{indent}  Slice:")
        if isinstance(node.slice, ast.Index):  # Python 3.8 and earlier
            print_type_info(node.slice.value, level + 2)
        else:  # Python 3.9 and later
            print_type_info(node.slice, level + 2)
    elif isinstance(node, ast.Tuple):
        print(f"{indent}Tuple:")
        for i, elt in enumerate(node.elts):
            print(f"{indent}  Element {i}:")
            print_type_info(elt, level + 2)
    elif isinstance(node, ast.Constant):
        print(f"{indent}Constant: {node.value}")
    elif isinstance(node, ast.Assign):
        print(f"{indent}Assignment:")
        print(f"{indent}  Target:")
        print_type_info(node.targets[0], level + 2)
        print(f"{indent}  Value:")
        print_type_info(node.value, level + 2)
    elif isinstance(node, ast.Call):
        print(f"{indent}Call:")
        print(f"{indent}  Function:")
        print_type_info(node.func, level + 2)
        print(f"{indent}  Arguments:")
        for i, arg in enumerate(node.args):
            print(f"{indent}    Argument {i}:")
            print_type_info(arg, level + 4)
    else:
        print(f"{indent}Other: {type(node)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 debug.py <python_file>")
        sys.exit(1)
    
    with open(sys.argv[1], "r") as f:
        source = f.read()
    
    tree = ast.parse(source)
    print("\nAST Structure:")
    print_ast(tree)
    
    print("\nType Information:")
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            print("\nFunction type information:")
            print_type_info(node)
        elif isinstance(node, ast.Assign):
            print("\nAssignment type information:")
            print_type_info(node) 