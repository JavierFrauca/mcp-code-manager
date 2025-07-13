"""
Servicio para gestión de operaciones Git
"""
import os
import hashlib
import tempfile
from typing import Dict, List, Any, Optional
from git import Repo, GitCommandError, InvalidGitRepositoryError
import git

from utils.exceptions import GitError, RepositoryError
from services.file_manager import FileManager

class GitManager:
    """Gestor de operaciones Git"""
    
    def __init__(self):
        self.file_manager = FileManager()
        self.cache_dir = os.path.join(tempfile.gettempdir(), "mcp_code_manager")
    
    async def clone_repository(self, repo_url: str, force: bool = False) -> str:
        """
        Clona un repositorio localmente
        
        Args:
            repo_url: URL del repositorio
            force: Si forzar la clonación (eliminar existente)
            
        Returns:
            Ruta local del repositorio
        """
        try:
            # Generar ruta local única
            repo_hash = hashlib.md5(repo_url.encode()).hexdigest()[:8]
            repo_name = self._extract_repo_name(repo_url)
            local_path = os.path.join(self.cache_dir, f"{repo_name}_{repo_hash}")
            
            # Si ya existe y force=True, eliminar
            if os.path.exists(local_path) and force:
                import shutil
                shutil.rmtree(local_path)
            
            # Si no existe, clonar
            if not os.path.exists(local_path):
                os.makedirs(self.cache_dir, exist_ok=True)
                Repo.clone_from(repo_url, local_path)
            
            return local_path
            
        except GitCommandError as e:
            raise GitError(f"Error clonando repositorio: {str(e)}")
        except Exception as e:
            raise RepositoryError(f"Error en operación de repositorio: {str(e)}")
    
    async def get_detailed_status(self, repo_url: str) -> Dict[str, Any]:
        """
        Obtiene el estado detallado del repositorio
        
        Args:
            repo_url: URL del repositorio
            
        Returns:
            Estado completo del repositorio
        """
        try:
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            # Información básica
            current_branch = repo.active_branch.name
            
            # Verificar estado con remoto (opcional, no obligatorio)
            ahead, behind = 0, 0
            try:
                if repo.remotes:
                    origin = repo.remotes.origin
                    try:
                        origin.fetch()
                        ahead, behind = self._calculate_ahead_behind(repo)
                    except Exception:
                        pass  # Continuar aunque no se pueda hacer fetch
            except Exception:
                pass  # No hay remotos configurados
            
            # Archivos staged
            staged_files = []
            try:
                for item in repo.index.diff("HEAD"):
                    staged_files.append({
                        "file": item.a_path,
                        "status": item.change_type
                    })
            except Exception:
                # Primer commit - obtener archivos staged de otra manera
                for path, stage in repo.index.entries.keys():
                    staged_files.append({
                        "file": path,
                        "status": "A"  # Added (nuevo archivo)
                    })
            
            # Archivos unstaged (modificados)
            unstaged_files = []
            try:
                for item in repo.index.diff(None):
                    unstaged_files.append({
                        "file": item.a_path,
                        "status": item.change_type
                    })
            except Exception:
                pass
            
            # Archivos untracked
            untracked_files = repo.untracked_files
            
            # Verificar conflictos
            conflicts = []
            try:
                unmerged = repo.index.unmerged_blobs()
                conflicts = list(unmerged.keys()) if unmerged else []
            except Exception:
                pass
            
            # Último commit
            last_commit = None
            try:
                commit = repo.head.commit
                last_commit = {
                    "hash": commit.hexsha[:8],
                    "author": commit.author.name,
                    "date": commit.committed_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    "message": commit.message.strip()
                }
            except Exception:
                # No hay commits aún
                pass
            
            # Determinar si el repositorio está "limpio"
            is_clean = (
                len(staged_files) == 0 and 
                len(unstaged_files) == 0 and 
                len(untracked_files) == 0 and 
                len(conflicts) == 0
            )
            
            # Generar resumen
            if is_clean:
                summary = "Working tree clean"
            else:
                parts = []
                if staged_files:
                    parts.append(f"{len(staged_files)} staged")
                if unstaged_files:
                    parts.append(f"{len(unstaged_files)} modified")
                if untracked_files:
                    parts.append(f"{len(untracked_files)} untracked")
                if conflicts:
                    parts.append(f"{len(conflicts)} conflicts")
                summary = ", ".join(parts)
            
            return {
                "success": True,
                "clean": is_clean,
                "branch": current_branch,
                "summary": summary,
                "staged": staged_files,
                "unstaged": unstaged_files,
                "untracked": untracked_files,
                "conflicts": conflicts,
                "ahead": ahead,
                "behind": behind,
                "last_commit": last_commit
            }
            
        except InvalidGitRepositoryError:
            raise GitError("El directorio no es un repositorio Git válido")
        except Exception as e:
            raise GitError(f"Error obteniendo estado del repositorio: {str(e)}")
            
            # Conflictos (si los hay)
            conflicts = []
            try:
                for item in repo.index.unmerged_blobs():
                    conflicts.append(item)
            except Exception:
                pass
            
            # Estado limpio
            is_clean = (
                len(staged_files) == 0 and 
                len(unstaged_files) == 0 and 
                len(untracked_files) == 0 and 
                len(conflicts) == 0
            )
            
            # Generar resumen
            summary_parts = []
            if ahead > 0:
                summary_parts.append(f"{ahead} commits ahead")
            if behind > 0:
                summary_parts.append(f"{behind} commits behind")
            if len(staged_files) > 0:
                summary_parts.append(f"{len(staged_files)} staged files")
            if len(unstaged_files) > 0:
                summary_parts.append(f"{len(unstaged_files)} unstaged files")
            if len(untracked_files) > 0:
                summary_parts.append(f"{len(untracked_files)} untracked files")
            if len(conflicts) > 0:
                summary_parts.append(f"{len(conflicts)} conflicts")
            
            summary = ", ".join(summary_parts) if summary_parts else "Working tree clean"
            
            return {
                "branch": current_branch,
                "behind": behind,
                "ahead": ahead,
                "staged": staged_files,
                "unstaged": unstaged_files,
                "untracked": untracked_files,
                "conflicts": conflicts,
                "clean": is_clean,
                "summary": summary,
                "last_commit": {
                    "hash": repo.head.commit.hexsha[:8],
                    "message": repo.head.commit.message.strip(),
                    "author": repo.head.commit.author.name,
                    "date": repo.head.commit.committed_datetime.isoformat()
                }
            }
            
        except InvalidGitRepositoryError:
            raise GitError("El directorio no es un repositorio Git válido")
        except Exception as e:
            raise GitError(f"Error obteniendo estado del repositorio: {str(e)}")
    
    async def get_diff(
        self, 
        repo_url: str, 
        file_path: Optional[str] = None, 
        staged: bool = False
    ) -> Dict[str, Any]:
        """
        Obtiene las diferencias del repositorio
        
        Args:
            repo_url: URL del repositorio
            file_path: Archivo específico (opcional)
            staged: Si mostrar diferencias staged
            
        Returns:
            Diferencias encontradas
        """
        try:
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            # Determinar qué comparar
            if staged:
                # Diferencias entre staged y HEAD
                try:
                    diff_index = repo.index.diff("HEAD")
                except Exception:
                    # Primer commit - diferencias entre staged y empty tree
                    diff_index = repo.index.diff(None)
            else:
                # Diferencias entre working tree e index
                diff_index = repo.index.diff(None)
            
            # Filtrar por archivo si se especifica
            if file_path:
                diff_index = [d for d in diff_index if d.a_path == file_path or d.b_path == file_path]
            
            # Procesar diferencias
            if not diff_index:
                return {
                    "success": True,
                    "message": "No hay diferencias" if not file_path else f"No hay diferencias en {file_path}",
                    "diff": "",
                    "type": "staged" if staged else "unstaged",
                    "file_path": file_path,
                    "total_files": 0
                }
            
            # Generar diff text
            diff_text_parts = []
            
            for diff_item in diff_index:
                file_name = diff_item.a_path or diff_item.b_path
                diff_text_parts.append(f"--- a/{file_name}")
                diff_text_parts.append(f"+++ b/{file_name}")
                
                try:
                    if hasattr(diff_item, 'diff'):
                        diff_content = diff_item.diff.decode('utf-8')
                    else:
                        # Usar git show para obtener el diff
                        diff_content = repo.git.diff(diff_item.a_path, cached=staged)
                    diff_text_parts.append(diff_content)
                except Exception:
                    diff_text_parts.append("Binary file or encoding error")
            
            full_diff = "\n".join(diff_text_parts)
            
            return {
                "success": True,
                "message": f"Diferencias {'staged' if staged else 'unstaged'} encontradas",
                "diff": full_diff,
                "type": "staged" if staged else "unstaged",
                "file_path": file_path,
                "total_files": len(diff_index)
            }
            
        except Exception as e:
            raise GitError(f"Error obteniendo diferencias: {str(e)}")
    
    async def commit_changes(
        self, 
        repo_url: str, 
        message: str,
        files: Optional[List[str]] = None,
        add_all: bool = False
    ) -> Dict[str, Any]:
        """
        Realiza un commit con los cambios
        
        Args:
            repo_url: URL del repositorio
            message: Mensaje del commit
            files: Archivos específicos (opcional)
            add_all: Si añadir todos los archivos modificados
            
        Returns:
            Información del commit
        """
        try:
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            # Configurar usuario por defecto si no está configurado
            try:
                # Verificar si hay configuración de usuario
                try:
                    repo.config_reader().get_value("user", "name")
                    repo.config_reader().get_value("user", "email")
                except Exception:
                    # No hay configuración, establecer una por defecto
                    with repo.config_writer() as git_config:
                        git_config.set_value("user", "name", "MCP Code Manager")
                        git_config.set_value("user", "email", "mcp@codemanager.local")
            except Exception as e:
                print(f"Warning: No se pudo configurar usuario Git: {e}")
            
            # Añadir archivos al stage
            if add_all:
                repo.git.add(A=True)
            elif files:
                for file in files:
                    repo.index.add([file])
            
            # Verificar que hay cambios para commitear
            if not repo.index.diff("HEAD"):
                # Si es el primer commit, verificar que hay archivos staged
                try:
                    staged_files = repo.index.diff("HEAD")
                except Exception:
                    # Probablemente primer commit - verificar archivos en index
                    if not list(repo.index.entries.keys()):
                        raise GitError("No hay cambios staged para commitear")
            
            # Realizar commit
            commit = repo.index.commit(message)
            
            # Obtener información del commit
            try:
                files_changed = len(repo.index.diff(commit.parents[0])) if commit.parents else len(list(repo.index.entries.keys()))
            except Exception:
                files_changed = len(list(repo.index.entries.keys()))
            
            return {
                "success": True,
                "status": "committed",
                "commit_hash": commit.hexsha,
                "short_hash": commit.hexsha[:8],
                "message": message,
                "author": commit.author.name,
                "email": commit.author.email,
                "date": commit.committed_datetime.isoformat(),
                "files_changed": files_changed,
                "branch": repo.active_branch.name,
                "committed_files": [str(f) for f in (files or ["All staged files"])]
            }
            
        except GitCommandError as e:
            raise GitError(f"Error en commit: {str(e)}")
        except Exception as e:
            raise GitError(f"Error realizando commit: {str(e)}")
    
    async def push_changes(
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
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            # Determinar rama
            if not branch:
                branch = repo.active_branch.name
            
            # Verificar que hay remoto
            if not repo.remotes:
                raise GitError("No hay remotos configurados")
            
            # Realizar push
            origin = repo.remotes.origin
            
            if force:
                push_info = origin.push(f"{branch}:{branch}", force=True)
            else:
                push_info = origin.push(f"{branch}:{branch}")
            
            # Procesar resultado
            pushed_commits = 0
            remote_url = str(origin.url) if hasattr(origin, 'url') else "unknown"
            
            for info in push_info:
                if hasattr(info, 'summary'):
                    pushed_commits += 1
            
            return {
                "success": True,
                "message": f"Push completado exitosamente",
                "pushed_branch": branch,
                "commits_pushed": pushed_commits,
                "remote_url": remote_url,
                "force": force
            }
            
        except GitCommandError as e:
            raise GitError(f"Error en push: {str(e)}")
        except Exception as e:
            raise GitError(f"Error subiendo cambios: {str(e)}")
    
    async def pull_changes(
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
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            # Determinar rama
            if not branch:
                branch = repo.active_branch.name
            
            # Verificar que hay remoto
            if not repo.remotes:
                raise GitError("No hay remotos configurados")
            
            # Realizar pull
            origin = repo.remotes.origin
            
            if rebase:
                pull_info = origin.pull(rebase=True)
            else:
                pull_info = origin.pull()
            
            # Procesar resultado
            commits_received = 0
            files_changed = []
            
            for info in pull_info:
                if hasattr(info, 'old_commit') and hasattr(info, 'commit'):
                    if info.old_commit and info.commit:
                        commits_received += 1
                        
            return {
                "success": True,
                "message": f"Pull completado exitosamente",
                "updated_branch": branch,
                "commits_received": commits_received,
                "files_changed": files_changed,
                "rebase": rebase
            }
            
        except GitCommandError as e:
            raise GitError(f"Error en pull: {str(e)}")
        except Exception as e:
            raise GitError(f"Error descargando cambios: {str(e)}")
    
    async def manage_branch(
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
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            if action == "list":
                # Listar todas las ramas
                local_branches = [{"name": branch.name, "current": branch == repo.active_branch, "remote": False} 
                                for branch in repo.branches]
                
                remote_branches = []
                if repo.remotes:
                    try:
                        for ref in repo.remotes.origin.refs:
                            if not ref.name.endswith('/HEAD'):
                                remote_branches.append({
                                    "name": ref.name,
                                    "current": False,
                                    "remote": True
                                })
                    except Exception:
                        pass
                
                all_branches = local_branches + remote_branches
                
                return {
                    "success": True,
                    "message": f"Ramas listadas: {len(all_branches)} encontradas",
                    "action": "list",
                    "branches": all_branches
                }
            
            elif action == "create":
                if not branch_name:
                    raise GitError("Nombre de rama requerido para crear")
                
                # Determinar rama base
                base_branch = from_branch or repo.active_branch.name
                
                # Crear nueva rama
                new_branch = repo.create_head(branch_name, base_branch)
                
                return {
                    "success": True,
                    "message": f"Rama '{branch_name}' creada desde '{base_branch}'",
                    "action": "create",
                    "branch_name": branch_name,
                    "from_branch": base_branch
                }
            
            elif action == "switch":
                if not branch_name:
                    raise GitError("Nombre de rama requerido para cambiar")
                
                # Cambiar a la rama
                repo.heads[branch_name].checkout()
                
                return {
                    "success": True,
                    "message": f"Cambiado a rama '{branch_name}'",
                    "action": "switch",
                    "branch_name": branch_name
                }
            
            elif action == "delete":
                if not branch_name:
                    raise GitError("Nombre de rama requerido para eliminar")
                
                # No permitir eliminar la rama actual
                if branch_name == repo.active_branch.name:
                    raise GitError("No se puede eliminar la rama actual")
                
                # Eliminar rama
                repo.delete_head(branch_name, force=True)
                
                return {
                    "success": True,
                    "message": f"Rama '{branch_name}' eliminada",
                    "action": "delete",
                    "branch_name": branch_name
                }
            
            elif action == "rename":
                if not branch_name:
                    raise GitError("Nuevo nombre de rama requerido para renombrar")
                
                old_name = repo.active_branch.name
                repo.active_branch.rename(branch_name)
                
                return {
                    "success": True,
                    "message": f"Rama '{old_name}' renombrada a '{branch_name}'",
                    "action": "rename",
                    "old_name": old_name,
                    "new_name": branch_name
                }
            
            else:
                raise GitError(f"Acción de rama no válida: {action}")
                
        except GitCommandError as e:
            raise GitError(f"Error en operación de rama: {str(e)}")
        except Exception as e:
            raise GitError(f"Error gestionando rama: {str(e)}")
    
    async def merge_branches(
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
            target_branch: Rama destino (opcional)
            no_ff: Si no usar fast-forward
            
        Returns:
            Resultado del merge
        """
        try:
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            # Determinar rama destino
            if target_branch:
                repo.heads[target_branch].checkout()
            else:
                target_branch = repo.active_branch.name
            
            # Verificar que las ramas existen
            if source_branch not in [b.name for b in repo.branches]:
                raise GitError(f"La rama origen '{source_branch}' no existe")
            
            # Realizar merge
            try:
                if no_ff:
                    repo.git.merge(source_branch, no_ff=True)
                    merge_type = "no-fast-forward"
                else:
                    merge_result = repo.git.merge(source_branch)
                    merge_type = "fast-forward" if "Fast-forward" in merge_result else "merge commit"
                
                # Obtener archivos fusionados
                files_merged = []
                try:
                    # Obtener archivos modificados en el último commit
                    last_commit = repo.head.commit
                    if last_commit.parents:
                        diff = last_commit.diff(last_commit.parents[0])
                        files_merged = [item.a_path for item in diff]
                except Exception:
                    pass
                
                return {
                    "success": True,
                    "message": f"Merge completado: {source_branch} → {target_branch}",
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "merge_type": merge_type,
                    "files_merged": files_merged,
                    "conflicts": []
                }
                
            except GitCommandError as e:
                # Verificar si hay conflictos
                conflicts = []
                try:
                    unmerged = repo.index.unmerged_blobs()
                    conflicts = list(unmerged.keys()) if unmerged else []
                except Exception:
                    pass
                
                if conflicts:
                    return {
                        "success": False,
                        "message": f"Merge con conflictos: {source_branch} → {target_branch}",
                        "source_branch": source_branch,
                        "target_branch": target_branch,
                        "merge_type": "conflict",
                        "files_merged": [],
                        "conflicts": conflicts
                    }
                else:
                    raise GitError(f"Error en merge: {str(e)}")
                    
        except GitCommandError as e:
            raise GitError(f"Error en merge: {str(e)}")
        except Exception as e:
            raise GitError(f"Error fusionando ramas: {str(e)}")
    
    async def manage_stash(
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
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            if action == "save":
                # Guardar en stash
                stash_message = message or "Stash automático"
                repo.git.stash("save", stash_message)
                
                # Obtener número de stashes
                stash_list = repo.git.stash("list").splitlines()
                
                return {
                    "success": True,
                    "message": f"Stash guardado: {stash_message}",
                    "action": "save",
                    "stash_message": stash_message,
                    "stash_count": len(stash_list)
                }
            
            elif action == "list":
                # Listar stashes
                stash_list_raw = repo.git.stash("list").splitlines()
                stashes = []
                
                for stash_entry in stash_list_raw:
                    # Parsear formato: stash@{0}: WIP on main: abc1234 message
                    parts = stash_entry.split(": ", 2)
                    if len(parts) >= 3:
                        stashes.append({
                            "index": parts[0],
                            "message": parts[2],
                            "date": "Unknown"  # Git stash list no incluye fecha por defecto
                        })
                
                return {
                    "success": True,
                    "message": f"Stashes listados: {len(stashes)} encontrados",
                    "action": "list",
                    "stashes": stashes,
                    "count": len(stashes)
                }
            
            elif action == "pop":
                # Recuperar último stash
                index = stash_index or 0
                repo.git.stash("pop", f"stash@{{{index}}}")
                
                return {
                    "success": True,
                    "message": f"Stash aplicado y eliminado: stash@{{{index}}}",
                    "action": "pop",
                    "index": index
                }
            
            elif action == "apply":
                # Aplicar stash sin eliminarlo
                index = stash_index or 0
                repo.git.stash("apply", f"stash@{{{index}}}")
                
                return {
                    "success": True,
                    "message": f"Stash aplicado: stash@{{{index}}}",
                    "action": "apply",
                    "index": index
                }
            
            elif action == "drop":
                # Eliminar stash
                index = stash_index or 0
                repo.git.stash("drop", f"stash@{{{index}}}")
                
                return {
                    "success": True,
                    "message": f"Stash eliminado: stash@{{{index}}}",
                    "action": "drop",
                    "index": index
                }
            
            else:
                raise GitError(f"Acción de stash no válida: {action}")
                
        except GitCommandError as e:
            raise GitError(f"Error en operación de stash: {str(e)}")
        except Exception as e:
            raise GitError(f"Error gestionando stash: {str(e)}")
    
    async def get_commit_history(
        self, 
        repo_url: str, 
        limit: int = 10,
        branch: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene el historial de commits
        
        Args:
            repo_url: URL del repositorio
            limit: Número de commits
            branch: Rama específica (opcional)
            file_path: Archivo específico (opcional)
            
        Returns:
            Historial de commits
        """
        try:
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            # Determinar rama robustamente
            branch_to_use = branch
            if branch_to_use:
                # Si la rama no existe, usar rama activa
                if branch_to_use not in [b.name for b in repo.branches]:
                    branch_to_use = repo.active_branch.name
            # Si no se especifica rama, usar rama activa
            if not branch_to_use:
                branch_to_use = repo.active_branch.name
            
            # Verificar que hay commits
            try:
                commits = list(repo.iter_commits(branch_to_use, max_count=limit, paths=file_path))
            except Exception:
                # No hay commits aún
                return {
                    "success": True,
                    "message": f"No hay commits en la rama '{branch_to_use}'",
                    "branch": branch_to_use,
                    "file_path": file_path,
                    "limit": limit,
                    "total_commits": 0,
                    "commits": []
                }
            
            # Procesar commits
            commit_list = []
            for commit in commits:
                try:
                    commit_info = {
                        "hash": commit.hexsha[:8],
                        "message": commit.message.strip(),
                        "author": commit.author.name,
                        "email": commit.author.email,
                        "date": commit.committed_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Agregar estadísticas si están disponibles
                    try:
                        commit_info["stats"] = {
                            "files": len(commit.stats.files),
                            "insertions": commit.stats.total['insertions'],
                            "deletions": commit.stats.total['deletions']
                        }
                    except Exception:
                        commit_info["stats"] = {"files": 0, "insertions": 0, "deletions": 0}
                    
                    commit_list.append(commit_info)
                except Exception as e:
                    # Si falla procesando un commit, agregarlo con información básica
                    commit_list.append({
                        "hash": str(commit)[:8],
                        "message": "Error procesando commit",
                        "author": "Unknown",
                        "email": "",
                        "date": "Unknown",
                        "stats": {"files": 0, "insertions": 0, "deletions": 0}
                    })
            
            return {
                "success": True,
                "message": f"Historial de commits obtenido ({len(commit_list)} commits)",
                "branch": branch_to_use,
                "file_path": file_path,
                "limit": limit,
                "total_commits": len(commit_list),
                "commits": commit_list
            }
            
        except GitCommandError as e:
            raise GitError(f"Error obteniendo historial: {str(e)}")
        except Exception as e:
            raise GitError(f"Error en historial de commits: {str(e)}")
    
    async def reset_repository(
        self, 
        repo_url: str, 
        mode: str = "mixed",
        commit_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resetea el repositorio a un estado anterior
        
        Args:
            repo_url: URL del repositorio
            mode: Modo de reset
            commit_hash: Hash del commit (opcional)
            
        Returns:
            Resultado del reset
        """
        try:
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            # Determinar commit objetivo
            target = commit_hash or "HEAD"
            
            # Obtener archivos que serán afectados antes del reset
            files_affected = []
            try:
                if mode in ["mixed", "hard"]:
                    # Obtener archivos staged que se perderán
                    for item in repo.index.diff("HEAD"):
                        files_affected.append(item.a_path)
                if mode == "hard":
                    # Obtener archivos modificados que se perderán
                    for item in repo.index.diff(None):
                        files_affected.append(item.a_path)
            except Exception:
                pass
            
            # Realizar reset
            if mode == "soft":
                repo.git.reset("--soft", target)
            elif mode == "mixed":
                repo.git.reset("--mixed", target)
            elif mode == "hard":
                repo.git.reset("--hard", target)
            else:
                raise GitError(f"Modo de reset no válido: {mode}")
            
            return {
                "success": True,
                "message": f"Reset {mode} completado a {target}",
                "reset_to": target,
                "mode": mode,
                "files_affected": files_affected,
                "current_commit": repo.head.commit.hexsha[:8]
            }
            
        except GitCommandError as e:
            raise GitError(f"Error en reset: {str(e)}")
        except Exception as e:
            raise GitError(f"Error reseteando repositorio: {str(e)}")
    
    async def manage_tag(
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
            action: Acción a realizar
            tag_name: Nombre del tag
            message: Mensaje del tag
            commit_hash: Hash del commit
            
        Returns:
            Resultado de la operación
        """
        try:
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            if action == "list":
                tags_info = []
                for tag in repo.tags:
                    try:
                        tag_info = {
                            "name": tag.name,
                            "commit": tag.commit.hexsha[:8],
                            "date": tag.commit.committed_datetime.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Verificar si es tag anotado
                        if hasattr(tag.tag, 'message') and tag.tag.message:
                            tag_info["message"] = tag.tag.message.strip()
                        
                        tags_info.append(tag_info)
                    except Exception:
                        # Tag simple sin información adicional
                        tags_info.append({"name": tag.name})
                
                return {
                    "success": True,
                    "message": f"Tags listados: {len(tags_info)} encontrados",
                    "action": "list",
                    "tags": tags_info,
                    "count": len(tags_info)
                }
            
            elif action == "create":
                if not tag_name:
                    raise GitError("Nombre de tag requerido")
                
                target = commit_hash or repo.head.commit
                
                if message:
                    # Tag anotado
                    tag = repo.create_tag(tag_name, ref=target, message=message)
                    tag_type = "anotado"
                else:
                    # Tag ligero
                    tag = repo.create_tag(tag_name, ref=target)
                    tag_type = "ligero"
                
                return {
                    "success": True,
                    "message": f"Tag {tag_type} '{tag_name}' creado",
                    "action": "create",
                    "tag_name": tag_name,
                    "tag_commit": target.hexsha[:8] if hasattr(target, 'hexsha') else str(target)[:8],
                    "message": message
                }
            
            elif action == "delete":
                if not tag_name:
                    raise GitError("Nombre de tag requerido")
                
                repo.delete_tag(tag_name)
                
                return {
                    "success": True,
                    "message": f"Tag '{tag_name}' eliminado",
                    "action": "delete",
                    "tag_name": tag_name
                }
            
            elif action == "push":
                if not repo.remotes:
                    raise GitError("No hay remotos configurados")
                
                remote_url = str(repo.remotes.origin.url) if hasattr(repo.remotes.origin, 'url') else "unknown"
                
                if tag_name:
                    repo.remotes.origin.push(tag_name)
                    message = f"Tag '{tag_name}' subido al remoto"
                else:
                    repo.remotes.origin.push(tags=True)
                    message = "Todos los tags subidos al remoto"
                
                return {
                    "success": True,
                    "message": message,
                    "action": "push",
                    "tag_name": tag_name or "all",
                    "remote_url": remote_url
                }
            
            else:
                raise GitError(f"Acción de tag no válida: {action}")
                
        except GitCommandError as e:
            raise GitError(f"Error en operación de tag: {str(e)}")
        except Exception as e:
            raise GitError(f"Error gestionando tag: {str(e)}")
    
    async def manage_remote(
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
            action: Acción a realizar
            remote_name: Nombre del remoto
            remote_url: URL del remoto
            
        Returns:
            Resultado de la operación
        """
        try:
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            if action == "list":
                remotes_info = []
                for remote in repo.remotes:
                    remote_info = {
                        "name": remote.name,
                        "url": list(remote.urls)[0] if remote.urls else "unknown"
                    }
                    
                    # Verificar si hay URLs diferentes para fetch y push
                    urls = list(remote.urls)
                    if len(urls) > 1:
                        remote_info["fetch_url"] = urls[0]
                        remote_info["push_url"] = urls[1]
                    
                    remotes_info.append(remote_info)
                
                return {
                    "success": True,
                    "message": f"Remotos listados: {len(remotes_info)} encontrados",
                    "action": "list",
                    "remotes": remotes_info
                }
            
            elif action == "add":
                if not remote_name or not remote_url:
                    raise GitError("Nombre y URL de remoto requeridos")
                
                repo.create_remote(remote_name, remote_url)
                
                return {
                    "success": True,
                    "message": f"Remoto '{remote_name}' agregado",
                    "action": "add",
                    "remote_name": remote_name,
                    "remote_url": remote_url
                }
            
            elif action == "remove":
                if not remote_name:
                    raise GitError("Nombre de remoto requerido")
                
                repo.delete_remote(remote_name)
                
                return {
                    "success": True,
                    "message": f"Remoto '{remote_name}' eliminado",
                    "action": "remove",
                    "remote_name": remote_name
                }
            
            elif action == "set-url":
                if not remote_name or not remote_url:
                    raise GitError("Nombre y URL de remoto requeridos")
                
                remote = repo.remotes[remote_name]
                remote.set_url(remote_url)
                
                return {
                    "success": True,
                    "message": f"URL del remoto '{remote_name}' actualizada",
                    "action": "set-url",
                    "remote_name": remote_name,
                    "remote_url": remote_url
                }
            
            else:
                raise GitError(f"Acción de remoto no válida: {action}")
                
        except GitCommandError as e:
            raise GitError(f"Error en operación de remoto: {str(e)}")
        except Exception as e:
            raise GitError(f"Error gestionando remoto: {str(e)}")
    
    async def _ensure_repo_exists(self, repo_url: str) -> str:
        """
        Asegura que el repositorio existe localmente
        
        Args:
            repo_url: URL del repositorio o ruta local
            
        Returns:
            Ruta local del repositorio
        """
        try:
            # Detectar si es una ruta local existente
            if os.path.exists(repo_url):
                # Es una ruta local existente
                path = os.path.abspath(repo_url)
                # Verificar que sea un repositorio git válido
                if os.path.exists(os.path.join(path, '.git')):
                    return path
                else:
                    raise GitError(f"El directorio '{repo_url}' no es un repositorio Git válido")
            
            # Si es "." usar el directorio actual
            if repo_url == ".":
                current_dir = os.getcwd()
                if os.path.exists(os.path.join(current_dir, '.git')):
                    return current_dir
                else:
                    raise GitError(f"El directorio actual '{current_dir}' no es un repositorio Git válido")
            
            # Para rutas relativas, convertir a absolutas
            if not repo_url.startswith(('http://', 'https://', 'git://', 'ssh://', 'git@')):
                abs_path = os.path.abspath(repo_url)
                if os.path.exists(abs_path):
                    if os.path.exists(os.path.join(abs_path, '.git')):
                        return abs_path
                    else:
                        raise GitError(f"El directorio '{repo_url}' no es un repositorio Git válido")
                else:
                    raise GitError(f"El directorio '{repo_url}' no existe")
            
            # Si llegamos aquí, es una URL remota - usar el comportamiento original
            try:
                return await self.file_manager.get_repo_path(repo_url)
            except RepositoryError:
                # Si no existe, clonarlo
                return await self.clone_repository(repo_url)
                
        except GitError:
            # Re-lanzar errores Git específicos
            raise
        except Exception as e:
            raise GitError(f"Error accediendo al repositorio: {str(e)}")
    
    def _calculate_ahead_behind(self, repo: Repo) -> tuple:
        """
        Calcula commits ahead/behind con respecto al remoto
        
        Args:
            repo: Repositorio Git
            
        Returns:
            Tupla (ahead, behind)
        """
        try:
            current_branch = repo.active_branch
            remote_branch = f"origin/{current_branch.name}"
            
            if remote_branch in repo.refs:
                ahead = len(list(repo.iter_commits(f"{remote_branch}..{current_branch.name}")))
                behind = len(list(repo.iter_commits(f"{current_branch.name}..{remote_branch}")))
                return ahead, behind
            else:
                return 0, 0
                
        except Exception:
            return 0, 0
    
    def _extract_repo_name(self, repo_url: str) -> str:
        """
        Extrae el nombre del repositorio de la URL
        
        Args:
            repo_url: URL del repositorio
            
        Returns:
            Nombre del repositorio
        """
        clean_url = repo_url.rstrip('/').replace('.git', '')
        parts = clean_url.split('/')
        return parts[-1] if parts else 'repo'

    async def init_repository(
        self, 
        repo_path: str, 
        bare: bool = False,
        initial_branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inicializa un nuevo repositorio Git
        
        Args:
            repo_path: Ruta donde inicializar
            bare: Si crear repositorio bare
            initial_branch: Nombre de la rama inicial
            
        Returns:
            Información del repositorio creado
        """
        try:
            # Verificar si ya existe un repositorio
            if os.path.exists(os.path.join(repo_path, '.git')):
                return {
                    "success": False,
                    "message": "Ya existe un repositorio Git en esta ubicación",
                    "path": repo_path
                }
            
            # Crear directorio si no existe
            os.makedirs(repo_path, exist_ok=True)
            
            # Inicializar repositorio con rama main por defecto
            if not initial_branch:
                initial_branch = "main"
            
            repo = Repo.init(repo_path, bare=bare, initial_branch=initial_branch)
            
            # Configurar usuario por defecto si no está configurado
            try:
                # Verificar si ya hay configuración global
                try:
                    repo.config_reader().get_value("user", "name")
                    repo.config_reader().get_value("user", "email")
                except Exception:
                    # No hay configuración, establecer una por defecto
                    with repo.config_writer() as git_config:
                        git_config.set_value("user", "name", "MCP Code Manager")
                        git_config.set_value("user", "email", "mcp@codemanager.local")
                        git_config.set_value("init", "defaultBranch", "main")
                        
            except Exception as e:
                # Si falla la configuración, solo loggear pero continuar
                print(f"Warning: No se pudo configurar usuario Git: {e}")
            
            return {
                "success": True,
                "message": f"Repositorio {'bare ' if bare else ''}inicializado correctamente",
                "path": repo_path,
                "bare": bare,
                "initial_branch": initial_branch
            }
            
        except Exception as e:
            raise GitError(f"Error inicializando repositorio: {str(e)}")
    
    async def add_files(
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
            files: Lista de archivos específicos
            all_files: Si agregar todos los archivos
            update: Si solo actualizar archivos tracked
            
        Returns:
            Resultado de la operación
        """
        try:
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            added_files = []
            
            if all_files:
                # git add .
                repo.git.add('.')
                added_files = ["Todos los archivos"]
                
            elif update:
                # git add -u
                repo.git.add('-u')
                added_files = ["Archivos tracked modificados"]
                
            elif files:
                # git add <files>
                for file_path in files:
                    try:
                        repo.git.add(file_path)
                        added_files.append(file_path)
                    except GitCommandError as e:
                        # Continuar con otros archivos si uno falla
                        continue
            else:
                return {
                    "success": False,
                    "message": "Debe especificar archivos, usar all_files=True o update=True"
                }
            
            # Verificar archivos en staging
            staged_files = []
            try:
                for item in repo.index.diff("HEAD"):
                    staged_files.append({
                        "file": item.a_path,
                        "status": item.change_type
                    })
            except:
                # Si no hay HEAD (primer commit), obtener archivos staged
                staged_files = [{"file": f, "status": "A"} for f in repo.git.diff("--cached", "--name-only").splitlines()]
            
            return {
                "success": True,
                "message": f"Archivos agregados al staging area: {len(added_files)}",
                "added_files": added_files,
                "staged_files": staged_files,
                "total_staged": len(staged_files)
            }
            
        except Exception as e:
            raise GitError(f"Error agregando archivos: {str(e)}")