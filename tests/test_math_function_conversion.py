import ast
from src.converter.code_generator_fixed import CodeGenerator
from src.rules.rule_manager import RuleManager


def translate(expr: str) -> str:
    node = ast.parse(expr).body[0].value
    generator = CodeGenerator(RuleManager())
    return generator._translate_expression(node, {})


def test_sqrt_translation():
    assert translate('math.sqrt(4)') == 'std::sqrt(4)'


def test_sin_translation():
    assert translate('math.sin(x)') == 'std::sin(x)'


def test_cos_translation():
    assert translate('math.cos(y)') == 'std::cos(y)'
