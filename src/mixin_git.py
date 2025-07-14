import sys
from typing import List
from mcp.types import TextContent

class GitAdapterMixin:
    async def _git_status(self, repository_path: str) -> List['TextContent']:
        """Obtiene el estado del repositorio Git usando el handler"""
        try:
            result = await self.git_handler.status(repository_path)
            if result.get("clean"):
                response_text = "✅ Repositorio limpio"
            else:
                response_text = "❌ Cambios pendientes"
            if result.get("last_commit"):
                response_text += f"\nÚltimo commit: {result['last_commit']}"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            self.logger.log_error(e, f"Error en _git_status para ruta: {repository_path}")
            return [TextContent(type="text", text=f"❌ Error ejecutando git status: {str(e)}")]

    async def _git_init(self, repo_path: str, bare: bool = False, initial_branch: str = None) -> List['TextContent']:
        """Inicializa un nuevo repositorio Git"""
        try:
            result = await self.git_handler.init(repo_path, bare, initial_branch)
            if result.get("success"):
                response_text = "✅ Repositorio inicializado"
            else:
                response_text = "❌ No se pudo inicializar"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error inicializando repositorio: {str(e)}")]

    async def _git_add(self, repo_url: str, files: List[str] = None, all_files: bool = False, update: bool = False) -> List['TextContent']:
        """Agrega archivos al staging area"""
        try:
            result = await self.git_handler.add(repo_url, files, all_files, update)
            if result.get("success"):
                response_text = "✅ Archivos agregados"
            else:
                response_text = "❌ No se pudo agregar"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error agregando archivos: {str(e)}")]

    async def _git_commit(self, repo_url: str, message: str, files: list = None, add_all: bool = False) -> List['TextContent']:
        """Realiza un commit en el repositorio especificado usando el handler."""
        try:
            result = await self.git_handler.commit(repo_url, message, files, add_all)
            if result.get("success"):
                response_text = "✅ Commit realizado"
            else:
                response_text = "❌ No se pudo commitear"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando commit: {str(e)}")]

    async def _git_diff(self, repo_url: str, file_path: str = None, staged: bool = False) -> List['TextContent']:
        """Muestra el diff del repositorio o de un archivo usando el handler."""
        try:
            result = await self.git_handler.diff(repo_url, file_path, staged)
            if result.get("success"):
                response_text = "✅ Diff generado"
            else:
                response_text = "❌ No se pudo generar diff"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando diff: {str(e)}")]

    async def _git_log(self, repo_url: str, limit: int = 10, branch: str = None, file_path: str = None) -> List['TextContent']:
        """Muestra el log de commits del repositorio usando el handler."""
        try:
            result = await self.git_handler.log(repo_url, limit, branch, file_path)
            if result.get("success"):
                response_text = "✅ Log generado"
            else:
                response_text = "❌ No se pudo obtener log"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando log: {str(e)}")]

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
            result = await self.git_handler.reset(repo_url, commit_hash, mode)
            
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

    async def _git_clone(self, repo_url: str, dest_path: str = None, force: bool = False) -> list:
        """Clona un repositorio Git en una carpeta destino"""
        try:
            result = await self.git_handler.clone(repo_url, dest_path, force)
            if result.get("success"):
                return [TextContent(type="text", text=f"✅ Repositorio clonado en: {result['path']}")]
            else:
                return [TextContent(type="text", text=f"❌ Error clonando repositorio: {result.get('error')}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error clonando repositorio: {str(e)}")]
