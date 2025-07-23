"""Performance analysis for Python code."""

from typing import Dict, List, Any, Optional
import ast
import logging

logger = logging.getLogger("PerformanceAnalyzer")

class PerformanceAnalyzer:
    """Specialized analyzer for performance bottlenecks and optimizations."""
    
    def __init__(self):
        self.performance_bottlenecks: List[Dict[str, Any]] = []
        self.complexity: Dict[str, int] = {}
        self.hot_paths: List[List[str]] = []
        self.memory_usage: Dict[str, int] = {}
    
    def analyze_performance(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze performance characteristics of the code."""
        self.performance_bottlenecks.clear()
        self.complexity.clear()
        self.hot_paths.clear()
        self.memory_usage.clear()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._analyze_function_performance(node)
            elif isinstance(node, ast.For):
                self._analyze_loop_performance(node)
            elif isinstance(node, ast.While):
                self._analyze_loop_performance(node)
            elif isinstance(node, ast.ListComp):
                self._analyze_comprehension_performance(node)
            elif isinstance(node, ast.Call):
                self._analyze_call_performance(node)
        
        return {
            'performance_bottlenecks': self.performance_bottlenecks.copy(),
            'complexity': self.complexity.copy(),
            'hot_paths': self.hot_paths.copy(),
            'memory_usage': self.memory_usage.copy()
        }
    
    def _analyze_function_performance(self, node: ast.FunctionDef) -> None:
        """Analyze performance characteristics of a function."""
        complexity = self._calculate_cyclomatic_complexity(node)
        self.complexity[node.name] = complexity
        
        # Check for potential bottlenecks
        if complexity > 10:
            self.performance_bottlenecks.append({
                'type': 'high_complexity',
                'function': node.name,
                'complexity': complexity,
                'line': node.lineno,
                'suggestion': 'Consider breaking down this function into smaller functions'
            })
        
        # Analyze memory usage patterns
        memory_score = self._estimate_memory_usage(node)
        self.memory_usage[node.name] = memory_score
        
        if memory_score > 50:
            self.performance_bottlenecks.append({
                'type': 'high_memory_usage',
                'function': node.name,
                'memory_score': memory_score,
                'line': node.lineno,
                'suggestion': 'Consider using more memory-efficient data structures'
            })
    
    def _analyze_loop_performance(self, node: ast.AST) -> None:
        """Analyze loop performance characteristics."""
        if isinstance(node, (ast.For, ast.While)):
            # Check for nested loops
            nested_loops = self._count_nested_loops(node)
            if nested_loops >= 2:  # Detect 2+ level nesting (changed from > 2)
                line = getattr(node, 'lineno', 0)
                self.performance_bottlenecks.append({
                    'type': 'nested_loops',
                    'description': f'Nested loop detected with {nested_loops} levels of nesting',
                    'nesting_level': nested_loops,
                    'line': line,
                    'suggestion': 'Consider algorithm optimization to reduce nesting'
                })
            
            # Check for expensive operations in loops
            expensive_ops = self._find_expensive_operations_in_loop(node)
            if expensive_ops:
                line = getattr(node, 'lineno', 0)
                self.performance_bottlenecks.append({
                    'type': 'expensive_loop_operations',
                    'description': f'Container modification in loop: {", ".join(expensive_ops)}',
                    'operations': expensive_ops,
                    'line': line,
                    'suggestion': 'Move expensive operations outside the loop when possible'
                })
    
    def _analyze_comprehension_performance(self, node: ast.ListComp) -> None:
        """Analyze list comprehension performance."""
        # List comprehensions are generally faster than equivalent loops
        # But check for complex expressions that might benefit from optimization
        if len(node.generators) > 1:
            line = getattr(node, 'lineno', 0)
            self.performance_bottlenecks.append({
                'type': 'complex_comprehension',
                'generators': len(node.generators),
                'line': line,
                'suggestion': 'Consider using itertools or breaking into simpler operations'
            })
    
    def _analyze_call_performance(self, node: ast.Call) -> None:
        """Analyze function call performance."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            # Check for known expensive operations
            expensive_functions = {
                'sorted': 'Consider using sort() for in-place sorting',
                'map': 'Consider using list comprehensions for better performance',
                'filter': 'Consider using list comprehensions for better performance',
                'reduce': 'Consider using more explicit loops for better readability'
            }
            
            if func_name in expensive_functions:
                line = getattr(node, 'lineno', 0)
                self.performance_bottlenecks.append({
                    'type': 'expensive_function',
                    'function': func_name,
                    'line': line,
                    'suggestion': expensive_functions[func_name]
                })
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each boolean operator adds complexity
                complexity += len(child.values) - 1
            elif isinstance(child, ast.Compare):
                # Each comparison operator adds complexity
                complexity += len(child.ops)
        
        return complexity
    
    def _estimate_memory_usage(self, node: ast.FunctionDef) -> int:
        """Estimate memory usage score for a function."""
        memory_score = 0
        
        for child in ast.walk(node):
            if isinstance(child, ast.List):
                # Lists consume memory
                memory_score += 10 + len(child.elts)
            elif isinstance(child, ast.Dict):
                # Dictionaries consume more memory
                memory_score += 15 + len(child.keys)
            elif isinstance(child, ast.Set):
                # Sets consume memory
                memory_score += 12 + len(child.elts)
            elif isinstance(child, ast.ListComp):
                # List comprehensions create new lists
                memory_score += 20
            elif isinstance(child, ast.DictComp):
                # Dict comprehensions create new dicts
                memory_score += 25
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    # Certain function calls are memory-intensive
                    if child.func.id in ['range', 'list', 'dict', 'set']:
                        memory_score += 15
        
        return memory_score
    
    def _count_nested_loops(self, node: ast.AST) -> int:
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
    
    def _find_expensive_operations_in_loop(self, node: ast.AST) -> List[str]:
        """Find expensive operations within a loop."""
        expensive_ops = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    func_name = child.func.id
                    if func_name in ['sorted', 'min', 'max', 'sum']:
                        expensive_ops.append(func_name)
                elif isinstance(child.func, ast.Attribute):
                    if child.func.attr in ['sort', 'append', 'extend', 'insert']:
                        expensive_ops.append(child.func.attr)
        
        return expensive_ops