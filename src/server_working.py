#!/usr/bin/env python3
"""
MCP Code Manager Server - Versión que funciona
Servidor MCP completamente funcional para Claude Desktop
"""

import asyncio
import sys
import json
import os
import subprocess
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List

# Importación para papelera de reciclaje en Windows
if sys.platform == "win32":
    try:
        import winshell
    except ImportError:
        winshell = None
        print("[WARNING] winshell no disponible - eliminación a papelera deshabilitada", file=sys.stderr)

# Configuración de encoding para Windows
if sys.platform == "win32":
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_ALL, 'C')

# Configurar streams para UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Importaciones MCP
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    from mcp.server.models import InitializationOptions
except ImportError as e:
    print(f"Error: MCP no instalado - {e}", file=sys.stderr)
    sys.exit(1)

# Importaciones de handlers y servicios
try:
    from handlers.file_handler import FileHandler
    from handlers.code_handler import CodeHandler
    from handlers.git_handler import GitHandler
    from handlers.csharp_test_handler import CSharpTestHandler
    from handlers.python_test_handler import PythonTestHandler
    from utils.exceptions import FileOperationError, CodeAnalysisError
    from utils.logger import setup_logging, get_logger
    from utils.logging_decorators import log_tool_execution, log_mcp_handler
    from utils.log_analyzer import get_log_analyzer
except ImportError as e:
    print(f"Error: Módulos de handlers no disponibles - {e}", file=sys.stderr)
    sys.exit(1)

