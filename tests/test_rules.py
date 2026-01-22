"""Tests for the rules module - conversion rules for Python to C++."""

import pytest
import ast
from src.rules.base_rule import ConversionRule
from src.rules.basic_rules import (
    VariableDeclarationRule,
    FunctionDefinitionRule,
    ClassDefinitionRule
)
from src.rules.rule_manager import RuleManager


class TestConversionRuleBase:
    """Tests for the base ConversionRule class."""
    
    def test_rule_priority(self):
        """Test that rule priority is set and retrieved correctly."""
        rule = VariableDeclarationRule()
        assert rule.get_priority() == 100
        
        rule2 = FunctionDefinitionRule()
        assert rule2.get_priority() == 90
    
    def test_context_setting(self):
        """Test that context can be set and retrieved."""
        rule = VariableDeclarationRule()
        context = {'type_info': {'x': 'int'}}
        rule.set_context(context)
        assert rule.context == context
    
    def test_required_headers(self):
        """Test that required headers are returned."""
        rule = ClassDefinitionRule()
        headers = rule.get_required_headers()
        assert '<string>' in headers
        assert '<vector>' in headers
        assert '<memory>' in headers
    
    def test_required_libraries(self):
        """Test that required libraries can be retrieved."""
        rule = VariableDeclarationRule()
        libraries = rule.get_required_libraries()
        assert isinstance(libraries, list)


class TestVariableDeclarationRule:
    """Tests for VariableDeclarationRule."""
    
    def test_matches_assign_node(self):
        """Test that the rule matches assignment nodes."""
        rule = VariableDeclarationRule()
        code = "x = 42"
        tree = ast.parse(code)
        assign_node = tree.body[0]
        
        assert rule.matches(assign_node)
    
    def test_does_not_match_other_nodes(self):
        """Test that the rule doesn't match non-assignment nodes."""
        rule = VariableDeclarationRule()
        code = "def foo(): pass"
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        assert not rule.matches(func_node)
    
    def test_convert_int_assignment(self):
        """Test conversion of integer assignment."""
        rule = VariableDeclarationRule()
        code = "x = 42"
        tree = ast.parse(code)
        assign_node = tree.body[0]
        
        rule.set_context({'type_info': {'x': 'int'}})
        result = rule.convert(assign_node)
        
        assert 'int' in result
        assert 'x' in result
        assert '42' in result
        assert result.endswith(';')
    
    def test_convert_string_assignment(self):
        """Test conversion of string assignment."""
        rule = VariableDeclarationRule()
        code = 's = "hello"'
        tree = ast.parse(code)
        assign_node = tree.body[0]
        
        rule.set_context({'type_info': {'s': 'std::string'}})
        result = rule.convert(assign_node)
        
        assert 'std::string' in result
        assert 's' in result
        assert '"hello"' in result
    
    def test_convert_with_auto_type(self):
        """Test conversion with auto type when type info not available."""
        rule = VariableDeclarationRule()
        code = "y = 3.14"
        tree = ast.parse(code)
        assign_node = tree.body[0]
        
        result = rule.convert(assign_node)
        
        assert 'auto' in result
        assert 'y' in result


class TestFunctionDefinitionRule:
    """Tests for FunctionDefinitionRule."""
    
    def test_matches_function_def(self):
        """Test that the rule matches function definition nodes."""
        rule = FunctionDefinitionRule()
        code = "def foo(): pass"
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        assert rule.matches(func_node)
    
    def test_does_not_match_other_nodes(self):
        """Test that the rule doesn't match non-function nodes."""
        rule = FunctionDefinitionRule()
        code = "x = 42"
        tree = ast.parse(code)
        assign_node = tree.body[0]
        
        assert not rule.matches(assign_node)
    
    def test_convert_simple_function(self):
        """Test conversion of simple function."""
        rule = FunctionDefinitionRule()
        code = "def add(a, b):\n    return a + b"
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        rule.set_context({
            'return_types': {'add': 'int'},
            'param_types': {'a': 'int', 'b': 'int'}
        })
        result = rule.convert(func_node)
        
        assert 'int' in result
        assert 'add' in result
        assert 'int a' in result
        assert 'int b' in result
    
    def test_convert_void_function(self):
        """Test conversion of void function."""
        rule = FunctionDefinitionRule()
        code = "def print_hello():\n    print('hello')"
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        result = rule.convert(func_node)
        
        assert 'void' in result
        assert 'print_hello' in result
    
    def test_convert_function_with_no_params(self):
        """Test conversion of function with no parameters."""
        rule = FunctionDefinitionRule()
        code = "def get_value():\n    return 42"
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        rule.set_context({'return_types': {'get_value': 'int'}})
        result = rule.convert(func_node)
        
        assert 'int get_value()' in result


