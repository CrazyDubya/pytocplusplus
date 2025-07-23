"""Enhanced error handling and user experience utilities."""

import logging
import traceback
from typing import Any, Dict, List, Optional
from pathlib import Path
import ast

class EnhancedLogger:
    """Enhanced logging with user-friendly messages and error handling."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up enhanced logging format."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional context."""
        if kwargs:
            message = f"{message} {self._format_context(kwargs)}"
        self.logger.info(f"✅ {message}")
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional context."""
        if kwargs:
            message = f"{message} {self._format_context(kwargs)}"
        self.logger.warning(f"⚠️  {message}")
    
    def error(self, message: str, **kwargs):
        """Log error message with optional context."""
        if kwargs:
            message = f"{message} {self._format_context(kwargs)}"
        self.logger.error(f"❌ {message}")
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional context."""
        if kwargs:
            message = f"{message} {self._format_context(kwargs)}"
        self.logger.debug(f"🔍 {message}")
    
    def success(self, message: str, **kwargs):
        """Log success message with optional context."""
        if kwargs:
            message = f"{message} {self._format_context(kwargs)}"
        self.logger.info(f"🎉 {message}")
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for logging."""
        if not context:
            return ""
        
        parts = []
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                parts.append(f"{key}={value}")
            else:
                parts.append(f"{key}={type(value).__name__}")
        
        return f"({', '.join(parts)})"

class ValidationHelper:
    """Helper for validating inputs and providing user-friendly error messages."""
    
    @staticmethod
    def validate_python_file(file_path: Path) -> None:
        """Validate that a Python file exists and is readable."""
        if not file_path.exists():
            raise FileNotFoundError(f"Python file not found: {file_path}")
        
        if not file_path.suffix == '.py':
            raise ValueError(f"File is not a Python file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            raise ValueError(f"File encoding error: {file_path}")
        except PermissionError:
            raise PermissionError(f"Permission denied: {file_path}")
    
    @staticmethod
    def validate_python_syntax(content: str, file_path: Path) -> ast.AST:
        """Validate Python syntax and return AST."""
        try:
            return ast.parse(content)
        except SyntaxError as e:
            raise SyntaxError(f"Python syntax error in {file_path} line {e.lineno}: {e.msg}")
    
    @staticmethod
    def validate_output_directory(output_dir: Path) -> None:
        """Validate and create output directory if needed."""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise PermissionError(f"Cannot create output directory: {output_dir}")
        except OSError as e:
            raise OSError(f"Error creating output directory: {output_dir} - {e}")

# Global helper functions
def get_enhanced_logger(name: str) -> EnhancedLogger:
    """Get an enhanced logger instance."""
    return EnhancedLogger(name)