"""
Decoradores para logging automático en MCP Code Manager
"""

import functools
import time
import json
from typing import Any, Callable, Dict, List
from .logger import get_logger

def log_tool_execution(tool_name: str = None):
    """
    Decorador para loggear automáticamente la ejecución de herramientas
    
    Args:
        tool_name: Nombre de la herramienta. Si es None, usa el nombre de la función
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger()
            name = tool_name or func.__name__
            
            # Preparar argumentos para logging (excluyendo 'self')
            log_args = {}
            if args and hasattr(args[0], '__class__'):
                # Primer argumento es 'self', excluirlo
                func_args = args[1:]
                # Obtener nombres de parámetros
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())[1:]  # Excluir 'self'
                log_args = dict(zip(param_names, func_args))
            else:
                func_args = args
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                log_args = dict(zip(param_names, func_args))
            
            log_args.update(kwargs)
            
            # Sanitizar argumentos para logging
            sanitized_args = _sanitize_for_logging(log_args)
            
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.log_tool_execution(
                    tool_name=name,
                    arguments=sanitized_args,
                    success=True,
                    result=_sanitize_for_logging(result),
                    execution_time=execution_time
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.log_tool_execution(
                    tool_name=name,
                    arguments=sanitized_args,
                    success=False,
                    error=str(e),
                    execution_time=execution_time
                )
                
                logger.log_error(e, f"Tool execution: {name}", {"arguments": sanitized_args})
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger()
            name = tool_name or func.__name__
            
            # Preparar argumentos para logging (excluyendo 'self')
            log_args = {}
            if args and hasattr(args[0], '__class__'):
                # Primer argumento es 'self', excluirlo
                func_args = args[1:]
                # Obtener nombres de parámetros
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())[1:]  # Excluir 'self'
                log_args = dict(zip(param_names, func_args))
            else:
                func_args = args
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                log_args = dict(zip(param_names, func_args))
            
            log_args.update(kwargs)
            
            # Sanitizar argumentos para logging
            sanitized_args = _sanitize_for_logging(log_args)
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.log_tool_execution(
                    tool_name=name,
                    arguments=sanitized_args,
                    success=True,
                    result=_sanitize_for_logging(result),
                    execution_time=execution_time
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.log_tool_execution(
                    tool_name=name,
                    arguments=sanitized_args,
                    success=False,
                    error=str(e),
                    execution_time=execution_time
                )
                
                logger.log_error(e, f"Tool execution: {name}", {"arguments": sanitized_args})
                raise
        
        # Detectar si la función es async
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def log_mcp_handler(method_name: str = None):
    """
    Decorador para loggear automáticamente las peticiones y respuestas MCP
    
    Args:
        method_name: Nombre del método MCP. Si es None, usa el nombre de la función
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger()
            method = method_name or func.__name__
            
            # Log de la petición
            request_params = _sanitize_for_logging(kwargs) if kwargs else {}
            logger.log_mcp_request(method, request_params)
            
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.log_mcp_response(
                    method=method,
                    success=True,
                    response_data=_sanitize_for_logging(result),
                    execution_time=execution_time
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.log_mcp_response(
                    method=method,
                    success=False,
                    execution_time=execution_time
                )
                
                logger.log_error(e, f"MCP handler: {method}", {"params": request_params})
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger()
            method = method_name or func.__name__
            
            # Log de la petición
            request_params = _sanitize_for_logging(kwargs) if kwargs else {}
            logger.log_mcp_request(method, request_params)
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.log_mcp_response(
                    method=method,
                    success=True,
                    response_data=_sanitize_for_logging(result),
                    execution_time=execution_time
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.log_mcp_response(
                    method=method,
                    success=False,
                    execution_time=execution_time
                )
                
                logger.log_error(e, f"MCP handler: {method}", {"params": request_params})
                raise
        
        # Detectar si la función es async
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def _sanitize_for_logging(data: Any, max_length: int = 1000) -> Any:
    """
    Sanitiza datos para logging, limitando el tamaño y removiendo información sensible
    
    Args:
        data: Datos a sanitizar
        max_length: Longitud máxima para strings
    
    Returns:
        Datos sanitizados
    """
    if data is None:
        return None
    
    if isinstance(data, str):
        if len(data) > max_length:
            return data[:max_length] + f"... (truncated, original length: {len(data)})"
        return data
    
    if isinstance(data, (int, float, bool)):
        return data
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Ocultar información sensible
            if any(sensitive in key.lower() for sensitive in ['password', 'token', 'secret', 'key', 'auth']):
                sanitized[key] = "[HIDDEN]"
            else:
                sanitized[key] = _sanitize_for_logging(value, max_length)
        return sanitized
    
    if isinstance(data, (list, tuple)):
        return [_sanitize_for_logging(item, max_length) for item in data[:10]]  # Limitar a 10 elementos
    
    # Para otros tipos, convertir a string y limitar longitud
    str_data = str(data)
    if len(str_data) > max_length:
        return str_data[:max_length] + f"... (truncated, original length: {len(str_data)})"
    
    return str_data
