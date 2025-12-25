"""Tests for exception classes."""

import pytest

from argus_cli.core.exceptions import (
    ArgusError,
    AuthenticationError,
    ConfigurationError,
    DatabaseError,
    FileOperationError,
    IpLookupError,
    NetworkError,
    ValidationError,
)


class TestArgusError:
    """Test cases for ArgusError base class."""

    def test_argus_error_creation(self):
        """Test creating basic ArgusError."""
        error = ArgusError("Test error")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.error_code is None

    def test_argus_error_with_code(self):
        """Test creating ArgusError with error code."""
        error = ArgusError("Test error", error_code="TEST_001")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.error_code == "TEST_001"

    def test_argus_error_inheritance(self):
        """Test that ArgusError inherits from Exception."""
        error = ArgusError("Test error")

        assert isinstance(error, Exception)
        assert isinstance(error, ArgusError)


class TestConfigurationError:
    """Test cases for ConfigurationError."""

    def test_configuration_error_creation(self):
        """Test creating ConfigurationError."""
        error = ConfigurationError("Config file not found", "CONFIG_001")

        assert str(error) == "Config file not found"
        assert error.error_code == "CONFIG_001"
        assert isinstance(error, ArgusError)

    def test_configuration_error_inheritance(self):
        """Test that ConfigurationError inherits properly."""
        error = ConfigurationError("Test config error")

        assert isinstance(error, Exception)
        assert isinstance(error, ArgusError)
        assert isinstance(error, ConfigurationError)


class TestDatabaseError:
    """Test cases for DatabaseError."""

    def test_database_error_creation(self):
        """Test creating DatabaseError."""
        error = DatabaseError("Database connection failed")

        assert str(error) == "Database connection failed"
        assert isinstance(error, ArgusError)
        assert isinstance(error, DatabaseError)


class TestIpLookupError:
    """Test cases for IpLookupError."""

    def test_ip_lookup_error_creation(self):
        """Test creating IpLookupError."""
        error = IpLookupError("IP lookup timeout", "LOOKUP_001")

        assert str(error) == "IP lookup timeout"
        assert error.error_code == "LOOKUP_001"
        assert isinstance(error, ArgusError)
        assert isinstance(error, IpLookupError)


class TestValidationError:
    """Test cases for ValidationError."""

    def test_validation_error_creation(self):
        """Test creating ValidationError."""
        error = ValidationError("Invalid IP address format")

        assert str(error) == "Invalid IP address format"
        assert isinstance(error, ArgusError)
        assert isinstance(error, ValidationError)


class TestFileOperationError:
    """Test cases for FileOperationError."""

    def test_file_operation_error_creation(self):
        """Test creating FileOperationError."""
        error = FileOperationError("File not readable: test.txt", "FILE_001")

        assert str(error) == "File not readable: test.txt"
        assert error.error_code == "FILE_001"
        assert isinstance(error, ArgusError)
        assert isinstance(error, FileOperationError)


class TestNetworkError:
    """Test cases for NetworkError."""

    def test_network_error_creation(self):
        """Test creating NetworkError."""
        error = NetworkError("Connection timeout")

        assert str(error) == "Connection timeout"
        assert isinstance(error, ArgusError)
        assert isinstance(error, NetworkError)


class TestAuthenticationError:
    """Test cases for AuthenticationError."""

    def test_authentication_error_creation(self):
        """Test creating AuthenticationError."""
        error = AuthenticationError("Invalid API key", "AUTH_001")

        assert str(error) == "Invalid API key"
        assert error.error_code == "AUTH_001"
        assert isinstance(error, ArgusError)
        assert isinstance(error, AuthenticationError)


class TestExceptionHierarchy:
    """Test the complete exception hierarchy."""

    def test_all_exceptions_inherit_from_argus_error(self):
        """Test that all custom exceptions inherit from ArgusError."""
        exceptions = [
            ConfigurationError("test"),
            DatabaseError("test"),
            IpLookupError("test"),
            ValidationError("test"),
            FileOperationError("test"),
            NetworkError("test"),
            AuthenticationError("test"),
        ]

        for error in exceptions:
            assert isinstance(error, ArgusError), f"{error.__class__.__name__} should inherit from ArgusError"
            assert isinstance(error, Exception), f"{error.__class__.__name__} should inherit from Exception"

    def test_exception_raising(self):
        """Test raising and catching custom exceptions."""

        def raise_configuration_error():
            raise ConfigurationError("Config file missing")  # noqa: TRY003

        def raise_validation_error():
            raise ValidationError("Invalid input")  # noqa: TRY003

        with pytest.raises(ConfigurationError) as exc_info:
            raise_configuration_error()

        assert str(exc_info.value) == "Config file missing"

        with pytest.raises(ValidationError) as exc_info:
            raise_validation_error()

        assert str(exc_info.value) == "Invalid input"

    def test_exception_chaining(self):
        """Test exception chaining."""
        original_error = ValueError("Original error")

        try:
            try:
                raise original_error
            except ValueError as e:
                raise ConfigurationError("Configuration failed") from e  # noqa: TRY003
        except ConfigurationError as config_error:
            assert config_error.__cause__ is original_error
            assert str(config_error) == "Configuration failed"
