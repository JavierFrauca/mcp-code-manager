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
            
            # Verificar estado con remoto
            origin = repo.remotes.origin
            try:
                origin.fetch()
            except Exception:
                pass  # Continuar aunque no se pueda hacer fetch
            
            # Calcular ahead/behind
            ahead, behind = self._calculate_ahead_behind(repo)
            
            # Archivos staged
            staged_files = []
            for item in repo.index.diff("HEAD"):
                staged_files.append({
                    "file": item.a_path,
                    "status": item.change_type
                })
            
            # Archivos unstaged (modificados)
            unstaged_files = []
            for item in repo.index.diff(None):
                unstaged_files.append({
                    "file": item.a_path,
                    "status": item.change_type
                })
            
            # Archivos untracked
            untracked_files = repo.untracked_files
            
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
                diff_index = repo.index.diff("HEAD")
            else:
                # Diferencias entre working tree e index
                diff_index = repo.index.diff(None)
            
            # Filtrar por archivo si se especifica
            if file_path:
                diff_index = [d for d in diff_index if d.a_path == file_path or d.b_path == file_path]
            
            # Procesar diferencias
            diffs = []
            for diff_item in diff_index:
                diff_text = ""
                try:
                    diff_text = diff_item.diff.decode('utf-8')
                except Exception:
                    diff_text = "Binary file or encoding error"
                
                diffs.append({
                    "file": diff_item.a_path or diff_item.b_path,
                    "change_type": diff_item.change_type,
                    "diff": diff_text,
                    "insertions": diff_text.count('\n+') if diff_text else 0,
                    "deletions": diff_text.count('\n-') if diff_text else 0
                })
            
            return {
                "type": "staged" if staged else "unstaged",
                "file_path": file_path,
                "total_files": len(diffs),
                "diffs": diffs
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
            
            # Añadir archivos al stage
            if add_all:
                repo.git.add(A=True)
            elif files:
                for file in files:
                    repo.index.add([file])
            
            # Verificar que hay cambios para commitear
            if not repo.index.diff("HEAD"):
                raise GitError("No hay cambios staged para commitear")
            
            # Realizar commit
            commit = repo.index.commit(message)
            
            # Información del commit
            files_changed = len(repo.index.diff(commit.parents[0])) if commit.parents else 0
            
            return {
                "status": "committed",
                "commit_hash": commit.hexsha,
                "short_hash": commit.hexsha[:8],
                "message": message,
                "author": commit.author.name,
                "email": commit.author.email,
                "date": commit.committed_datetime.isoformat(),
                "files_changed": files_changed,
                "branch": repo.active_branch.name
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
            
            # Realizar push
            origin = repo.remotes.origin
            
            if force:
                push_info = origin.push(f"{branch}:{branch}", force=True)
            else:
                push_info = origin.push(f"{branch}:{branch}")
            
            # Procesar resultado
            result = {
                "status": "pushed",
                "branch": branch,
                "remote": "origin",
                "force": force,
                "results": []
            }
            
            for info in push_info:
                result["results"].append({
                    "local_ref": str(info.local_ref),
                    "remote_ref": str(info.remote_ref),
                    "flags": info.flags,
                    "summary": info.summary
                })
            
            return result
            
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
            
            # Realizar pull
            origin = repo.remotes.origin
            
            if rebase:
                pull_info = origin.pull(rebase=True)
            else:
                pull_info = origin.pull()
            
            # Procesar resultado
            result = {
                "status": "pulled",
                "branch": branch,
                "remote": "origin",
                "rebase": rebase,
                "results": []
            }
            
            for info in pull_info:
                result["results"].append({
                    "ref": str(info.ref),
                    "flags": info.flags,
                    "note": info.note,
                    "old_commit": info.old_commit.hexsha[:8] if info.old_commit else None,
                    "commit": info.commit.hexsha[:8] if info.commit else None
                })
            
            return result
            
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
                branches = {
                    "local": [branch.name for branch in repo.branches],
                    "remote": [ref.name for ref in repo.remotes.origin.refs],
                    "current": repo.active_branch.name
                }
                return {
                    "action": "list",
                    "branches": branches
                }
            
            elif action == "create":
                if not branch_name:
                    raise GitError("Nombre de rama requerido para crear")
                
                # Determinar rama base
                base_branch = from_branch or repo.active_branch.name
                
                # Crear nueva rama
                new_branch = repo.create_head(branch_name, base_branch)
                
                return {
                    "action": "create",
                    "branch_name": branch_name,
                    "from_branch": base_branch,
                    "status": "created"
                }
            
            elif action == "switch":
                if not branch_name:
                    raise GitError("Nombre de rama requerido para cambiar")
                
            elif action == "switch":
                if not branch_name:
                    raise GitError("Nombre de rama requerido para cambiar")
                
                # Cambiar a la rama
                repo.heads[branch_name].checkout()
                
                return {
                    "action": "switch",
                    "branch_name": branch_name,
                    "status": "switched"
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
                    "action": "delete",
                    "branch_name": branch_name,
                    "status": "deleted"
                }
            
            elif action == "rename":
                if not branch_name:
                    raise GitError("Nuevo nombre de rama requerido para renombrar")
                
                old_name = repo.active_branch.name
                repo.active_branch.rename(branch_name)
                
                return {
                    "action": "rename",
                    "old_name": old_name,
                    "new_name": branch_name,
                    "status": "renamed"
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
            
            # Realizar merge
            merge_base = repo.merge_base(repo.heads[source_branch], repo.heads[target_branch])
            
            try:
                if no_ff:
                    repo.git.merge(source_branch, no_ff=True)
                else:
                    repo.git.merge(source_branch)
                
                return {
                    "status": "merged",
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "no_ff": no_ff,
                    "conflicts": []
                }
                
            except GitCommandError as e:
                # Verificar si hay conflictos
                conflicts = []
                try:
                    for item in repo.index.unmerged_blobs():
                        conflicts.append(item)
                except Exception:
                    pass
                
                if conflicts:
                    return {
                        "status": "conflict",
                        "source_branch": source_branch,
                        "target_branch": target_branch,
                        "conflicts": conflicts,
                        "message": "Merge tiene conflictos que deben resolverse manualmente"
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
                
                return {
                    "action": "save",
                    "message": stash_message,
                    "status": "saved"
                }
            
            elif action == "list":
                # Listar stashes
                stash_list = repo.git.stash("list").splitlines()
                
                return {
                    "action": "list",
                    "stashes": stash_list,
                    "count": len(stash_list)
                }
            
            elif action == "pop":
                # Recuperar último stash
                index = stash_index or 0
                repo.git.stash("pop", f"stash@{{{index}}}")
                
                return {
                    "action": "pop",
                    "index": index,
                    "status": "popped"
                }
            
            elif action == "apply":
                # Aplicar stash sin eliminarlo
                index = stash_index or 0
                repo.git.stash("apply", f"stash@{{{index}}}")
                
                return {
                    "action": "apply",
                    "index": index,
                    "status": "applied"
                }
            
            elif action == "drop":
                # Eliminar stash
                index = stash_index or 0
                repo.git.stash("drop", f"stash@{{{index}}}")
                
                return {
                    "action": "drop",
                    "index": index,
                    "status": "dropped"
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
            
            # Determinar rama
            if branch:
                commits = list(repo.iter_commits(branch, max_count=limit, paths=file_path))
            else:
                commits = list(repo.iter_commits(max_count=limit, paths=file_path))
            
            # Procesar commits
            commit_list = []
            for commit in commits:
                commit_info = {
                    "hash": commit.hexsha,
                    "short_hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": commit.author.name,
                    "email": commit.author.email,
                    "date": commit.committed_datetime.isoformat(),
                    "stats": {
                        "files": len(commit.stats.files),
                        "insertions": commit.stats.total['insertions'],
                        "deletions": commit.stats.total['deletions']
                    }
                }
                
                commit_list.append(commit_info)
            
            return {
                "branch": branch or repo.active_branch.name,
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
        commit_hash: Optional[str] = None,
        mode: str = "mixed"
    ) -> Dict[str, Any]:
        """
        Resetea el repositorio a un estado anterior
        
        Args:
            repo_url: URL del repositorio
            commit_hash: Hash del commit (opcional)
            mode: Modo de reset
            
        Returns:
            Resultado del reset
        """
        try:
            repo_path = await self._ensure_repo_exists(repo_url)
            repo = Repo(repo_path)
            
            # Determinar commit
            target = commit_hash or "HEAD"
            
            # Realizar reset
            if mode == "soft":
                repo.git.reset("--soft", target)
            elif mode == "mixed":
                repo.git.reset("--mixed", target)
            elif mode == "hard":
                repo.git.reset("--hard", target)
            
            return {
                "status": "reset",
                "target": target,
                "mode": mode,
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
                tags = [tag.name for tag in repo.tags]
                return {
                    "action": "list",
                    "tags": tags,
                    "count": len(tags)
                }
            
            elif action == "create":
                if not tag_name:
                    raise GitError("Nombre de tag requerido")
                
                target = commit_hash or repo.head.commit
                
                if message:
                    # Tag anotado
                    tag = repo.create_tag(tag_name, ref=target, message=message)
                else:
                    # Tag ligero
                    tag = repo.create_tag(tag_name, ref=target)
                
                return {
                    "action": "create",
                    "tag_name": tag_name,
                    "commit": target.hexsha[:8] if hasattr(target, 'hexsha') else str(target),
                    "message": message,
                    "status": "created"
                }
            
            elif action == "delete":
                if not tag_name:
                    raise GitError("Nombre de tag requerido")
                
                repo.delete_tag(tag_name)
                
                return {
                    "action": "delete",
                    "tag_name": tag_name,
                    "status": "deleted"
                }
            
            elif action == "push":
                if tag_name:
                    repo.remotes.origin.push(tag_name)
                else:
                    repo.remotes.origin.push(tags=True)
                
                return {
                    "action": "push",
                    "tag_name": tag_name or "all",
                    "status": "pushed"
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
                remotes = {}
                for remote in repo.remotes:
                    remotes[remote.name] = list(remote.urls)
                
                return {
                    "action": "list",
                    "remotes": remotes
                }
            
            elif action == "add":
                if not remote_name or not remote_url:
                    raise GitError("Nombre y URL de remoto requeridos")
                
                repo.create_remote(remote_name, remote_url)
                
                return {
                    "action": "add",
                    "remote_name": remote_name,
                    "remote_url": remote_url,
                    "status": "added"
                }
            
            elif action == "remove":
                if not remote_name:
                    raise GitError("Nombre de remoto requerido")
                
                repo.delete_remote(remote_name)
                
                return {
                    "action": "remove",
                    "remote_name": remote_name,
                    "status": "removed"
                }
            
            elif action == "set-url":
                if not remote_name or not remote_url:
                    raise GitError("Nombre y URL de remoto requeridos")
                
                remote = repo.remotes[remote_name]
                remote.set_url(remote_url)
                
                return {
                    "action": "set-url",
                    "remote_name": remote_name,
                    "remote_url": remote_url,
                    "status": "updated"
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
            repo_url: URL del repositorio
            
        Returns:
            Ruta local del repositorio
        """
        try:
            # Intentar obtener la ruta existente
            return await self.file_manager.get_repo_path(repo_url)
        except RepositoryError:
            # Si no existe, clonarlo
            return await self.clone_repository(repo_url)
    
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