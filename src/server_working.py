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
    from utils.exceptions import FileOperationError, CodeAnalysisError
except ImportError as e:
    print(f"Error: Módulos de handlers no disponibles - {e}", file=sys.stderr)
    sys.exit(1)

class MCPWorkingServer:
    """Servidor MCP que funciona correctamente"""
    
    def __init__(self):
        self.server = Server("mcp-code-manager")
        self.file_handler = FileHandler()
        self.code_handler = CodeHandler()
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
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Ejecuta una herramienta específica"""
            try:
                print(f"[TOOL] Ejecutando: {name} con argumentos: {arguments}", file=sys.stderr)
                
                if name == "ping":
                    return [TextContent(type="text", text="pong")]
                
                elif name == "echo":
                    message = arguments.get("message", "")
                    return [TextContent(type="text", text=f"Echo: {message}")]
                
                elif name == "get_file_content":
                    file_path = arguments.get("file_path", "")
                    return await self._get_file_content(file_path)
                
                elif name == "list_directory":
                    directory_path = arguments.get("directory_path", ".")
                    return await self._list_directory(directory_path)
                
                elif name == "git_status":
                    repository_path = arguments.get("repository_path", ".")
                    return await self._git_status(repository_path)
                
                elif name == "create_directory":
                    directory_path = arguments.get("directory_path", "")
                    return await self._create_directory(directory_path)
                
                elif name == "rename_directory":
                    old_path = arguments.get("old_path", "")
                    new_path = arguments.get("new_path", "")
                    return await self._rename_directory(old_path, new_path)
                
                elif name == "delete_directory":
                    directory_path = arguments.get("directory_path", "")
                    return await self._delete_directory(directory_path)
                
                elif name == "set_file_content":
                    file_path = arguments.get("file_path", "")
                    content = arguments.get("content", "")
                    create_backup = arguments.get("create_backup", True)
                    return await self._set_file_content_enhanced(file_path, content, create_backup)
                
                elif name == "rename_file":
                    source_path = arguments.get("source_path", "")
                    dest_path = arguments.get("dest_path", "")
                    return await self._rename_file(source_path, dest_path)
                
                elif name == "delete_file":
                    file_path = arguments.get("file_path", "")
                    return await self._delete_file(file_path)
                
                elif name == "copy_file":
                    source_path = arguments.get("source_path", "")
                    dest_path = arguments.get("dest_path", "")
                    return await self._copy_file(source_path, dest_path)
                
                elif name == "check_permissions":
                    target_path = arguments.get("target_path", ".")
                    return await self._check_permissions(target_path)
                
                elif name == "list_files":
                    directory_path = arguments.get("directory_path", ".")
                    file_pattern = arguments.get("file_pattern")
                    include_directories = arguments.get("include_directories", False)
                    max_depth = arguments.get("max_depth", 1)
                    return await self._list_files(directory_path, file_pattern, include_directories, max_depth)
                
                # Herramientas de análisis de código C#
                elif name == "find_class":
                    repo_url = arguments.get("repo_url", "")
                    class_name = arguments.get("class_name", "")
                    search_type = arguments.get("search_type", "direct")
                    return await self._find_class(repo_url, class_name, search_type)
                
                elif name == "get_cs_file_content":
                    repo_url = arguments.get("repo_url", "")
                    file_path = arguments.get("file_path", "")
                    return await self._get_cs_file_content(repo_url, file_path)
                
                elif name == "find_elements":
                    repo_url = arguments.get("repo_url", "")
                    element_type = arguments.get("element_type", "")
                    element_name = arguments.get("element_name", "")
                    return await self._find_elements(repo_url, element_type, element_name)
                
                elif name == "get_solution_structure":
                    repo_url = arguments.get("repo_url", "")
                    return await self._get_solution_structure(repo_url)
                
                else:
                    return [TextContent(
                        type="text", 
                        text=f"Error: Herramienta desconocida '{name}'"
                    )]
                    
            except Exception as e:
                error_msg = f"Error ejecutando herramienta '{name}': {str(e)}"
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
        """Obtiene el estado del repositorio Git"""
        try:
            if not repository_path:
                repository_path = "."
            
            path = Path(repository_path)
            if not path.exists():
                return [TextContent(type="text", text=f"Error: El directorio '{repository_path}' no existe")]
            
            # Verificar si es un repositorio Git
            git_dir = path / ".git"
            if not git_dir.exists():
                return [TextContent(type="text", text=f"Error: '{repository_path}' no es un repositorio Git")]
            
            # Ejecutar git status
            original_cwd = os.getcwd()
            try:
                os.chdir(repository_path)
                
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    timeout=30
                )
                
                if result.returncode == 0:
                    if result.stdout.strip():
                        status_lines = result.stdout.strip().split('\n')
                        formatted_status = []
                        for line in status_lines:
                            if line.startswith(' M '):
                                formatted_status.append(f"🔸 Modificado: {line[3:]}")
                            elif line.startswith('M  '):
                                formatted_status.append(f"🔹 Staged: {line[3:]}")
                            elif line.startswith('?? '):
                                formatted_status.append(f"❓ No rastreado: {line[3:]}")
                            elif line.startswith(' D '):
                                formatted_status.append(f"🗑️ Eliminado: {line[3:]}")
                            elif line.startswith('A  '):
                                formatted_status.append(f"➕ Agregado: {line[3:]}")
                            else:
                                formatted_status.append(f"📝 {line}")
                        
                        content = f"Estado Git en '{repository_path}':\n\n" + "\n".join(formatted_status)
                    else:
                        content = f"✅ Repositorio Git limpio en '{repository_path}' (sin cambios)"
                else:
                    content = f"❌ Error ejecutando git status: {result.stderr}"
                
                return [TextContent(type="text", text=content)]
                
            finally:
                os.chdir(original_cwd)
                
        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text="❌ Timeout ejecutando git status")]
        except FileNotFoundError:
            return [TextContent(type="text", text="❌ Git no está instalado o no está en PATH")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando git status: {str(e)}")]
    
    async def _create_directory(self, directory_path: str) -> List[TextContent]:
        """Crea una nueva carpeta/directorio"""
        try:
            if not directory_path:
                return [TextContent(type="text", text="❌ Error: Ruta de directorio no especificada")]
            
            path = Path(directory_path)
            
            # Verificar si ya existe
            if path.exists():
                if path.is_dir():
                    return [TextContent(type="text", text=f"⚠️ La carpeta '{directory_path}' ya existe")]
                else:
                    return [TextContent(type="text", text=f"❌ Error: '{directory_path}' existe pero no es una carpeta")]
            
            # Crear directorio y todos los directorios padre necesarios
            path.mkdir(parents=True, exist_ok=True)
            
            return [TextContent(type="text", text=f"✅ Carpeta creada exitosamente: '{directory_path}'")]
            
        except PermissionError:
            return [TextContent(type="text", text=f"❌ Error: Sin permisos para crear la carpeta '{directory_path}'")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error creando carpeta: {str(e)}")]
    
    async def _rename_directory(self, old_path: str, new_path: str) -> List[TextContent]:
        """Renombra una carpeta/directorio"""
        try:
            if not old_path or not new_path:
                return [TextContent(type="text", text="❌ Error: Rutas de origen y destino requeridas")]
            
            old_dir = Path(old_path)
            new_dir = Path(new_path)
            
            # Verificar que el directorio origen existe
            if not old_dir.exists():
                return [TextContent(type="text", text=f"❌ Error: La carpeta origen '{old_path}' no existe")]
            
            if not old_dir.is_dir():
                return [TextContent(type="text", text=f"❌ Error: '{old_path}' no es una carpeta")]
            
            # Verificar que el destino no existe
            if new_dir.exists():
                return [TextContent(type="text", text=f"❌ Error: El destino '{new_path}' ya existe")]
            
            # Crear directorio padre del destino si no existe
            new_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # Renombrar/mover directorio
            old_dir.rename(new_dir)
            
            return [TextContent(type="text", text=f"✅ Carpeta renombrada exitosamente: '{old_path}' → '{new_path}'")]
            
        except PermissionError:
            return [TextContent(type="text", text=f"❌ Error: Sin permisos para renombrar la carpeta")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error renombrando carpeta: {str(e)}")]
    
    async def _delete_directory(self, directory_path: str) -> List[TextContent]:
        """Elimina una carpeta/directorio enviándola a la papelera"""
        try:
            if not directory_path:
                return [TextContent(type="text", text="❌ Error: Ruta de directorio no especificada")]
            
            path = Path(directory_path)
            
            # Verificar que existe
            if not path.exists():
                return [TextContent(type="text", text=f"❌ Error: La carpeta '{directory_path}' no existe")]
            
            if not path.is_dir():
                return [TextContent(type="text", text=f"❌ Error: '{directory_path}' no es una carpeta")]
            
            # Intentar enviar a papelera si está disponible en Windows
            if sys.platform == "win32" and winshell is not None:
                try:
                    winshell.delete_file(str(path), no_confirm=True, silent=True)
                    return [TextContent(type="text", text=f"🗑️ Carpeta enviada a la papelera: '{directory_path}'")]
                except Exception as e:
                    print(f"[WARNING] Error enviando a papelera, usando eliminación permanente: {e}", file=sys.stderr)
            
            # Fallback: eliminación permanente
            import stat
            
            # Función para manejar archivos de solo lectura en Windows
            def handle_remove_readonly(func, path, exc):
                if os.path.exists(path):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
            
            shutil.rmtree(str(path), onerror=handle_remove_readonly)
            
            if sys.platform == "win32" and winshell is None:
                return [TextContent(type="text", text=f"🗑️ Carpeta eliminada permanentemente: '{directory_path}' (winshell no disponible para papelera)")]
            else:
                return [TextContent(type="text", text=f"🗑️ Carpeta eliminada permanentemente: '{directory_path}'")]
            
        except PermissionError:
            return [TextContent(type="text", text=f"❌ Error: Sin permisos para eliminar la carpeta '{directory_path}'")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error eliminando carpeta: {str(e)}")]

    async def _set_file_content_enhanced(self, file_path: str, content: str, create_backup: bool = True) -> List[TextContent]:
        """Crea un archivo nuevo o modifica el contenido usando FileHandler"""
        try:
            if not file_path:
                return [TextContent(type="text", text="❌ Error: Ruta de archivo no especificada")]
            
            if content is None:
                content = ""
            
            path = Path(file_path)
            file_exists = path.exists() and path.is_file()
            
            # Crear backup manual si se solicita y el archivo existe
            backup_created = False
            backup_path = None
            if file_exists and create_backup:
                try:
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = path.parent / f"{path.stem}.backup_{timestamp}{path.suffix}"
                    shutil.copy2(str(path), str(backup_path))
                    backup_created = True
                    print(f"[BACKUP] Creado backup en: {backup_path}", file=sys.stderr)
                except Exception as e:
                    print(f"[WARNING] No se pudo crear backup: {e}", file=sys.stderr)
            
            # Usar el directorio current_dir como repositorio ficticio
            current_dir = Path.cwd()
            fake_repo_url = f"file://{current_dir}"
            
            try:
                if file_exists:
                    # Actualizar archivo existente
                    result = await self.file_handler.update_file(fake_repo_url, file_path, content)
                else:
                    # Crear archivo nuevo
                    result = await self.file_handler.create_file(fake_repo_url, file_path, content)
                
                # Preparar respuesta
                file_info = result.get("file_info", {})
                response_text = f"✅ {result.get('message', 'Operación completada')}\n"
                response_text += f"📄 Tamaño: {file_info.get('size', 0)} bytes, Líneas: {file_info.get('lines', 0)}"
                
                if backup_created:
                    response_text += f"\n💾 Backup creado: '{backup_path}'"
                elif file_exists and create_backup:
                    response_text += f"\n⚠️ Sin backup (no se pudo crear)"
                
                return [TextContent(type="text", text=response_text)]
                
            except FileOperationError as e:
                return [TextContent(type="text", text=f"❌ {str(e)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error escribiendo archivo: {str(e)}")]

    async def _rename_file(self, source_path: str, dest_path: str) -> List[TextContent]:
        """Renombra o mueve un archivo usando FileHandler"""
        try:
            if not source_path or not dest_path:
                return [TextContent(type="text", text="❌ Error: Rutas origen y destino requeridas")]
            
            # Usar el directorio current_dir como repositorio ficticio
            current_dir = Path.cwd()
            fake_repo_url = f"file://{current_dir}"
            
            try:
                result = await self.file_handler.move_file(fake_repo_url, source_path, dest_path)
                
                return [TextContent(type="text", text=f"✅ {result.get('message', 'Archivo renombrado exitosamente')}")]
                
            except FileOperationError as e:
                return [TextContent(type="text", text=f"❌ {str(e)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error renombrando archivo: {str(e)}")]

    async def _delete_file(self, file_path: str) -> List[TextContent]:
        """Elimina un archivo enviándolo a la papelera"""
        try:
            if not file_path:
                return [TextContent(type="text", text="❌ Error: Ruta de archivo no especificada")]
            
            path = Path(file_path)
            
            # Verificar que existe y es un archivo
            if not path.exists():
                return [TextContent(type="text", text=f"❌ Error: El archivo '{file_path}' no existe")]
            
            if not path.is_file():
                return [TextContent(type="text", text=f"❌ Error: '{file_path}' no es un archivo")]
            
            # Intentar enviar a papelera si está disponible en Windows
            if sys.platform == "win32" and winshell is not None:
                try:
                    winshell.delete_file(str(path), no_confirm=True, silent=True)
                    return [TextContent(type="text", text=f"🗑️ Archivo enviado a la papelera: '{file_path}'")]
                except Exception as e:
                    print(f"[WARNING] Error enviando a papelera, usando eliminación permanente: {e}", file=sys.stderr)
            
            # Fallback: eliminación permanente
            try:
                path.unlink()
                if sys.platform == "win32" and winshell is None:
                    return [TextContent(type="text", text=f"🗑️ Archivo eliminado permanentemente: '{file_path}' (winshell no disponible)")]
                else:
                    return [TextContent(type="text", text=f"🗑️ Archivo eliminado permanentemente: '{file_path}'")]
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Error eliminando archivo: {str(e)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error eliminando archivo: {str(e)}")]

    async def _copy_file(self, source_path: str, dest_path: str) -> List[TextContent]:
        """Copia un archivo a otra ubicación usando FileHandler"""
        try:
            if not source_path or not dest_path:
                return [TextContent(type="text", text="❌ Error: Rutas origen y destino requeridas")]
            
            # Usar el directorio current_dir como repositorio ficticio
            current_dir = Path.cwd()
            fake_repo_url = f"file://{current_dir}"
            
            try:
                result = await self.file_handler.copy_file(fake_repo_url, source_path, dest_path)
                
                return [TextContent(type="text", text=f"✅ {result.get('message', 'Archivo copiado exitosamente')}")]
                
            except FileOperationError as e:
                return [TextContent(type="text", text=f"❌ {str(e)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error copiando archivo: {str(e)}")]

    async def _check_permissions(self, target_path: str) -> List[TextContent]:
        """Verifica permisos CRUD usando FileHandler"""
        try:
            if not target_path:
                target_path = "."
            
            # Usar el directorio current_dir como repositorio ficticio
            current_dir = Path.cwd()
            fake_repo_url = f"file://{current_dir}"
            
            try:
                # Si target_path es relativo, hacerlo relativo al directorio de trabajo
                if not os.path.isabs(target_path):
                    check_path = target_path
                else:
                    # Convertir ruta absoluta a relativa si está dentro del directorio actual
                    abs_target = Path(target_path).resolve()
                    abs_current = Path.cwd().resolve()
                    try:
                        check_path = str(abs_target.relative_to(abs_current))
                    except ValueError:
                        check_path = target_path
                
                result = await self.file_handler.check_repository_permissions(fake_repo_url, check_path)
                
                # Formatear respuesta
                permissions = result.get("permissions", {})
                summary = result.get("summary", {})
                git_info = result.get("git", {})
                
                response_text = f"🔐 Permisos para '{result.get('path', target_path)}':\n\n"
                
                # Estado básico
                if result.get("exists"):
                    if result.get("is_file"):
                        response_text += "📄 Tipo: Archivo\n"
                    elif result.get("is_directory"):
                        response_text += "📁 Tipo: Directorio\n"
                else:
                    response_text += "❓ El elemento no existe\n"
                
                # Permisos básicos
                response_text += "\n🔍 Permisos básicos:\n"
                response_text += f"  • Lectura: {'✅' if permissions.get('readable') else '❌'}\n"
                response_text += f"  • Escritura: {'✅' if permissions.get('writable') else '❌'}\n"
                response_text += f"  • Ejecución: {'✅' if permissions.get('executable') else '❌'}\n"
                
                # Permisos de archivos
                response_text += "\n📁 Permisos de archivos:\n"
                response_text += f"  • Crear archivos: {'✅' if permissions.get('can_create_files') else '❌'}\n"
                response_text += f"  • Eliminar archivos: {'✅' if permissions.get('can_delete_files') else '❌'}\n"
                response_text += f"  • Crear directorios: {'✅' if permissions.get('can_create_directories') else '❌'}\n"
                
                # Resumen de capacidades
                response_text += "\n📋 Capacidades CRUD:\n"
                response_text += f"  • Leer archivos: {'✅' if summary.get('can_read_files') else '❌'}\n"
                response_text += f"  • Modificar archivos: {'✅' if summary.get('can_modify_files') else '❌'}\n"
                response_text += f"  • Crear archivos nuevos: {'✅' if summary.get('can_create_new_files') else '❌'}\n"
                response_text += f"  • Eliminar archivos: {'✅' if summary.get('can_delete_existing_files') else '❌'}\n"
                
                # Estado general
                if summary.get('fully_functional'):
                    response_text += "\n🎉 Estado: Totalmente funcional para operaciones CRUD"
                else:
                    response_text += "\n⚠️ Estado: Limitaciones en operaciones CRUD"
                
                # Información Git
                if git_info.get("is_git_repository"):
                    response_text += f"\n\n🔀 Git: Repositorio válido"
                    response_text += f"\n  • Lectura Git: {'✅' if git_info.get('can_read_git') else '❌'}"
                    response_text += f"\n  • Escritura Git: {'✅' if git_info.get('can_write_git') else '❌'}"
                
                # Errores si los hay
                errors = result.get("errors", [])
                if errors:
                    response_text += "\n\n⚠️ Advertencias:\n"
                    for error in errors[:3]:  # Mostrar máximo 3 errores
                        response_text += f"  • {error}\n"
                
                return [TextContent(type="text", text=response_text)]
                
            except FileOperationError as e:
                return [TextContent(type="text", text=f"❌ {str(e)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error verificando permisos: {str(e)}")]

    async def _list_files(self, directory_path: str, file_pattern: str = None, include_directories: bool = False, max_depth: int = 1) -> List[TextContent]:
        """Lista archivos con filtros usando FileHandler"""
        try:
            if not directory_path:
                directory_path = "."
            
            # Usar el directorio current_dir como repositorio ficticio
            current_dir = Path.cwd()
            fake_repo_url = f"file://{current_dir}"
            
            try:
                result = await self.file_handler.list_repository_files(
                    fake_repo_url,
                    file_pattern=file_pattern,
                    include_directories=include_directories,
                    max_depth=max_depth
                )
                
                # Formatear respuesta
                files = result.get("files", [])
                total_files = result.get("total_files", 0)
                total_dirs = result.get("total_directories", 0)
                total_size = result.get("total_size_formatted", "0 B")
                extensions_stats = result.get("extensions_stats", {})
                
                response_text = f"📁 Contenido de '{directory_path}':\n\n"
                response_text += f"📊 Resumen: {total_files} archivos, {total_dirs} directorios, {total_size}\n"
                
                if file_pattern:
                    response_text += f"🔍 Filtro: {file_pattern}\n"
                
                response_text += f"📏 Profundidad: {max_depth if max_depth > 0 else 'Ilimitada'}\n\n"
                
                # Mostrar archivos/directorios
                if files:
                    response_text += "📋 Elementos encontrados:\n"
                    for file_info in files[:50]:  # Limitar a 50 elementos
                        if file_info['type'] == 'directory':
                            response_text += f"📁 {file_info['path']}/\n"
                        else:
                            size_info = file_info.get('size_formatted', '')
                            response_text += f"📄 {file_info['path']} ({size_info})\n"
                    
                    if len(files) > 50:
                        response_text += f"\n... y {len(files) - 50} elementos más\n"
                else:
                    response_text += "📭 No se encontraron elementos\n"
                
                # Estadísticas de extensiones
                if extensions_stats:
                    response_text += "\n📈 Extensiones más comunes:\n"
                    sorted_exts = sorted(extensions_stats.items(), key=lambda x: x[1]['count'], reverse=True)
                    for ext, stats in sorted_exts[:5]:
                        ext_display = ext if ext != 'sin_extension' else '(sin extensión)'
                        response_text += f"  • {ext_display}: {stats['count']} archivos\n"
                
                return [TextContent(type="text", text=response_text)]
                
            except FileOperationError as e:
                return [TextContent(type="text", text=f"❌ {str(e)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error listando archivos: {str(e)}")]
    
    # === Métodos auxiliares para análisis de código C# ===
    
    async def _find_class(self, repo_url: str, class_name: str, search_type: str = "direct") -> List[TextContent]:
        """Localiza una clase específica en el repositorio C#"""
        try:
            if not repo_url or not class_name:
                return [TextContent(type="text", text="❌ Error: URL del repositorio y nombre de clase requeridos")]
            
            result = await self.code_handler.find_class(repo_url, class_name, search_type)
            
            response_text = f"🔍 Búsqueda de clase '{class_name}' (método: {search_type})\n\n"
            response_text += f"✅ Clase encontrada: {result['class_name']}\n"
            response_text += f"📄 Archivo: {result['file_path']}\n"
            response_text += f"🔍 Método: {result['search_type']}\n\n"
            
            # Información del análisis si está disponible
            analysis = result.get('analysis')
            if analysis:
                response_text += "📊 Análisis del archivo:\n"
                response_text += f"  • Namespace: {analysis.get('namespace', 'N/A')}\n"
                response_text += f"  • Líneas: {analysis.get('lines', 0)}\n"
                response_text += f"  • Elementos: {len(analysis.get('elements', []))}\n"
                response_text += f"  • Métodos: {len(analysis.get('methods', []))}\n"
                response_text += f"  • Propiedades: {len(analysis.get('properties', []))}\n"
            
            return [TextContent(type="text", text=response_text)]
            
        except CodeAnalysisError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error buscando clase: {str(e)}")]
    
    async def _get_cs_file_content(self, repo_url: str, file_path: str) -> List[TextContent]:
        """Obtiene contenido de archivo C# con análisis"""
        try:
            if not repo_url or not file_path:
                return [TextContent(type="text", text="❌ Error: URL del repositorio y ruta del archivo requeridos")]
            
            result = await self.code_handler.get_file_content(repo_url, file_path)
            
            response_text = f"📄 Archivo: {result['file_path']}\n\n"
            response_text += f"📊 Información básica:\n"
            response_text += f"  • Tamaño: {result['size']} bytes\n"
            response_text += f"  • Líneas: {result['lines']}\n"
            response_text += f"  • Encoding: {result['encoding']}\n\n"
            
            # Información del análisis si es C#
            analysis = result.get('analysis')
            if analysis:
                response_text += "🔍 Análisis de código C#:\n"
                response_text += f"  • Namespace: {analysis.get('namespace', 'N/A')}\n"
                response_text += f"  • Elementos: {len(analysis.get('elements', []))}\n"
                response_text += f"  • Métodos: {len(analysis.get('methods', []))}\n"
                response_text += f"  • Propiedades: {len(analysis.get('properties', []))}\n\n"
                
                # Listar elementos encontrados
                elements = analysis.get('elements', [])
                if elements:
                    response_text += "📋 Elementos encontrados:\n"
                    for element in elements[:10]:  # Mostrar máximo 10
                        response_text += f"  • {element['type']}: {element['name']}\n"
                    if len(elements) > 10:
                        response_text += f"  ... y {len(elements) - 10} elementos más\n"
            
            response_text += f"\n📝 Contenido del archivo:\n\n{result['content']}"
            
            return [TextContent(type="text", text=response_text)]
            
        except FileOperationError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error obteniendo contenido: {str(e)}")]
    
    async def _find_elements(self, repo_url: str, element_type: str, element_name: str) -> List[TextContent]:
        """Busca elementos específicos en el repositorio C#"""
        try:
            if not repo_url or not element_type or not element_name:
                return [TextContent(type="text", text="❌ Error: URL del repositorio, tipo y nombre de elemento requeridos")]
            
            results = await self.code_handler.find_elements(repo_url, element_type, element_name)
            
            response_text = f"🔍 Búsqueda de {element_type}s que contengan '{element_name}'\n\n"
            
            if not results:
                response_text += "❌ No se encontraron elementos coincidentes"
                return [TextContent(type="text", text=response_text)]
            
            response_text += f"✅ Encontrados {len(results)} elemento(s):\n\n"
            
            for i, result in enumerate(results, 1):
                response_text += f"{i}. 📋 {result['element_name']}\n"
                response_text += f"   • Tipo: {result['element_type']}\n"
                response_text += f"   • Archivo: {result['file_path']}\n"
                if result.get('namespace'):
                    response_text += f"   • Namespace: {result['namespace']}\n"
                if result.get('line_number'):
                    response_text += f"   • Línea: {result['line_number']}\n"
                if result.get('modifiers'):
                    response_text += f"   • Modificadores: {', '.join(result['modifiers'])}\n"
                if result.get('summary'):
                    response_text += f"   • Resumen: {result['summary']}\n"
                response_text += "\n"
            
            return [TextContent(type="text", text=response_text)]
            
        except CodeAnalysisError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error buscando elementos: {str(e)}")]
    
    async def _get_solution_structure(self, repo_url: str) -> List[TextContent]:
        """Obtiene la estructura completa de la solución C#"""
        try:
            if not repo_url:
                return [TextContent(type="text", text="❌ Error: URL del repositorio requerida")]
            
            structure = await self.code_handler.get_solution_structure(repo_url)
            
            response_text = f"🏗️ Estructura de la solución C#\n\n"
            response_text += f"📁 Directorio: {structure['solution_path']}\n"
            response_text += f"📄 Total archivos C#: {structure['total_cs_files']}\n\n"
            
            # Resumen estadístico
            summary = structure['summary']
            response_text += "📊 Resumen estadístico:\n"
            response_text += f"  • Clases: {summary['total_classes']}\n"
            response_text += f"  • Interfaces: {summary['total_interfaces']}\n"
            response_text += f"  • Enums: {summary['total_enums']}\n"
            response_text += f"  • Records: {summary['total_records']}\n\n"
            
            # Tipos de archivo
            file_types = structure['file_types']
            response_text += "📋 Tipos de archivos:\n"
            response_text += f"  • Controllers: {len(file_types['controllers'])}\n"
            response_text += f"  • Services: {len(file_types['services'])}\n"
            response_text += f"  • Models: {len(file_types['models'])}\n"
            response_text += f"  • DTOs: {len(file_types['dtos'])}\n"
            response_text += f"  • Interfaces: {len(file_types['interfaces'])}\n"
            response_text += f"  • Enums: {len(file_types['enums'])}\n"
            response_text += f"  • Configuraciones: {len(file_types['configurations'])}\n"
            response_text += f"  • Otros: {len(file_types['others'])}\n\n"
            
            # Namespaces principales
            namespaces = structure['namespaces']
            if namespaces:
                response_text += "🗂️ Namespaces encontrados:\n"
                for namespace, files in list(namespaces.items())[:10]:  # Mostrar máximo 10
                    response_text += f"  • {namespace}: {len(files)} archivo(s)\n"
                if len(namespaces) > 10:
                    response_text += f"  ... y {len(namespaces) - 10} namespaces más\n"
            
            # Proyectos
            projects = structure['projects']
            if projects:
                response_text += f"\n📦 Proyectos detectados ({len(projects)}):\n"
                for project_name, project_info in projects.items():
                    files_count = len(project_info.get('files', []))
                    response_text += f"  • {project_name}: {files_count} archivo(s)\n"
            
            return [TextContent(type="text", text=response_text)]
            
        except CodeAnalysisError as e:
            return [TextContent(type="text", text=f"❌ {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error obteniendo estructura: {str(e)}")]
            
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
