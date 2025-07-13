#!/usr/bin/env python3
"""
Script de prueba para verificar git_status con directorio actual
"""
import asyncio
import os
import sys
sys.path.append('src')

from services.git_manager import GitManager
from services.file_manager import FileManager

async def test_git_status():
    """Prueba git_status con el directorio actual"""
    
    git_manager = GitManager()
    
    print("=" * 50)
    print("PRUEBA DE GIT STATUS")
    print("=" * 50)
    
    # Probar con "."
    print(f"\n1. Probando con '.' (directorio actual: {os.getcwd()})")
    try:
        result = await git_manager.get_detailed_status(".")
        print(f"✅ Éxito: {result}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Probar con ruta absoluta del directorio actual
    current_dir = os.getcwd()
    print(f"\n2. Probando con ruta absoluta: {current_dir}")
    try:
        result = await git_manager.get_detailed_status(current_dir)
        print(f"✅ Éxito: {result}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Verificar si existe .git
    git_dir = os.path.join(current_dir, '.git')
    print(f"\n3. Verificando existencia de .git:")
    print(f"   Directorio .git existe: {os.path.exists(git_dir)}")
    if os.path.exists(git_dir):
        print(f"   Es directorio: {os.path.isdir(git_dir)}")
        print(f"   Contenido: {os.listdir(git_dir)[:5]}...")  # Primeros 5 elementos
    
    # Verificar estado con GitPython directamente
    print(f"\n4. Verificando con GitPython directamente:")
    try:
        from git import Repo
        repo = Repo(current_dir)
        print(f"   Repositorio válido: {not repo.bare}")
        print(f"   Branch activo: {repo.active_branch.name if repo.active_branch else 'Sin branch'}")
        print(f"   Archivos modificados: {len(list(repo.iter_commits(max_count=1)))}")
    except Exception as e:
        print(f"   Error GitPython: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_git_status())
