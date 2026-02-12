"""Custom exceptions for CLI operations."""

class ProcessError(Exception):
    """Base process exception."""


class ProcessAlreadyRunning(ProcessError):
    """Process already running."""


class ProcessNotRunning(ProcessError):
    """Process not running."""


class InvalidPIDFile(ProcessError):
    """PID file invalid or corrupted."""


class PIDSecurityError(ProcessError):
    """PID file security violation."""


class ProcessTimeout(ProcessError):
    """Process stop timeout."""


class ConfigError(Exception):
    """Configuration loading or validation error."""