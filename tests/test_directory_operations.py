#!/usr/bin/env python3
"""
Script de prueba para las operaciones de directorio del MCP Code Manager
"""

import asyncio
import sys
import os
from pathlib import Path

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from server_working import MCPWorkingServer

async def test_directory_operations():
    """Prueba las nuevas operaciones de directorio"""
    print("🧪 Probando operaciones de directorio del MCP Code Manager\n")
    
    # Crear instancia del servidor
    server = MCPWorkingServer()
    
    # Crear directorio de prueba
    test_dir = Path("./test_temp_dir")
    renamed_dir = Path("./test_renamed_dir")
    
    print("1. ✅ Probando creación de directorio...")
    result = await server._create_directory(str(test_dir))
    print(f"   Resultado: {result[0].text}")
    
    # Verificar que se creó
    if test_dir.exists():
        print("   ✅ Directorio creado exitosamente")
    else:
        print("   ❌ Error: Directorio no se creó")
        return
    
    print("\n2. ✅ Probando renombrado de directorio...")
    result = await server._rename_directory(str(test_dir), str(renamed_dir))
    print(f"   Resultado: {result[0].text}")
    
    # Verificar el renombrado
    if renamed_dir.exists() and not test_dir.exists():
        print("   ✅ Directorio renombrado exitosamente")
    else:
        print("   ❌ Error: Directorio no se renombró correctamente")
        return
    
    print("\n3. ✅ Probando eliminación de directorio (a papelera)...")
    result = await server._delete_directory(str(renamed_dir))
    print(f"   Resultado: {result[0].text}")
    
    # Verificar la eliminación
    if not renamed_dir.exists():
        print("   ✅ Directorio eliminado exitosamente")
    else:
        print("   ❌ Error: Directorio no se eliminó")
    
    print("\n4. ✅ Probando errores: crear directorio que ya existe...")
    # Crear un directorio para probar error
    existing_dir = Path("./test_existing")
    existing_dir.mkdir(exist_ok=True)
    
    result = await server._create_directory(str(existing_dir))
    print(f"   Resultado: {result[0].text}")
    
    print("\n5. ✅ Probando errores: renombrar directorio inexistente...")
    result = await server._rename_directory("./directorio_inexistente", "./nuevo_nombre")
    print(f"   Resultado: {result[0].text}")
    
    print("\n6. ✅ Probando errores: eliminar directorio inexistente...")
    result = await server._delete_directory("./directorio_inexistente")
    print(f"   Resultado: {result[0].text}")
    
    # Limpiar
    if existing_dir.exists():
        import shutil
        shutil.rmtree(str(existing_dir))
    
    print("\n🎉 Todas las pruebas completadas!")

if __name__ == "__main__":
    # Configurar event loop para Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(test_directory_operations())
