# MCP Code Manager - API Documentation

## Overview

El MCP Code Manager proporciona endpoints especializados para la gestión de código C# y operaciones Git. Todos los endpoints siguen el protocolo MCP y retornan respuestas estructuradas en JSON.

## Authentication

El servidor utiliza la configuración global de Git para autenticación. Asegúrate de tener configurado:

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu.email@ejemplo.com"
```

Para repositorios privados, configura SSH keys o tokens de acceso.

## Code Management Endpoints

### find_class

Localiza una clase específica en el repositorio C#.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `class_name` (string, required): Nombre de la clase a buscar
- `search_type` (string, optional): "direct" o "deep" (default: "direct")

**Response:**

```json
{
  "class_name": "UserService",
  "file_path": "src/Services/UserService.cs",
  "full_path": "/path/to/repo/src/Services/UserService.cs",
  "search_type": "direct",
  "analysis": {
    "namespace": "MyApp.Services",
    "elements": [...],
    "methods": [...],
    "properties": [...]
  }
}
```

**Example:**

```python
await find_class(
    repo_url="https://github.com/user/project.git",
    class_name="UserService",
    search_type="direct"
)
```

### get_file_content

Obtiene el contenido completo de un archivo con metadatos.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `file_path` (string, required): Ruta relativa del archivo

**Response:**

```json
{
  "file_path": "src/Models/User.cs",
  "content": "public class User { ... }",
  "size": 1024,
  "lines": 45,
  "analysis": {...},
  "encoding": "utf-8"
}
```

### find_elements

Busca elementos específicos por tipo (DTOs, Services, Controllers, etc.).

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `element_type` (enum, required): "dto", "service", "controller", "interface", "enum"
- `element_name` (string, required): Nombre del elemento a buscar

**Response:**

```json
[
  {
    "element_name": "UserDto",
    "element_type": "class",
    "file_path": "src/Models/UserDto.cs",
    "line_number": 10,
    "namespace": "MyApp.Models",
    "modifiers": ["public"],
    "summary": "Data transfer object for user information"
  }
]
```

### get_solution_structure

Obtiene la estructura completa de la solución C# organizada por namespaces y tipos.

**Parameters:**

- `repo_url` (string, required): URL del repositorio

**Response:**

```json
{
  "solution_path": "/path/to/repo",
  "total_cs_files": 25,
  "namespaces": {
    "MyApp.Controllers": [...],
    "MyApp.Services": [...],
    "MyApp.Models": [...]
  },
  "file_types": {
    "controllers": [...],
    "services": [...],
    "dtos": [...],
    "interfaces": [...]
  },
  "summary": {
    "total_classes": 15,
    "total_interfaces": 5,
    "total_enums": 3,
    "total_records": 2
  }
}
```

## File Management Endpoints

### create_file

Crea un nuevo archivo en el repositorio.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `file_path` (string, required): Ruta donde crear el archivo
- `content` (string, required): Contenido del archivo

**Response:**

```json
{
  "status": "created",
  "message": "Archivo creado exitosamente: src/NewClass.cs",
  "file_info": {
    "path": "src/NewClass.cs",
    "size": 256,
    "lines": 12
  }
}
```

### update_file

Actualiza un archivo existente.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `file_path` (string, required): Ruta del archivo
- `content` (string, required): Nuevo contenido

**Response:**

```json
{
  "status": "updated",
  "message": "Archivo actualizado exitosamente: src/User.cs",
  "changes": {
    "original_size": 1024,
    "new_size": 1156,
    "size_diff": 132,
    "lines_diff": 5
  }
}
```

### delete_file

Elimina un archivo del repositorio.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `file_path` (string, required): Ruta del archivo

### list_files

Lista todos los archivos del repositorio con filtros opcionales.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `file_pattern` (string, optional): Patrón de archivos (ej: "*.cs", "*.json")
- `include_directories` (boolean, optional): Incluir directorios (default: false)
- `max_depth` (integer, optional): Profundidad máxima (-1 = ilimitada)
- `exclude_patterns` (array, optional): Patrones a excluir

**Response:**

```json
{
  "repository_url": "https://github.com/user/project.git",
  "total_files": 45,
  "total_directories": 8,
  "total_size": 2048576,
  "total_size_formatted": "2.0 MB",
  "extensions_stats": {
    ".cs": {"count": 25, "size": 1024000},
    ".json": {"count": 3, "size": 2048}
  },
  "files": [
    {
      "path": "src/Controllers/UserController.cs",
      "name": "UserController.cs",
      "type": "file",
      "size": 2048,
      "extension": ".cs",
      "is_csharp": true,
      "directory": "src/Controllers",
      "depth": 2
    }
  ]
}
```

### check_permissions

Verifica permisos de acceso en el directorio del repositorio.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `target_path` (string, optional): Ruta específica a verificar

**Response:**

```json
{
  "path": "src/Controllers",
  "exists": true,
  "is_directory": true,
  "permissions": {
    "readable": true,
    "writable": true,
    "can_create_files": true,
    "can_delete_files": true,
    "can_create_directories": true
  },
  "git": {
    "is_git_repository": true,
    "can_read_git": true,
    "can_write_git": true,
    "remotes_accessible": true
  },
  "summary": {
    "fully_functional": true
  },
  "errors": []
}
```

## Git Operations Endpoints

### git_status

Obtiene el estado completo del repositorio.

**Response:**

```json
{
  "branch": "main",
  "ahead": 2,
  "behind": 0,
  "staged": [
    {"file": "src/User.cs", "status": "modified"}
  ],
  "unstaged": [
    {"file": "src/UserService.cs", "status": "modified"}
  ],
  "untracked": ["src/NewFile.cs"],
  "conflicts": [],
  "clean": false,
  "summary": "2 commits ahead, 1 staged file, 1 unstaged file, 1 untracked file"
}
```

### git_diff

Muestra diferencias entre versiones.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `file_path` (string, optional): Archivo específico
- `staged` (boolean, optional): Diferencias staged (default: false)

### git_commit

Realiza un commit con los cambios.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `message` (string, required): Mensaje del commit
- `files` (array, optional): Archivos específicos
- `add_all` (boolean, optional): Añadir todos los archivos (default: false)

**Response:**

```json
{
  "status": "committed",
  "commit_hash": "abc123def456...",
  "short_hash": "abc123d",
  "message": "feat: add user authentication",
  "author": "Developer Name",
  "files_changed": 3,
  "branch": "main"
}
```

### git_push

Sube cambios al repositorio remoto.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `branch` (string, optional): Rama específica
- `force` (boolean, optional): Push forzado (default: false)

### git_pull

Descarga cambios del repositorio remoto.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `branch` (string, optional): Rama específica
- `rebase` (boolean, optional): Usar rebase (default: false)

### git_branch

Gestiona ramas del repositorio.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `action` (enum, required): "create", "delete", "switch", "list", "rename"
- `branch_name` (string, optional): Nombre de la rama
- `from_branch` (string, optional): Rama base para crear

### git_merge

Fusiona ramas.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `source_branch` (string, required): Rama origen
- `target_branch` (string, optional): Rama destino
- `no_ff` (boolean, optional): No fast-forward (default: false)

### git_stash

Gestiona el stash.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `action` (enum, required): "save", "pop", "list", "apply", "drop"
- `message` (string, optional): Mensaje del stash
- `stash_index` (integer, optional): Índice del stash

### git_log

Muestra el historial de commits.

**Parameters:**

- `repo_url` (string, required): URL del repositorio
- `limit` (integer, optional): Número de commits (default: 10)
- `branch` (string, optional): Rama específica
- `file_path` (string, optional): Archivo específico

**Response:**

```json
{
  "branch": "main",
  "total_commits": 5,
  "commits": [
    {
      "hash": "abc123def456...",
      "short_hash": "abc123d",
      "message": "feat: add user authentication",
      "author": "Developer Name",
      "date": "2024-01-15T10:30:00Z",
      "stats": {
        "files": 3,
        "insertions": 45,
        "deletions": 12
      }
    }
  ]
}
```

## Error Handling

Todos los endpoints manejan errores de manera consistente:

```json
{
  "error": "ValidationError",
  "message": "Nombre de clase es requerido",
  "code": "VALIDATION_ERROR"
}
```

### Error Types

- `ValidationError`: Error de validación de parámetros
- `RepositoryError`: Error relacionado con el repositorio
- `GitError`: Error en operaciones Git
- `FileOperationError`: Error en operaciones de archivo
- `CodeAnalysisError`: Error en análisis de código
- `NetworkError`: Error de conectividad
- `AuthenticationError`: Error de autenticación

## Rate Limits

No hay límites de rate específicos, pero las operaciones están optimizadas para:

- Cache local de repositorios
- Operaciones asíncronas
- Timeouts configurables

## Best Practices

1. **Usar búsqueda directa primero**: Para mejor rendimiento
2. **Verificar permisos**: Antes de operaciones de escritura
3. **Validar estado Git**: Antes de commits y merges
4. **Manejar conflictos**: Verificar estado después de merges
5. **Usar patrones específicos**: En listado de archivos para mejor rendimiento

## Directory Management Endpoints

### create_directory

Crea una nueva carpeta/directorio en el sistema de archivos.

**Parámetros:**

- `directory_path` (string, requerido): Ruta completa de la carpeta a crear

**Respuesta:**

```json
{
  "type": "text",
  "text": "✅ Carpeta creada exitosamente: 'ruta/del/directorio'"
}
```

**Errores comunes:**

- Carpeta ya existe: `⚠️ La carpeta 'ruta' ya existe`
- Sin permisos: `❌ Error: Sin permisos para crear la carpeta`

### rename_directory

Renombra una carpeta/directorio existente.

**Parámetros:**

- `old_path` (string, requerido): Ruta actual de la carpeta
- `new_path` (string, requerido): Nueva ruta/nombre de la carpeta

**Respuesta:**

```json
{
  "type": "text", 
  "text": "✅ Carpeta renombrada exitosamente: 'ruta_vieja' → 'ruta_nueva'"
}
```

**Errores comunes:**

- Carpeta origen no existe: `❌ Error: La carpeta origen 'ruta' no existe`
- Destino ya existe: `❌ Error: El destino 'ruta' ya existe`

### delete_directory

Elimina una carpeta/directorio enviándola a la papelera de reciclaje (Windows).

**Parámetros:**

- `directory_path` (string, requerido): Ruta completa de la carpeta a eliminar

**Respuesta:**

```json
{
  "type": "text",
  "text": "🗑️ Carpeta enviada a la papelera: 'ruta/del/directorio'"
}
```

**Comportamiento:**

- En Windows con `winshell` instalado: Se envía a la papelera de reciclaje
- Sin `winshell` o en otros sistemas: Eliminación permanente con advertencia

**Errores comunes:**

- Carpeta no existe: `❌ Error: La carpeta 'ruta' no existe`
- Sin permisos: `❌ Error: Sin permisos para eliminar la carpeta`
