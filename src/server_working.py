#!/usr/bin/env python3
"""
MCP Code Manager Server - Versión que funciona
Servidor MCP completamente funcional para Claude Desktop
"""

import asyncio
import sys
from pathlib import Path

# Importación para papelera de reciclaje en Windows
if sys.platform == "win32":
    try:
        import winshell
    except ImportError:
        winshell = None
        print("[WARNING] winshell no disponible - eliminación a papelera deshabilitada", file=sys.stderr)

# Configuración de encoding para Windows
if sys.platform == "win32":
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_ALL, 'C')

# Configurar streams para UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Importaciones MCP
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    from mcp.server.models import InitializationOptions
except ImportError as e:
    print(f"Error: MCP no instalado - {e}", file=sys.stderr)
    sys.exit(1)

# Importaciones de handlers y servicios
try:
    from handlers.file_handler import FileHandler
    from handlers.code_handler import CodeHandler
    from handlers.git_handler import GitHandler
    from handlers.csharp_test_handler import CSharpTestHandler
    from handlers.python_test_handler import PythonTestHandler
    from utils.exceptions import FileOperationError, CodeAnalysisError
    from utils.logger import setup_logging, get_logger
    from utils.logging_decorators import log_tool_execution, log_mcp_handler
    from utils.log_analyzer import get_log_analyzer
except ImportError as e:
    print(f"Error: Módulos de handlers no disponibles - {e}", file=sys.stderr)
    sys.exit(1)

from mixin_setup_tools import SetupToolsAdapterMixin
from mixin_git import GitAdapterMixin
from mixin_python import PythonAdapterMixin
from mixin_dotnet import DotnetAdapterMixin
from mixin_file import FileAdapterMixin

class MCPWorkingServer(GitAdapterMixin, PythonAdapterMixin, DotnetAdapterMixin, FileAdapterMixin, SetupToolsAdapterMixin):
    """Servidor MCP que funciona correctamente"""
    
    def __init__(self):
        # Configuración de logging y paths
        project_root = Path(__file__).parent.parent
        self.logger = setup_logging(str(project_root / "logs"))

        self.server = Server("mcp-code-manager")
        self.file_handler = FileHandler()
        self.code_handler = CodeHandler()
        self.git_handler = GitHandler()
        self.csharp_handler = CSharpTestHandler()
        self.python_handler = PythonTestHandler()

        # Verbose startup info
        print("\n================ MCP Code Manager Server ================", file=sys.stderr)
        print(f"Project root: {project_root}", file=sys.stderr)
        print(f"Python version: {sys.version}", file=sys.stderr)
        print(f"Platform: {sys.platform}", file=sys.stderr)
        print(f"Logging directory: {project_root / 'logs'}", file=sys.stderr)
        print("Handlers loaded: file, code, git, csharp, python", file=sys.stderr)
        print("Initializing tools...", file=sys.stderr)

        self._setup_tools()

        # List available tools after setup
        try:
            available_tools = [t.name for t in self.server._tools] if hasattr(self.server, '_tools') else []
            print(f"Total tools registered: {len(available_tools)}", file=sys.stderr)
            if available_tools:
                print("Available tools:", file=sys.stderr)
                for t in sorted(available_tools):
                    print(f"  - {t}", file=sys.stderr)
            else:
                print("No tools registered.", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] Could not list tools at startup: {e}", file=sys.stderr)

        self.logger.log_debug("Servidor MCP inicializado", {
            "handlers": ["file", "code", "git", "csharp", "python"],
            "tools_count": len(available_tools) if 'available_tools' in locals() else 'unknown'
        })
        print("MCP Code Manager Server started successfully.\n", file=sys.stderr)
            
async def main():
    """Función principal del servidor"""
    print("[START] Iniciando MCP Code Manager Server (Working Version)...", file=sys.stderr)
    
    try:
        # Crear instancia del servidor
        server_instance = MCPWorkingServer()
        print("[READY] Servidor configurado, iniciando protocolo MCP...", file=sys.stderr)
        
        # Crear opciones de inicialización correctamente
        # Esto le dice a Claude qué capacidades tiene nuestro servidor
        init_options = server_instance.server.create_initialization_options()
        print(f"[CAPABILITIES] Servidor con capacidades: {init_options.capabilities}", file=sys.stderr)
        
        # Iniciar servidor con stdio
        async with stdio_server() as (read_stream, write_stream):
            print("[RUNNING] Servidor MCP activo y listo para recibir comandos", file=sys.stderr)
            
            # Ejecutar servidor con las capacidades correctas
            await server_instance.server.run(
                read_stream,
                write_stream,
                init_options
            )
            
    except KeyboardInterrupt:
        print("[STOP] Servidor detenido por el usuario", file=sys.stderr)
    except Exception as e:
        print(f"[FATAL] Error en servidor MCP: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

if __name__ == "__main__":
    try:
        # Configurar event loop para Windows
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Ejecutar servidor
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("[EXIT] Salida limpia", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"[FATAL] Error fatal: {str(e)}", file=sys.stderr)
        sys.exit(1)