"""Tests for the utils module - error handling and validation utilities."""

import pytest
import tempfile
import ast
from pathlib import Path
import logging
from src.utils.error_handling import (
    EnhancedLogger,
    ValidationHelper,
    get_enhanced_logger
)


class TestEnhancedLogger:
    """Tests for EnhancedLogger class."""
    
    def test_logger_creation(self):
        """Test that logger can be created."""
        logger = EnhancedLogger('test_logger')
        assert logger is not None
        assert logger.logger.name == 'test_logger'
    
    def test_logger_has_handler(self):
        """Test that logger has a handler configured."""
        logger = EnhancedLogger('test_logger_handler')
        assert len(logger.logger.handlers) > 0
    
    def test_info_logging(self, caplog):
        """Test info level logging."""
        logger = EnhancedLogger('test_info')
        logger.logger.setLevel(logging.INFO)
        
        with caplog.at_level(logging.INFO):
            logger.info("Test info message")
        
        assert "Test info message" in caplog.text
        assert "✅" in caplog.text
    
    def test_warning_logging(self, caplog):
        """Test warning level logging."""
        logger = EnhancedLogger('test_warning')
        logger.logger.setLevel(logging.WARNING)
        
        with caplog.at_level(logging.WARNING):
            logger.warning("Test warning message")
        
        assert "Test warning message" in caplog.text
        assert "⚠️" in caplog.text
    
    def test_error_logging(self, caplog):
        """Test error level logging."""
        logger = EnhancedLogger('test_error')
        logger.logger.setLevel(logging.ERROR)
        
        with caplog.at_level(logging.ERROR):
            logger.error("Test error message")
        
        assert "Test error message" in caplog.text
        assert "❌" in caplog.text
    
    def test_debug_logging(self, caplog):
        """Test debug level logging."""
        logger = EnhancedLogger('test_debug')
        logger.logger.setLevel(logging.DEBUG)
        
        with caplog.at_level(logging.DEBUG):
            logger.debug("Test debug message")
        
        assert "Test debug message" in caplog.text
        assert "🔍" in caplog.text
    
    def test_success_logging(self, caplog):
        """Test success level logging."""
        logger = EnhancedLogger('test_success')
        logger.logger.setLevel(logging.INFO)
        
        with caplog.at_level(logging.INFO):
            logger.success("Test success message")
        
        assert "Test success message" in caplog.text
        assert "🎉" in caplog.text
    
    def test_logging_with_context(self, caplog):
        """Test logging with context dictionary."""
        logger = EnhancedLogger('test_context')
        logger.logger.setLevel(logging.INFO)
        
        with caplog.at_level(logging.INFO):
            logger.info("Processing file", file="test.py", line=10)
        
        assert "Processing file" in caplog.text
        assert "file=test.py" in caplog.text
        assert "line=10" in caplog.text
    
    def test_context_formatting(self):
        """Test context formatting helper."""
        logger = EnhancedLogger('test_format')
        
        # Test with simple types
        context = {'name': 'test', 'count': 5, 'active': True}
        formatted = logger._format_context(context)
        
        assert 'name=test' in formatted
        assert 'count=5' in formatted
        assert 'active=True' in formatted
    
    def test_context_with_complex_types(self):
        """Test context formatting with complex types."""
        logger = EnhancedLogger('test_complex')
        
        context = {'data': [1, 2, 3], 'config': {'key': 'value'}}
        formatted = logger._format_context(context)
        
        assert 'data=list' in formatted
        assert 'config=dict' in formatted
    
    def test_empty_context(self):
        """Test context formatting with empty context."""
        logger = EnhancedLogger('test_empty')
        formatted = logger._format_context({})
        assert formatted == ""


