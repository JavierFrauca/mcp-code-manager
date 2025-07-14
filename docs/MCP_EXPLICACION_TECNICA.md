# Explicación Técnica: MCP Code Manager

Este documento describe el funcionamiento técnico del MCP Code Manager, su arquitectura, componentes principales y flujo de trabajo. Está orientado a desarrolladores o usuarios con conocimientos técnicos que deseen entender cómo opera internamente la herramienta.

---

## 1. Arquitectura General

MCP Code Manager está estructurado en módulos Python organizados en carpetas como `src/handlers`, `src/services` y `src/utils`. Utiliza la librería GitPython para interactuar con repositorios Git y abstrae operaciones comunes en clases y servicios reutilizables.

### Componentes principales

- **handlers/**: Gestionan la lógica de alto nivel y orquestan las peticiones del usuario.
- **services/**: Implementan la lógica de negocio, como operaciones Git, análisis de código, gestión de archivos, etc.
- **utils/**: Utilidades y funciones auxiliares (validaciones, logging, excepciones personalizadas).

---

## 2. Flujo de Trabajo Básico

1. **Recepción de la petición**: Un handler recibe la petición del usuario (por ejemplo, clonar un repositorio).
2. **Delegación al servicio**: El handler llama al servicio correspondiente (por ejemplo, `GitManager`) para ejecutar la operación.
3. **Ejecución de la lógica**: El servicio realiza la operación usando GitPython y otras utilidades.
4. **Gestión de errores**: Si ocurre un error, se lanza una excepción personalizada (`GitError`, `RepositoryError`, etc.) que es capturada y devuelta al usuario de forma amigable.
5. **Respuesta**: El resultado se devuelve al handler, que lo presenta al usuario o lo utiliza en otro flujo.

---

## 3. Ejemplo de Operación: Commit

- El usuario solicita guardar cambios (commit).
- El handler llama a `GitManager.commit_changes()`.
- El método verifica la configuración de usuario, añade los archivos al staging, y ejecuta el commit.
- Si el repositorio no tiene commits previos, maneja el caso especial de HEAD no resuelto.
- Devuelve información del commit realizado (hash, autor, archivos afectados, etc.).

---

## 4. Manejo de Repositorios

- **Clonado**: Se genera una ruta local única para cada repositorio remoto usando un hash de la URL.
- **Inicialización**: Permite crear repositorios nuevos, configurando rama inicial y usuario por defecto.
- **Verificación**: Antes de operar, se asegura que el repositorio existe y es válido (estructura `.git`).

---

## 5. Operaciones Git Soportadas

- Clonar, inicializar, obtener estado, ver diferencias, hacer commit, push, pull, gestión de ramas, merge, stash, historial de commits, reset, tags y remotos.
- Todas las operaciones están encapsuladas en métodos asíncronos para facilitar la integración en aplicaciones web o de escritorio.

---

## 6. Manejo de Errores y Robustez

- Uso intensivo de excepciones personalizadas para distinguir errores de Git, de repositorio, o de lógica interna.
- Se capturan y gestionan casos especiales como repositorios vacíos, HEAD no resuelto, conflictos de merge, etc.

---

## 7. Extensibilidad

- La arquitectura modular permite añadir nuevos servicios o handlers fácilmente.
- El uso de clases y métodos bien definidos facilita el mantenimiento y la ampliación de funcionalidades.

---

## 8. Dependencias Principales

- **GitPython**: Para todas las operaciones Git.
- **Python estándar**: os, shutil, tempfile, hashlib, etc.

---

## 9. Seguridad y Buenas Prácticas

- No se ejecutan comandos shell directos; todo se realiza vía API de GitPython.
- Se valida la existencia y validez de rutas antes de operar.
- Se evita la exposición de información sensible en los mensajes de error.

---

## 10. Logs y Depuración

- Los logs de operaciones y errores se almacenan en la carpeta `logs/` para facilitar la depuración y el soporte.

---

## 11. Integración y Uso

- Puede integrarse en aplicaciones web, de escritorio o usarse como script standalone.
- El diseño orientado a servicios y handlers permite desacoplar la lógica de negocio de la interfaz de usuario.

---

---

## 12. Diagrama de bloques (flujo principal)

```text
┌──────────────┐
│   Usuario    │
└─────┬────────┘
      │
      ▼
┌──────────────┐
│   Handler    │  (Recibe petición y valida)
└─────┬────────┘
      │
      ▼
┌──────────────┐
│   Servicio   │  (Ejecuta lógica: GitManager, etc)
└─────┬────────┘
      │
      ▼
┌──────────────┐
│   Utils      │  (Validaciones, logs, excepciones)
└─────┬────────┘
      │
      ▼
┌──────────────┐
│  GitPython   │  (Operaciones Git reales)
└─────┬────────┘
      │
      ▼
┌──────────────┐
│   Respuesta  │  (Resultado devuelto al usuario)
└──────────────┘
```

**Notas:**

- El usuario interactúa con la interfaz (CLI, web, etc.), que llama a un handler.
- El handler delega la operación al servicio correspondiente.
- El servicio usa utilidades y GitPython para realizar la acción.
- El resultado (o error) se devuelve al usuario.

Para más detalles, revisa el código fuente en las carpetas `src/services/`, `src/handlers/` y `src/utils/`.
