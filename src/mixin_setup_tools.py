import sys
import time
from typing import Any, Dict, List
from mcp import Tool
from mcp.types import Tool
from mcp.types import TextContent

from handlers.code_handler import CodeHandler

class SetupToolsAdapterMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code_handler = CodeHandler()

    def _setup_tools(self):
        """Método legacy - las tools ahora se registran automáticamente via decoradores"""
        # Las tools ahora se registran automáticamente con los decoradores @server.list_tools() y @server.call_tool()
        # No necesitamos llamar manualmente a add_tool
        self._setup_tools_decorators()

    # Métodos que delegan en CodeHandler para las tools de análisis C#
    async def _find_class(self, repo_url, class_name, search_type="direct"):
        try:
            result = await self.code_handler.find_class(repo_url, class_name, search_type)
            from mcp.types import TextContent
            import json
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        except Exception as e:
            from mcp.types import TextContent
            return [TextContent(type="text", text=f"❌ Error en find_class: {str(e)}")]

    async def _find_elements(self, repo_url, element_type, element_name):
        try:
            result = await self.code_handler.find_elements(repo_url, element_type, element_name)
            from mcp.types import TextContent
            import json
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        except Exception as e:
            from mcp.types import TextContent
            return [TextContent(type="text", text=f"❌ Error en find_elements: {str(e)}")]

    async def _get_solution_structure(self, repo_url):
        try:
            result = await self.code_handler.get_solution_structure(repo_url)
            from mcp.types import TextContent
            import json
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        except Exception as e:
            from mcp.types import TextContent
            return [TextContent(type="text", text=f"❌ Error en get_solution_structure: {str(e)}")]

    async def _get_cs_file_content(self, repo_url, file_path):
        try:
            result = await self.code_handler.get_file_content(repo_url, file_path)
            from mcp.types import TextContent
            import json
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        except Exception as e:
            from mcp.types import TextContent
            return [TextContent(type="text", text=f"❌ Error en get_cs_file_content: {str(e)}")]

    def _setup_tools_decorators(self):
        """Configura las herramientas del servidor usando decoradores"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """Lista todas las herramientas disponibles"""
            return [
                Tool(
                    name="list_repository_files",
                    description="Lista todos los archivos del repositorio con filtros avanzados (usa FileHandler)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {"type": "string", "description": "URL del repositorio"},
                            "file_pattern": {"type": "string", "description": "Patrón de archivos (opcional)"},
                            "include_directories": {"type": "boolean", "description": "Incluir directorios", "default": False},
                            "exclude_patterns": {"type": "array", "items": {"type": "string"}, "description": "Patrones a excluir (opcional)"},
                            "max_depth": {"type": "integer", "description": "Profundidad máxima", "default": 10}
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="check_repository_permissions",
                    description="Verifica permisos de lectura/escritura en el repositorio o ruta específica (usa FileHandler)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {"type": "string", "description": "URL del repositorio"},
                            "target_path": {"type": "string", "description": "Ruta relativa a verificar (opcional)"}
                        },
                        "required": ["repo_url"]
                    }
                ),
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
                    name="git_clone",
                    description="Clona un repositorio Git en una carpeta destino",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {"type": "string", "description": "URL del repositorio Git"},
                            "dest_path": {"type": "string", "description": "Carpeta destino (opcional)"},
                            "force": {"type": "boolean", "description": "Forzar si ya existe", "default": False}
                        },
                        "required": ["repo_url"]
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
                    description="Obtiene el contenido de un archivo (soporta rutas absolutas y relativas)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Ruta del archivo (absoluta o relativa)"
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
                    description="Crea una nueva carpeta/directorio (soporta rutas absolutas y relativas)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "Ruta de la carpeta a crear (absoluta o relativa)"
                            }
                        },
                        "required": ["directory_path"]
                    }
                ),
                Tool(
                    name="rename_directory",
                    description="Renombra una carpeta/directorio existente (soporta rutas absolutas y relativas)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "old_path": {
                                "type": "string",
                                "description": "Ruta actual de la carpeta (absoluta o relativa)"
                            },
                            "new_path": {
                                "type": "string",
                                "description": "Nueva ruta/nombre de la carpeta (absoluta o relativa)"
                            }
                        },
                        "required": ["old_path", "new_path"]
                    }
                ),
                Tool(
                    name="delete_directory",
                    description="Elimina una carpeta/directorio enviándola a la papelera (soporta rutas absolutas y relativas)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "Ruta de la carpeta a eliminar (absoluta o relativa)"
                            }
                        },
                        "required": ["directory_path"]
                    }
                ),
                Tool(
                    name="set_file_content",
                    description="Crea un archivo nuevo o modifica el contenido de un archivo existente (soporta rutas absolutas y relativas)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Ruta del archivo a crear o modificar (absoluta o relativa)"
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

                if name == "list_repository_files":
                    repo_url = arguments.get("repo_url")
                    file_pattern = arguments.get("file_pattern")
                    include_directories = arguments.get("include_directories", False)
                    exclude_patterns = arguments.get("exclude_patterns")
                    max_depth = arguments.get("max_depth", 10)
                    return await self._list_repository_files(repo_url, file_pattern, include_directories, exclude_patterns, max_depth)

                elif name == "check_repository_permissions":
                    repo_url = arguments.get("repo_url")
                    target_path = arguments.get("target_path")
                    return await self._check_repository_permissions(repo_url, target_path)

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
                
                elif name == "git_clone":
                    repo_url = arguments.get("repo_url")
                    dest_path = arguments.get("dest_path")
                    force = arguments.get("force", False)
                    result = await self._git_clone(repo_url, dest_path, force)
                    execution_time = time.time() - start_time
                    
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
                    # Use empty string as repo_url for local file operations
                    result = await self._get_file_content("", file_path)
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
                    # Use empty string as repo_url for local directory operations
                    result = await self._list_directory("", directory_path)
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
                    # Use empty string as repo_url for local directory operations
                    result = await self._create_directory("", directory_path)
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
                    # Use empty string as repo_url for local directory operations
                    result = await self._rename_directory("", old_path, new_path)
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
                    # Use empty string as repo_url for local directory operations
                    result = await self._delete_directory("", directory_path)
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
                    # Use empty string as repo_url for local file operations
                    result = await self._set_file_content_enhanced("", file_path, content, create_backup)
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
                    # Use empty string as repo_url for local file operations
                    result = await self._rename_file("", source_path, dest_path)
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
                    # Use empty string as repo_url for local file operations
                    result = await self._delete_file("", file_path)
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
                    try:
                        repo_url = arguments.get("repo_url", "")
                        project_name = arguments.get("project_name", "")
                        template = arguments.get("template", "console")
                        base_path = arguments.get("base_path", "")
                        framework = arguments.get("framework")
                        result = await self._dotnet_create_project(repo_url, project_name, template, base_path, framework)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en dotnet_create_project: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "dotnet_add_project_to_solution":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        solution_file = arguments.get("solution_file", "")
                        project_file = arguments.get("project_file", "")
                        result = await self._dotnet_add_project_to_solution(repo_url, solution_file, project_file)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en dotnet_add_project_to_solution: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "dotnet_list_solution_projects":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        solution_file = arguments.get("solution_file", "")
                        result = await self._dotnet_list_solution_projects(repo_url, solution_file)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en dotnet_list_solution_projects: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "dotnet_add_package":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        project_file = arguments.get("project_file", "")
                        package_name = arguments.get("package_name", "")
                        version = arguments.get("version")
                        result = await self._dotnet_add_package(repo_url, project_file, package_name, version)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en dotnet_add_package: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "dotnet_build_solution":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        solution_file = arguments.get("solution_file")
                        configuration = arguments.get("configuration", "Debug")
                        result = await self._dotnet_build_solution(repo_url, solution_file, configuration)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en dotnet_build_solution: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "dotnet_build_project":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        project_file = arguments.get("project_file", "")
                        configuration = arguments.get("configuration", "Debug")
                        result = await self._dotnet_build_project(repo_url, project_file, configuration)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en dotnet_build_project: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "dotnet_restore_packages":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        project_path = arguments.get("project_path", "")
                        result = await self._dotnet_restore_packages(repo_url, project_path)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en dotnet_restore_packages: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "dotnet_test_all":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        test_path = arguments.get("test_path", "")
                        collect_coverage = arguments.get("collect_coverage", False)
                        result = await self._dotnet_test_all(repo_url, test_path, collect_coverage)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en dotnet_test_all: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "dotnet_test_filter":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        filter_expression = arguments.get("filter_expression", "")
                        test_path = arguments.get("test_path", "")
                        collect_coverage = arguments.get("collect_coverage", False)
                        result = await self._dotnet_test_filter(repo_url, filter_expression, test_path, collect_coverage)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en dotnet_test_filter: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "dotnet_get_test_filters":
                    try:
                        result = await self._dotnet_get_test_filters()
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en dotnet_get_test_filters: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                # === Handlers de Python ===
                elif name == "python_check_environment":
                    try:
                        repo_url = arguments.get("repo_url")
                        result = await self._python_check_environment(repo_url)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en python_check_environment: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "python_create_venv":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        venv_name = arguments.get("venv_name", "venv")
                        base_path = arguments.get("base_path", "")
                        result = await self._python_create_venv(repo_url, venv_name, base_path)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en python_create_venv: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "python_install_packages":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        packages = arguments.get("packages", [])
                        venv_name = arguments.get("venv_name")
                        base_path = arguments.get("base_path", "")
                        result = await self._python_install_packages(repo_url, packages, venv_name, base_path)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en python_install_packages: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "python_install_requirements":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        requirements_file = arguments.get("requirements_file", "requirements.txt")
                        venv_name = arguments.get("venv_name")
                        base_path = arguments.get("base_path", "")
                        result = await self._python_install_requirements(repo_url, requirements_file, venv_name, base_path)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en python_install_requirements: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                    return await self._python_install_requirements(repo_url, requirements_file, venv_name, base_path)
                
                elif name == "python_freeze":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        venv_name = arguments.get("venv_name")
                        base_path = arguments.get("base_path", "")
                        result = await self._python_freeze(repo_url, venv_name, base_path)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en python_freeze: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "python_run_pytest":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        test_path = arguments.get("test_path", ".")
                        venv_name = arguments.get("venv_name")
                        test_pattern = arguments.get("test_pattern")
                        collect_coverage = arguments.get("collect_coverage", False)
                        verbose = arguments.get("verbose", False)
                        result = await self._python_run_pytest(repo_url, test_path, venv_name, test_pattern, collect_coverage, verbose)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en python_run_pytest: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "python_run_unittest":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        test_path = arguments.get("test_path", ".")
                        venv_name = arguments.get("venv_name")
                        test_pattern = arguments.get("test_pattern")
                        verbose = arguments.get("verbose", False)
                        result = await self._python_run_unittest(repo_url, test_path, venv_name, test_pattern, verbose)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en python_run_unittest: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "python_lint":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        linter = arguments.get("linter", "flake8")
                        venv_name = arguments.get("venv_name")
                        base_path = arguments.get("base_path", "")
                        result = await self._python_lint(repo_url, linter, venv_name, base_path)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en python_lint: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "python_format":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        formatter = arguments.get("formatter", "black")
                        venv_name = arguments.get("venv_name")
                        base_path = arguments.get("base_path", "")
                        result = await self._python_format(repo_url, formatter, venv_name, base_path)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en python_format: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "python_detect_project":
                    try:
                        repo_url = arguments.get("repo_url", "")
                        result = await self._python_detect_project(repo_url)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error en python_detect_project: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "python_get_test_patterns":
                    try:
                        result = await self._python_get_test_patterns()
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error obteniendo patrones de test: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "python_get_tools_info":
                    try:
                        result = await self._python_get_tools_info()
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error obteniendo información de herramientas: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "get_logs_stats":
                    try:
                        hours = arguments.get("hours", 24)
                        result = await self._get_logs_stats(hours)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error obteniendo estadísticas de logs: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "search_logs":
                    try:
                        query = arguments.get("query", "")
                        max_results = arguments.get("max_results", 50)
                        result = await self._search_logs(query, max_results)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error buscando en logs: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "get_recent_errors":
                    try:
                        hours = arguments.get("hours", 24)
                        result = await self._get_recent_errors(hours)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error obteniendo errores recientes: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
                elif name == "export_log_summary":
                    try:
                        hours = arguments.get("hours", 24)
                        result = await self._export_log_summary(hours)
                        execution_time = time.time() - start_time
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=True,
                            result=result,
                            execution_time=execution_time
                        )
                        
                        return result
                    except Exception as e:
                        execution_time = time.time() - start_time
                        result = [TextContent(type="text", text=f"❌ Error exportando resumen de logs: {str(e)}")]
                        
                        self.logger.log_tool_execution(
                            tool_name=name,
                            arguments=arguments,
                            success=False,
                            error=str(e),
                            execution_time=execution_time
                        )
                        
                        return result
                
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
