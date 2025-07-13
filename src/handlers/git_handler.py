"""
Handler para operaciones Git
"""
from typing import Dict, List, Any, Optional
import json

from services.git_manager import GitManager
from utils.exceptions import GitError
from utils.validators import (
    validate_git_branch_name, 
    validate_commit_message, 
    validate_git_action
)

class GitHandler:
    """Handler para operaciones Git en repositorios"""
    
    def __init__(self):
        self.git_manager = GitManager()
    
    async def status(self, repo_url: str) -> Dict[str, Any]:
        """
        Obtiene el estado completo del repositorio Git
        
        Args:
            repo_url: URL del repositorio
            
        Returns:
            Estado detallado del repositorio
        """
        try:
            return await self.git_manager.get_detailed_status(repo_url)
        except Exception as e:
            raise GitError(f"Error obteniendo estado del repositorio: {str(e)}")
    
    async def diff(
        self, 
        repo_url: str, 
        file_path: Optional[str] = None, 
        staged: bool = False
    ) -> Dict[str, Any]:
        """
        Muestra diferencias entre versiones
        
        Args:
            repo_url: URL del repositorio
            file_path: Archivo específico (opcional)
            staged: Si mostrar diferencias staged
            
        Returns:
            Diferencias encontradas
        """
        try:
            return await self.git_manager.get_diff(repo_url, file_path, staged)
        except Exception as e:
            raise GitError(f"Error obteniendo diferencias: {str(e)}")
    
    async def commit(
        self, 
        repo_url: str, 
        message: str, 
        files: Optional[List[str]] = None,
        add_all: bool = False
    ) -> Dict[str, Any]:
        """
        Realiza un commit
        
        Args:
            repo_url: URL del repositorio
            message: Mensaje del commit
            files: Archivos específicos (opcional)
            add_all: Si añadir todos los archivos modificados
            
        Returns:
            Información del commit realizado
        """
        try:
            # Validar mensaje
            message = validate_commit_message(message)
            
            return await self.git_manager.commit_changes(repo_url, message, files, add_all)
        except Exception as e:
            raise GitError(f"Error realizando commit: {str(e)}")
    
    async def push(
        self, 
        repo_url: str, 
        branch: Optional[str] = None, 
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Sube cambios al repositorio remoto
        
        Args:
            repo_url: URL del repositorio
            branch: Rama específica (opcional)
            force: Si realizar push forzado
            
        Returns:
            Resultado del push
        """
        try:
            return await self.git_manager.push_changes(repo_url, branch, force)
        except Exception as e:
            raise GitError(f"Error subiendo cambios: {str(e)}")
    
    async def pull(
        self, 
        repo_url: str, 
        branch: Optional[str] = None, 
        rebase: bool = False
    ) -> Dict[str, Any]:
        """
        Descarga cambios del repositorio remoto
        
        Args:
            repo_url: URL del repositorio
            branch: Rama específica (opcional)
            rebase: Si usar rebase en lugar de merge
            
        Returns:
            Resultado del pull
        """
        try:
            return await self.git_manager.pull_changes(repo_url, branch, rebase)
        except Exception as e:
            raise GitError(f"Error descargando cambios: {str(e)}")
    
    async def branch(
        self, 
        repo_url: str, 
        action: str, 
        branch_name: Optional[str] = None,
        from_branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gestiona ramas del repositorio
        
        Args:
            repo_url: URL del repositorio
            action: Acción a realizar
            branch_name: Nombre de la rama
            from_branch: Rama base (para crear)
            
        Returns:
            Resultado de la operación
        """
        try:
            # Validar acción
            valid_actions = ["create", "delete", "switch", "list", "rename"]
            action = validate_git_action(action, valid_actions)
            
            # Validar nombre de rama si se proporciona
            if branch_name:
                branch_name = validate_git_branch_name(branch_name)
            
            return await self.git_manager.manage_branch(repo_url, action, branch_name, from_branch)
        except Exception as e:
            raise GitError(f"Error gestionando rama: {str(e)}")
    
    async def merge(
        self, 
        repo_url: str, 
        source_branch: str,
        target_branch: Optional[str] = None,
        no_ff: bool = False
    ) -> Dict[str, Any]:
        """
        Fusiona ramas
        
        Args:
            repo_url: URL del repositorio
            source_branch: Rama origen
            target_branch: Rama destino (opcional, por defecto actual)
            no_ff: Si no usar fast-forward
            
        Returns:
            Resultado del merge
        """
        try:
            # Validar nombres de rama
            source_branch = validate_git_branch_name(source_branch)
            if target_branch:
                target_branch = validate_git_branch_name(target_branch)
            
            return await self.git_manager.merge_branches(repo_url, source_branch, target_branch, no_ff)
        except Exception as e:
            raise GitError(f"Error fusionando ramas: {str(e)}")
    
    async def stash(
        self, 
        repo_url: str, 
        action: str,
        message: Optional[str] = None,
        stash_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Gestiona el stash
        
        Args:
            repo_url: URL del repositorio
            action: Acción del stash
            message: Mensaje del stash (para save)
            stash_index: Índice del stash (para pop/apply/drop)
            
        Returns:
            Resultado de la operación
        """
        try:
            # Validar acción
            valid_actions = ["save", "pop", "list", "apply", "drop"]
            action = validate_git_action(action, valid_actions)
            
            return await self.git_manager.manage_stash(repo_url, action, message, stash_index)
        except Exception as e:
            raise GitError(f"Error gestionando stash: {str(e)}")
    
    async def log(
        self, 
        repo_url: str, 
        limit: int = 10,
        branch: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Muestra el historial de commits
        
        Args:
            repo_url: URL del repositorio
            limit: Número de commits a mostrar
            branch: Rama específica (opcional)
            file_path: Archivo específico (opcional)
            
        Returns:
            Historial de commits
        """
        try:
            # Validar límite
            if limit <= 0 or limit > 100:
                limit = 10
            
            # Validar nombre de rama si se proporciona
            if branch:
                branch = validate_git_branch_name(branch)
            
            return await self.git_manager.get_commit_history(repo_url, limit, branch, file_path)
        except Exception as e:
            raise GitError(f"Error obteniendo historial: {str(e)}")
    
    async def reset(
        self, 
        repo_url: str, 
        commit_hash: Optional[str] = None,
        mode: str = "mixed"
    ) -> Dict[str, Any]:
        """
        Resetea el repositorio a un estado anterior
        
        Args:
            repo_url: URL del repositorio
            commit_hash: Hash del commit (opcional, HEAD por defecto)
            mode: Modo de reset (soft, mixed, hard)
            
        Returns:
            Resultado del reset
        """
        try:
            # Validar modo
            valid_modes = ["soft", "mixed", "hard"]
            if mode not in valid_modes:
                raise GitError(f"Modo de reset inválido: {mode}. Válidos: {', '.join(valid_modes)}")
            
            return await self.git_manager.reset_repository(repo_url, commit_hash, mode)
        except Exception as e:
            raise GitError(f"Error reseteando repositorio: {str(e)}")
    
    async def tag(
        self, 
        repo_url: str, 
        action: str,
        tag_name: Optional[str] = None,
        message: Optional[str] = None,
        commit_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gestiona tags del repositorio
        
        Args:
            repo_url: URL del repositorio
            action: Acción (create, delete, list, push)
            tag_name: Nombre del tag
            message: Mensaje del tag (para create)
            commit_hash: Hash del commit (opcional)
            
        Returns:
            Resultado de la operación
        """
        try:
            # Validar acción
            valid_actions = ["create", "delete", "list", "push"]
            action = validate_git_action(action, valid_actions)
            
            return await self.git_manager.manage_tag(repo_url, action, tag_name, message, commit_hash)
        except Exception as e:
            raise GitError(f"Error gestionando tag: {str(e)}")
    
    async def remote(
        self, 
        repo_url: str, 
        action: str,
        remote_name: Optional[str] = None,
        remote_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gestiona remotos del repositorio
        
        Args:
            repo_url: URL del repositorio
            action: Acción (add, remove, list, set-url)
            remote_name: Nombre del remoto
            remote_url: URL del remoto
            
        Returns:
            Resultado de la operación
        """
        try:
            # Validar acción
            valid_actions = ["add", "remove", "list", "set-url"]
            action = validate_git_action(action, valid_actions)
            
            return await self.git_manager.manage_remote(repo_url, action, remote_name, remote_url)
        except Exception as e:
            raise GitError(f"Error gestionando remoto: {str(e)}")

    async def init(
        self, 
        repo_path: str, 
        bare: bool = False,
        initial_branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inicializa un nuevo repositorio Git
        
        Args:
            repo_path: Ruta donde inicializar el repositorio
            bare: Si crear un repositorio bare
            initial_branch: Nombre de la rama inicial (opcional)
            
        Returns:
            Resultado de la inicialización
        """
        try:
            return await self.git_manager.init_repository(repo_path, bare, initial_branch)
        except Exception as e:
            raise GitError(f"Error inicializando repositorio: {str(e)}")
    
    async def add(
        self, 
        repo_url: str, 
        files: Optional[List[str]] = None,
        all_files: bool = False,
        update: bool = False
    ) -> Dict[str, Any]:
        """
        Agrega archivos al staging area
        
        Args:
            repo_url: URL del repositorio
            files: Lista de archivos específicos (opcional)
            all_files: Si agregar todos los archivos (git add .)
            update: Si solo actualizar archivos ya tracked (git add -u)
            
        Returns:
            Resultado de la operación add
        """
        try:
            return await self.git_manager.add_files(repo_url, files, all_files, update)
        except Exception as e:
            raise GitError(f"Error agregando archivos: {str(e)}")