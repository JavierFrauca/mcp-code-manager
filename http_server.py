"""
HTTP Wrapper para MCP Code Manager Server
Convierte el servidor MCP local en un endpoint HTTP REST compatible con Claude AI
"""
import asyncio
import json
import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import sys
import os

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.server import MCPCodeManagerServer

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Code Manager HTTP API",
    description="HTTP wrapper para el servidor MCP de gestión de código C#",
    version="1.0.0"
)

# Configurar CORS para Claude AI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para manejar autenticación de Claude AI
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Middleware para manejar la autenticación de Claude AI"""
    
    # Permitir todas las requests sin autenticación para compatibilidad
    response = await call_next(request)
    
    # Añadir headers para Claude AI
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# Instancia global del servidor MCP
mcp_server = None

class ToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class ToolResponse(BaseModel):
    success: bool
    result: Any = None
    error: str = None

@app.on_event("startup")
async def startup_event():
    """Inicializa el servidor MCP al arrancar"""
    global mcp_server
    try:
        mcp_server = MCPCodeManagerServer()
        logger.info("✅ Servidor MCP inicializado correctamente")
    except Exception as e:
        logger.error(f"❌ Error al inicializar servidor MCP: {e}")
        raise

@app.get("/")
async def root():
    """Endpoint raíz con información del API compatible con Claude AI"""
    return {
        "name": "MCP Code Manager",
        "version": "1.0.0",
        "status": "active",
        "protocol": "mcp",
        "description": "HTTP wrapper para servidor MCP de gestión de código C#",
        "capabilities": {
            "tools": True,
            "prompts": True,
            "resources": True
        },
        "endpoints": {
            "capabilities": "/capabilities",
            "tools": "/tools",
            "tools_call": "/tools/call",
            "execute": "/execute",
            "health": "/health"
        }
    }

@app.options("/{path:path}")
async def options_handler(path: str):
    """Maneja las requests OPTIONS para CORS"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/capabilities")
async def get_capabilities():
    """Endpoint de capacidades compatible con Claude AI MCP"""
    return {
        "capabilities": {
            "tools": {
                "listChanged": False
            },
            "prompts": {
                "listChanged": False  
            },
            "resources": {
                "subscribe": False,
                "listChanged": False
            }
        },
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "mcp-code-manager",
            "version": "1.0.0"
        }
    }

@app.get("/health")
async def health_check():
    """Verificación de salud del servidor"""
    return {
        "status": "healthy",
        "server": "mcp-code-manager",
        "timestamp": "2025-07-12"
    }

@app.get("/tools/list")
@app.post("/tools/list")
async def list_tools_mcp():
    """Lista todas las herramientas en formato MCP estándar"""
    try:
        tools = [
            {
                "name": "find_class",
                "description": "Localiza clases específicas en repositorios C# con búsqueda directa o profunda",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string", "description": "URL del repositorio"},
                        "class_name": {"type": "string", "description": "Nombre de la clase"},
                        "search_type": {"type": "string", "enum": ["direct", "deep"], "default": "direct"}
                    },
                    "required": ["repo_url", "class_name"]
                }
            },
            {
                "name": "get_file_content",
                "description": "Obtiene el contenido completo de archivos",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string", "description": "URL del repositorio"},
                        "file_path": {"type": "string", "description": "Ruta del archivo"}
                    },
                    "required": ["repo_url", "file_path"]
                }
            },
            {
                "name": "find_elements",
                "description": "Busca elementos específicos como DTOs, Services, Controllers, Interfaces, Enums",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string", "description": "URL del repositorio"},
                        "element_type": {"type": "string", "enum": ["dto", "service", "controller", "interface", "enum"]},
                        "element_name": {"type": "string", "description": "Nombre del elemento"}
                    },
                    "required": ["repo_url", "element_type", "element_name"]
                }
            },
            {
                "name": "get_solution_structure",
                "description": "Obtiene la estructura completa de soluciones C# organizadas por namespaces",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string", "description": "URL del repositorio"}
                    },
                    "required": ["repo_url"]
                }
            },
            {
                "name": "git_status",
                "description": "Obtiene el estado actual del repositorio Git",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string", "description": "URL del repositorio"}
                    },
                    "required": ["repo_url"]
                }
            },
            {
                "name": "git_commit",
                "description": "Realiza commits con mensajes descriptivos",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string", "description": "URL del repositorio"},
                        "message": {"type": "string", "description": "Mensaje del commit"},
                        "files": {"type": "array", "items": {"type": "string"}},
                        "add_all": {"type": "boolean", "default": False}
                    },
                    "required": ["repo_url", "message"]
                }
            },
            {
                "name": "list_files",
                "description": "Lista archivos del repositorio con patrones y filtros",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string", "description": "URL del repositorio"},
                        "file_pattern": {"type": "string", "description": "Patrón de archivos"},
                        "max_depth": {"type": "integer", "default": -1}
                    },
                    "required": ["repo_url"]
                }
            }
        ]
        
        return {
            "tools": tools
        }
    except Exception as e:
        logger.error(f"Error listando herramientas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/call")
