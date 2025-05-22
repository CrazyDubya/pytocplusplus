import ast
import astunparse
import sys

def analyze_function_ast(file_path, function_name):
    # Read the Python file
    with open(file_path, 'r') as file:
        source_code = file.read()
    
    # Parse the source code into an AST
    tree = ast.parse(source_code)
    
    # Find the target function
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            print(f"AST Structure for function '{function_name}':\n")
            
            # Print the function signature
            print("Function Signature:")
            print(f"  Name: {node.name}")
            args = node.args
            print(f"  Arguments: {[a.arg for a in args.args]}")
            
            # Print annotations if they exist
            annotations = []
            for arg in args.args:
                if arg.annotation:
                    if isinstance(arg.annotation, ast.Name):
                        annotations.append(f"{arg.arg}: {arg.annotation.id}")
                    else:
                        annotations.append(f"{arg.arg}: <complex_annotation>")
            if annotations:
                print(f"  Type annotations: {annotations}")
            
            if node.returns:
                if isinstance(node.returns, ast.Name):
                    print(f"  Return type: {node.returns.id}")
                else:
                    print(f"  Return type: <complex_return_type>")
            
            # Print function docstring if it exists
            if ast.get_docstring(node):
                print(f"  Docstring: {ast.get_docstring(node)}")
            
            # Print the body structure with detailed information
            print("\nFunction Body AST Structure:")
            for i, stmt in enumerate(node.body):
                print(f"\nStatement {i+1}: {ast.dump(stmt, annotate_fields=True, include_attributes=False)}")
                print(f"Source: {astunparse.unparse(stmt).strip()}")
            
            # Provide a more readable representation of the function
            print("\nFunction Full AST:")
            print(ast.dump(node, annotate_fields=True, include_attributes=False))
            
            return True
    
    print(f"Function '{function_name}' not found in {file_path}")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ast_analyzer.py <file_path> <function_name>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    function_name = sys.argv[2]
    analyze_function_ast(file_path, function_name)