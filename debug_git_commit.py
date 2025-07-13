#!/usr/bin/env python3
"""
Script de prueba para verificar git_commit
"""
import asyncio
import os
import sys
sys.path.append('src')

from services.git_manager import GitManager

async def test_git_commit():
    """Prueba git_commit con un commit de prueba"""
    
    git_manager = GitManager()
    
    print("=" * 50)
    print("PRUEBA DE GIT COMMIT")
    print("=" * 50)
    
    # Probar commit simple
    print(f"\n1. Probando commit con '.' (directorio actual: {os.getcwd()})")
    try:
        result = await git_manager.commit_changes(
            repo_url=".",
            message="Prueba de commit desde script de depuración",
            add_all=True  # Añadir todos los archivos modificados
        )
        print(f"✅ Éxito: {result}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Verificar configuración Git
    print(f"\n2. Verificando configuración Git:")
    try:
        from git import Repo
        repo = Repo(".")
        
        # Intentar leer configuración
        config = repo.config_reader()
        try:
            user_name = config.get_value("user", "name")
            user_email = config.get_value("user", "email")
            print(f"   Usuario configurado: {user_name} <{user_email}>")
        except Exception:
            print("   ⚠️  Usuario Git no configurado globalmente")
            
        # Verificar si hay algo que hacer commit
        if repo.is_dirty() or repo.untracked_files:
            print(f"   Archivos modificados: {len(repo.git.diff('--name-only').splitlines())}")
            print(f"   Archivos no rastreados: {len(repo.untracked_files)}")
            print(f"   Archivos en stage: {len(repo.git.diff('--staged', '--name-only').splitlines())}")
        else:
            print("   Repositorio limpio - nada que hacer commit")
            
    except Exception as e:
        print(f"   Error verificando configuración: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_git_commit())
