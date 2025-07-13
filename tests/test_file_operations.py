#!/usr/bin/env python3
"""
Script de prueba para las operaciones de archivo del MCP Code Manager
Específicamente para probar set_file_content
"""

import asyncio
import sys
import os
from pathlib import Path

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server_working import MCPWorkingServer

async def test_file_operations():
    """Prueba las operaciones de archivo, especialmente set_file_content"""
    print("🧪 Probando operaciones de archivo del MCP Code Manager\n")
    
    # Crear instancia del servidor
    server = MCPWorkingServer()
    
    # Archivos de prueba
    test_file = Path("./test_nuevo_archivo.txt")
    test_file_existing = Path("./test_archivo_existente.py")
    test_dir = Path("./test_subdir")
    test_file_in_dir = test_dir / "archivo_en_directorio.md"
    
    print("1. ✅ Probando creación de archivo nuevo...")
    content_nuevo = """# Archivo de Prueba
Este es un archivo creado por el MCP Code Manager.

## Características
- Creación automática
- Contenido UTF-8
- Directorios padre automáticos
"""
    
    result = await server._set_file_content(str(test_file), content_nuevo)
    print(f"   Resultado: {result[0].text}")
    
    # Verificar que se creó
    if test_file.exists():
        print("   ✅ Archivo creado exitosamente")
        print(f"   📄 Tamaño real: {test_file.stat().st_size} bytes")
    else:
        print("   ❌ Error: Archivo no se creó")
        return
    
    print("\n2. ✅ Probando modificación de archivo existente...")
    
    # Crear archivo existente primero
    test_file_existing.write_text("# Contenido original\nprint('Hola mundo')\n")
    
    content_modificado = """# Contenido Modificado por MCP
print('Hola desde MCP Code Manager!')

def nueva_funcion():
    return "Función agregada por modificación"

if __name__ == "__main__":
    print(nueva_funcion())
"""
    
    result = await server._set_file_content(str(test_file_existing), content_modificado, create_backup=True)
    print(f"   Resultado: {result[0].text}")
    
    # Verificar backup
    backup_files = list(test_file_existing.parent.glob(f"{test_file_existing.stem}.backup_*{test_file_existing.suffix}"))
    if backup_files:
        print(f"   ✅ Backup creado: {backup_files[0].name}")
    else:
        print("   ⚠️ No se encontró backup")
    
    print("\n3. ✅ Probando creación en directorio no existente...")
    result = await server._set_file_content(str(test_file_in_dir), "# Archivo en subdirectorio\nCreado automáticamente.")
    print(f"   Resultado: {result[0].text}")
    
    # Verificar que se creó el directorio y el archivo
    if test_dir.exists() and test_file_in_dir.exists():
        print("   ✅ Directorio y archivo creados exitosamente")
    else:
        print("   ❌ Error: No se creó el directorio o archivo")
    
    print("\n4. ✅ Probando modificación sin backup...")
    result = await server._set_file_content(str(test_file), "Contenido sin backup", create_backup=False)
    print(f"   Resultado: {result[0].text}")
    
    print("\n5. ✅ Probando contenido con caracteres especiales...")
    contenido_especial = """# Prueba de Caracteres Especiales
print("Texto con acentos: áéíóú ñÑ")
print("Símbolos: €£¥₹ ©®™")
print("Emojis: 🎉🚀✅❌🔧")

# Código Python válido
def función_con_ñ():
    return "¡Funciona con UTF-8!"
"""
    
    result = await server._set_file_content("./test_utf8.py", contenido_especial)
    print(f"   Resultado: {result[0].text}")
    
    print("\n6. ✅ Probando errores: archivo vacío...")
    result = await server._set_file_content("./test_vacio.txt", "")
    print(f"   Resultado: {result[0].text}")
    
    print("\n7. ✅ Probando errores: ruta vacía...")
    result = await server._set_file_content("", "contenido")
    print(f"   Resultado: {result[0].text}")
    
    print("\n8. ✅ Verificando contenido con get_file_content...")
    result = await server._get_file_content(str(test_file_existing))
    print(f"   Primeras líneas del archivo modificado:")
    lines = result[0].text.split('\n')[:5]
    for line in lines:
        print(f"   > {line}")
    
    # Limpiar archivos de prueba
    print("\n🧹 Limpiando archivos de prueba...")
    cleanup_files = [test_file, test_file_existing, test_file_in_dir, Path("./test_utf8.py"), Path("./test_vacio.txt")]
    cleanup_dirs = [test_dir]
    
    for file in cleanup_files:
        if file.exists():
            try:
                file.unlink()
                print(f"   🗑️ Eliminado: {file}")
            except:
                pass
    
    # Limpiar backups
    for backup in test_file_existing.parent.glob("*.backup_*"):
        try:
            backup.unlink()
            print(f"   🗑️ Backup eliminado: {backup.name}")
        except:
            pass
    
    for directory in cleanup_dirs:
        if directory.exists():
            try:
                import shutil
                shutil.rmtree(str(directory))
                print(f"   🗑️ Directorio eliminado: {directory}")
            except:
                pass
    
    print("\n🎉 Todas las pruebas de archivo completadas!")

if __name__ == "__main__":
    # Configurar event loop para Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(test_file_operations())