class TestValidationHelper:
    """Tests for ValidationHelper class."""
    
    def test_validate_existing_python_file(self):
        """Test validation of an existing Python file."""
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as temp:
            temp.write("x = 42\n")
            temp_path = Path(temp.name)
        
        try:
            # Should not raise any exception
            ValidationHelper.validate_python_file(temp_path)
        finally:
            temp_path.unlink()
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file raises FileNotFoundError."""
        nonexistent = Path("/tmp/nonexistent_file_12345.py")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            ValidationHelper.validate_python_file(nonexistent)
        
        assert "not found" in str(exc_info.value)
    
    def test_validate_non_python_file(self):
        """Test validation of non-Python file raises ValueError."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp:
            temp_path = Path(temp.name)
        
        try:
            with pytest.raises(ValueError) as exc_info:
                ValidationHelper.validate_python_file(temp_path)
            
            assert "not a Python file" in str(exc_info.value)
        finally:
            temp_path.unlink()
    
    def test_validate_python_syntax_valid(self):
        """Test validation of valid Python syntax."""
        code = """
def hello():
    print("Hello, World!")
    return 42
"""
        tree = ValidationHelper.validate_python_syntax(code, Path("test.py"))
        
        assert isinstance(tree, ast.AST)
        assert len(tree.body) == 1
        assert isinstance(tree.body[0], ast.FunctionDef)
    
    def test_validate_python_syntax_invalid(self):
        """Test validation of invalid Python syntax raises SyntaxError."""
        code = """
def broken(:
    print("This is broken")
"""
        
        with pytest.raises(SyntaxError) as exc_info:
            ValidationHelper.validate_python_syntax(code, Path("broken.py"))
        
        assert "syntax error" in str(exc_info.value).lower()
        assert "broken.py" in str(exc_info.value)
    
    def test_validate_output_directory_creation(self):
        """Test that output directory is created if it doesn't exist."""
        # Create a unique temporary directory path
        temp_dir = Path(tempfile.gettempdir()) / f"test_output_{id(self)}"
        
        try:
            # Directory should not exist yet
            assert not temp_dir.exists()
            
            # Validate should create it
            ValidationHelper.validate_output_directory(temp_dir)
            
            # Directory should now exist
            assert temp_dir.exists()
            assert temp_dir.is_dir()
        finally:
            if temp_dir.exists():
                temp_dir.rmdir()
    
    def test_validate_output_directory_existing(self):
        """Test validation of existing output directory."""
        # Use a temporary directory that already exists
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Should not raise any exception
            ValidationHelper.validate_output_directory(temp_path)
            
            # Directory should still exist
            assert temp_path.exists()
    
    def test_validate_output_directory_nested(self):
        """Test creation of nested output directories."""
        # Create a unique nested temporary directory path
        temp_dir = Path(tempfile.gettempdir()) / f"test_nested_{id(self)}" / "subdir" / "output"
        
        try:
            # Directory should not exist yet
            assert not temp_dir.exists()
            
            # Validate should create it with all parents
            ValidationHelper.validate_output_directory(temp_dir)
            
            # Directory should now exist
            assert temp_dir.exists()
            assert temp_dir.is_dir()
        finally:
            # Clean up nested directories
            if temp_dir.exists():
                temp_dir.rmdir()
                temp_dir.parent.rmdir()
                temp_dir.parent.parent.rmdir()
    
    def test_validate_file_encoding_error(self):
        """Test validation of file with encoding errors."""
        # Create a file with binary content
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='wb') as temp:
            # Write invalid UTF-8 bytes
            temp.write(b'\xff\xfe\xfd')
            temp_path = Path(temp.name)
        
        try:
            with pytest.raises(ValueError) as exc_info:
                ValidationHelper.validate_python_file(temp_path)
            
            assert "encoding error" in str(exc_info.value).lower()
        finally:
            temp_path.unlink()


class TestGetEnhancedLogger:
    """Tests for the get_enhanced_logger helper function."""
    
    def test_get_enhanced_logger(self):
        """Test that get_enhanced_logger returns an EnhancedLogger instance."""
        logger = get_enhanced_logger('test_function')
        
        assert isinstance(logger, EnhancedLogger)
        assert logger.logger.name == 'test_function'
    
    def test_multiple_loggers(self):
        """Test creating multiple logger instances."""
        logger1 = get_enhanced_logger('logger1')
        logger2 = get_enhanced_logger('logger2')
        
        assert logger1.logger.name == 'logger1'
        assert logger2.logger.name == 'logger2'
        assert logger1.logger is not logger2.logger


class TestIntegrationScenarios:
    """Integration tests combining logger and validator."""
    
    def test_validation_with_logging(self, caplog):
        """Test validation workflow with logging."""
        logger = get_enhanced_logger('validation_test')
        logger.logger.setLevel(logging.INFO)
        
        # Create a valid Python file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as temp:
            temp.write("def test(): pass\n")
            temp_path = Path(temp.name)
        
        try:
            with caplog.at_level(logging.INFO):
                logger.info("Validating file", file=str(temp_path))
                ValidationHelper.validate_python_file(temp_path)
                logger.success("File validated successfully")
            
            assert "Validating file" in caplog.text
            assert "validated successfully" in caplog.text
        finally:
            temp_path.unlink()
    
    def test_error_handling_workflow(self, caplog):
        """Test error handling with logging."""
        logger = get_enhanced_logger('error_test')
        logger.logger.setLevel(logging.ERROR)
        
        nonexistent = Path("/tmp/does_not_exist_12345.py")
        
        try:
            with caplog.at_level(logging.ERROR):
                ValidationHelper.validate_python_file(nonexistent)
        except FileNotFoundError:
            logger.error("File validation failed", file=str(nonexistent))
        
        assert "validation failed" in caplog.text


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
