"""
Servicio para gestión de archivos y repositorios
"""
import os
import hashlib
import tempfile
import shutil
from typing import Dict, Optional
from pathlib import Path
import aiofiles

from utils.exceptions import FileOperationError, RepositoryError

class FileManager:
    """Gestor de archivos y repositorios locales"""
    
    def __init__(self):
        self.cache_dir = os.path.join(tempfile.gettempdir(), "mcp_code_manager")
        self.ensure_cache_directory()
    
    def ensure_cache_directory(self) -> None:
        """Asegura que el directorio de cache existe"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except Exception as e:
            raise FileOperationError(f"Error creando directorio de cache: {str(e)}")
    
    async def get_repo_path(self, repo_url: str) -> str:
        """
        Obtiene la ruta local del repositorio
        
        Args:
            repo_url: URL del repositorio
            
        Returns:
            Ruta local del repositorio
        """
        try:
            # Generar nombre único basado en la URL
            repo_hash = hashlib.md5(repo_url.encode()).hexdigest()[:8]
            repo_name = self._extract_repo_name(repo_url)
            local_path = os.path.join(self.cache_dir, f"{repo_name}_{repo_hash}")
            
            # Si no existe localmente, se debe clonar primero
            if not os.path.exists(local_path):
                raise RepositoryError(f"Repositorio no encontrado localmente: {repo_url}. Debe clonarse primero.")
            
            return local_path
            
        except Exception as e:
            if isinstance(e, RepositoryError):
                raise
            raise FileOperationError(f"Error obteniendo ruta del repositorio: {str(e)}")
    
    async def read_file(self, file_path: str) -> str:
        """
        Lee el contenido de un archivo de forma asíncrona
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Contenido del archivo
        """
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except FileNotFoundError:
            raise FileOperationError(f"Archivo no encontrado: {file_path}")
        except UnicodeDecodeError:
            # Intentar con diferentes encodings
            try:
                async with aiofiles.open(file_path, 'r', encoding='latin-1') as f:
                    return await f.read()
            except Exception:
                raise FileOperationError(f"No se puede decodificar el archivo: {file_path}")
        except Exception as e:
            raise FileOperationError(f"Error leyendo archivo '{file_path}': {str(e)}")
    
    async def write_file(self, file_path: str, content: str) -> None:
        """
        Escribe contenido a un archivo de forma asíncrona
        
        Args:
            file_path: Ruta del archivo
            content: Contenido a escribir
        """
        try:
            # Asegurar que el directorio padre existe
            parent_dir = os.path.dirname(file_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
                
        except Exception as e:
            raise FileOperationError(f"Error escribiendo archivo '{file_path}': {str(e)}")
    
    async def copy_file(self, source_path: str, dest_path: str) -> None:
        """
        Copia un archivo de forma asíncrona
        
        Args:
            source_path: Ruta origen
            dest_path: Ruta destino
        """
        try:
            # Asegurar que el directorio padre del destino existe
            parent_dir = os.path.dirname(dest_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # Leer y escribir de forma asíncrona
            content = await self.read_file(source_path)
            await self.write_file(dest_path, content)
            
        except Exception as e:
            raise FileOperationError(f"Error copiando archivo '{source_path}' a '{dest_path}': {str(e)}")
    
    async def move_file(self, source_path: str, dest_path: str) -> None:
        """
        Mueve un archivo de forma asíncrona
        
        Args:
            source_path: Ruta origen
            dest_path: Ruta destino
        """
        try:
            await self.copy_file(source_path, dest_path)
            os.remove(source_path)
            
        except Exception as e:
            raise FileOperationError(f"Error moviendo archivo '{source_path}' a '{dest_path}': {str(e)}")
    
    async def delete_file(self, file_path: str) -> None:
        """
        Elimina un archivo
        
        Args:
            file_path: Ruta del archivo
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            else:
                raise FileOperationError(f"Archivo no encontrado: {file_path}")
                
        except Exception as e:
            raise FileOperationError(f"Error eliminando archivo '{file_path}': {str(e)}")
    
    async def file_exists(self, file_path: str) -> bool:
        """
        Verifica si un archivo existe
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            True si el archivo existe
        """
        return os.path.exists(file_path)
    
    async def get_file_info(self, file_path: str) -> Dict[str, any]:
        """
        Obtiene información detallada de un archivo
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Información del archivo
        """
        try:
            if not os.path.exists(file_path):
                raise FileOperationError(f"Archivo no encontrado: {file_path}")
            
            stat = os.stat(file_path)
            
            return {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'accessed': stat.st_atime,
                'is_file': os.path.isfile(file_path),
                'is_directory': os.path.isdir(file_path),
                'extension': os.path.splitext(file_path)[1],
                'parent_directory': os.path.dirname(file_path)
            }
            
        except Exception as e:
            raise FileOperationError(f"Error obteniendo información del archivo '{file_path}': {str(e)}")
    
    async def list_directory(self, directory_path: str, pattern: Optional[str] = None) -> list:
        """
        Lista el contenido de un directorio
        
        Args:
            directory_path: Ruta del directorio
            pattern: Patrón de archivos (opcional)
            
        Returns:
            Lista de archivos y directorios
        """
        try:
            if not os.path.exists(directory_path):
                raise FileOperationError(f"Directorio no encontrado: {directory_path}")
            
            if not os.path.isdir(directory_path):
                raise FileOperationError(f"La ruta no es un directorio: {directory_path}")
            
            items = []
            for item in os.listdir(directory_path):
                # Excluir entradas especiales de directorio
                if item in ('.', '..'):
                    continue
                    
                item_path = os.path.join(directory_path, item)
                
                # Filtrar por patrón si se especifica
                if pattern and not self._matches_pattern(item, pattern):
                    continue
                
                item_info = await self.get_file_info(item_path)
                items.append(item_info)
            
            return items
            
        except Exception as e:
            raise FileOperationError(f"Error listando directorio '{directory_path}': {str(e)}")
    
    async def create_directory(self, directory_path: str) -> None:
        """
        Crea un directorio y sus padres si no existen
        
        Args:
            directory_path: Ruta del directorio
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
        except Exception as e:
            raise FileOperationError(f"Error creando directorio '{directory_path}': {str(e)}")
    
    async def delete_directory(self, directory_path: str, force: bool = False) -> None:
        """
        Elimina un directorio
        
        Args:
            directory_path: Ruta del directorio
            force: Si eliminar incluso si no está vacío
        """
        try:
            if not os.path.exists(directory_path):
                raise FileOperationError(f"Directorio no encontrado: {directory_path}")
            
            if force:
                shutil.rmtree(directory_path)
            else:
                os.rmdir(directory_path)  # Solo elimina si está vacío
                
        except OSError as e:
            if e.errno == 39:  # Directory not empty
                raise FileOperationError(f"Directorio no está vacío: {directory_path}. Use force=True para eliminarlo.")
            else:
                raise FileOperationError(f"Error eliminando directorio '{directory_path}': {str(e)}")
        except Exception as e:
            raise FileOperationError(f"Error eliminando directorio '{directory_path}': {str(e)}")
    
    async def search_files(self, directory_path: str, pattern: str, recursive: bool = True) -> list:
        """
        Busca archivos que coincidan con un patrón
        
        Args:
            directory_path: Directorio base
            pattern: Patrón de búsqueda
            recursive: Si buscar recursivamente
            
        Returns:
            Lista de archivos encontrados
        """
        try:
            found_files = []
            
            if recursive:
                for root, dirs, files in os.walk(directory_path):
                    # Excluir directorios irrelevantes
                    dirs[:] = [d for d in dirs if d not in {'.git', 'bin', 'obj', 'packages', 'node_modules'}]
                    
                    for file in files:
                        if self._matches_pattern(file, pattern):
                            file_path = os.path.join(root, file)
                            file_info = await self.get_file_info(file_path)
                            found_files.append(file_info)
            else:
                items = await self.list_directory(directory_path, pattern)
                found_files = [item for item in items if item['is_file']]
            
            return found_files
            
        except Exception as e:
            raise FileOperationError(f"Error buscando archivos en '{directory_path}': {str(e)}")
    
    def _extract_repo_name(self, repo_url: str) -> str:
        """
        Extrae el nombre del repositorio de la URL
        
        Args:
            repo_url: URL del repositorio
            
        Returns:
            Nombre del repositorio
        """
        # Remover .git al final si existe
        clean_url = repo_url.rstrip('/').replace('.git', '')
        
        # Extraer el último segmento de la URL
        parts = clean_url.split('/')
        return parts[-1] if parts else 'repo'
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """
        Verifica si un nombre de archivo coincide con un patrón
        
        Args:
            filename: Nombre del archivo
            pattern: Patrón a verificar
            
        Returns:
            True si coincide
        """
        import fnmatch
        return fnmatch.fnmatch(filename.lower(), pattern.lower())
    
    async def cleanup_cache(self, max_age_days: int = 7) -> Dict[str, any]:
        """
        Limpia archivos antiguos del cache
        
        Args:
            max_age_days: Edad máxima en días
            
        Returns:
            Información de la limpieza
        """
        try:
            import time
            
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            cleaned_files = 0
            cleaned_size = 0
            
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > max_age_seconds:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cleaned_files += 1
                        cleaned_size += file_size
            
            return {
                'cleaned_files': cleaned_files,
                'cleaned_size_bytes': cleaned_size,
                'cleaned_size_mb': round(cleaned_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            raise FileOperationError(f"Error limpiando cache: {str(e)}")