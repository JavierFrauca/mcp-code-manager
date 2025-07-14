"""
Handler para operaciones de archivos
"""
import os
import shutil
from typing import Dict, Any, Optional, List
from pathlib import Path

from services.file_manager import FileManager
from utils.exceptions import FileOperationError
from utils.validators import validate_file_path, validate_file_content

class FileHandler:
    async def get_file_content(self, repo_url: str, file_path: str) -> Dict[str, Any]:
        """Obtiene el contenido de un archivo"""
        try:
            file_path = validate_file_path(file_path, allow_absolute=True)
            repo_path = await self.file_manager.get_repo_path(repo_url)
            full_path = os.path.join(repo_path, file_path)
            if not os.path.exists(full_path):
                return {"error": f"El archivo '{file_path}' no existe"}
            if not os.path.isfile(full_path):
                return {"error": f"'{file_path}' no es un archivo"}
            try:
                content = await self.file_manager.read_file(full_path)
            except UnicodeDecodeError:
                with open(full_path, encoding='latin-1') as f:
                    content = f.read()
            except Exception:
                with open(full_path, encoding='utf-8', errors='replace') as f:
                    content = f.read()
            return {"content": f"Contenido de '{file_path}':\n\n{content}"}
        except Exception as e:
            return {"error": f"Error leyendo archivo: {str(e)}"}

    async def create_directory(self, repo_url: str, directory_path: str) -> Dict[str, Any]:
        """Crea un nuevo directorio"""
        try:
            directory_path = validate_file_path(directory_path, allow_absolute=True)
            repo_path = await self.file_manager.get_repo_path(repo_url)
            full_path = os.path.join(repo_path, directory_path)
            if os.path.exists(full_path):
                if os.path.isdir(full_path):
                    return {"message": f"📁 El directorio '{directory_path}' ya existe"}
                else:
                    return {"error": f"❌ Error: '{directory_path}' existe pero no es un directorio"}
            os.makedirs(full_path, exist_ok=True)
            response_text = f"✅ Directorio creado exitosamente\n📁 **Directorio creado:** {directory_path}\n"
            if len(Path(full_path).parts) > 1:
                response_text += "📂 **Directorios padre creados automáticamente**\n"
            return {"message": response_text}
        except PermissionError:
            return {"error": f"❌ Error: Sin permisos para crear directorio en '{directory_path}'"}
        except Exception as e:
            return {"error": f"❌ Error creando directorio: {str(e)}"}

    async def delete_directory(self, repo_url: str, directory_path: str) -> Dict[str, Any]:
        """Elimina un directorio"""
        try:
            directory_path = validate_file_path(directory_path, allow_absolute=True)
            repo_path = await self.file_manager.get_repo_path(repo_url)
            full_path = os.path.join(repo_path, directory_path)
            if not os.path.exists(full_path):
                return {"error": f"❌ Error: '{directory_path}' no existe"}
            if not os.path.isdir(full_path):
                return {"error": f"❌ Error: '{directory_path}' no es un directorio"}
            import sys
            moved_to_trash = False
            try:
                if sys.platform == "win32":
                    import winshell
                    try:
                        winshell.delete_file(str(full_path))
                        moved_to_trash = True
                    except Exception:
                        pass
            except ImportError:
                pass
            import shutil
            if not moved_to_trash:
                shutil.rmtree(full_path)
            response_text = f"✅ Directorio eliminado exitosamente\n🗑️ **Directorio eliminado:** {directory_path}\n"
            if moved_to_trash:
                response_text += "♻️ **Movido a papelera de reciclaje**\n"
            return {"message": response_text}
        except Exception as e:
            return {"error": f"❌ Error eliminando directorio: {str(e)}"}

    async def rename_directory(self, repo_url: str, old_path: str, new_path: str) -> Dict[str, Any]:
        """Renombra un directorio"""
        try:
            old_path = validate_file_path(old_path, allow_absolute=True)
            new_path = validate_file_path(new_path, allow_absolute=True)
            repo_path = await self.file_manager.get_repo_path(repo_url)
            full_old = os.path.join(repo_path, old_path)
            full_new = os.path.join(repo_path, new_path)
            if not os.path.exists(full_old):
                return {"error": f"❌ Error: '{old_path}' no existe"}
            if not os.path.isdir(full_old):
                return {"error": f"❌ Error: '{old_path}' no es un directorio"}
            if os.path.exists(full_new):
                return {"error": f"❌ Error: '{new_path}' ya existe"}
            import shutil
            shutil.move(full_old, full_new)
            response_text = f"✅ Directorio renombrado exitosamente\n📁 **Origen:** {old_path}\n📂 **Destino:** {new_path}\n"
            return {"message": response_text}
        except Exception as e:
            return {"error": f"❌ Error renombrando directorio: {str(e)}"}

    async def rename_file(self, repo_url: str, source_path: str, dest_path: str) -> Dict[str, Any]:
        """Renombra un archivo"""
        try:
            source_path = validate_file_path(source_path, allow_absolute=True)
            dest_path = validate_file_path(dest_path, allow_absolute=True)
            repo_path = await self.file_manager.get_repo_path(repo_url)
            full_source = os.path.join(repo_path, source_path)
            full_dest = os.path.join(repo_path, dest_path)
            if not os.path.exists(full_source):
                return {"error": f"❌ Error: '{source_path}' no existe"}
            if not os.path.isfile(full_source):
                return {"error": f"❌ Error: '{source_path}' no es un archivo"}
            if os.path.exists(full_dest):
                return {"error": f"❌ Error: '{dest_path}' ya existe"}
            import shutil
            shutil.move(full_source, full_dest)
            response_text = f"✅ Archivo renombrado exitosamente\n📄 **Origen:** {source_path}\n📝 **Destino:** {dest_path}\n"
            return {"message": response_text}
        except Exception as e:
            return {"error": f"❌ Error renombrando archivo: {str(e)}"}

    async def list_directory(self, repo_url: str, directory_path: str) -> Dict[str, Any]:
        """Lista el contenido de un directorio"""
        try:
            directory_path = validate_file_path(directory_path, allow_absolute=True)
            repo_path = await self.file_manager.get_repo_path(repo_url)
            full_path = os.path.join(repo_path, directory_path)
            if not os.path.exists(full_path):
                return {"error": f"Error: El directorio '{directory_path}' no existe"}
            if not os.path.isdir(full_path):
                return {"error": f"Error: '{directory_path}' no es un directorio"}
            items = []
            for item in sorted(os.listdir(full_path)):
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    items.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(item_path)
                    items.append(f"📄 {item} ({size} bytes)")
            if not items:
                content = f"Directorio '{directory_path}' está vacío"
            else:
                content = f"Contenido de '{directory_path}':\n\n" + "\n".join(items)
            return {"content": content}
        except Exception as e:
            return {"error": f"Error listando directorio: {str(e)}"}
    """Handler para gestión de archivos en repositorios"""
    
    def __init__(self):
        self.file_manager = FileManager()
    
    async def create_file(
        self, 
        repo_url: str, 
        file_path: str, 
        content: str
    ) -> Dict[str, Any]:
        """
        Crea un nuevo archivo en el repositorio
        
        Args:
            repo_url: URL del repositorio
            file_path: Ruta relativa donde crear el archivo
            content: Contenido del archivo
            
        Returns:
            Información del archivo creado
        """
        try:
            # Validar parámetros
            file_path = validate_file_path(file_path, allow_absolute=True)
            content = validate_file_content(content, file_path)
            
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            full_path = os.path.join(repo_path, file_path)
            
            # Verificar que el archivo no existe
            if os.path.exists(full_path):
                raise FileOperationError(f"El archivo ya existe: {file_path}")
            
            # Crear directorios padre si no existen
            parent_dir = os.path.dirname(full_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # Escribir el archivo
            await self.file_manager.write_file(full_path, content)
            
            # Obtener información del archivo creado
            file_info = await self._get_file_info(full_path, file_path)
            
            return {
                "status": "created",
                "message": f"Archivo creado exitosamente: {file_path}",
                "file_info": file_info
            }
            
        except Exception as e:
            raise FileOperationError(f"Error creando archivo '{file_path}': {str(e)}")
    
    async def update_file(
        self, 
        repo_url: str, 
        file_path: str, 
        content: str
    ) -> Dict[str, Any]:
        """
        Actualiza un archivo existente
        
        Args:
            repo_url: URL del repositorio
            file_path: Ruta relativa del archivo
            content: Nuevo contenido del archivo
            
        Returns:
            Información de la actualización
        """
        try:
            # Validar parámetros
            file_path = validate_file_path(file_path, allow_absolute=True)
            content = validate_file_content(content, file_path)
            
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            full_path = os.path.join(repo_path, file_path)
            
            # Verificar que el archivo existe
            if not os.path.exists(full_path):
                raise FileOperationError(f"El archivo no existe: {file_path}")
            
            # Hacer backup del contenido anterior
            original_content = await self.file_manager.read_file(full_path)
            
            # Escribir el nuevo contenido
            await self.file_manager.write_file(full_path, content)
            
            # Obtener información del archivo actualizado
            file_info = await self._get_file_info(full_path, file_path)
            
            return {
                "status": "updated",
                "message": f"Archivo actualizado exitosamente: {file_path}",
                "file_info": file_info,
                "changes": {
                    "original_size": len(original_content),
                    "new_size": len(content),
                    "size_diff": len(content) - len(original_content),
                    "original_lines": len(original_content.splitlines()),
                    "new_lines": len(content.splitlines()),
                    "lines_diff": len(content.splitlines()) - len(original_content.splitlines())
                }
            }
            
        except Exception as e:
            raise FileOperationError(f"Error actualizando archivo '{file_path}': {str(e)}")
    
    async def delete_file(self, repo_url: str, file_path: str) -> Dict[str, Any]:
        """
        Elimina un archivo del repositorio
        
        Args:
            repo_url: URL del repositorio
            file_path: Ruta relativa del archivo
            
        Returns:
            Información de la eliminación
        """
        try:
            # Validar parámetros
            file_path = validate_file_path(file_path, allow_absolute=True)
            
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            full_path = os.path.join(repo_path, file_path)
            
            # Verificar que el archivo existe
            if not os.path.exists(full_path):
                raise FileOperationError(f"El archivo no existe: {file_path}")
            
            # Obtener información antes de eliminar
            file_info = await self._get_file_info(full_path, file_path)
            
            # Eliminar el archivo
            os.remove(full_path)
            
            # Limpiar directorios vacíos
            await self._cleanup_empty_dirs(os.path.dirname(full_path), repo_path)
            
            return {
                "status": "deleted",
                "message": f"Archivo eliminado exitosamente: {file_path}",
                "deleted_file_info": file_info
            }
            
        except Exception as e:
            raise FileOperationError(f"Error eliminando archivo '{file_path}': {str(e)}")
    
    async def copy_file(
        self, 
        repo_url: str, 
        source_path: str, 
        dest_path: str
    ) -> Dict[str, Any]:
        """
        Copia un archivo a otra ubicación
        
        Args:
            repo_url: URL del repositorio
            source_path: Ruta origen
            dest_path: Ruta destino
            
        Returns:
            Información de la copia
        """
        try:
            # Validar parámetros
            source_path = validate_file_path(source_path, allow_absolute=True)
            dest_path = validate_file_path(dest_path, allow_absolute=True)
            
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            full_source = os.path.join(repo_path, source_path)
            full_dest = os.path.join(repo_path, dest_path)
            
            # Verificar que el archivo origen existe
            if not os.path.exists(full_source):
                raise FileOperationError(f"Archivo origen no existe: {source_path}")
            
            # Verificar que el destino no existe
            if os.path.exists(full_dest):
                raise FileOperationError(f"Archivo destino ya existe: {dest_path}")
            
            # Crear directorios padre si no existen
            parent_dir = os.path.dirname(full_dest)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # Copiar el archivo
            shutil.copy2(full_source, full_dest)
            
            # Obtener información de ambos archivos
            source_info = await self._get_file_info(full_source, source_path)
            dest_info = await self._get_file_info(full_dest, dest_path)
            
            return {
                "status": "copied",
                "message": f"Archivo copiado exitosamente: {source_path} -> {dest_path}",
                "source_file": source_info,
                "dest_file": dest_info
            }
            
        except Exception as e:
            raise FileOperationError(f"Error copiando archivo '{source_path}' a '{dest_path}': {str(e)}")
    
    async def move_file(
        self, 
        repo_url: str, 
        source_path: str, 
        dest_path: str
    ) -> Dict[str, Any]:
        """
        Mueve un archivo a otra ubicación
        
        Args:
            repo_url: URL del repositorio
            source_path: Ruta origen
            dest_path: Ruta destino
            
        Returns:
            Información del movimiento
        """
        try:
            # Validar parámetros
            source_path = validate_file_path(source_path, allow_absolute=True)
            dest_path = validate_file_path(dest_path, allow_absolute=True)
            
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            full_source = os.path.join(repo_path, source_path)
            full_dest = os.path.join(repo_path, dest_path)
            
            # Verificar que el archivo origen existe
            if not os.path.exists(full_source):
                raise FileOperationError(f"Archivo origen no existe: {source_path}")
            
            # Verificar que el destino no existe
            if os.path.exists(full_dest):
                raise FileOperationError(f"Archivo destino ya existe: {dest_path}")
            
            # Obtener información antes del movimiento
            source_info = await self._get_file_info(full_source, source_path)
            
            # Crear directorios padre si no existen
            parent_dir = os.path.dirname(full_dest)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # Mover el archivo
            shutil.move(full_source, full_dest)
            
            # Limpiar directorios vacíos en origen
            await self._cleanup_empty_dirs(os.path.dirname(full_source), repo_path)
            
            # Obtener información del archivo movido
            dest_info = await self._get_file_info(full_dest, dest_path)
            
            return {
                "status": "moved",
                "message": f"Archivo movido exitosamente: {source_path} -> {dest_path}",
                "original_file": source_info,
                "new_file": dest_info
            }
            
        except Exception as e:
            raise FileOperationError(f"Error moviendo archivo '{source_path}' a '{dest_path}': {str(e)}")
    
    async def list_repository_files(
        self,
        repo_url: str,
        file_pattern: Optional[str] = None,
        include_directories: bool = False,
        max_depth: int = -1,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Lista todos los archivos del repositorio con sus rutas
        
        Args:
            repo_url: URL del repositorio
            file_pattern: Patrón de archivos (ej: *.cs, *.json)
            include_directories: Si incluir directorios en la lista
            max_depth: Profundidad máxima de búsqueda (-1 = ilimitada)
            exclude_patterns: Patrones de directorios/archivos a excluir
            
        Returns:
            Lista completa de archivos con metadatos
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Patrones por defecto a excluir
            if exclude_patterns is None:
                exclude_patterns = ["bin", "obj", ".git", "node_modules", "packages", ".vs", "Debug", "Release"]
            
            files_info = []
            total_size = 0
            file_count = 0
            dir_count = 0
            
            # Recorrer directorio
            for root, dirs, files in os.walk(repo_path):
                # Calcular profundidad actual
                current_depth = root[len(repo_path):].count(os.sep)
                
                # Verificar profundidad máxima
                if max_depth >= 0 and current_depth >= max_depth:
                    dirs.clear()  # No seguir más profundo
                    continue
                
                # Filtrar directorios excluidos
                dirs[:] = [d for d in dirs if not any(
                    self._matches_exclude_pattern(d, pattern) for pattern in exclude_patterns
                )]
                
                # Añadir directorios si se solicita
                if include_directories:
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        relative_path = os.path.relpath(dir_path, repo_path)
                        
                        try:
                            dir_info = {
                                "path": relative_path.replace(os.sep, '/'),
                                "name": dir_name,
                                "type": "directory",
                                "size": 0,
                                "modified": os.path.getmtime(dir_path),
                                "depth": current_depth + 1
                            }
                            files_info.append(dir_info)
                            dir_count += 1
                        except Exception:
                            continue
                
                # Procesar archivos
                for file_name in files:
                    # Verificar si el archivo coincide con el patrón
                    if file_pattern and not self.file_manager._matches_pattern(file_name, file_pattern):
                        continue
                    
                    # Verificar si está excluido
                    if any(self._matches_exclude_pattern(file_name, pattern) for pattern in exclude_patterns):
                        continue
                    
                    file_path = os.path.join(root, file_name)
                    relative_path = os.path.relpath(file_path, repo_path)
                    
                    try:
                        # Obtener información del archivo
                        stat = os.stat(file_path)
                        file_size = stat.st_size
                        
                        file_info = {
                            "path": relative_path.replace(os.sep, '/'),
                            "name": file_name,
                            "type": "file",
                            "size": file_size,
                            "size_formatted": self._format_file_size(file_size),
                            "extension": os.path.splitext(file_name)[1].lower(),
                            "modified": stat.st_mtime,
                            "depth": current_depth,
                            "is_csharp": file_name.endswith('.cs'),
                            "is_config": file_name.lower() in ['appsettings.json', 'web.config', 'app.config'],
                            "is_project": file_name.endswith(('.csproj', '.sln')),
                            "directory": os.path.dirname(relative_path).replace(os.sep, '/') if os.path.dirname(relative_path) else ''
                        }
                        
                        files_info.append(file_info)
                        total_size += file_size
                        file_count += 1
                        
                    except Exception:
                        # Continuar con otros archivos si uno falla
                        continue
            
            # Ordenar por ruta
            files_info.sort(key=lambda x: x['path'])
            
            # Estadísticas por tipo de archivo
            extensions_stats = {}
            for file_info in files_info:
                if file_info['type'] == 'file':
                    ext = file_info['extension'] or 'sin_extension'
                    if ext not in extensions_stats:
                        extensions_stats[ext] = {'count': 0, 'size': 0}
                    extensions_stats[ext]['count'] += 1
                    extensions_stats[ext]['size'] += file_info['size']
            
            return {
                "repository_url": repo_url,
                "total_files": file_count,
                "total_directories": dir_count,
                "total_items": len(files_info),
                "total_size": total_size,
                "total_size_formatted": self._format_file_size(total_size),
                "file_pattern": file_pattern,
                "max_depth_searched": max_depth,
                "include_directories": include_directories,
                "extensions_stats": extensions_stats,
                "files": files_info
            }
            
        except Exception as e:
            raise FileOperationError(f"Error listando archivos del repositorio: {str(e)}")
    
    async def check_repository_permissions(
        self,
        repo_url: str,
        target_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verifica permisos de acceso en el directorio del repositorio
        
        Args:
            repo_url: URL del repositorio
            target_path: Ruta específica a verificar (opcional)
            
        Returns:
            Información detallada de permisos
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Determinar ruta a verificar
            if target_path:
                # Validar y construir ruta específica
                target_path = validate_file_path(target_path, allow_absolute=True)
                check_path = os.path.join(repo_path, target_path)
                
                # Verificar que la ruta esté dentro del repositorio
                if not check_path.startswith(repo_path):
                    raise FileOperationError("La ruta especificada está fuera del repositorio")
            else:
                check_path = repo_path
                target_path = ""
            
            # Verificar si la ruta existe
            path_exists = os.path.exists(check_path)
            is_directory = os.path.isdir(check_path) if path_exists else False
            is_file = os.path.isfile(check_path) if path_exists else False
            
            permissions = {
                "path": target_path,
                "full_path": check_path,
                "exists": path_exists,
                "is_directory": is_directory,
                "is_file": is_file,
                "permissions": {
                    "readable": False,
                    "writable": False,
                    "executable": False,
                    "can_create_files": False,
                    "can_delete_files": False,
                    "can_create_directories": False
                },
                "errors": []
            }
            
            if path_exists:
                # Verificar permisos básicos
                try:
                    permissions["permissions"]["readable"] = os.access(check_path, os.R_OK)
                except Exception as e:
                    permissions["errors"].append(f"Error verificando lectura: {str(e)}")
                
                try:
                    permissions["permissions"]["writable"] = os.access(check_path, os.W_OK)
                except Exception as e:
                    permissions["errors"].append(f"Error verificando escritura: {str(e)}")
                
                try:
                    permissions["permissions"]["executable"] = os.access(check_path, os.X_OK)
                except Exception as e:
                    permissions["errors"].append(f"Error verificando ejecución: {str(e)}")
                
                # Verificar permisos específicos para directorios
                if is_directory:
                    # Probar creación de archivo temporal
                    try:
                        test_file = os.path.join(check_path, ".mcp_test_file")
                        with open(test_file, 'w') as f:
                            f.write("test")
                        os.remove(test_file)
                        permissions["permissions"]["can_create_files"] = True
                        permissions["permissions"]["can_delete_files"] = True
                    except Exception as e:
                        permissions["errors"].append(f"No se pueden crear/eliminar archivos: {str(e)}")
                    
                    # Probar creación de directorio temporal
                    try:
                        test_dir = os.path.join(check_path, ".mcp_test_dir")
                        os.mkdir(test_dir)
                        os.rmdir(test_dir)
                        permissions["permissions"]["can_create_directories"] = True
                    except Exception as e:
                        permissions["errors"].append(f"No se pueden crear directorios: {str(e)}")
                
                # Información adicional del sistema de archivos
                if hasattr(os, 'statvfs'):
                    try:
                        statvfs = os.statvfs(check_path)
                        permissions["filesystem_info"] = {
                            "free_space": statvfs.f_bavail * statvfs.f_frsize,
                            "free_space_formatted": self._format_file_size(statvfs.f_bavail * statvfs.f_frsize),
                            "total_space": statvfs.f_blocks * statvfs.f_frsize,
                            "total_space_formatted": self._format_file_size(statvfs.f_blocks * statvfs.f_frsize)
                        }
                    except Exception:
                        pass
            else:
                permissions["errors"].append("La ruta especificada no existe")
                
                # Verificar si se puede crear en el directorio padre
                parent_dir = os.path.dirname(check_path)
                if os.path.exists(parent_dir):
                    try:
                        permissions["permissions"]["can_create_files"] = os.access(parent_dir, os.W_OK)
                        permissions["permissions"]["can_create_directories"] = os.access(parent_dir, os.W_OK)
                    except Exception as e:
                        permissions["errors"].append(f"Error verificando directorio padre: {str(e)}")
            
            # Verificar si es un repositorio Git y permisos Git
            git_permissions = await self._check_git_permissions(repo_path)
            permissions["git"] = git_permissions
            
            # Resumen de capacidades
            caps = permissions["permissions"]
            permissions["summary"] = {
                "can_read_files": caps["readable"] and path_exists,
                "can_modify_files": caps["writable"] and path_exists,
                "can_create_new_files": caps["can_create_files"],
                "can_delete_existing_files": caps["can_delete_files"] and caps["writable"],
                "fully_functional": all([
                    caps["readable"] or caps["can_create_files"],
                    caps["can_create_files"],
                    caps["can_delete_files"] or caps["writable"]
                ]) and len(permissions["errors"]) == 0
            }
            
            return permissions
            
        except Exception as e:
            raise FileOperationError(f"Error verificando permisos: {str(e)}")
    
    async def _check_git_permissions(self, repo_path: str) -> Dict[str, Any]:
        """
        Verifica permisos específicos de Git
        
        Args:
            repo_path: Ruta del repositorio
            
        Returns:
            Información de permisos Git
        """
        git_info = {
            "is_git_repository": False,
            "can_read_git": False,
            "can_write_git": False,
            "git_config_accessible": False,
            "remotes_accessible": False,
            "errors": []
        }
        
        try:
            from git import Repo, InvalidGitRepositoryError
            
            # Verificar si es un repositorio Git
            try:
                repo = Repo(repo_path)
                git_info["is_git_repository"] = True
                git_info["can_read_git"] = True
                
                # Verificar acceso a configuración
                try:
                    config = repo.config_reader()
                    git_info["git_config_accessible"] = True
                except Exception as e:
                    git_info["errors"].append(f"No se puede leer configuración Git: {str(e)}")
                
                # Verificar acceso a remotos
                try:
                    remotes = list(repo.remotes)
                    git_info["remotes_accessible"] = True
                    git_info["remotes_count"] = len(remotes)
                except Exception as e:
                    git_info["errors"].append(f"No se pueden leer remotos: {str(e)}")
                
                # Probar operación de escritura (verificar si se puede hacer commit)
                try:
                    # Verificar si hay cambios para commitear o si se puede acceder al índice
                    index = repo.index
                    git_info["can_write_git"] = True
                except Exception as e:
                    git_info["errors"].append(f"No se puede escribir en Git: {str(e)}")
                    
            except InvalidGitRepositoryError:
                git_info["errors"].append("El directorio no es un repositorio Git válido")
            except Exception as e:
                git_info["errors"].append(f"Error accediendo a Git: {str(e)}")
                
        except ImportError:
            git_info["errors"].append("GitPython no está disponible")
        
        return git_info
    
    def _matches_exclude_pattern(self, name: str, pattern: str) -> bool:
        """
        Verifica si un nombre coincide con un patrón de exclusión
        
        Args:
            name: Nombre del archivo/directorio
            pattern: Patrón de exclusión
            
        Returns:
            True si debe ser excluido
        """
        import fnmatch
        return (
            fnmatch.fnmatch(name.lower(), pattern.lower()) or
            pattern.lower() in name.lower()
        )
    
    async def _get_file_info(self, full_path: str, relative_path: str) -> Dict[str, Any]:
        """
        Obtiene información detallada de un archivo
        
        Args:
            full_path: Ruta completa del archivo
            relative_path: Ruta relativa del archivo
            
        Returns:
            Información del archivo
        """
        try:
            stat = os.stat(full_path)
            
            # Leer contenido para obtener más información
            content = await self.file_manager.read_file(full_path)
            
            return {
                "path": relative_path,
                "full_path": full_path,
                "size": stat.st_size,
                "size_formatted": self._format_file_size(stat.st_size),
                "lines": len(content.splitlines()) if content else 0,
                "characters": len(content) if content else 0,
                "extension": os.path.splitext(relative_path)[1],
                "filename": os.path.basename(relative_path),
                "directory": os.path.dirname(relative_path),
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "is_csharp": relative_path.endswith('.cs'),
                "encoding": "utf-8"
            }
            
        except Exception as e:
            raise FileOperationError(f"Error obteniendo información del archivo: {str(e)}")
    
    async def _cleanup_empty_dirs(self, dir_path: str, repo_path: str) -> None:
        """
        Elimina directorios vacíos hasta el directorio del repositorio
        
        Args:
            dir_path: Directorio a verificar
            repo_path: Directorio raíz del repositorio
        """
        try:
            # No eliminar el directorio del repositorio
            if dir_path == repo_path:
                return
            
            # Verificar si el directorio está vacío
            if os.path.exists(dir_path) and not os.listdir(dir_path):
                os.rmdir(dir_path)
                
                # Recursivamente verificar el directorio padre
                parent_dir = os.path.dirname(dir_path)
                await self._cleanup_empty_dirs(parent_dir, repo_path)
                
        except Exception:
            # Ignorar errores en la limpieza de directorios
            pass
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Formatea el tamaño del archivo en unidades legibles
        
        Args:
            size_bytes: Tamaño en bytes
            
        Returns:
            Tamaño formateado
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"