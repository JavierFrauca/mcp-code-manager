#!/usr/bin/env python3
"""
Script de prueba para el sistema de logging de MCP Code Manager
"""

import sys
import asyncio
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.logger import setup_logging, get_logger
from utils.log_analyzer import get_log_analyzer

async def test_logging():
    """Prueba el sistema de logging"""
    
    print("🧪 Probando sistema de logging...")
    
    # Configurar logging
    logger = setup_logging()
    
    # Pruebas básicas de logging
    print("📝 Probando logging básico...")
    logger.log_debug("Mensaje de debug de prueba", {"test": True})
    logger.log_mcp_request("test_method", {"param1": "value1"})
    logger.log_mcp_response("test_method", True, {"result": "success"}, execution_time=0.123)
    
    # Prueba de logging de herramientas
    print("🔧 Probando logging de herramientas...")
    logger.log_tool_execution(
        tool_name="test_tool",
        arguments={"arg1": "test"},
        success=True,
        result=["test result"],
        execution_time=0.456
    )
    
    # Prueba de logging de errores
    print("❌ Probando logging de errores...")
    try:
        raise ValueError("Error de prueba")
    except Exception as e:
        logger.log_error(e, "Prueba de error", {"additional": "data"})
    
    # Probar analizador de logs
    print("📊 Probando analizador de logs...")
    analyzer = get_log_analyzer()
    
    # Obtener estadísticas
    tool_stats = analyzer.get_tool_stats(1)  # 1 hora
    mcp_stats = analyzer.get_mcp_request_stats(1)
    
    print(f"  📈 Ejecuciones de herramientas: {tool_stats['total_executions']}")
    print(f"  📡 Peticiones MCP: {mcp_stats['total_requests']}")
    
    # Buscar en logs
    search_results = analyzer.search_logs("test", max_results=5)
    print(f"  🔍 Resultados de búsqueda 'test': {len(search_results)}")
    
    # Obtener errores recientes
    recent_errors = analyzer.get_recent_errors(1)
    print(f"  🚨 Errores recientes: {len(recent_errors)}")
    
    # Exportar resumen
    summary = analyzer.export_log_summary(1)
    print(f"  📋 Resumen generado: {summary['timestamp']}")
    
    # Obtener estadísticas de archivos
    log_stats = logger.get_log_stats()
    print(f"  📁 Directorio de logs: {log_stats['logs_directory']}")
    print(f"  📄 Archivos de log: {len(log_stats['log_files'])}")
    
    print("✅ Pruebas de logging completadas exitosamente!")
    print(f"📂 Los logs se han guardado en: {Path(__file__).parent / 'logs'}")

if __name__ == "__main__":
    try:
        asyncio.run(test_logging())
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
        sys.exit(1)
