"""
Tests para FileHandler
"""
import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch

from src.handlers.file_handler import FileHandler
from src.utils.exceptions import FileOperationError

class TestFileHandler:
    """Tests para el FileHandler"""
    
    @pytest.fixture
    def file_handler(self):
        """Fixture para FileHandler"""
        return FileHandler()
    
    @pytest.fixture
    def mock_repo_path(self):
        """Fixture para ruta de repositorio mock"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Crear estructura de ejemplo
            os.makedirs(os.path.join(temp_dir, "src", "Controllers"))
            os.makedirs(os.path.join(temp_dir, "src", "Services"))
            os.makedirs(os.path.join(temp_dir, "src", "Models"))
            
            # Crear archivos de ejemplo
            files = [
                "src/Controllers/UserController.cs",
                "src/Services/UserService.cs", 
                "src/Models/UserDto.cs",
                "src/Models/User.cs",
                "Program.cs",
                "appsettings.json"
            ]
            
            for file_path in files:
                full_path = os.path.join(temp_dir, file_path)
                with open(full_path, 'w') as f:
                    f.write(f"// Contenido de {file_path}")
            
            yield temp_dir
    
    @pytest.mark.asyncio
    async def test_create_file_success(self, file_handler, mock_repo_path):
        """Test creación exitosa de archivo"""
        # Mock del file_manager
        file_handler.file_manager.get_repo_path = AsyncMock(return_value=mock_repo_path)
        file_handler.file_manager.write_file = AsyncMock()
        
        result = await file_handler.create_file(
            repo_url="https://github.com/test/repo.git",
            file_path="src/NewFile.cs",
            content="public class NewFile { }"
        )
        
        assert result["status"] == "created"
        assert "src/NewFile.cs" in result["message"]
        assert "file_info" in result
    
    @pytest.mark.asyncio
    async def test_list_repository_files_all(self, file_handler, mock_repo_path):
        """Test listado de todos los archivos del repositorio"""
        # Mock del file_manager
        file_handler.file_manager.get_repo_path = AsyncMock(return_value=mock_repo_path)
        
        result = await file_handler.list_repository_files(
            repo_url="https://github.com/test/repo.git"
        )
        
        assert result["total_files"] > 0
        assert "files" in result
        assert result["repository_url"] == "https://github.com/test/repo.git"
        
        # Verificar que se encontraron archivos C#
        cs_files = [f for f in result["files"] if f["extension"] == ".cs"]
        assert len(cs_files) > 0
        
        # Verificar estructura de archivo
        file_info = result["files"][0]
        required_fields = ["path", "name", "type", "size", "extension", "modified"]
        for field in required_fields:
            assert field in file_info
    
    @pytest.mark.asyncio
    async def test_list_repository_files_with_pattern(self, file_handler, mock_repo_path):
        """Test listado con patrón específico"""
        file_handler.file_manager.get_repo_path = AsyncMock(return_value=mock_repo_path)
        
        result = await file_handler.list_repository_files(
            repo_url="https://github.com/test/repo.git",
            file_pattern="*.cs"
        )
        
        # Todos los archivos deben ser .cs
        for file_info in result["files"]:
            if file_info["type"] == "file":
                assert file_info["extension"] == ".cs"
    
    @pytest.mark.asyncio
    async def test_list_repository_files_with_directories(self, file_handler, mock_repo_path):
        """Test listado incluyendo directorios"""
        file_handler.file_manager.get_repo_path = AsyncMock(return_value=mock_repo_path)
        
        result = await file_handler.list_repository_files(
            repo_url="https://github.com/test/repo.git",
            include_directories=True
        )
        
        # Debe incluir directorios
        directories = [f for f in result["files"] if f["type"] == "directory"]
        assert len(directories) > 0
        assert result["total_directories"] > 0
    
    @pytest.mark.asyncio
    async def test_check_repository_permissions_success(self, file_handler, mock_repo_path):
        """Test verificación exitosa de permisos"""
        file_handler.file_manager.get_repo_path = AsyncMock(return_value=mock_repo_path)
        
        result = await file_handler.check_repository_permissions(
            repo_url="https://github.com/test/repo.git"
        )
        
        assert result["exists"] == True
        assert result["is_directory"] == True
        assert "permissions" in result
        assert "summary" in result
        
        # Verificar estructura de permisos
        perms = result["permissions"]
        required_perms = ["readable", "writable", "can_create_files", "can_delete_files"]
        for perm in required_perms:
            assert perm in perms
    
    @pytest.mark.asyncio
    async def test_check_repository_permissions_specific_path(self, file_handler, mock_repo_path):
        """Test verificación de permisos en ruta específica"""
        file_handler.file_manager.get_repo_path = AsyncMock(return_value=mock_repo_path)
        
        result = await file_handler.check_repository_permissions(
            repo_url="https://github.com/test/repo.git",
            target_path="src/Controllers"
        )
        
        assert result["path"] == "src/Controllers"
        assert result["exists"] == True
        assert result["is_directory"] == True
    
    @pytest.mark.asyncio
    async def test_check_repository_permissions_nonexistent_path(self, file_handler, mock_repo_path):
        """Test verificación de permisos en ruta inexistente"""
        file_handler.file_manager.get_repo_path = AsyncMock(return_value=mock_repo_path)
        
        result = await file_handler.check_repository_permissions(
            repo_url="https://github.com/test/repo.git",
            target_path="nonexistent/path"
        )
        
        assert result["exists"] == False
        assert len(result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_list_files_with_exclusions(self, file_handler, mock_repo_path):
        """Test listado con patrones de exclusión"""
        # Crear directorios que deben ser excluidos
        os.makedirs(os.path.join(mock_repo_path, "bin"))
        os.makedirs(os.path.join(mock_repo_path, "obj"))
        
        with open(os.path.join(mock_repo_path, "bin", "test.dll"), 'w') as f:
            f.write("binary")
        
        file_handler.file_manager.get_repo_path = AsyncMock(return_value=mock_repo_path)
        
        result = await file_handler.list_repository_files(
            repo_url="https://github.com/test/repo.git",
            exclude_patterns=["bin", "obj"]
        )
        
        # No debe incluir archivos de bin/ o obj/
        for file_info in result["files"]:
            assert not file_info["path"].startswith("bin/")
            assert not file_info["path"].startswith("obj/")
    
    @pytest.mark.asyncio
    async def test_extensions_stats(self, file_handler, mock_repo_path):
        """Test estadísticas por extensión"""
        file_handler.file_manager.get_repo_path = AsyncMock(return_value=mock_repo_path)
        
        result = await file_handler.list_repository_files(
            repo_url="https://github.com/test/repo.git"
        )
        
        assert "extensions_stats" in result
        assert ".cs" in result["extensions_stats"]
        assert ".json" in result["extensions_stats"]
        
        # Verificar estructura de estadísticas
        cs_stats = result["extensions_stats"][".cs"]
        assert "count" in cs_stats
        assert "size" in cs_stats
        assert cs_stats["count"] > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, file_handler):
        """Test manejo de errores"""
        # Mock que falla
        file_handler.file_manager.get_repo_path = AsyncMock(
            side_effect=Exception("Repository not found")
        )
        
        with pytest.raises(FileOperationError):
            await file_handler.list_repository_files(
                repo_url="https://github.com/invalid/repo.git"
            )
    
    def test_matches_exclude_pattern(self, file_handler):
        """Test función de coincidencia de patrones de exclusión"""
        assert file_handler._matches_exclude_pattern("bin", "bin") == True
        assert file_handler._matches_exclude_pattern("obj", "obj") == True
        assert file_handler._matches_exclude_pattern("packages", "pack*") == True
        assert file_handler._matches_exclude_pattern("normal_file.cs", "bin") == False
    
    def test_format_file_size(self, file_handler):
        """Test formateo de tamaño de archivo"""
        assert "B" in file_handler._format_file_size(100)
        assert "KB" in file_handler._format_file_size(1024)
        assert "MB" in file_handler._format_file_size(1024 * 1024)