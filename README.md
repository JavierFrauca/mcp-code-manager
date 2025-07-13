# MCP Code Manager

Un servidor MCP (Model Context Protocol) comple### 🔍 A### 🔐 Verificación de Sistema

- **`check_permissions`** - Verifica permisos CRUD completos sobre rutaslisis de Código C#

- **`find_class`** - Localiza clases específicas con búsqueda directa o profunda para la gestión de archivos, directorios y operaciones Git. Permite a las IAs interactuar con el sistema de archivos local mediante herramientas robustas y seguras con soporte para papelera de reciclaje, validaciones avanzadas y verificación de permisos.

## 🚀 Características

### 📁 Gestión Completa de Archivos

- **CRUD Completo**: Crear, leer, actualizar, eliminar, copiar y renombrar archivos
- **Backups Automáticos**: Copias de seguridad automáticas antes de modificaciones
- **Eliminación Segura**: Envío a papelera de reciclaje en Windows (con fallback)
- **Validación Robusta**: Verificación de rutas, encoding inteligente y manejo de errores
- **Soporte UTF-8**: Manejo completo de caracteres especiales y emojis

### 📂 Gestión Avanzada de Directorios

- **Creación Inteligente**: Crear carpetas con directorios padre automáticamente
- **Renombrado/Movimiento**: Renombrar y mover directorios de forma segura
- **Eliminación a Papelera**: Envío a papelera de reciclaje en Windows (con fallback a eliminación permanente)
- **Limpieza Automática**: Eliminación de directorios vacíos tras operaciones
- **Validaciones Robustas**: Verificación de permisos, existencia y prevención de conflictos

### 🔐 Verificación de Permisos

- **Análisis CRUD**: Verificación completa de permisos de lectura, escritura, creación y eliminación
- **Diagnóstico Detallado**: Información sobre capacidades del sistema de archivos
- **Integración Git**: Verificación de permisos específicos para repositorios Git
- **Prevención de Errores**: Validación previa antes de operaciones críticas

### 📋 Listado Inteligente de Archivos

- **Filtros Avanzados**: Búsqueda por patrones de archivos (`*.py`, `*.txt`, etc.)
- **Exploración Profunda**: Control de profundidad de búsqueda en subdirectorios
- **Estadísticas Detalladas**: Información de tamaños, tipos y extensiones
- **Exclusión Inteligente**: Omisión automática de directorios temporales y de sistema

### 🔀 Funcionalidades Git

- **Estado Detallado**: Información completa de archivos staged/unstaged/untracked
- **Integración Nativa**: Verificación de repositorios Git y permisos
- **Formato Visual**: Presentación clara del estado de cambios con emojis

### 🛡️ Características de Seguridad

- **Validación de Rutas**: Prevención de path traversal y rutas maliciosas
- **Manejo de Errores**: Captura y reporte detallado de excepciones
- **Operaciones Atómicas**: Verificaciones previas antes de modificaciones destructivas
- **Logs Detallados**: Registro completo de operaciones para debugging

### 📊 Sistema de Logging y Diagnóstico

- **Logging Automático**: Registro automático de todas las peticiones MCP y ejecuciones de herramientas
- **Múltiples Niveles**: Logs separados para requests/responses, ejecuciones, errores y debug
- **Rotación Automática**: Archivos de log con rotación por tamaño (10MB) y backup (5 archivos)
- **Análisis Integrado**: Herramientas de análisis estadístico y búsqueda en logs
- **Diagnóstico Inteligente**: Detección automática de problemas y recomendaciones
- **Sanitización de Datos**: Ocultación automática de información sensible en logs
- **Exportación de Reportes**: Generación de resúmenes completos para diagnóstico

#### Herramientas de Logging Disponibles

- **`get_logs_stats`** - Estadísticas de uso y rendimiento
- **`search_logs`** - Búsqueda de texto específico en logs
- **`get_recent_errors`** - Lista de errores recientes del sistema
- **`export_log_summary`** - Resumen completo para diagnóstico

#### Archivos de Log