async def call_tool_mcp(request: dict):
    """Ejecuta una herramienta en formato MCP estándar"""
    try:
        tool_name = request.get("name")
        arguments = request.get("arguments", {})
        
        if not mcp_server:
            raise HTTPException(status_code=500, detail="Servidor MCP no inicializado")
        
        # Ejecutar la herramienta según el nombre
        if tool_name.startswith("git_"):
            result = await mcp_server._handle_git_tool(tool_name, arguments)
        elif tool_name in ["create_file", "update_file", "delete_file"]:
            result = await mcp_server._handle_file_tool(tool_name, arguments)
        elif tool_name in ["list_files", "check_permissions"]:
            result = await mcp_server._handle_repository_tool(tool_name, arguments)
        else:
            result = await mcp_server._handle_code_tool(tool_name, arguments)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(result)
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error ejecutando herramienta {tool_name}: {e}")
        return {
            "content": [
                {
                    "type": "text", 
                    "text": f"Error: {str(e)}"
                }
            ],
            "isError": True
        }

@app.post("/execute")
async def execute_tool(request: ToolRequest) -> ToolResponse:
    """Ejecuta una herramienta específica"""
    try:
        if not mcp_server:
            raise HTTPException(status_code=500, detail="Servidor MCP no inicializado")
        
        # Ejecutar la herramienta según el nombre
        if request.tool_name.startswith("git_"):
            result = await mcp_server._handle_git_tool(request.tool_name, request.arguments)
        elif request.tool_name in ["create_file", "update_file", "delete_file"]:
            result = await mcp_server._handle_file_tool(request.tool_name, request.arguments)
        elif request.tool_name in ["list_files", "check_permissions"]:
            result = await mcp_server._handle_repository_tool(request.tool_name, request.arguments)
        else:
            result = await mcp_server._handle_code_tool(request.tool_name, request.arguments)
        
        return ToolResponse(success=True, result=result)
        
    except Exception as e:
        logger.error(f"Error ejecutando herramienta {request.tool_name}: {e}")
        return ToolResponse(success=False, error=str(e))

@app.post("/tools/{tool_name}")
async def execute_tool_by_path(tool_name: str, arguments: Dict[str, Any]) -> ToolResponse:
    """Ejecuta una herramienta específica por path"""
    request = ToolRequest(tool_name=tool_name, arguments=arguments)
    return await execute_tool(request)

# Endpoints específicos para herramientas populares
@app.post("/analyze")
async def analyze_repository(repo_url: str):
    """Análisis completo de un repositorio C#"""
    try:
        # Ejecutar múltiples herramientas para análisis completo
        structure = await execute_tool(ToolRequest(
            tool_name="get_solution_structure",
            arguments={"repo_url": repo_url}
        ))
        
        files = await execute_tool(ToolRequest(
            tool_name="list_files",
            arguments={"repo_url": repo_url, "file_pattern": "*.cs"}
        ))
        
        git_status = await execute_tool(ToolRequest(
            tool_name="git_status",
            arguments={"repo_url": repo_url}
        ))
        
        return {
            "success": True,
            "repository": repo_url,
            "analysis": {
                "structure": structure.result if structure.success else None,
                "files": files.result if files.success else None,
                "git_status": git_status.result if git_status.success else None
            }
        }
    except Exception as e:
        logger.error(f"Error en análisis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Iniciando MCP Code Manager HTTP Server...")
    print("📡 Servidor disponible en: http://localhost:8000")
    print("📖 Documentación API: http://localhost:8000/docs")
    print("🔧 Herramientas disponibles: http://localhost:8000/tools")
    
    uvicorn.run(
        "http_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
