from src.analyzer.code_analyzer import AnalysisResult, ClassInfo
from src.rules.rule_manager import RuleManager
from typing import Dict, Optional
from pathlib import Path
import logging

from .types import TypeHandler
from .expressions import ExpressionTranslator
from .statements import StatementTranslator
from .functions import FunctionGenerator
from .classes import ClassGenerator
from .output import OutputGenerator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CodeGenerator")


class CodeGenerator:
    """Generates C++ code from Python code analysis results."""
    
    def __init__(self, rule_manager: RuleManager):
        self.rule_manager = rule_manager
        self.generated_code: Dict[str, str] = {}
        self.analysis_result: Optional[AnalysisResult] = None
        
        # Initialize submodules
        self.types = TypeHandler(self)
        self.expressions = ExpressionTranslator(self)
        self.statements = StatementTranslator(self)
        self.functions = FunctionGenerator(self)
        self.classes = ClassGenerator(self)
        self.output = OutputGenerator(self)
    
    def generate_code(self, analysis_result: AnalysisResult, output_dir: Path) -> None:
        """Generate C++ code from analysis results."""
        logger.info(f"Generating C++ code in: {output_dir}")
        self.analysis_result = analysis_result
        output_dir = Path(output_dir)
        
        # Generate header file
        header_content = self.output._generate_header(analysis_result)
        self.generated_code['header'] = header_content
        
        # Generate implementation file
        impl_content = self.output._generate_implementation(analysis_result)
        self.generated_code['implementation'] = impl_content
        
        # Generate main.cpp file
        main_content = self.output._generate_main_cpp()
        self.generated_code['main'] = main_content
        
        # Generate pybind11 wrapper
        wrapper_content = self.output._generate_pybind_wrapper()
        self.generated_code['wrapper'] = wrapper_content
        
        # Generate Python wrapper
        python_wrapper_content = self.output._generate_python_wrapper()
        self.generated_code['python_wrapper'] = python_wrapper_content
        
        # Generate CMake file
        cmake_content = self.output._generate_cmake()
        self.generated_code['cmake'] = cmake_content
        
        # Create output directories
        output_dir.mkdir(parents=True, exist_ok=True)
        python_module_dir = output_dir / "python_wrapper"
        python_module_dir.mkdir(exist_ok=True)
        
        # Write files
        try:
            with open(output_dir / "generated.hpp", "w") as f:
                f.write(self.generated_code['header'])
            
            with open(output_dir / "generated.cpp", "w") as f:
                f.write(self.generated_code['implementation'])
            
            with open(output_dir / "main.cpp", "w") as f:
                f.write(self.generated_code['main'])
            
            with open(output_dir / "wrapper.cpp", "w") as f:
                f.write(self.generated_code['wrapper'])
            
            with open(output_dir / "CMakeLists.txt", "w") as f:
                f.write(self.generated_code['cmake'])
            
            # Write Python wrapper
            with open(python_module_dir / "__init__.py", "w") as f:
                f.write(self.generated_code['python_wrapper'])
            
            # Create setup.py for Python package
            setup_content = [
                'from setuptools import setup, find_packages',
                '',
                'setup(',
                '    name="optimized_numerical",',
                '    version="0.1.0",',
                '    packages=find_packages(),',
                '    install_requires=[',
                '        "numpy",',
                '    ],',
                '    author="PyToCpp",',
                '    description="Optimized numerical operations using C++",',
                ')',
            ]
            
            with open(output_dir / "setup.py", "w") as f:
                f.write('\n'.join(setup_content))
                
            logger.info("✅ C++ code generation successful")
        except Exception as e:
            logger.error(f"❌ Error writing files: {e}")
            raise
    
    # Delegate methods to submodules for backward compatibility
    def _generate_header(self, analysis_result: AnalysisResult) -> str:
        return self.output._generate_header(analysis_result)
    
    def _generate_implementation(self, analysis_result: AnalysisResult) -> str:
        return self.output._generate_implementation(analysis_result)
    
    def _generate_main_cpp(self) -> str:
        return self.output._generate_main_cpp()
    
    def _generate_pybind_wrapper(self) -> str:
        return self.output._generate_pybind_wrapper()
    
    def _generate_python_wrapper(self) -> str:
        return self.output._generate_python_wrapper()
    
    def _generate_cmake(self) -> str:
        return self.output._generate_cmake()
    
    def _generate_class_declaration(self, class_name: str, class_info: ClassInfo) -> str:
        return self.classes._generate_class_declaration(class_name, class_info)
    
    def _generate_class_implementation(self, class_name: str, class_info: ClassInfo, analysis_result: AnalysisResult) -> str:
        return self.classes._generate_class_implementation(class_name, class_info, analysis_result)
    
    def _generate_function_impl(self, func_name: str, func_info: Dict) -> str:
        return self.functions._generate_function_impl(func_name, func_info)
    
    def _generate_class_binding(self, class_name: str, class_info: ClassInfo) -> list:
        return self.classes._generate_class_binding(class_name, class_info)
    
    def _translate_expression(self, node, local_vars: Dict[str, str]) -> str:
        return self.expressions._translate_expression(node, local_vars)
    
    def _translate_statement(self, node, local_vars: Dict[str, str], indent_level: int) -> str:
        return self.statements._translate_statement(node, local_vars, indent_level)
    
    def _infer_cpp_type(self, node, local_vars: Dict[str, str]) -> str:
        return self.types._infer_cpp_type(node, local_vars)
    
    def _get_default_value(self, type_str: str) -> str:
        return self.types._get_default_value(type_str)