- **`logs/mcp_requests.log`** - Todas las peticiones y respuestas MCP
- **`logs/tools_execution.log`** - Ejecución de herramientas con tiempos y resultados
- **`logs/errors.log`** - Errores del sistema con stack traces completos
- **`logs/debug.log`** - Información detallada de debug y trazabilidad

### 🔍 Análisis de Código C Sharp

- **Búsqueda de Clases**: Localización directa por nombre de archivo o búsqueda profunda en contenido
- **Análisis Automático**: Extracción de metadatos de archivos C# (namespaces, clases, métodos, propiedades)
- **Búsqueda de Elementos**: Localización específica de DTOs, Services, Controllers, Interfaces, Enums
- **Estructura de Solución**: Análisis completo de proyectos C# con estadísticas detalladas
- **Categorización Inteligente**: Organización automática por tipos de archivo y namespaces
- **Estadísticas de Proyecto**: Resúmenes de clases, interfaces, métodos y líneas de código

## � Herramientas Disponibles

### 🧪 Herramientas de Sistema

- **`ping`** - Test de conectividad (responde con "pong")
- **`echo`** - Repite el mensaje enviado

### 📄 Gestión de Archivos

- **`get_file_content`** - Lee el contenido completo de un archivo
- **`set_file_content`** - Crea o modifica archivos con backup automático
- **`rename_file`** - Renombra o mueve archivos
- **`delete_file`** - Elimina archivos a la papelera de reciclaje
- **`copy_file`** - Copia archivos a otra ubicación

### 📁 Gestión de Directorios

- **`list_directory`** - Lista contenido básico de directorios
- **`list_files`** - Listado avanzado con filtros, patrones y estadísticas
- **`create_directory`** - Crea directorios con estructura padre automática
- **`rename_directory`** - Renombra/mueve directorios
- **`delete_directory`** - Elimina directorios a la papelera

### � Análisis de Código C Sharp

- **`find_class`** - Localiza clases específicas con búsqueda directa o profunda
- **`get_cs_file_content`** - Obtiene contenido de archivos C# con análisis automático
- **`find_elements`** - Busca DTOs, Services, Controllers, Interfaces, Enums
- **`get_solution_structure`** - Estructura completa de soluciones C# con estadísticas

### �🔐 Verificación de Sistema

- **`check_permissions`** - Verifica permisos CRUD completos sobre rutas
  - Permisos de lectura, escritura, ejecución
  - Capacidades de creación/eliminación de archivos y directorios
  - Información de espacio en disco
  - Estado de repositorio Git

### 🔀 Operaciones Git

- **`git_status`** - Estado detallado del repositorio con formato visual

### ✨ Características Especiales

- **Papelera de Reciclaje**: Eliminación segura en Windows con `winshell`
- **Backups Automáticos**: Copias de seguridad antes de modificaciones
- **Encoding Inteligente**: Detección automática UTF-8/Latin-1
- **Validación Robusta**: Prevención de operaciones peligrosas
- **Limpieza Automática**: Eliminación de directorios vacíos
- **Análisis Inteligente**: Análisis automático de código C# con estadísticas

## �📋 Requisitos

- Python 3.9+
- Git configurado globalmente
- Acceso a repositorios Git (HTTPS/SSH)
- **Windows**: `winshell` (opcional, para papelera de reciclaje) - se instala automáticamente

## 🛠️ Instalación

1. **Clonar y configurar el proyecto:**

```bash
# Ejecutar el script de configuración
.\setup-mcp-code-manager.ps1
cd mcp-code-manager
```

2.**Crear entorno virtual:**

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3.**Instalar dependencias:**

```bash
pip install -r requirements.txt
```

4.**Instalar en modo desarrollo:**

```bash
pip install -e .
```

## 🚀 Uso

### Iniciar el servidor MCP

```bash
python src/server_working.py
```

### Herramientas Principales

#### Gestión de Archivos

