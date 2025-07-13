"""
Excepciones personalizadas para MCP Code Manager
"""

class MCPError(Exception):
    """Excepción base para errores del MCP"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

class ValidationError(MCPError):
    """Error de validación de parámetros"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")

class RepositoryError(MCPError):
    """Error relacionado con operaciones de repositorio"""
    def __init__(self, message: str, repo_url: str = None):
        self.repo_url = repo_url
        super().__init__(message, "REPOSITORY_ERROR")

class GitError(MCPError):
    """Error en operaciones Git"""
    def __init__(self, message: str, git_command: str = None):
        self.git_command = git_command
        super().__init__(message, "GIT_ERROR")

class FileOperationError(MCPError):
    """Error en operaciones de archivo"""
    def __init__(self, message: str, file_path: str = None):
        self.file_path = file_path
        super().__init__(message, "FILE_ERROR")

class CodeAnalysisError(MCPError):
    """Error en análisis de código"""
    def __init__(self, message: str, file_path: str = None):
        self.file_path = file_path
        super().__init__(message, "CODE_ANALYSIS_ERROR")

class NetworkError(MCPError):
    """Error de red/conectividad"""
    def __init__(self, message: str, url: str = None):
        self.url = url
        super().__init__(message, "NETWORK_ERROR")

class AuthenticationError(MCPError):
    """Error de autenticación"""
    def __init__(self, message: str, service: str = None):
        self.service = service
        super().__init__(message, "AUTH_ERROR")

class ConfigurationError(MCPError):
    """Error de configuración"""
    def __init__(self, message: str, config_key: str = None):
        self.config_key = config_key
        super().__init__(message, "CONFIG_ERROR")