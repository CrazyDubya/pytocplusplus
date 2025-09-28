from typing import Dict, List, Any, Optional, Union, Set, Tuple
import ast
import networkx as nx
from dataclasses import dataclass, field
from pathlib import Path
import logging

# Import specialized analyzers
from .type_inference import TypeInferenceAnalyzer
from .class_analyzer import ClassAnalyzer, ClassInfo
from .performance_analyzer import PerformanceAnalyzer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CodeAnalyzer")

@dataclass
class AnalysisResult:
    """Container for code analysis results."""
    type_info: Dict[str, Any]
    class_info: Dict[str, ClassInfo]  # class_name -> ClassInfo
    performance_bottlenecks: List[Dict[str, Any]]
    memory_usage: Dict[str, int]
    hot_paths: List[List[str]]
    dependencies: nx.DiGraph
    complexity: Dict[str, int]

class CodeAnalyzer:
    """Analyzes Python code for conversion to C++."""
    
    def __init__(self):
        # Initialize specialized analyzers
        self.type_analyzer = TypeInferenceAnalyzer()
        self.class_analyzer = ClassAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        
        # Dependencies analysis - kept local for now
        self.dependencies = nx.DiGraph()
        self.hot_paths: List[List[str]] = []
    
    def analyze_file(self, file_path: Path) -> AnalysisResult:
        """Analyze a Python file and return the results."""
        logger.info(f"Analyzing Python code: {file_path}")
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Use specialized analyzers
            logger.debug("Running class analysis...")
            class_info = self.class_analyzer.analyze_classes(tree)
            
            logger.debug("Running type inference...")
            type_info = self.type_analyzer.analyze_types(tree)
            
            logger.debug("Running performance analysis...")
            perf_results = self.performance_analyzer.analyze_performance(tree)
            
            # Simple dependency and hot path analysis
            self._analyze_dependencies(tree)
            self._analyze_hot_paths(tree)
            
            return AnalysisResult(
                type_info=type_info,
                class_info=class_info,
                performance_bottlenecks=perf_results['performance_bottlenecks'],
                memory_usage=perf_results['memory_usage'],
                hot_paths=self.hot_paths,
                dependencies=self.dependencies,
                complexity=perf_results['complexity']
            )
        except Exception as e:
            logger.error(f"Error analyzing file: {e}")
            raise
    
    def _analyze_dependencies(self, tree: ast.AST) -> None:
        """Analyze dependencies between functions and classes."""
        self.dependencies.clear()
        
        # Simple dependency analysis - can be enhanced
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                self.dependencies.add_node(node.name, type='function')
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
                self.dependencies.add_node(node.name, type='class')
                # Add inheritance dependencies
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        self.dependencies.add_edge(base.id, node.name, type='inheritance')
        
        # Analyze function calls to create dependencies
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    caller = self._find_containing_function_or_class(node, tree)
                    if caller and node.func.id in functions:
                        self.dependencies.add_edge(caller, node.func.id, type='call')
    
    def _analyze_hot_paths(self, tree: ast.AST) -> None:
        """Identify potential hot paths in the code."""
        self.hot_paths.clear()
        
        # Simple heuristic: nested loops and frequently called functions
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check for nested loops
                nested_level = self._count_loop_nesting(node)
                if nested_level > 1:
                    path = [f"nested_loop_level_{nested_level}"]
                    self.hot_paths.append(path)
    
    # Backward compatibility methods for tests
    def _infer_expression_type(self, expr: ast.AST) -> str:
        """Backward compatibility method for tests."""
        return self.type_analyzer._infer_expression_type(expr) or 'auto'

    def _get_type_name(self, node: ast.AST) -> str:
        """Backward compatibility method for tests."""
        return self.type_analyzer._annotation_to_cpp_type(node) or 'auto'

    def _infer_variable_type(self, node: ast.Assign) -> None:
        """Backward compatibility method for tests."""
        self.type_analyzer._infer_variable_type(node)
        # Update local type_info from the analyzer
        for var_name, var_type in self.type_analyzer.type_info.items():
            if isinstance(var_type, str):  # Only copy simple type strings
                if not hasattr(self, 'type_info'):
                    self.type_info = {}
                self.type_info[var_name] = var_type

    def _infer_function_types(self, node: ast.FunctionDef) -> None:
        """Backward compatibility method for tests."""
        self.type_analyzer._analyze_function_types(node)
        # Update local type_info from the analyzer
        for var_name, var_type in self.type_analyzer.type_info.items():
            if not hasattr(self, 'type_info'):
                self.type_info = {}
            self.type_info[var_name] = var_type
    
    def _find_containing_function_or_class(self, target_node: ast.AST, tree: ast.AST) -> Optional[str]:
        """Find the function or class containing a given node."""
        # Simple implementation - could be enhanced
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if self._node_contains(node, target_node):
                    return node.name
        return None
    
    def _node_contains(self, container: ast.AST, target: ast.AST) -> bool:
        """Check if a container node contains a target node."""
        for child in ast.walk(container):
            if child is target:
                return True
        return False
    
    def _count_loop_nesting(self, node: ast.AST) -> int:
        """Count the nesting level of loops."""
        max_nesting = 0
        current_nesting = 0
        
        def visit_node(n):
            nonlocal max_nesting, current_nesting
            
            if isinstance(n, (ast.For, ast.While)):
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
                
                for child in ast.iter_child_nodes(n):
                    visit_node(child)
                
                current_nesting -= 1
            else:
                for child in ast.iter_child_nodes(n):
                    visit_node(child)
        
        visit_node(node)
        return max_nesting