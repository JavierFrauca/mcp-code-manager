"""
Validadores para MCP Code Manager
"""
import re
import os
from typing import List, Optional
from urllib.parse import urlparse
from pathlib import Path

from .exceptions import ValidationError

def validate_repo_url(url: str) -> str:
    """
    Valida una URL de repositorio Git
    
    Args:
        url: URL del repositorio
        
    Returns:
        URL normalizada
        
    Raises:
        ValidationError: Si la URL no es válida
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL del repositorio es requerida")
    
    url = url.strip()
    
    # Patrones válidos para repositorios Git
    git_patterns = [
        r'^https?://github\.com/[\w\-\.]+/[\w\-\.]+(?:\.git)?/?$',
        r'^git@github\.com:[\w\-\.]+/[\w\-\.]+(?:\.git)?$',
        r'^https?://gitlab\.com/[\w\-\.]+/[\w\-\.]+(?:\.git)?/?$',
        r'^https?://bitbucket\.org/[\w\-\.]+/[\w\-\.]+(?:\.git)?/?$',
        r'^https?://[\w\-\.]+/[\w\-\.\/]+(?:\.git)?/?$',  # Otros servidores Git
    ]
    
    if not any(re.match(pattern, url, re.IGNORECASE) for pattern in git_patterns):
        raise ValidationError(f"URL de repositorio inválida: {url}")
    
    return url

def validate_file_path(file_path: str, allow_absolute: bool = False) -> str:
    """
    Valida una ruta de archivo
    
    Args:
        file_path: Ruta del archivo
        allow_absolute: Si permite rutas absolutas
        
    Returns:
        Ruta normalizada
        
    Raises:
        ValidationError: Si la ruta no es válida
    """
    if not file_path or not isinstance(file_path, str):
        raise ValidationError("Ruta de archivo es requerida")
    
    file_path = file_path.strip()
    
    # Verificar caracteres peligrosos
    dangerous_chars = ['..', '<', '>', '|', '*', '?']
    if any(char in file_path for char in dangerous_chars):
        raise ValidationError(f"Ruta contiene caracteres no permitidos: {file_path}")
    
    # Verificar si es ruta absoluta cuando no está permitido
    if not allow_absolute and os.path.isabs(file_path):
        raise ValidationError("Rutas absolutas no están permitidas")
    
    # Normalizar ruta
    normalized_path = os.path.normpath(file_path)
    
    # Verificar que no escape del directorio base
    if normalized_path.startswith('..'):
        raise ValidationError("Ruta no puede escapar del directorio base")
    
    return normalized_path

def validate_class_name(class_name: str) -> str:
    """
    Valida un nombre de clase C#
    
    Args:
        class_name: Nombre de la clase
        
    Returns:
        Nombre validado
        
    Raises:
        ValidationError: Si el nombre no es válido
    """
    if not class_name or not isinstance(class_name, str):
        raise ValidationError("Nombre de clase es requerido")
    
    class_name = class_name.strip()
    
    # Patrón para nombres de clase C# válidos
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', class_name):
        raise ValidationError(f"Nombre de clase inválido: {class_name}")
    
    # Verificar palabras reservadas de C#
    reserved_words = {
        'abstract', 'as', 'base', 'bool', 'break', 'byte', 'case', 'catch',
        'char', 'checked', 'class', 'const', 'continue', 'decimal', 'default',
        'delegate', 'do', 'double', 'else', 'enum', 'event', 'explicit',
        'extern', 'false', 'finally', 'fixed', 'float', 'for', 'foreach',
        'goto', 'if', 'implicit', 'in', 'int', 'interface', 'internal',
        'is', 'lock', 'long', 'namespace', 'new', 'null', 'object',
        'operator', 'out', 'override', 'params', 'private', 'protected',
        'public', 'readonly', 'ref', 'return', 'sbyte', 'sealed', 'short',
        'sizeof', 'stackalloc', 'static', 'string', 'struct', 'switch',
        'this', 'throw', 'true', 'try', 'typeof', 'uint', 'ulong',
        'unchecked', 'unsafe', 'ushort', 'using', 'virtual', 'void',
        'volatile', 'while'
    }
    
    if class_name.lower() in reserved_words:
        raise ValidationError(f"'{class_name}' es una palabra reservada de C#")
    
    return class_name

def validate_element_type(element_type: str) -> str:
    """
    Valida un tipo de elemento C#
    
    Args:
        element_type: Tipo de elemento
        
    Returns:
        Tipo validado
        
    Raises:
        ValidationError: Si el tipo no es válido
    """
    valid_types = {'dto', 'service', 'controller', 'interface', 'enum', 'class', 'record'}
    
    if not element_type or not isinstance(element_type, str):
        raise ValidationError("Tipo de elemento es requerido")
    
    element_type = element_type.lower().strip()
    
    if element_type not in valid_types:
        raise ValidationError(f"Tipo de elemento inválido: {element_type}. Válidos: {', '.join(valid_types)}")
    
    return element_type

def validate_git_branch_name(branch_name: str) -> str:
    """
    Valida un nombre de rama Git
    
    Args:
        branch_name: Nombre de la rama
        
    Returns:
        Nombre validado
        
    Raises:
        ValidationError: Si el nombre no es válido
    """
    if not branch_name or not isinstance(branch_name, str):
        raise ValidationError("Nombre de rama es requerido")
    
    branch_name = branch_name.strip()
    
    # Reglas de nombres de rama Git
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._/-]*[a-zA-Z0-9]$', branch_name):
        raise ValidationError(f"Nombre de rama inválido: {branch_name}")
    
    # Verificar patrones no permitidos
    invalid_patterns = [
        r'\.\.',  # Dos puntos consecutivos
        r'^-',    # Empieza con guión
        r'-$',    # Termina con guión
        r'/$',    # Termina con slash
        r'//',    # Doble slash
    ]
    
    if any(re.search(pattern, branch_name) for pattern in invalid_patterns):
        raise ValidationError(f"Nombre de rama contiene patrones inválidos: {branch_name}")
    
    return branch_name

def validate_commit_message(message: str) -> str:
    """
    Valida un mensaje de commit
    
    Args:
        message: Mensaje del commit
        
    Returns:
        Mensaje validado
        
    Raises:
        ValidationError: Si el mensaje no es válido
    """
    if not message or not isinstance(message, str):
        raise ValidationError("Mensaje de commit es requerido")
    
    message = message.strip()
    
    if len(message) < 10:
        raise ValidationError("Mensaje de commit debe tener al menos 10 caracteres")
    
    if len(message) > 500:
        raise ValidationError("Mensaje de commit no puede exceder 500 caracteres")
    
    return message

def validate_file_content(content: str, file_path: str = None) -> str:
    """
    Valida el contenido de un archivo
    
    Args:
        content: Contenido del archivo
        file_path: Ruta del archivo (opcional)
        
    Returns:
        Contenido validado
        
    Raises:
        ValidationError: Si el contenido no es válido
    """
    if content is None:
        raise ValidationError("Contenido de archivo no puede ser None")
    
    if not isinstance(content, str):
        raise ValidationError("Contenido debe ser una cadena de texto")
    
    # Verificar tamaño del archivo (límite de 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if len(content.encode('utf-8')) > max_size:
        raise ValidationError(f"Archivo excede el tamaño máximo de {max_size // (1024*1024)}MB")
    
    # Verificar caracteres de control peligrosos (excepto los básicos)
    allowed_control_chars = {'\n', '\r', '\t'}
    for char in content:
        if ord(char) < 32 and char not in allowed_control_chars:
            raise ValidationError(f"Contenido contiene caracteres de control no permitidos")
    
    return content

def validate_search_type(search_type: str) -> str:
    """
    Valida el tipo de búsqueda
    
    Args:
        search_type: Tipo de búsqueda
        
    Returns:
        Tipo validado
        
    Raises:
        ValidationError: Si el tipo no es válido
    """
    valid_types = {'direct', 'deep'}
    
    if not search_type or not isinstance(search_type, str):
        search_type = 'direct'  # Valor por defecto
    
    search_type = search_type.lower().strip()
    
    if search_type not in valid_types:
        raise ValidationError(f"Tipo de búsqueda inválido: {search_type}. Válidos: {', '.join(valid_types)}")
    
    return search_type

def validate_git_action(action: str, valid_actions: List[str]) -> str:
    """
    Valida una acción Git
    
    Args:
        action: Acción a validar
        valid_actions: Lista de acciones válidas
        
    Returns:
        Acción validada
        
    Raises:
        ValidationError: Si la acción no es válida
    """
    if not action or not isinstance(action, str):
        raise ValidationError("Acción es requerida")
    
    action = action.lower().strip()
    
    if action not in valid_actions:
        raise ValidationError(f"Acción inválida: {action}. Válidas: {', '.join(valid_actions)}")
    
    return action