```python
# Leer archivo
get_file_content(file_path="src/ejemplo.py")

# Crear/modificar archivo con backup
set_file_content(
    file_path="nuevo_archivo.txt", 
    content="Contenido del archivo",
    create_backup=True
)

# Renombrar archivo
rename_file(source_path="viejo.txt", dest_path="nuevo.txt")

# Eliminar archivo a papelera
delete_file(file_path="archivo_temporal.txt")

# Copiar archivo
copy_file(source_path="original.py", dest_path="copia.py")
```

#### Gestión de Directorios

```python
# Crear directorio
create_directory(directory_path="nueva_carpeta/subcarpeta")

# Renombrar directorio
rename_directory(old_path="carpeta_vieja", new_path="carpeta_nueva")

# Eliminar directorio a papelera
delete_directory(directory_path="carpeta_temporal")

# Listar archivos con filtros
list_files(
    directory_path="src",
    file_pattern="*.py",
    include_directories=True,
    max_depth=3
)
```

#### Verificación de Permisos

```python
# Verificar permisos CRUD
check_permissions(target_path="carpeta_proyecto")

# Resultado incluye:
# - Permisos de lectura/escritura/ejecución
# - Capacidad de crear/eliminar archivos y directorios
# - Estado del repositorio Git
# - Información de espacio en disco
```

#### Verificar estado del repositorio

```python
status = await git_status("https://github.com/usuario/proyecto.git")
# Retorna: archivos staged, unstaged, untracked, conflictos, ahead/behind
```

#### Actualizar un archivo

```python
await update_file(
    repo_url="https://github.com/usuario/proyecto.git",
    file_path="src/Models/UserDto.cs", 
    content=nuevo_contenido
)
```

#### Hacer commit y push

```python
# Commit con archivos específicos
await git_commit(
    repo_url="https://github.com/usuario/proyecto.git",
    message="feat: añadir nueva funcionalidad de usuario",
    files=["src/Models/UserDto.cs", "src/Services/UserService.cs"]
)

# Push a repositorio remoto
await git_push("https://github.com/usuario/proyecto.git")
```

#### Gestionar ramas

```python
# Crear nueva rama feature
await git_branch(
    repo_url="https://github.com/usuario/proyecto.git",
    action="create",
    branch_name="feature/nueva-funcionalidad",
    from_branch="main"
)

# Cambiar a la rama
await git_branch(
    repo_url="https://github.com/usuario/proyecto.git",
    action="switch", 
    branch_name="feature/nueva-funcionalidad"
)
```

#### 🆕 Ejemplos de Gestión de Directorios

```python
# Crear un nuevo directorio
await create_directory(directory_path="./src/NewModule")

# Renombrar/mover un directorio  
await rename_directory(
    old_path="./src/OldModule",
    new_path="./src/RenamedModule"
)

# Eliminar directorio (envía a papelera en Windows)
await delete_directory(directory_path="./temp/obsolete_files")

# Listar contenido de directorio
await list_directory(directory_path="./src")
```

#### Análisis de Código C Sharp

```python
# Buscar una clase específica
find_class(
    repo_url="https://github.com/usuario/proyecto-csharp.git",
    class_name="UserService",
    search_type="direct"  # o "deep" para búsqueda profunda
)

# Obtener contenido de archivo C# con análisis
get_cs_file_content(
    repo_url="https://github.com/usuario/proyecto-csharp.git",
    file_path="src/Services/UserService.cs"
)

# Buscar elementos específicos (DTOs, Services, Controllers, etc.)
find_elements(
    repo_url="https://github.com/usuario/proyecto-csharp.git",
    element_type="dto",  # dto, service, controller, interface, enum, class
    element_name="User"
)

# Obtener estructura completa de la solución
get_solution_structure(
    repo_url="https://github.com/usuario/proyecto-csharp.git"
)
```

## 📚 API Reference

### Herramientas de Análisis de Código C Sharp

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `find_class` | Localiza clases específicas | `repo_url`, `class_name`, `search_type` |
| `get_cs_file_content` | Contenido de archivo C# con análisis | `repo_url`, `file_path` |
| `find_elements` | Busca DTOs, Services, Controllers, etc. | `repo_url`, `element_type`, `element_name` |
| `get_solution_structure` | Estructura completa de solución C# | `repo_url` |

