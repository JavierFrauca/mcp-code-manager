# Configuración Manual para Claude Desktop

## Problema

Claude AI está tratando de usar autenticación MCP específica que no es compatible con nuestro servidor HTTP.

## Solución: Configuración Local MCP

En lugar de usar el conector remoto, configura el servidor MCP localmente:

### 1. Ubicación del archivo de configuración

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

### 2. Contenido del archivo `claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mcp-code-manager": {
      "command": "python",
      "args": ["C:\\repo\\mcp-code-manager\\src\\server.py"],
      "env": {
        "PYTHONPATH": "C:\\repo\\mcp-code-manager"
      }
    }
  }
}
```

### 3. Pasos para configurar

1. **Cerrar Claude Desktop** completamente
2. **Navegar** a la carpeta `%APPDATA%\Claude\`
3. **Crear o editar** el archivo `claude_desktop_config.json`
4. **Copiar** la configuración de arriba
5. **Ajustar** la ruta absoluta a tu instalación
6. **Reiniciar** Claude Desktop

### 4. Verificar configuración

- Abrir Claude Desktop
- Buscar en la lista de herramientas disponibles
- Deberías ver las herramientas de MCP Code Manager

### 5. Crear script de configuración automática

Ver: `setup_claude_config.bat`

## Alternativa: Usar el archivo DXT

El archivo `mcp-code-manager-client.dxt` debería funcionar arrastrándolo directamente a Claude Desktop, pero si no funciona, usa la configuración manual de arriba.