class TestClassDefinitionRule:
    """Tests for ClassDefinitionRule."""
    
    def test_matches_class_def(self):
        """Test that the rule matches class definition nodes."""
        rule = ClassDefinitionRule()
        code = "class MyClass:\n    pass"
        tree = ast.parse(code)
        class_node = tree.body[0]
        
        assert rule.matches(class_node)
    
    def test_does_not_match_other_nodes(self):
        """Test that the rule doesn't match non-class nodes."""
        rule = ClassDefinitionRule()
        code = "x = 42"
        tree = ast.parse(code)
        assign_node = tree.body[0]
        
        assert not rule.matches(assign_node)
    
    def test_convert_simple_class(self):
        """Test conversion of simple class."""
        rule = ClassDefinitionRule()
        code = "class Point:\n    pass"
        tree = ast.parse(code)
        class_node = tree.body[0]
        
        result = rule.convert(class_node)
        
        assert 'class Point' in result
        assert 'public:' in result
        assert result.endswith(';')
    
    def test_class_required_headers(self):
        """Test that class conversion requires appropriate headers."""
        rule = ClassDefinitionRule()
        headers = rule.get_required_headers()
        
        assert '<string>' in headers
        assert '<vector>' in headers
        assert '<memory>' in headers


class TestRuleManager:
    """Tests for RuleManager."""
    
    def test_rule_registration(self):
        """Test that rules can be registered."""
        manager = RuleManager()
        rule = VariableDeclarationRule()
        manager.register_rule(rule)
        
        # Verify rule was registered
        assert len(manager.rules) > 0
    
    def test_rule_priority_ordering(self):
        """Test that rules are ordered by priority."""
        manager = RuleManager()
        rule1 = VariableDeclarationRule()  # Priority 100
        rule2 = FunctionDefinitionRule()   # Priority 90
        rule3 = ClassDefinitionRule()      # Priority 80
        
        manager.register_rule(rule2)
        manager.register_rule(rule3)
        manager.register_rule(rule1)
        
        # Get rules and verify they're sorted by priority (descending)
        priorities = [rule.get_priority() for rule in manager.rules]
        
        assert priorities == sorted(priorities, reverse=True)
    
    def test_get_matching_rule(self):
        """Test that the correct rule is returned for a node."""
        manager = RuleManager()
        manager.register_rule(VariableDeclarationRule())
        manager.register_rule(FunctionDefinitionRule())
        
        # Test with assignment node
        code = "x = 42"
        tree = ast.parse(code)
        assign_node = tree.body[0]
        
        rule = manager.get_matching_rule(assign_node)
        assert isinstance(rule, VariableDeclarationRule)
        
        # Test with function node
        code = "def foo(): pass"
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        rule = manager.get_matching_rule(func_node)
        assert isinstance(rule, FunctionDefinitionRule)
    
    def test_get_all_required_headers(self):
        """Test getting all required headers from all rules."""
        manager = RuleManager()
        manager.register_rule(ClassDefinitionRule())
        
        headers = manager.get_required_headers()
        assert '<string>' in headers
        assert '<vector>' in headers
        assert '<memory>' in headers
    
    def test_context_propagation(self):
        """Test that context is propagated to all rules."""
        manager = RuleManager()
        rule1 = VariableDeclarationRule()
        rule2 = FunctionDefinitionRule()
        
        manager.register_rule(rule1)
        manager.register_rule(rule2)
        
        context = {'type_info': {'x': 'int'}}
        manager.set_context(context)
        
        # Verify context was set on all rules
        for rule in manager.rules:
            assert rule.context == context


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