class MCPWorkingServer:
    """Servidor MCP que funciona correctamente"""
    
    def __init__(self):
        # Configurar logging
        project_root = Path(__file__).parent.parent
        self.logger = setup_logging(str(project_root / "logs"))
        
        self.server = Server("mcp-code-manager")
        self.file_handler = FileHandler()
        self.code_handler = CodeHandler()
        self.git_handler = GitHandler()
        self.csharp_handler = CSharpTestHandler()
        self.python_handler = PythonTestHandler()
        
        self.logger.log_debug("Servidor MCP inicializado", {
            "handlers": ["file", "code", "git", "csharp", "python"]
        })
        print("[INIT] Servidor MCP inicializado", file=sys.stderr)
        self._setup_tools()
        
    def _setup_tools(self):
        """Configura las herramientas del servidor"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """Lista todas las herramientas disponibles"""
            return [
                Tool(
                    name="ping",
                    description="Test de conectividad - responde con pong",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="echo",
                    description="Repite el mensaje enviado",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Mensaje a repetir"
                            }
                        },
                        "required": ["message"]
                    }
                ),
                Tool(
                    name="get_file_content",
                    description="Obtiene el contenido de un archivo",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Ruta completa del archivo"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="list_directory",
                    description="Lista el contenido de un directorio",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "Ruta del directorio a listar",
                                "default": "."
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="git_status",
                    description="Obtiene el estado del repositorio Git",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repository_path": {
                                "type": "string",
                                "description": "Ruta del repositorio Git",
                                "default": "."
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="git_init",
                    description="Inicializa un nuevo repositorio Git",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_path": {
                                "type": "string",
                                "description": "Ruta donde inicializar el repositorio"
                            },
                            "bare": {
                                "type": "boolean",
                                "description": "Si crear un repositorio bare",
                                "default": False
                            },
                            "initial_branch": {
                                "type": "string",
                                "description": "Nombre de la rama inicial (opcional)"
                            }
                        },
                        "required": ["repo_path"]
                    }
                ),
                Tool(
                    name="git_add",
                    description="Agrega archivos al staging area",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista de archivos específicos (opcional)"
                            },
                            "all_files": {
                                "type": "boolean",
                                "description": "Si agregar todos los archivos (git add .)",
                                "default": False
                            },
                            "update": {
                                "type": "boolean",
                                "description": "Si solo actualizar archivos tracked (git add -u)",
                                "default": False
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="git_diff",
                    description="Muestra diferencias entre versiones",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Archivo específico (opcional)"
                            },
                            "staged": {
                                "type": "boolean",
                                "description": "Si mostrar diferencias staged",
                                "default": False
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="git_commit",
                    description="Realiza un commit",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "message": {
                                "type": "string",
                                "description": "Mensaje del commit"
                            },
                            "files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Archivos específicos (opcional)"
                            },
                            "add_all": {
                                "type": "boolean",
                                "description": "Si añadir todos los archivos modificados",
                                "default": False
                            }
                        },
                        "required": ["repo_url", "message"]
                    }
                ),
                Tool(
                    name="git_push",
                    description="Sube cambios al repositorio remoto",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "branch": {
                                "type": "string",
                                "description": "Rama específica (opcional)"
                            },
                            "force": {
                                "type": "boolean",
                                "description": "Si realizar push forzado",
                                "default": False
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="git_pull",
                    description="Descarga cambios del repositorio remoto",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "branch": {
                                "type": "string",
                                "description": "Rama específica (opcional)"
                            },
                            "rebase": {
                                "type": "boolean",
                                "description": "Si usar rebase en lugar de merge",
                                "default": False
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="git_branch",
                    description="Gestiona ramas del repositorio",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "action": {
                                "type": "string",
                                "description": "Acción a realizar",
                                "enum": ["create", "delete", "switch", "list", "rename"]
                            },
                            "branch_name": {
                                "type": "string",
                                "description": "Nombre de la rama"
                            },
                            "from_branch": {
                                "type": "string",
                                "description": "Rama base (para crear)"
                            }
                        },
                        "required": ["repo_url", "action"]
                    }
                ),
                Tool(
                    name="git_merge",
                    description="Fusiona ramas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "source_branch": {
                                "type": "string",
                                "description": "Rama origen"
                            },
                            "target_branch": {
                                "type": "string",
                                "description": "Rama destino (opcional, por defecto actual)"
                            },
                            "no_ff": {
                                "type": "boolean",
                                "description": "Si no usar fast-forward",
                                "default": False
                            }
                        },
                        "required": ["repo_url", "source_branch"]
                    }
                ),
                Tool(
                    name="git_stash",
                    description="Gestiona el stash",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "action": {
                                "type": "string",
                                "description": "Acción del stash",
                                "enum": ["save", "pop", "list", "apply", "drop"]
                            },
                            "message": {
                                "type": "string",
                                "description": "Mensaje del stash (para save)"
                            },
                            "stash_index": {
                                "type": "integer",
                                "description": "Índice del stash (para pop/apply/drop)"
                            }
                        },
                        "required": ["repo_url", "action"]
                    }
                ),
                Tool(
                    name="git_log",
                    description="Muestra el historial de commits",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Número de commits a mostrar",
                                "default": 10
                            },
                            "branch": {
                                "type": "string",
                                "description": "Rama específica (opcional)"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Archivo específico (opcional)"
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="git_reset",
                    description="Resetea el repositorio a un estado anterior",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "commit_hash": {
                                "type": "string",
                                "description": "Hash del commit (opcional, HEAD por defecto)"
                            },
                            "mode": {
                                "type": "string",
                                "description": "Modo de reset",
                                "enum": ["soft", "mixed", "hard"],
                                "default": "mixed"
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="git_tag",
                    description="Gestiona tags del repositorio",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "action": {
                                "type": "string",
                                "description": "Acción a realizar",
                                "enum": ["create", "delete", "list", "push"]
                            },
                            "tag_name": {
                                "type": "string",
                                "description": "Nombre del tag"
                            },
                            "message": {
                                "type": "string",
                                "description": "Mensaje del tag (para create)"
                            },
                            "commit_hash": {
                                "type": "string",
                                "description": "Hash del commit (opcional)"
                            }
                        },
                        "required": ["repo_url", "action"]
                    }
                ),
                Tool(
                    name="git_remote",
                    description="Gestiona remotos del repositorio",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "action": {
                                "type": "string",
                                "description": "Acción a realizar",
                                "enum": ["add", "remove", "list", "set-url"]
                            },
                            "remote_name": {
                                "type": "string",
                                "description": "Nombre del remoto"
                            },
                            "remote_url": {
                                "type": "string",
                                "description": "URL del remoto"
                            }
                        },
                        "required": ["repo_url", "action"]
                    }
                ),
                Tool(
                    name="create_directory",
                    description="Crea una nueva carpeta/directorio",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "Ruta completa de la carpeta a crear"
                            }
                        },
                        "required": ["directory_path"]
                    }
                ),
                Tool(
                    name="rename_directory",
                    description="Renombra una carpeta/directorio existente",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "old_path": {
                                "type": "string",
                                "description": "Ruta actual de la carpeta"
                            },
                            "new_path": {
                                "type": "string",
                                "description": "Nueva ruta/nombre de la carpeta"
                            }
                        },
                        "required": ["old_path", "new_path"]
                    }
                ),
                Tool(
                    name="delete_directory",
                    description="Elimina una carpeta/directorio enviándola a la papelera",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "Ruta completa de la carpeta a eliminar"
                            }
                        },
                        "required": ["directory_path"]
                    }
                ),
                Tool(
                    name="set_file_content",
                    description="Crea un archivo nuevo o modifica el contenido de un archivo existente",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Ruta completa del archivo a crear o modificar"
                            },
                            "content": {
                                "type": "string",
                                "description": "Contenido a escribir en el archivo"
                            },
                            "create_backup": {
                                "type": "boolean",
                                "description": "Si crear backup del archivo existente antes de modificar",
                                "default": True
                            }
                        },
                        "required": ["file_path", "content"]
                    }
                ),
                Tool(
                    name="rename_file",
                    description="Renombra o mueve un archivo a otra ubicación",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_path": {
                                "type": "string",
                                "description": "Ruta actual del archivo"
                            },
                            "dest_path": {
                                "type": "string",
                                "description": "Nueva ruta/nombre del archivo"
                            }
                        },
                        "required": ["source_path", "dest_path"]
                    }
                ),
                Tool(
                    name="delete_file",
                    description="Elimina un archivo enviándolo a la papelera de reciclaje",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Ruta completa del archivo a eliminar"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="copy_file",
                    description="Copia un archivo a otra ubicación",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_path": {
                                "type": "string",
                                "description": "Ruta del archivo origen"
                            },
                            "dest_path": {
                                "type": "string",
                                "description": "Ruta donde copiar el archivo"
                            }
                        },
                        "required": ["source_path", "dest_path"]
                    }
                ),
                Tool(
                    name="check_permissions",
                    description="Verifica permisos CRUD sobre una carpeta o archivo específico",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target_path": {
                                "type": "string",
                                "description": "Ruta a verificar (archivo o directorio)",
                                "default": "."
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="list_files",
                    description="Lista archivos del directorio con filtros y metadatos detallados",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "Ruta del directorio a listar",
                                "default": "."
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "Patrón de archivos (ej: *.py, *.txt)"
                            },
                            "include_directories": {
                                "type": "boolean",
                                "description": "Incluir directorios en la lista",
                                "default": False
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "Profundidad máxima de búsqueda (-1 = ilimitada)",
                                "default": 1
                            }
                        },
                        "required": []
                    }
                ),
                # Herramientas de análisis de código C#
                Tool(
                    name="find_class",
                    description="Localiza clases específicas en repositorios C# con búsqueda directa o profunda",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio C#"
                            },
                            "class_name": {
                                "type": "string",
                                "description": "Nombre de la clase a buscar"
                            },
                            "search_type": {
                                "type": "string",
                                "enum": ["direct", "deep"],
                                "description": "Tipo de búsqueda (direct: por nombre de archivo, deep: contenido completo)",
                                "default": "direct"
                            }
                        },
                        "required": ["repo_url", "class_name"]
                    }
                ),
                Tool(
                    name="get_cs_file_content",
                    description="Obtiene contenido de archivos C# con análisis automático de código",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio C#"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Ruta relativa del archivo C#"
                            }
                        },
                        "required": ["repo_url", "file_path"]
                    }
                ),
                Tool(
                    name="find_elements",
                    description="Busca elementos específicos como DTOs, Services, Controllers, Interfaces, Enums en código C#",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio C#"
                            },
                            "element_type": {
                                "type": "string",
                                "enum": ["dto", "service", "controller", "interface", "enum", "class"],
                                "description": "Tipo de elemento a buscar"
                            },
                            "element_name": {
                                "type": "string",
                                "description": "Nombre del elemento (búsqueda parcial)"
                            }
                        },
                        "required": ["repo_url", "element_type", "element_name"]
                    }
                ),
                Tool(
                    name="get_solution_structure",
                    description="Obtiene la estructura completa de una solución C# con análisis detallado",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio C#"
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                # === Herramientas de C# Testing y Gestión ===
                Tool(
                    name="dotnet_check_environment",
                    description="Verifica el entorno dotnet y proyectos existentes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio (opcional)"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="dotnet_create_solution",
                    description="Crea una nueva solución C#",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "solution_name": {
                                "type": "string",
                                "description": "Nombre de la solución"
                            },
                            "base_path": {
                                "type": "string",
                                "description": "Subdirectorio donde crear la solución",
                                "default": ""
                            }
                        },
                        "required": ["repo_url", "solution_name"]
                    }
                ),
                Tool(
                    name="dotnet_create_project",
                    description="Crea un nuevo proyecto C#",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "project_name": {
                                "type": "string",
                                "description": "Nombre del proyecto"
                            },
                            "template": {
                                "type": "string",
                                "description": "Tipo de proyecto",
                                "enum": ["console", "classlib", "web", "webapi", "mvc", "razor", "blazorserver", "blazorwasm", "wpf", "winforms", "worker", "mstest", "nunit", "xunit"],
                                "default": "console"
                            },
                            "base_path": {
                                "type": "string",
                                "description": "Subdirectorio donde crear el proyecto",
                                "default": ""
                            },
                            "framework": {
                                "type": "string",
                                "description": "Target framework (ej: net8.0, net6.0)"
                            }
                        },
                        "required": ["repo_url", "project_name"]
                    }
                ),
                Tool(
                    name="dotnet_add_project_to_solution",
                    description="Agrega un proyecto a una solución existente",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "solution_file": {
                                "type": "string",
                                "description": "Ruta relativa al archivo .sln"
                            },
                            "project_file": {
                                "type": "string",
                                "description": "Ruta relativa al archivo .csproj"
                            }
                        },
                        "required": ["repo_url", "solution_file", "project_file"]
                    }
                ),
                Tool(
                    name="dotnet_list_solution_projects",
                    description="Lista los proyectos en una solución",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "solution_file": {
                                "type": "string",
                                "description": "Ruta relativa al archivo .sln"
                            }
                        },
                        "required": ["repo_url", "solution_file"]
                    }
                ),
                Tool(
                    name="dotnet_add_package",
                    description="Agrega un paquete NuGet a un proyecto",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "project_file": {
                                "type": "string",
                                "description": "Ruta relativa al archivo .csproj"
                            },
                            "package_name": {
                                "type": "string",
                                "description": "Nombre del paquete NuGet"
                            },
                            "version": {
                                "type": "string",
                                "description": "Versión específica del paquete (opcional)"
                            }
                        },
                        "required": ["repo_url", "project_file", "package_name"]
                    }
                ),
                Tool(
                    name="dotnet_build_solution",
                    description="Compila una solución C# completa",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "solution_file": {
                                "type": "string",
                                "description": "Archivo .sln específico (opcional, usa todo el directorio si no se especifica)"
                            },
                            "configuration": {
                                "type": "string",
                                "description": "Configuración de compilación",
                                "enum": ["Debug", "Release"],
                                "default": "Debug"
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="dotnet_build_project",
                    description="Compila un proyecto C# específico",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "project_file": {
                                "type": "string",
                                "description": "Ruta relativa al archivo .csproj"
                            },
                            "configuration": {
                                "type": "string",
                                "description": "Configuración de compilación",
                                "enum": ["Debug", "Release"],
                                "default": "Debug"
                            }
                        },
                        "required": ["repo_url", "project_file"]
                    }
                ),
                Tool(
                    name="dotnet_restore_packages",
                    description="Restaura paquetes NuGet de un proyecto o solución",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "project_path": {
                                "type": "string",
                                "description": "Subdirectorio específico (opcional)",
                                "default": ""
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="dotnet_test_all",
                    description="Ejecuta todos los tests en una solución o proyecto",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "test_path": {
                                "type": "string",
                                "description": "Subdirectorio específico con tests (opcional)",
                                "default": ""
                            },
                            "collect_coverage": {
                                "type": "boolean",
                                "description": "Si recopilar coverage de código",
                                "default": False
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="dotnet_test_filter",
                    description="Ejecuta tests con filtro específico",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "filter_expression": {
                                "type": "string",
                                "description": "Expresión de filtro para tests (ej: TestCategory=Unit, Name~Calculator)"
                            },
                            "test_path": {
                                "type": "string",
                                "description": "Subdirectorio específico con tests (opcional)",
                                "default": ""
                            },
                            "collect_coverage": {
                                "type": "boolean",
                                "description": "Si recopilar coverage de código",
                                "default": False
                            }
                        },
                        "required": ["repo_url", "filter_expression"]
                    }
                ),
                Tool(
                    name="dotnet_get_test_filters",
                    description="Obtiene filtros de test comunes con ejemplos",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                # === Herramientas de Python Testing y Gestión ===
                Tool(
                    name="python_check_environment",
                    description="Verifica el entorno Python y estructura del proyecto",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio (opcional)"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="python_create_venv",
                    description="Crea un entorno virtual Python",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "venv_name": {
                                "type": "string",
                                "description": "Nombre del entorno virtual",
                                "default": "venv"
                            },
                            "base_path": {
                                "type": "string",
                                "description": "Subdirectorio donde crear el entorno",
                                "default": ""
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="python_install_packages",
                    description="Instala paquetes Python usando pip",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "packages": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista de paquetes a instalar"
                            },
                            "venv_name": {
                                "type": "string",
                                "description": "Nombre del entorno virtual (opcional)"
                            },
                            "base_path": {
                                "type": "string",
                                "description": "Subdirectorio del proyecto",
                                "default": ""
                            }
                        },
                        "required": ["repo_url", "packages"]
                    }
                ),
                Tool(
                    name="python_install_requirements",
                    description="Instala dependencias desde requirements.txt",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "requirements_file": {
                                "type": "string",
                                "description": "Nombre del archivo requirements",
                                "default": "requirements.txt"
                            },
                            "venv_name": {
                                "type": "string",
                                "description": "Nombre del entorno virtual (opcional)"
                            },
                            "base_path": {
                                "type": "string",
                                "description": "Subdirectorio del proyecto",
                                "default": ""
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="python_freeze",
                    description="Genera archivo requirements.txt",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "venv_name": {
                                "type": "string",
                                "description": "Nombre del entorno virtual (opcional)"
                            },
                            "base_path": {
                                "type": "string",
                                "description": "Subdirectorio del proyecto",
                                "default": ""
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="python_run_pytest",
                    description="Ejecuta tests usando pytest",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "test_path": {
                                "type": "string",
                                "description": "Directorio o archivo de tests",
                                "default": "."
                            },
                            "venv_name": {
                                "type": "string",
                                "description": "Nombre del entorno virtual (opcional)"
                            },
                            "test_pattern": {
                                "type": "string",
                                "description": "Patrón de tests específicos (opcional)"
                            },
                            "collect_coverage": {
                                "type": "boolean",
                                "description": "Si recopilar coverage",
                                "default": False
                            },
                            "verbose": {
                                "type": "boolean",
                                "description": "Salida verbose",
                                "default": False
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="python_run_unittest",
                    description="Ejecuta tests usando unittest",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "test_path": {
                                "type": "string",
                                "description": "Directorio o módulo de tests",
                                "default": "."
                            },
                            "venv_name": {
                                "type": "string",
                                "description": "Nombre del entorno virtual (opcional)"
                            },
                            "test_pattern": {
                                "type": "string",
                                "description": "Patrón de tests específicos (opcional)"
                            },
                            "verbose": {
                                "type": "boolean",
                                "description": "Salida verbose",
                                "default": False
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="python_lint",
                    description="Ejecuta linting de código Python",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "linter": {
                                "type": "string",
                                "description": "Herramienta de linting",
                                "enum": ["flake8", "pylint"],
                                "default": "flake8"
                            },
                            "venv_name": {
                                "type": "string",
                                "description": "Nombre del entorno virtual (opcional)"
                            },
                            "base_path": {
                                "type": "string",
                                "description": "Subdirectorio del proyecto",
                                "default": ""
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="python_format",
                    description="Formatea código Python",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            },
                            "formatter": {
                                "type": "string",
                                "description": "Herramienta de formateo",
                                "enum": ["black", "autopep8"],
                                "default": "black"
                            },
                            "venv_name": {
                                "type": "string",
                                "description": "Nombre del entorno virtual (opcional)"
                            },
                            "base_path": {
                                "type": "string",
                                "description": "Subdirectorio del proyecto",
                                "default": ""
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="python_detect_project",
                    description="Analiza la estructura del proyecto Python",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "URL del repositorio"
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="python_get_test_patterns",
                    description="Obtiene patrones de test comunes con ejemplos",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="python_get_tools_info",
                    description="Obtiene información sobre herramientas de calidad disponibles",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Ejecuta una herramienta específica"""
            start_time = time.time()
            
            try:
                self.logger.log_debug(f"Iniciando ejecución de herramienta", {
                    "tool_name": name,
                    "arguments": arguments
                })
                
                print(f"[TOOL] Ejecutando: {name} con argumentos: {arguments}", file=sys.stderr)
                
                if name == "ping":
                    execution_time = time.time() - start_time
                    result = [TextContent(type="text", text="pong")]
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "echo":
                    message = arguments.get("message", "")
                    execution_time = time.time() - start_time
                    result = [TextContent(type="text", text=f"Echo: {message}")]
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "get_file_content":
                    file_path = arguments.get("file_path", "")
                    result = await self._get_file_content(file_path)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "list_directory":
                    directory_path = arguments.get("directory_path", ".")
                    result = await self._list_directory(directory_path)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_status":
                    repository_path = arguments.get("repository_path", ".")
                    result = await self._git_status(repository_path)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_init":
                    repo_path = arguments.get("repo_path")
                    bare = arguments.get("bare", False)
                    initial_branch = arguments.get("initial_branch")
                    result = await self._git_init(repo_path, bare, initial_branch)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_add":
                    repo_url = arguments.get("repo_url")
                    files = arguments.get("files")
                    all_files = arguments.get("all_files", False)
                    update = arguments.get("update", False)
                    result = await self._git_add(repo_url, files, all_files, update)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_diff":
                    repo_url = arguments.get("repo_url")
                    file_path = arguments.get("file_path")
                    staged = arguments.get("staged", False)
                    result = await self._git_diff(repo_url, file_path, staged)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_commit":
                    repo_url = arguments.get("repo_url")
                    message = arguments.get("message")
                    files = arguments.get("files")
                    add_all = arguments.get("add_all", False)
                    result = await self._git_commit(repo_url, message, files, add_all)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_push":
                    repo_url = arguments.get("repo_url")
                    branch = arguments.get("branch")
                    force = arguments.get("force", False)
                    result = await self._git_push(repo_url, branch, force)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_pull":
                    repo_url = arguments.get("repo_url")
                    branch = arguments.get("branch")
                    rebase = arguments.get("rebase", False)
                    result = await self._git_pull(repo_url, branch, rebase)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_branch":
                    repo_url = arguments.get("repo_url")
                    action = arguments.get("action")
                    branch_name = arguments.get("branch_name")
                    from_branch = arguments.get("from_branch")
                    result = await self._git_branch(repo_url, action, branch_name, from_branch)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_merge":
                    repo_url = arguments.get("repo_url")
                    source_branch = arguments.get("source_branch")
                    target_branch = arguments.get("target_branch")
                    no_ff = arguments.get("no_ff", False)
                    result = await self._git_merge(repo_url, source_branch, target_branch, no_ff)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_stash":
                    repo_url = arguments.get("repo_url")
                    action = arguments.get("action")
                    message = arguments.get("message")
                    stash_index = arguments.get("stash_index")
                    result = await self._git_stash(repo_url, action, message, stash_index)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_log":
                    repo_url = arguments.get("repo_url")
                    limit = arguments.get("limit", 10)
                    branch = arguments.get("branch")
                    file_path = arguments.get("file_path")
                    result = await self._git_log(repo_url, limit, branch, file_path)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_reset":
                    repo_url = arguments.get("repo_url")
                    commit_hash = arguments.get("commit_hash")
                    mode = arguments.get("mode", "mixed")
                    result = await self._git_reset(repo_url, commit_hash, mode)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_tag":
                    repo_url = arguments.get("repo_url")
                    action = arguments.get("action")
                    tag_name = arguments.get("tag_name")
                    message = arguments.get("message")
                    commit_hash = arguments.get("commit_hash")
                    result = await self._git_tag(repo_url, action, tag_name, message, commit_hash)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "git_remote":
                    repo_url = arguments.get("repo_url")
                    action = arguments.get("action")
                    remote_name = arguments.get("remote_name")
                    remote_url = arguments.get("remote_url")
                    result = await self._git_remote(repo_url, action, remote_name, remote_url)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "create_directory":
                    directory_path = arguments.get("directory_path", "")
                    result = await self._create_directory(directory_path)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "rename_directory":
                    old_path = arguments.get("old_path", "")
                    new_path = arguments.get("new_path", "")
                    result = await self._rename_directory(old_path, new_path)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "delete_directory":
                    directory_path = arguments.get("directory_path", "")
                    result = await self._delete_directory(directory_path)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "set_file_content":
                    file_path = arguments.get("file_path", "")
                    content = arguments.get("content", "")
                    create_backup = arguments.get("create_backup", True)
                    result = await self._set_file_content_enhanced(file_path, content, create_backup)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "rename_file":
                    source_path = arguments.get("source_path", "")
                    dest_path = arguments.get("dest_path", "")
                    result = await self._rename_file(source_path, dest_path)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "delete_file":
                    file_path = arguments.get("file_path", "")
                    result = await self._delete_file(file_path)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "copy_file":
                    source_path = arguments.get("source_path", "")
                    dest_path = arguments.get("dest_path", "")
                    result = await self._copy_file(source_path, dest_path)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "check_permissions":
                    target_path = arguments.get("target_path", ".")
                    result = await self._check_permissions(target_path)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "list_files":
                    directory_path = arguments.get("directory_path", ".")
                    file_pattern = arguments.get("file_pattern")
                    include_directories = arguments.get("include_directories", False)
                    max_depth = arguments.get("max_depth", 1)
                    result = await self._list_files(directory_path, file_pattern, include_directories, max_depth)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                # Herramientas de análisis de código C#
                elif name == "find_class":
                    repo_url = arguments.get("repo_url", "")
                    class_name = arguments.get("class_name", "")
                    search_type = arguments.get("search_type", "direct")
                    result = await self._find_class(repo_url, class_name, search_type)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "get_cs_file_content":
                    repo_url = arguments.get("repo_url", "")
                    file_path = arguments.get("file_path", "")
                    result = await self._get_cs_file_content(repo_url, file_path)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "find_elements":
                    repo_url = arguments.get("repo_url", "")
                    element_type = arguments.get("element_type", "")
                    element_name = arguments.get("element_name", "")
                    result = await self._find_elements(repo_url, element_type, element_name)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "get_solution_structure":
                    repo_url = arguments.get("repo_url", "")
                    result = await self._get_solution_structure(repo_url)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                # === Manejadores de herramientas C# Testing ===
                
                elif name == "dotnet_check_environment":
                    repo_url = arguments.get("repo_url")
                    result = await self._dotnet_check_environment(repo_url)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "dotnet_create_solution":
                    repo_url = arguments.get("repo_url", "")
                    solution_name = arguments.get("solution_name", "")
                    base_path = arguments.get("base_path", "")
                    result = await self._dotnet_create_solution(repo_url, solution_name, base_path)
                    execution_time = time.time() - start_time
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=True,
                        result=result,
                        execution_time=execution_time
                    )
                    
                    return result
                
                elif name == "dotnet_create_project":
                    repo_url = arguments.get("repo_url", "")
                    project_name = arguments.get("project_name", "")
                    template = arguments.get("template", "console")
                    base_path = arguments.get("base_path", "")
                    framework = arguments.get("framework")
                    return await self._dotnet_create_project(repo_url, project_name, template, base_path, framework)
                
                elif name == "dotnet_add_project_to_solution":
                    repo_url = arguments.get("repo_url", "")
                    solution_file = arguments.get("solution_file", "")
                    project_file = arguments.get("project_file", "")
                    return await self._dotnet_add_project_to_solution(repo_url, solution_file, project_file)
                
                elif name == "dotnet_list_solution_projects":
                    repo_url = arguments.get("repo_url", "")
                    solution_file = arguments.get("solution_file", "")
                    return await self._dotnet_list_solution_projects(repo_url, solution_file)
                
                elif name == "dotnet_add_package":
                    repo_url = arguments.get("repo_url", "")
                    project_file = arguments.get("project_file", "")
                    package_name = arguments.get("package_name", "")
                    version = arguments.get("version")
                    return await self._dotnet_add_package(repo_url, project_file, package_name, version)
                
                elif name == "dotnet_build_solution":
                    repo_url = arguments.get("repo_url", "")
                    solution_file = arguments.get("solution_file")
                    configuration = arguments.get("configuration", "Debug")
                    return await self._dotnet_build_solution(repo_url, solution_file, configuration)
                
                elif name == "dotnet_build_project":
                    repo_url = arguments.get("repo_url", "")
                    project_file = arguments.get("project_file", "")
                    configuration = arguments.get("configuration", "Debug")
                    return await self._dotnet_build_project(repo_url, project_file, configuration)
                
                elif name == "dotnet_restore_packages":
                    repo_url = arguments.get("repo_url", "")
                    project_path = arguments.get("project_path", "")
                    return await self._dotnet_restore_packages(repo_url, project_path)
                
                elif name == "dotnet_test_all":
                    repo_url = arguments.get("repo_url", "")
                    test_path = arguments.get("test_path", "")
                    collect_coverage = arguments.get("collect_coverage", False)
                    return await self._dotnet_test_all(repo_url, test_path, collect_coverage)
                
                elif name == "dotnet_test_filter":
                    repo_url = arguments.get("repo_url", "")
                    filter_expression = arguments.get("filter_expression", "")
                    test_path = arguments.get("test_path", "")
                    collect_coverage = arguments.get("collect_coverage", False)
                    return await self._dotnet_test_filter(repo_url, filter_expression, test_path, collect_coverage)
                
                elif name == "dotnet_get_test_filters":
                    return await self._dotnet_get_test_filters()
                
                # === Handlers de Python ===
                elif name == "python_check_environment":
                    repo_url = arguments.get("repo_url")
                    return await self._python_check_environment(repo_url)
                
                elif name == "python_create_venv":
                    repo_url = arguments.get("repo_url", "")
                    venv_name = arguments.get("venv_name", "venv")
                    base_path = arguments.get("base_path", "")
                    return await self._python_create_venv(repo_url, venv_name, base_path)
                
                elif name == "python_install_packages":
                    repo_url = arguments.get("repo_url", "")
                    packages = arguments.get("packages", [])
                    venv_name = arguments.get("venv_name")
                    base_path = arguments.get("base_path", "")
                    return await self._python_install_packages(repo_url, packages, venv_name, base_path)
                
                elif name == "python_install_requirements":
                    repo_url = arguments.get("repo_url", "")
                    requirements_file = arguments.get("requirements_file", "requirements.txt")
                    venv_name = arguments.get("venv_name")
                    base_path = arguments.get("base_path", "")
                    return await self._python_install_requirements(repo_url, requirements_file, venv_name, base_path)
                
                elif name == "python_freeze":
                    repo_url = arguments.get("repo_url", "")
                    venv_name = arguments.get("venv_name")
                    base_path = arguments.get("base_path", "")
                    return await self._python_freeze(repo_url, venv_name, base_path)
                
                elif name == "python_run_pytest":
                    repo_url = arguments.get("repo_url", "")
                    test_path = arguments.get("test_path", ".")
                    venv_name = arguments.get("venv_name")
                    test_pattern = arguments.get("test_pattern")
                    collect_coverage = arguments.get("collect_coverage", False)
                    verbose = arguments.get("verbose", False)
                    return await self._python_run_pytest(repo_url, test_path, venv_name, test_pattern, collect_coverage, verbose)
                
                elif name == "python_run_unittest":
                    repo_url = arguments.get("repo_url", "")
                    test_path = arguments.get("test_path", ".")
                    venv_name = arguments.get("venv_name")
                    test_pattern = arguments.get("test_pattern")
                    verbose = arguments.get("verbose", False)
                    return await self._python_run_unittest(repo_url, test_path, venv_name, test_pattern, verbose)
                
                elif name == "python_lint":
                    repo_url = arguments.get("repo_url", "")
                    linter = arguments.get("linter", "flake8")
                    venv_name = arguments.get("venv_name")
                    base_path = arguments.get("base_path", "")
                    return await self._python_lint(repo_url, linter, venv_name, base_path)
                
                elif name == "python_format":
                    repo_url = arguments.get("repo_url", "")
                    formatter = arguments.get("formatter", "black")
                    venv_name = arguments.get("venv_name")
                    base_path = arguments.get("base_path", "")
                    return await self._python_format(repo_url, formatter, venv_name, base_path)
                
                elif name == "python_detect_project":
                    repo_url = arguments.get("repo_url", "")
                    return await self._python_detect_project(repo_url)
                
                elif name == "python_get_test_patterns":
                    return await self._python_get_test_patterns()
                
                elif name == "python_get_tools_info":
                    return await self._python_get_tools_info()
                
                elif name == "get_logs_stats":
                    hours = arguments.get("hours", 24)
                    return await self._get_logs_stats(hours)
                
                elif name == "search_logs":
                    query = arguments.get("query", "")
                    max_results = arguments.get("max_results", 50)
                    return await self._search_logs(query, max_results)
                
                elif name == "get_recent_errors":
                    hours = arguments.get("hours", 24)
                    return await self._get_recent_errors(hours)
                
                elif name == "export_log_summary":
                    hours = arguments.get("hours", 24)
                    return await self._export_log_summary(hours)
                
                else:
                    execution_time = time.time() - start_time
                    result = [TextContent(
                        type="text", 
                        text=f"Error: Herramienta desconocida '{name}'"
                    )]
                    
                    self.logger.log_tool_execution(
                        tool_name=name,
                        arguments=arguments,
                        success=False,
                        error=f"Herramienta desconocida '{name}'",
                        execution_time=execution_time
                    )
                    
                    return result
                    
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"Error ejecutando herramienta '{name}': {str(e)}"
                
                self.logger.log_tool_execution(
                    tool_name=name,
                    arguments=arguments,
                    success=False,
                    error=str(e),
                    execution_time=execution_time
                )
                
                self.logger.log_error(e, f"Ejecución de herramienta: {name}", {
                    "arguments": arguments,
                    "execution_time": execution_time
                })
                
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                return [TextContent(type="text", text=error_msg)]
    
    async def _get_file_content(self, file_path: str) -> List[TextContent]:
        """Obtiene el contenido de un archivo"""
        try:
            if not file_path:
                return [TextContent(type="text", text="Error: Ruta de archivo no especificada")]
            
            path = Path(file_path)
            if not path.exists():
                return [TextContent(type="text", text=f"Error: El archivo '{file_path}' no existe")]
            
            if not path.is_file():
                return [TextContent(type="text", text=f"Error: '{file_path}' no es un archivo")]
            
            # Leer archivo con manejo de encoding
            try:
                content = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    content = path.read_text(encoding='latin-1')
                except Exception:
                    content = path.read_text(encoding='utf-8', errors='replace')
            
            return [TextContent(
                type="text", 
                text=f"Contenido de '{file_path}':\n\n{content}"
            )]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error leyendo archivo: {str(e)}")]
    
    async def _list_directory(self, directory_path: str) -> List[TextContent]:
        """Lista el contenido de un directorio"""
        try:
            if not directory_path:
                directory_path = "."
            
            path = Path(directory_path)
            if not path.exists():
                return [TextContent(type="text", text=f"Error: El directorio '{directory_path}' no existe")]
            
            if not path.is_dir():
                return [TextContent(type="text", text=f"Error: '{directory_path}' no es un directorio")]
            
            items = []
            for item in sorted(path.iterdir()):
                if item.is_dir():
                    items.append(f"📁 {item.name}/")
                else:
                    size = item.stat().st_size
                    items.append(f"📄 {item.name} ({size} bytes)")
            
            if not items:
                content = f"Directorio '{directory_path}' está vacío"
            else:
                content = f"Contenido de '{directory_path}':\n\n" + "\n".join(items)
            
            return [TextContent(type="text", text=content)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error listando directorio: {str(e)}")]
    
    async def _git_status(self, repository_path: str) -> List[TextContent]:
        """Obtiene el estado del repositorio Git usando el handler"""
        try:
            if not repository_path:
                repository_path = "."
            result = await self.git_handler.status(repository_path)
            if result.get("clean"):
                response_text = f"✅ Repositorio Git limpio en '{repository_path}' (sin cambios)\n\n"
            else:
                response_text = f"🔎 Estado Git en '{repository_path}':\n"
                response_text += f"🌿 Rama: {result.get('branch', '?')}\n"
                response_text += f"📋 {result.get('summary', '')}\n\n"
                if result.get("staged"):
                    response_text += "🟢 Archivos staged:\n"
                    for item in result["staged"]:
                        response_text += f"  • {item['file']} [{item['status']}]\n"
                if result.get("unstaged"):
                    response_text += "🟡 Archivos modificados (no staged):\n"
                    for item in result["unstaged"]:
                        response_text += f"  • {item['file']} [{item['status']}]\n"
                if result.get("untracked"):
                    response_text += "❓ No rastreados:\n"
                    for file in result["untracked"]:
                        response_text += f"  • {file}\n"
                if result.get("conflicts"):
                    response_text += "❌ Conflictos:\n"
                    for file in result["conflicts"]:
                        response_text += f"  • {file}\n"
            if result.get("last_commit"):
                c = result["last_commit"]
                response_text += f"\nÚltimo commit: {c['hash']} - {c['author']} - {c['date']}\n📝 {c['message']}\n"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            self.logger.log_error(e, f"Error en _git_status para ruta: {repository_path}")
            return [TextContent(type="text", text=f"❌ Error ejecutando git status: {str(e)}")]
    
    async def _git_init(self, repo_path: str, bare: bool = False, initial_branch: str = None) -> List[TextContent]:
        """Inicializa un nuevo repositorio Git"""
        try:
            result = await self.git_handler.init(repo_path, bare, initial_branch)
            
            if result.get("success"):
                response_text = f"✅ {result['message']}\n"
                response_text += f"📁 **Ubicación:** {result['path']}\n"
                if result.get("bare"):
                    response_text += "🔧 **Tipo:** Repositorio bare\n"
                response_text += f"🌿 **Rama inicial:** {result['initial_branch']}"
            else:
                response_text = f"❌ {result['message']}"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error inicializando repositorio: {str(e)}")]

    async def _git_add(self, repo_url: str, files: List[str] = None, all_files: bool = False, update: bool = False) -> List[TextContent]:
        """Agrega archivos al staging area"""
        try:
            result = await self.git_handler.add(repo_url, files, all_files, update)
            
            if result.get("success"):
                response_text = f"✅ {result['message']}\n\n"
                
                if result.get("added_files"):
                    response_text += "📝 **Archivos agregados:**\n"
                    for file in result["added_files"]:
                        response_text += f"  • {file}\n"
                
                if result.get("staged_files"):
                    response_text += f"\n📋 **Total en staging:** {result['total_staged']} archivos\n"
                    response_text += "🔍 **Archivos staged:**\n"
                    for staged in result["staged_files"][:10]:  # Mostrar máximo 10
                        status_icon = {"A": "➕", "M": "🔄", "D": "🗑️"}.get(staged["status"], "📝")
                        response_text += f"  {status_icon} {staged['file']}\n"
                    
                    if len(result["staged_files"]) > 10:
                        response_text += f"  ... y {len(result['staged_files']) - 10} archivos más\n"
            else:
                response_text = f"❌ {result['message']}"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error agregando archivos: {str(e)}")]

    async def _git_commit(self, repo_url: str, message: str, files: list = None, add_all: bool = False) -> List[TextContent]:
        """Realiza un commit en el repositorio especificado usando el handler."""
        try:
            result = await self.git_handler.commit(repo_url, message, files, add_all)
            if result.get("success"):
                response_text = f"✅ {result['message']}\n"
                if result.get("commit_hash"):
                    response_text += f"🔢 **Hash:** {result['commit_hash']}\n"
                if result.get("committed_files"):
                    response_text += "📝 **Archivos commiteados:**\n"
                    for file in result["committed_files"]:
                        response_text += f"- {file}\n"
                if result.get("summary"):
                    response_text += f"\n📋 **Resumen:** {result['summary']}\n"
            else:
                response_text = f"❌ {result['message']}"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando commit: {str(e)}")]

    async def _git_diff(self, repo_url: str, file_path: str = None, staged: bool = False) -> List[TextContent]:
        """Muestra el diff del repositorio o de un archivo usando el handler."""
        try:
            result = await self.git_handler.diff(repo_url, file_path, staged)
            if result.get("success"):
                diff_text = result.get("diff", "")
                if diff_text.strip():
                    response_text = f"📄 **Diff:**\n\n{diff_text}"
                else:
                    response_text = "✅ No hay diferencias."
            else:
                response_text = f"❌ {result['message']}"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando diff: {str(e)}")]

    async def _git_log(self, repo_url: str, limit: int = 10, branch: str = None, file_path: str = None) -> List[TextContent]:
        """Muestra el log de commits del repositorio usando el handler."""
        try:
            result = await self.git_handler.log(repo_url, limit, branch, file_path)
            if result.get("success"):
                commits = result.get("commits", [])
                if commits:
                    lines = [f"🔢 {c['hash']} | {c['author']} | {c['date']}\n📝 {c['message']}" for c in commits]
                    response_text = f"📜 **Log de commits:**\n\n" + "\n\n".join(lines)
                else:
                    response_text = "No hay commits."
            else:
                response_text = f"❌ {result['message']}"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando log: {str(e)}")]
    
    async def _python_check_environment(self, repo_url: str) -> List[TextContent]:
        """Verifica el entorno Python"""
        try:
            result = await self.python_handler.check_python_environment(repo_url)
            
            if result.get("success"):
                response_text = f"✅ {result['message']}\n\n"
                
                if result.get("python_version"):
                    response_text += f"🐍 **Python:** {result['python_version']}\n"
                
                if result.get("virtual_env"):
                    response_text += f"📦 **Entorno virtual:** {result['virtual_env']}\n"
                
                if result.get("pip_version"):
                    response_text += f"📋 **Pip:** {result['pip_version']}\n"
                
                if result.get("installed_packages"):
                    response_text += f"\n📚 **Paquetes instalados:** {len(result['installed_packages'])}\n"
                    for pkg in result["installed_packages"][:5]:  # Mostrar primeros 5
                        response_text += f"  • {pkg}\n"
                    if len(result["installed_packages"]) > 5:
                        response_text += f"  ... y {len(result['installed_packages']) - 5} más\n"
            else:
                response_text = f"❌ {result['message']}"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error verificando entorno Python: {str(e)}")]

    async def _create_directory(self, directory_path: str) -> List[TextContent]:
        """Crea un nuevo directorio"""
        try:
            import os
            from pathlib import Path
            
            if not directory_path:
                return [TextContent(type="text", text="❌ Error: Ruta de directorio no especificada")]
            
            path = Path(directory_path)
            
            # Verificar si ya existe
            if path.exists():
                if path.is_dir():
                    return [TextContent(type="text", text=f"📁 El directorio '{directory_path}' ya existe")]
                else:
                    return [TextContent(type="text", text=f"❌ Error: '{directory_path}' existe pero no es un directorio")]
            
            # Crear directorio con padres si es necesario
            path.mkdir(parents=True, exist_ok=True)
            
            response_text = f"✅ Directorio creado exitosamente\n"
            response_text += f"📁 **Directorio creado:** {directory_path}\n"
            if len(path.parts) > 1:
                response_text += "📂 **Directorios padre creados automáticamente**\n"
            
            return [TextContent(type="text", text=response_text)]
            
        except PermissionError:
            return [TextContent(type="text", text=f"❌ Error: Sin permisos para crear directorio en '{directory_path}'")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error creando directorio: {str(e)}")]

    async def _set_file_content_enhanced(self, file_path: str, content: str, create_backup: bool = True) -> List[TextContent]:
        """Establece el contenido de un archivo con funcionalidades mejoradas"""
        try:
            from pathlib import Path
            import shutil
            import os
            
            if not file_path:
                return [TextContent(type="text", text="❌ Error: Ruta de archivo no especificada")]
            
            path = Path(file_path)
            
            # Crear directorio padre si no existe
            path.parent.mkdir(parents=True, exist_ok=True)
            
            backup_path = None
            
            # Crear backup si el archivo existe y se solicita
            if path.exists() and create_backup:
                backup_path = str(path) + ".backup"
                shutil.copy2(path, backup_path)
            
            # Escribir contenido
            try:
                path.write_text(content, encoding='utf-8')
                encoding = 'utf-8'
            except Exception:
                path.write_text(content, encoding='latin-1')
                encoding = 'latin-1'
            
            # Obtener tamaño del archivo
            size = path.stat().st_size
            
            response_text = f"✅ Archivo guardado exitosamente\n"
            response_text += f"📄 **Archivo:** {file_path}\n"
            response_text += f"📊 **Tamaño:** {size} bytes\n"
            
            if backup_path:
                response_text += f"💾 **Backup creado:** {backup_path}\n"
            
            response_text += f"🔤 **Codificación:** {encoding}\n"
            
            return [TextContent(type="text", text=response_text)]
            
        except PermissionError:
            return [TextContent(type="text", text=f"❌ Error: Sin permisos para escribir archivo '{file_path}'")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error escribiendo archivo: {str(e)}")]

    async def _rename_directory(self, old_path: str, new_path: str) -> List[TextContent]:
        """Renombra un directorio"""
        try:
            from pathlib import Path
            import shutil
            
            old = Path(old_path)
            new = Path(new_path)
            
            if not old.exists():
                return [TextContent(type="text", text=f"❌ Error: '{old_path}' no existe")]
            
            if not old.is_dir():
                return [TextContent(type="text", text=f"❌ Error: '{old_path}' no es un directorio")]
            
            if new.exists():
                return [TextContent(type="text", text=f"❌ Error: '{new_path}' ya existe")]
            
            shutil.move(str(old), str(new))
            
            response_text = f"✅ Directorio renombrado exitosamente\n"
            response_text += f"📁 **Origen:** {old_path}\n"
            response_text += f"📂 **Destino:** {new_path}\n"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error renombrando directorio: {str(e)}")]

    async def _delete_directory(self, directory_path: str) -> List[TextContent]:
        """Elimina un directorio"""
        try:
            from pathlib import Path
            import shutil
            
            path = Path(directory_path)
            
            if not path.exists():
                return [TextContent(type="text", text=f"❌ Error: '{directory_path}' no existe")]
            
            if not path.is_dir():
                return [TextContent(type="text", text=f"❌ Error: '{directory_path}' no es un directorio")]
            
            # Intentar mover a papelera en Windows
            moved_to_trash = False
            if sys.platform == "win32" and winshell:
                try:
                    winshell.delete_file(str(path))
                    moved_to_trash = True
                except Exception:
                    pass
            
            if not moved_to_trash:
                shutil.rmtree(path)
            
            response_text = f"✅ Directorio eliminado exitosamente\n"
            response_text += f"🗑️ **Directorio eliminado:** {directory_path}\n"
            
            if moved_to_trash:
                response_text += "♻️ **Movido a papelera de reciclaje**\n"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error eliminando directorio: {str(e)}")]

    async def _rename_file(self, source_path: str, dest_path: str) -> List[TextContent]:
        """Renombra un archivo"""
        try:
            from pathlib import Path
            import shutil
            
            source = Path(source_path)
            dest = Path(dest_path)
            
            if not source.exists():
                return [TextContent(type="text", text=f"❌ Error: '{source_path}' no existe")]
            
            if not source.is_file():
                return [TextContent(type="text", text=f"❌ Error: '{source_path}' no es un archivo")]
            
            if dest.exists():
                return [TextContent(type="text", text=f"❌ Error: '{dest_path}' ya existe")]
            
            shutil.move(str(source), str(dest))
            
            response_text = f"✅ Archivo renombrado exitosamente\n"
            response_text += f"📄 **Origen:** {source_path}\n"
            response_text += f"📝 **Destino:** {dest_path}\n"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error renombrando archivo: {str(e)}")]

    async def _delete_file(self, file_path: str) -> List[TextContent]:
        """Elimina un archivo"""
        try:
            from pathlib import Path
            
            path = Path(file_path)
            
            if not path.exists():
                return [TextContent(type="text", text=f"❌ Error: '{file_path}' no existe")]
            
            if not path.is_file():
                return [TextContent(type="text", text=f"❌ Error: '{file_path}' no es un archivo")]
            
            # Intentar mover a papelera en Windows
            moved_to_trash = False
            if sys.platform == "win32" and winshell:
                try:
                    winshell.delete_file(str(path))
                    moved_to_trash = True
                except Exception:
                    pass
            
            if not moved_to_trash:
                path.unlink()
            
            response_text = f"✅ Archivo eliminado exitosamente\n"
            response_text += f"🗑️ **Archivo eliminado:** {file_path}\n"
            
            if moved_to_trash:
                response_text += "♻️ **Movido a papelera de reciclaje**\n"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error eliminando archivo: {str(e)}")]

    async def _copy_file(self, source_path: str, dest_path: str) -> List[TextContent]:
        """Copia un archivo"""
        try:
            from pathlib import Path
            import shutil
            
            source = Path(source_path)
            dest = Path(dest_path)
            
            if not source.exists():
                return [TextContent(type="text", text=f"❌ Error: '{source_path}' no existe")]
            
            if not source.is_file():
                return [TextContent(type="text", text=f"❌ Error: '{source_path}' no es un archivo")]
            
            # Crear directorio destino si no existe
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, dest)
            size = dest.stat().st_size
            
            response_text = f"✅ Archivo copiado exitosamente\n"
            response_text += f"📄 **Origen:** {source_path}\n"
            response_text += f"📝 **Destino:** {dest_path}\n"
            response_text += f"📊 **Tamaño:** {size} bytes\n"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error copiando archivo: {str(e)}")]

    async def _check_permissions(self, target_path: str) -> List[TextContent]:
        """Verifica permisos de un archivo o directorio"""
        try:
            from pathlib import Path
            import os
            
            path = Path(target_path)
            
            if not path.exists():
                return [TextContent(type="text", text=f"❌ Error: '{target_path}' no existe")]
            
            # Verificar permisos
            readable = os.access(path, os.R_OK)
            writable = os.access(path, os.W_OK)
            executable = os.access(path, os.X_OK)
            
            response_text = f"✅ Permisos de '{target_path}':\n\n"
            response_text += f"📝 **Lectura:** {'✅' if readable else '❌'}\n"
            response_text += f"✏️ **Escritura:** {'✅' if writable else '❌'}\n"
            response_text += f"🔧 **Ejecución:** {'✅' if executable else '❌'}\n"
            
            # Información adicional
            stat = path.stat()
            if path.is_file():
                response_text += f"📊 **Tamaño:** {stat.st_size} bytes\n"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error verificando permisos: {str(e)}")]

    async def _list_files(self, directory_path: str, file_pattern: str = None, include_directories: bool = False, max_depth: int = 1) -> List[TextContent]:
        """Lista archivos con filtros avanzados"""
        try:
            from pathlib import Path
            import fnmatch

            path = Path(directory_path)

            if not path.exists():
                return [TextContent(type="text", text=f"❌ Error: '{directory_path}' no existe")]

            if not path.is_dir():
                return [TextContent(type="text", text=f"❌ Error: '{directory_path}' no es un directorio")]

            files = []
            directories = []

            def scan_directory(current_path: Path, current_depth: int):
                if current_depth > max_depth:
                    return
                try:
                    for item in current_path.iterdir():
                        if item.is_file():
                            files.append({
                                "name": str(item.relative_to(path)),
                                "size": item.stat().st_size,
                                "is_directory": False
                            })
                        elif item.is_dir():
                            if include_directories:
                                directories.append({
                                    "name": str(item.relative_to(path)),
                                    "size": 0,
                                    "is_directory": True
                                })
                            if current_depth < max_depth:
                                scan_directory(item, current_depth + 1)
                except PermissionError:
                    pass

            scan_directory(path, 1)

            # Aplica el filtro file_pattern después de la recursividad
            filtered_files = files
            if file_pattern:
                filtered_files = [f for f in files if fnmatch.fnmatch(f["name"], file_pattern)]

            response_text = f"📂 **Archivos en '{directory_path}':**\n\n"
            if file_pattern:
                response_text += f"🔍 **Patrón:** {file_pattern}\n"
            response_text += f"📊 **Profundidad:** {max_depth}\n\n"

            all_items = filtered_files + (directories if include_directories else [])

            if all_items:
                for item in all_items[:20]:  # Mostrar máximo 20
                    icon = "📁" if item["is_directory"] else "📄"
                    size_info = f" ({item['size']} bytes)" if not item["is_directory"] else ""
                    response_text += f"{icon} {item['name']}{size_info}\n"
                if len(all_items) > 20:
                    response_text += f"\n... y {len(all_items) - 20} archivos más\n"
                response_text += f"\n📈 **Total:** {len(filtered_files)} archivos"
                if include_directories:
                    response_text += f", {len(directories)} directorios"
            else:
                response_text += "📭 **Sin archivos encontrados**"

            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error listando archivos: {str(e)}")]

    # Implementaciones faltantes de métodos

    # ===============================================
    # MÉTODOS GIT FALTANTES - IMPLEMENTACIÓN COMPLETA
    # ===============================================
    
    async def _git_push(self, repo_url: str, branch: str = None, force: bool = False) -> List[TextContent]:
        """Sube cambios al repositorio remoto"""
        try:
            result = await self.git_handler.push(repo_url, branch, force)
            
            if result.get("success"):
                response_text = f"✅ {result['message']}\n"
                
                if result.get("pushed_branch"):
                    response_text += f"🌿 **Rama:** {result['pushed_branch']}\n"
                
                if result.get("commits_pushed"):
                    response_text += f"📤 **Commits subidos:** {result['commits_pushed']}\n"
                
                if result.get("remote_url"):
                    response_text += f"🔗 **Remoto:** {result['remote_url']}\n"
                
                if force:
                    response_text += "⚠️ **Push forzado realizado**\n"
                
            else:
                response_text = f"❌ {result['message']}"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando git push: {str(e)}")]

    async def _git_pull(self, repo_url: str, branch: str = None, rebase: bool = False) -> List[TextContent]:
        """Descarga cambios del repositorio remoto"""
        try:
            result = await self.git_handler.pull(repo_url, branch, rebase)
            
            if result.get("success"):
                response_text = f"✅ {result['message']}\n"
                
                if result.get("updated_branch"):
                    response_text += f"🌿 **Rama actualizada:** {result['updated_branch']}\n"
                
                if result.get("commits_received"):
                    response_text += f"📥 **Commits recibidos:** {result['commits_received']}\n"
                
                if result.get("files_changed"):
                    response_text += f"📝 **Archivos modificados:** {len(result['files_changed'])}\n"
                    for file_change in result["files_changed"][:5]:  # Mostrar primeros 5
                        response_text += f"  • {file_change}\n"
                    if len(result["files_changed"]) > 5:
                        response_text += f"  ... y {len(result['files_changed']) - 5} archivos más\n"
                
                if rebase:
                    response_text += "🔄 **Rebase aplicado**\n"
                
            else:
                response_text = f"❌ {result['message']}"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando git pull: {str(e)}")]

    async def _git_branch(self, repo_url: str, action: str, branch_name: str = None, from_branch: str = None) -> List[TextContent]:
        """Gestiona ramas del repositorio"""
        try:
            result = await self.git_handler.branch(repo_url, action, branch_name, from_branch)
            
            if result.get("success"):
                response_text = f"✅ {result['message']}\n"
                
                if action == "list":
                    if result.get("branches"):
                        response_text += "🌿 **Ramas disponibles:**\n"
                        for branch_info in result["branches"]:
                            prefix = "➤ " if branch_info.get("current") else "  "
                            remote_info = " (remota)" if branch_info.get("remote") else ""
                            response_text += f"{prefix}{branch_info['name']}{remote_info}\n"
                
                elif action == "create":
                    response_text += f"🌱 **Nueva rama creada:** {branch_name}\n"
                    if from_branch:
                        response_text += f"📍 **Basada en:** {from_branch}\n"
                
                elif action == "delete":
                    response_text += f"🗑️ **Rama eliminada:** {branch_name}\n"
                
                elif action == "switch":
                    response_text += f"🔄 **Rama cambiada a:** {branch_name}\n"
                    if result.get("files_changed"):
                        response_text += f"📝 **Archivos afectados:** {len(result['files_changed'])}\n"
                
                elif action == "rename":
                    response_text += f"🏷️ **Rama renombrada:** {from_branch} → {branch_name}\n"
                
            else:
                response_text = f"❌ {result['message']}"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando git branch: {str(e)}")]

    async def _git_merge(self, repo_url: str, source_branch: str, target_branch: str = None, no_ff: bool = False) -> List[TextContent]:
        """Fusiona ramas del repositorio"""
        try:
            result = await self.git_handler.merge(repo_url, source_branch, target_branch, no_ff)
            
            if result.get("success"):
                response_text = f"✅ {result['message']}\n"
                
                if result.get("merge_type"):
                    response_text += f"🔀 **Tipo de merge:** {result['merge_type']}\n"
                
                if result.get("source_branch"):
                    response_text += f"📤 **Rama origen:** {result['source_branch']}\n"
                
                if result.get("target_branch"):
                    response_text += f"📥 **Rama destino:** {result['target_branch']}\n"
                
                if result.get("files_merged"):
                    response_text += f"📝 **Archivos fusionados:** {len(result['files_merged'])}\n"
                    for file in result["files_merged"][:5]:
                        response_text += f"  • {file}\n"
                    if len(result["files_merged"]) > 5:
                        response_text += f"  ... y {len(result['files_merged']) - 5} archivos más\n"
                
                if result.get("conflicts"):
                    response_text += f"⚠️ **Conflictos detectados:** {len(result['conflicts'])}\n"
                    for conflict in result["conflicts"]:
                        response_text += f"  ❌ {conflict}\n"
                    response_text += "\n🔧 **Resuelve los conflictos y realiza commit**\n"
                
                if no_ff:
                    response_text += "🔗 **Merge commit creado (--no-ff)**\n"
                
            else:
                response_text = f"❌ {result['message']}"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando git merge: {str(e)}")]

    async def _git_stash(self, repo_url: str, action: str, message: str = None, stash_index: int = None) -> List[TextContent]:
        """Gestiona el stash del repositorio"""
        try:
            result = await self.git_handler.stash(repo_url, action, message, stash_index)
            
            if result.get("success"):
                response_text = f"✅ {result['message']}\n"
                
                if action == "save":
                    response_text += f"💾 **Stash guardado:** {message or 'WIP'}\n"
                    if result.get("stash_count"):
                        response_text += f"📦 **Total stashes:** {result['stash_count']}\n"
                
                elif action == "list":
                    if result.get("stashes"):
                        response_text += "📦 **Stashes disponibles:**\n"
                        for i, stash in enumerate(result["stashes"]):
                            response_text += f"  {i}: {stash['message']} ({stash['date']})\n"
                    else:
                        response_text += "📦 **No hay stashes guardados**\n"
                
                elif action in ["pop", "apply"]:
                    response_text += f"📤 **Stash {'aplicado y eliminado' if action == 'pop' else 'aplicado'}**\n"
                    if result.get("files_restored"):
                        response_text += f"📝 **Archivos restaurados:** {len(result['files_restored'])}\n"
                        for file in result["files_restored"][:5]:
                            response_text += f"  • {file}\n"
                        if len(result["files_restored"]) > 5:
                            response_text += f"  ... y {len(result['files_restored']) - 5} archivos más\n"
                
                elif action == "drop":
                    response_text += f"🗑️ **Stash eliminado:** stash@{{{stash_index or 0}}}\n"
                
            else:
                response_text = f"❌ {result['message']}"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando git stash: {str(e)}")]

    async def _git_reset(self, repo_url: str, commit_hash: str = None, mode: str = "mixed") -> List[TextContent]:
        """Resetea el repositorio a un estado anterior"""
        try:
            result = await self.git_handler.reset(repo_url, mode, commit_hash)
            
            if result.get("success"):
                response_text = f"✅ {result['message']}\n"
                
                response_text += f"🔄 **Modo de reset:** {mode}\n"
                
                if result.get("reset_to"):
                    response_text += f"📍 **Reset a:** {result['reset_to']}\n"
                
                if result.get("files_affected"):
                    response_text += f"📝 **Archivos afectados:** {len(result['files_affected'])}\n"
                    for file in result["files_affected"][:5]:
                        response_text += f"  • {file}\n"
                    if len(result["files_affected"]) > 5:
                        response_text += f"  ... y {len(result['files_affected']) - 5} archivos más\n"
                
                # Explicar qué hace cada modo
                if mode == "soft":
                    response_text += "\n💡 **Soft reset:** Los cambios se mantienen en staging\n"
                elif mode == "mixed":
                    response_text += "\n💡 **Mixed reset:** Los cambios se mantienen pero no en staging\n"
                elif mode == "hard":
                    response_text += "\n⚠️ **Hard reset:** Todos los cambios han sido descartados\n"
                
            else:
                response_text = f"❌ {result['message']}"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando git reset: {str(e)}")]

    async def _git_tag(self, repo_url: str, action: str, tag_name: str = None, message: str = None, commit_hash: str = None) -> List[TextContent]:
        """Gestiona etiquetas del repositorio"""
        try:
            result = await self.git_handler.tag(repo_url, action, tag_name, message, commit_hash)
            
            if result.get("success"):
                response_text = f"✅ {result['message']}\n"
                
                if action == "create":
                    response_text += f"🏷️ **Etiqueta creada:** {tag_name}\n"
                    if result.get("tag_commit"):
                        response_text += f"📍 **En commit:** {result['tag_commit']}\n"
                    if message:
                        response_text += f"📝 **Mensaje:** {message}\n"
                
                elif action == "list":
                    if result.get("tags"):
                        response_text += "🏷️ **Etiquetas disponibles:**\n"
                        for tag in result["tags"]:
                            if isinstance(tag, dict):
                                response_text += f"  • {tag['name']} ({tag['date']}) - {tag['commit'][:8]}\n"
                                if tag.get("message"):
                                    response_text += f"    📝 {tag['message']}\n"
                            else:
                                response_text += f"  • {tag}\n"
                    else:
                        response_text += "🏷️ **No hay etiquetas creadas**\n"
                
                elif action == "delete":
                    response_text += f"🗑️ **Etiqueta eliminada:** {tag_name}\n"
                
                elif action == "push":
                    response_text += f"📤 **Etiqueta subida al remoto:** {tag_name}\n"
                    if result.get("remote_url"):
                        response_text += f"🔗 **Remoto:** {result['remote_url']}\n"
                
            else:
                response_text = f"❌ {result['message']}"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando git tag: {str(e)}")]

    async def _git_remote(self, repo_url: str, action: str, remote_name: str = None, remote_url: str = None) -> List[TextContent]:
        """Gestiona repositorios remotos"""
        try:
            result = await self.git_handler.remote(repo_url, action, remote_name, remote_url)
            
            if result.get("success"):
                response_text = f"✅ {result['message']}\n"
                
                if action == "list":
                    if result.get("remotes"):
                        response_text += "🔗 **Remotos configurados:**\n"
                        for remote in result["remotes"]:
                            if isinstance(remote, dict):
                                response_text += f"  • {remote['name']}: {remote['url']}\n"
                                if remote.get("fetch_url") and remote["fetch_url"] != remote["url"]:
                                    response_text += f"    📥 Fetch: {remote['fetch_url']}\n"
                            else:
                                response_text += f"  • {remote}\n"
                    else:
                        response_text += "🔗 **No hay remotos configurados**\n"
                
                elif action == "add":
                    response_text += f"➕ **Remoto agregado:** {remote_name}\n"
                    response_text += f"🔗 **URL:** {remote_url}\n"
                
                elif action == "remove":
                    response_text += f"🗑️ **Remoto eliminado:** {remote_name}\n"
                
                elif action == "set-url":
                    response_text += f"🔄 **URL actualizada para:** {remote_name}\n"
                    response_text += f"🔗 **Nueva URL:** {remote_url}\n"
                
            else:
                response_text = f"❌ {result['message']}"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando git remote: {str(e)}")]
    
async def main():
    """Función principal del servidor"""
    print("[START] Iniciando MCP Code Manager Server (Working Version)...", file=sys.stderr)
    
    try:
        # Crear instancia del servidor
        server_instance = MCPWorkingServer()
        print("[READY] Servidor configurado, iniciando protocolo MCP...", file=sys.stderr)
        
        # Crear opciones de inicialización correctamente
        # Esto le dice a Claude qué capacidades tiene nuestro servidor
        init_options = server_instance.server.create_initialization_options()
        print(f"[CAPABILITIES] Servidor con capacidades: {init_options.capabilities}", file=sys.stderr)
        
        # Iniciar servidor con stdio
        async with stdio_server() as (read_stream, write_stream):
            print("[RUNNING] Servidor MCP activo y listo para recibir comandos", file=sys.stderr)
            
            # Ejecutar servidor con las capacidades correctas
            await server_instance.server.run(
                read_stream,
                write_stream,
                init_options
            )
            
    except KeyboardInterrupt:
        print("[STOP] Servidor detenido por el usuario", file=sys.stderr)
    except Exception as e:
        print(f"[FATAL] Error en servidor MCP: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

if __name__ == "__main__":
    try:
        # Configurar event loop para Windows
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Ejecutar servidor
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("[EXIT] Salida limpia", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"[FATAL] Error fatal: {str(e)}", file=sys.stderr)
        sys.exit(1)