### Herramientas de Archivos

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `get_file_content` | Lee contenido completo de archivo | `file_path` |
| `set_file_content` | Crea/modifica archivos con backup | `file_path`, `content`, `create_backup` |
| `rename_file` | Renombra/mueve archivos | `source_path`, `dest_path` |
| `delete_file` | Elimina archivos a papelera | `file_path` |
| `copy_file` | Copia archivos | `source_path`, `dest_path` |

### 🆕 Herramientas de Directorios

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `create_directory` | Crea nueva carpeta | `directory_path` |
| `rename_directory` | Renombra/mueve carpeta | `old_path`, `new_path` |
| `delete_directory` | Elimina carpeta (a papelera) | `directory_path` |
| `list_directory` | Lista contenido de directorio | `directory_path?` |

### Herramientas Git

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `git_status` | Estado del repositorio | `repo_url` |
| `git_diff` | Diferencias entre versiones | `repo_url`, `file_path?`, `staged?` |
| `git_commit` | Realizar commit | `repo_url`, `message`, `files?`, `add_all?` |
| `git_push` | Subir cambios | `repo_url`, `branch?`, `force?` |
| `git_pull` | Descargar cambios | `repo_url`, `branch?`, `rebase?` |
| `git_branch` | Gestionar ramas | `repo_url`, `action`, `branch_name?` |
| `git_merge` | Fusionar ramas | `repo_url`, `source_branch`, `target_branch?` |
| `git_stash` | Gestionar stash | `repo_url`, `action`, `message?` |
| `git_log` | Historial de commits | `repo_url`, `limit?`, `branch?` |

## 🔧 Configuración

### Variables de Entorno

```bash
# Opcional: Configurar directorio de cache
MCP_CACHE_DIR=/path/to/cache

# Opcional: Configurar timeout para operaciones Git
GIT_TIMEOUT=300

# Opcional: Configurar logging
LOG_LEVEL=INFO
```

### Configuración Git

Asegúrate de tener Git configurado globalmente:

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu.email@ejemplo.com"
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Tests con cobertura
pytest --cov=src

# Tests específicos
pytest tests/test_code_handler.py

# Tests de integración
pytest -m integration
```

## 🐛 Troubleshooting

### Problemas Comunes

#### Error: "Repositorio no encontrado"

- Verifica que la URL del repositorio sea correcta
- Asegúrate de tener acceso al repositorio
- Para repositorios privados, configura SSH keys o tokens

#### Error: "Git command failed"

- Verifica que Git esté instalado y en el PATH
- Comprueba la configuración global de Git
- Revisa permisos de escritura en el directorio de trabajo

#### Error: "Archivo no encontrado"

- Verifica que la ruta del archivo sea correcta y relativa al repositorio
- Asegúrate de que el archivo exista en la rama actual

#### 🆕 Error: "Sin permisos para crear/eliminar carpeta"

- Verifica que tengas permisos de escritura en el directorio padre
- En Windows, ejecuta como administrador si es necesario
- Comprueba que la carpeta no esté siendo usada por otro proceso

#### 🆕 Error: "Carpeta no enviada a papelera"

- Asegúrate de que `winshell` esté instalado: `pip install winshell`
- En sistemas no-Windows, la eliminación será permanente (es normal)
- Verifica que la papelera de reciclaje esté habilitada en Windows

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -am 'feat: añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🙏 Agradecimientos

- [Model Context Protocol](https://modelcontextprotocol.io/) por la especificación MCP
- [GitPython](https://gitpython.readthedocs.io/) por las operaciones Git
- [Tree-sitter](https://tree-sitter.github.io/) para el análisis de código

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/tuusuario/mcp-code-manager/issues)
- **Discusiones**: [GitHub Discussions](https://github.com/tuusuario/mcp-code-manager/discussions)

---

**MCP Code Manager** - Llevando la gestión de código C# al siguiente nivel con IA 🚀
