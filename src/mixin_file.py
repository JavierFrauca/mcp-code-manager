from pathlib import Path
import sys
import os
from typing import List
from mcp.types import TextContent

if sys.platform == "win32":
    try:
        import winshell
    except ImportError:
        winshell = None
        print("[WARNING] winshell no disponible - eliminación a papelera deshabilitada", file=sys.stderr)


from handlers.file_handler import FileHandler

class FileAdapterMixin:
    async def _list_repository_files(self, repo_url: str, file_pattern: str = None, include_directories: bool = False, exclude_patterns: list = None, max_depth: int = 10) -> List[TextContent]:
        """Lista archivos del repositorio usando FileHandler (wrapper avanzado)"""
        try:
            result = await self.file_handler.list_repository_files(
                repo_url=repo_url,
                file_pattern=file_pattern,
                include_directories=include_directories,
                exclude_patterns=exclude_patterns,
                max_depth=max_depth
            )
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error listando archivos del repositorio: {str(e)}")]

    async def _check_repository_permissions(self, repo_url: str, target_path: str = None) -> List[TextContent]:
        """Verifica permisos en el repositorio usando FileHandler (wrapper avanzado)"""
        try:
            result = await self.file_handler.check_repository_permissions(
                repo_url=repo_url,
                target_path=target_path
            )
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error verificando permisos en el repositorio: {str(e)}")]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_handler = FileHandler()

    async def _get_file_content(self, repo_url: str, file_path: str) -> List[TextContent]:
        """Obtiene el contenido de un archivo delegando en FileHandler"""
        try:
            result = await self.file_handler.get_file_content(repo_url, file_path)
            if isinstance(result, dict) and "content" in result:
                return [TextContent(type="text", text=result["content"])]
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error leyendo archivo: {str(e)}")]
    
    async def _list_directory(self, repo_url: str, directory_path: str) -> List[TextContent]:
        """Lista el contenido de un directorio delegando en FileHandler"""
        try:
            result = await self.file_handler.list_directory(repo_url, directory_path)
            if isinstance(result, dict) and "content" in result:
                return [TextContent(type="text", text=result["content"])]
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error listando directorio: {str(e)}")]

    async def _create_directory(self, repo_url: str, directory_path: str) -> List[TextContent]:
        """Crea un nuevo directorio delegando en FileHandler"""
        try:
            result = await self.file_handler.create_directory(repo_url, directory_path)
            if isinstance(result, dict) and "message" in result:
                return [TextContent(type="text", text=result["message"])]
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error creando directorio: {str(e)}")]

    async def _set_file_content_enhanced(self, repo_url: str, file_path: str, content: str, create_backup: bool = True) -> List[TextContent]:
        """Establece el contenido de un archivo - crea si no existe, actualiza si existe"""
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_handler.file_manager.get_repo_path(repo_url)
            full_path = os.path.join(repo_path, file_path)
            
            # Verificar si el archivo existe para decidir crear o actualizar
            if os.path.exists(full_path):
                # Archivo existe - actualizar
                result = await self.file_handler.update_file(repo_url, file_path, content)
            else:
                # Archivo no existe - crear
                result = await self.file_handler.create_file(repo_url, file_path, content)
                
            if isinstance(result, dict) and "message" in result:
                return [TextContent(type="text", text=result["message"])]
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error escribiendo archivo: {str(e)}")]

    async def _rename_directory(self, repo_url: str, old_path: str, new_path: str) -> List[TextContent]:
        """Renombra un directorio delegando en FileHandler"""
        try:
            result = await self.file_handler.rename_directory(repo_url, old_path, new_path)
            if isinstance(result, dict) and "message" in result:
                return [TextContent(type="text", text=result["message"])]
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error renombrando directorio: {str(e)}")]

    async def _delete_directory(self, repo_url: str, directory_path: str) -> List[TextContent]:
        """Elimina un directorio delegando en FileHandler"""
        try:
            result = await self.file_handler.delete_directory(repo_url, directory_path)
            if isinstance(result, dict) and "message" in result:
                return [TextContent(type="text", text=result["message"])]
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error eliminando directorio: {str(e)}")]

    async def _rename_file(self, repo_url: str, source_path: str, dest_path: str) -> List[TextContent]:
        """Renombra un archivo delegando en FileHandler"""
        try:
            result = await self.file_handler.rename_file(repo_url, source_path, dest_path)
            if isinstance(result, dict) and "message" in result:
                return [TextContent(type="text", text=result["message"])]
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error renombrando archivo: {str(e)}")]

    async def _delete_file(self, repo_url: str, file_path: str) -> List[TextContent]:
        """Elimina un archivo delegando en FileHandler"""
        try:
            result = await self.file_handler.delete_file(repo_url, file_path)
            if isinstance(result, dict) and "message" in result:
                return [TextContent(type="text", text=result["message"])]
            return [TextContent(type="text", text=str(result))]
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
