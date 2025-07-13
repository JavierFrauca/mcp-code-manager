"""
Sistema de logging para MCP Code Manager
Registra todas las peticiones MCP y ejecuciones de herramientas
"""

import logging
import logging.handlers
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import os
import sys

class MCPLogger:
    """Logger especializado para MCP Code Manager"""
    
    def __init__(self, logs_dir: str = None):
        """
        Inicializa el logger
        
        Args:
            logs_dir: Directorio donde guardar los logs. Si es None, usa ./logs
        """
        if logs_dir is None:
            # Obtener directorio del proyecto
            project_root = Path(__file__).parent.parent.parent
            logs_dir = project_root / "logs"
        
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Configurar loggers
        self._setup_loggers()
    
    def _setup_loggers(self):
        """Configura los diferentes loggers"""
        
        # Formatter común
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Logger principal MCP
        self.mcp_logger = self._create_logger(
            name='mcp.requests',
            filename='mcp_requests.log',
            formatter=formatter,
            level=logging.INFO
        )
        
        # Logger para herramientas
        self.tools_logger = self._create_logger(
            name='mcp.tools',
            filename='tools_execution.log',
            formatter=formatter,
            level=logging.INFO
        )
        
        # Logger para errores
        self.error_logger = self._create_logger(
            name='mcp.errors',
            filename='errors.log',
            formatter=formatter,
            level=logging.ERROR
        )
        
        # Logger para debug
        self.debug_logger = self._create_logger(
            name='mcp.debug',
            filename='debug.log',
            formatter=formatter,
            level=logging.DEBUG
        )
    
    def _create_logger(self, name: str, filename: str, formatter: logging.Formatter, level: int) -> logging.Logger:
        """Crea un logger con configuración específica"""
        
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Evitar duplicar handlers
        if logger.handlers:
            return logger
        
        # Handler para archivo con rotación
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.logs_dir / filename,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Handler para consola (solo errores y warnings)
        if level <= logging.WARNING:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def log_mcp_request(self, method: str, params: Dict[str, Any] = None, request_id: str = None):
        """Registra una petición MCP entrante"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'request',
            'method': method,
            'params': params or {},
            'request_id': request_id
        }
        
        self.mcp_logger.info(f"REQUEST | {method} | {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_mcp_response(self, method: str, success: bool, response_data: Any = None, request_id: str = None, execution_time: float = None):
        """Registra una respuesta MCP"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'response',
            'method': method,
            'success': success,
            'response_size': len(str(response_data)) if response_data else 0,
            'request_id': request_id,
            'execution_time_ms': round(execution_time * 1000, 2) if execution_time else None
        }
        
        level = logging.INFO if success else logging.WARNING
        status = "SUCCESS" if success else "FAILED"
        
        self.mcp_logger.log(level, f"RESPONSE | {method} | {status} | {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_tool_execution(self, tool_name: str, arguments: Dict[str, Any], success: bool, 
                          result: Any = None, error: str = None, execution_time: float = None):
        """Registra la ejecución de una herramienta"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'tool_name': tool_name,
            'arguments': arguments,
            'success': success,
            'execution_time_ms': round(execution_time * 1000, 2) if execution_time else None,
            'result_size': len(str(result)) if result else 0,
            'error': error
        }
        
        level = logging.INFO if success else logging.ERROR
        status = "SUCCESS" if success else "FAILED"
        
        self.tools_logger.log(level, f"TOOL | {tool_name} | {status} | {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_error(self, error: Exception, context: str = None, additional_data: Dict[str, Any] = None):
        """Registra un error con contexto completo"""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'traceback': traceback.format_exc(),
            'additional_data': additional_data or {}
        }
        
        self.error_logger.error(f"ERROR | {context or 'Unknown'} | {json.dumps(error_data, ensure_ascii=False)}")
    
    def log_debug(self, message: str, data: Dict[str, Any] = None):
        """Registra información de debug"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'data': data or {}
        }
        
        self.debug_logger.debug(f"DEBUG | {message} | {json.dumps(log_data, ensure_ascii=False)}")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de los logs"""
        stats = {
            'logs_directory': str(self.logs_dir),
            'log_files': []
        }
        
        for log_file in self.logs_dir.glob('*.log'):
            try:
                file_stats = log_file.stat()
                stats['log_files'].append({
                    'name': log_file.name,
                    'size_bytes': file_stats.st_size,
                    'size_mb': round(file_stats.st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                })
            except Exception as e:
                stats['log_files'].append({
                    'name': log_file.name,
                    'error': str(e)
                })
        
        return stats

# Instancia global del logger
_logger_instance = None

def get_logger() -> MCPLogger:
    """Obtiene la instancia global del logger"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = MCPLogger()
    return _logger_instance

def setup_logging(logs_dir: str = None) -> MCPLogger:
    """Configura el sistema de logging"""
    global _logger_instance
    _logger_instance = MCPLogger(logs_dir)
    return _logger_instance
