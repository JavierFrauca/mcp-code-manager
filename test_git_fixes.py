#!/usr/bin/env python3
"""
Test de verificación de herramientas Git corregidas
"""

import asyncio
import sys
import os
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from handlers.git_handler import GitHandler
from services.git_manager import GitManager

async def test_git_tools():
    """Prueba las herramientas Git corregidas"""
    
    print("🧪 Iniciando pruebas de herramientas Git...")
    
    # Crear instancias
    git_handler = GitHandler()
    git_manager = GitManager()
    
    # Directorio de prueba
    test_repo = "."  # Directorio actual
    
    try:
        print("\n1. 🔍 Probando git_status...")
        status_result = await git_handler.status(test_repo)
        print(f"   ✅ Status: {status_result.get('success', False)}")
        print(f"   📊 Rama: {status_result.get('branch', 'N/A')}")
        print(f"   🧹 Limpio: {status_result.get('clean', False)}")
        
        print("\n2. 📜 Probando git_log...")
        log_result = await git_handler.log(test_repo, limit=3)
        print(f"   ✅ Log: {log_result.get('success', False)}")
        print(f"   📈 Commits: {log_result.get('total_commits', 0)}")
        
        print("\n3. 📄 Probando git_diff...")
        diff_result = await git_handler.diff(test_repo, staged=False)
        print(f"   ✅ Diff: {diff_result.get('success', False)}")
        print(f"   📝 Archivos: {diff_result.get('total_files', 0)}")
        
        print("\n4. 🌿 Probando git_branch (list)...")
        branch_result = await git_handler.branch(test_repo, "list")
        print(f"   ✅ Branch: {branch_result.get('success', False)}")
        branches = branch_result.get('branches', [])
        print(f"   🌱 Ramas: {len(branches)}")
        
        print("\n5. 📦 Probando git_stash (list)...")
        stash_result = await git_handler.stash(test_repo, "list")
        print(f"   ✅ Stash: {stash_result.get('success', False)}")
        print(f"   💾 Stashes: {stash_result.get('count', 0)}")
        
        print("\n6. 🏷️ Probando git_tag (list)...")
        tag_result = await git_handler.tag(test_repo, "list")
        print(f"   ✅ Tag: {tag_result.get('success', False)}")
        print(f"   🔖 Tags: {tag_result.get('count', 0)}")
        
        print("\n7. 🔗 Probando git_remote (list)...")
        remote_result = await git_handler.remote(test_repo, "list")
        print(f"   ✅ Remote: {remote_result.get('success', False)}")
        remotes = remote_result.get('remotes', [])
        print(f"   🌐 Remotos: {len(remotes)}")
        
        print("\n🎉 Todas las pruebas completadas exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error en pruebas: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_git_tools())
    sys.exit(0 if success else 1)
