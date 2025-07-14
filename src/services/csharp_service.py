"""
Servicio para operaciones con proyectos y soluciones C#
"""
import os
import subprocess
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import asyncio

from utils.exceptions import CodeAnalysisError

class CSharpService:
    """Servicio para gestión de proyectos y soluciones C#"""
    
    def __init__(self):
        self.dotnet_timeout = 300  # 5 minutos timeout para operaciones
        
    async def check_dotnet_installed(self) -> Dict[str, Any]:
        """
        Verifica si dotnet CLI está instalado y disponible
        
        Returns:
            Información sobre la instalación de dotnet
        """
        try:
            result = await self._run_dotnet_command(["--version"])
            
            if result["success"]:
                # Obtener información adicional
                info_result = await self._run_dotnet_command(["--info"])
                
                return {
                    "installed": True,
                    "version": result["output"].strip(),
                    "info": info_result.get("output", ""),
                    "path": await self._get_dotnet_path()
                }
            else:
                return {
                    "installed": False,
                    "error": result.get("error", "dotnet command not found")
                }
                
        except Exception as e:
            return {
                "installed": False,
                "error": str(e)
            }
    
    async def create_solution(self, solution_path: str, solution_name: str) -> Dict[str, Any]:
        """
        Crea una nueva solución C#
        
        Args:
            solution_path: Directorio donde crear la solución
            solution_name: Nombre de la solución
            
        Returns:
            Resultado de la operación
        """
        try:
            # Crear directorio si no existe
            os.makedirs(solution_path, exist_ok=True)
            
            # Ejecutar dotnet new sln
            result = await self._run_dotnet_command(
                ["new", "sln", "-n", solution_name],
                cwd=solution_path
            )
            
            if result["success"]:
                sln_file = os.path.join(solution_path, f"{solution_name}.sln")
                return {
                    "success": True,
                    "message": f"Solución creada exitosamente: {solution_name}",
                    "solution_file": sln_file,
                    "output": result["output"]
                }
            else:
                raise CodeAnalysisError(f"Error creando solución: {result['error']}")
                
        except Exception as e:
            raise CodeAnalysisError(f"Error creando solución: {str(e)}")
    
    async def create_project(self, project_path: str, project_name: str, template: str = "console") -> Dict[str, Any]:
        """
        Crea un nuevo proyecto C#
        
        Args:
            project_path: Directorio donde crear el proyecto
            project_name: Nombre del proyecto
            template: Tipo de proyecto (console, classlib, web, etc.)
            
        Returns:
            Resultado de la operación
        """
        try:
            # Crear directorio si no existe
            os.makedirs(project_path, exist_ok=True)
            
            # Ejecutar dotnet new [template]
            result = await self._run_dotnet_command(
                ["new", template, "-n", project_name],
                cwd=project_path
            )
            
            if result["success"]:
                proj_file = os.path.join(project_path, project_name, f"{project_name}.csproj")
                return {
                    "success": True,
                    "message": f"Proyecto creado exitosamente: {project_name}",
                    "project_file": proj_file,
                    "template": template,
                    "output": result["output"]
                }
            else:
                raise CodeAnalysisError(f"Error creando proyecto: {result['error']}")
                
        except Exception as e:
            raise CodeAnalysisError(f"Error creando proyecto: {str(e)}")
    
    async def add_project_to_solution(self, solution_file: str, project_file: str) -> Dict[str, Any]:
        """
        Agrega un proyecto a una solución
        
        Args:
            solution_file: Ruta al archivo .sln
            project_file: Ruta al archivo .csproj
            
        Returns:
            Resultado de la operación
        """
        try:
            if not os.path.exists(solution_file):
                raise CodeAnalysisError(f"Archivo de solución no encontrado: {solution_file}")
            
            if not os.path.exists(project_file):
                raise CodeAnalysisError(f"Archivo de proyecto no encontrado: {project_file}")
            
            # Ejecutar dotnet sln add
            result = await self._run_dotnet_command(
                ["sln", solution_file, "add", project_file]
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Proyecto agregado a la solución exitosamente",
                    "output": result["output"]
                }
            else:
                raise CodeAnalysisError(f"Error agregando proyecto a solución: {result['error']}")
                
        except Exception as e:
            raise CodeAnalysisError(f"Error agregando proyecto a solución: {str(e)}")
    
    async def build_solution(self, solution_path: str, configuration: str = "Debug") -> Dict[str, Any]:
        """
        Compila una solución C# con configuración NuGet mejorada
        
        Args:
            solution_path: Directorio de la solución o archivo .sln
            configuration: Configuración (Debug/Release)
            
        Returns:
            Resultado de la compilación
        """
        try:
            # Validar parámetros
            if not solution_path or not solution_path.strip():
                raise CodeAnalysisError("La ruta de la solución es requerida")
            
            if not configuration or not configuration.strip():
                configuration = "Debug"
            
            solution_path = solution_path.strip()
            configuration = configuration.strip()
            
            # Normalizar ruta usando rutas absolutas
            solution_path = os.path.normpath(os.path.abspath(solution_path))
            
            if not os.path.exists(solution_path):
                raise CodeAnalysisError(f"Ruta de solución no encontrada: {solution_path}")
            
            # Determinar si es archivo o directorio
            if os.path.isfile(solution_path) and solution_path.endswith('.sln'):
                # Es un archivo .sln específico
                cwd_path = os.path.dirname(solution_path)
                sln_filename = os.path.basename(solution_path)
                cmd = ["build", sln_filename, "--configuration", configuration, "--verbosity", "normal"]
            elif os.path.isfile(solution_path) and solution_path.endswith(('.csproj', '.fsproj', '.vbproj')):
                # Es un archivo de proyecto específico
                cwd_path = os.path.dirname(solution_path)
                proj_filename = os.path.basename(solution_path)
                cmd = ["build", proj_filename, "--configuration", configuration, "--verbosity", "normal"]
            else:
                # Es un directorio - buscar archivos .sln o .csproj
                cwd_path = solution_path
                cmd = ["build", "--configuration", configuration, "--verbosity", "normal"]
            
            # Verificar que el directorio de trabajo existe
            if not os.path.exists(cwd_path):
                raise CodeAnalysisError(f"Directorio de trabajo no encontrado: {cwd_path}")
            
            # PASO 1: Asegurar que los paquetes estén restaurados
            restore_result = await self.restore_packages(cwd_path)
            
            # PASO 2: Validar que se generaron los archivos project.assets.json
            assets_validation = await self._validate_project_assets(cwd_path)
            
            if not assets_validation["assets_found"]:
                # Intentar restauración forzada
                await self._clear_nuget_cache()
                await self._clean_project_artifacts(cwd_path)
                restore_result = await self.restore_packages(cwd_path)
                assets_validation = await self._validate_project_assets(cwd_path)
            
            # Agregar flags para mejorar la estabilidad
            cmd.extend(["--nologo", "--no-restore"])  # No restaurar de nuevo
            
            # PASO 3: Ejecutar dotnet build
            result = await self._run_dotnet_command(cmd, cwd=cwd_path)
            
            # Analizar errores y warnings
            build_analysis = self._analyze_build_output(result.get("output", ""), result.get("error", ""))
            
            return {
                "success": result["success"],
                "message": "Compilación completada" if result["success"] else "Compilación falló",
                "output": result["output"],
                "error": result.get("error", ""),
                "configuration": configuration,
                "analysis": build_analysis,
                "working_directory": cwd_path,
                "restore_result": restore_result,
                "assets_validation": assets_validation
            }
                
        except Exception as e:
            raise CodeAnalysisError(f"Error compilando solución: {str(e)}")
    
    async def run_tests(self, test_path: str, filter_expression: str = None, collect_coverage: bool = False) -> Dict[str, Any]:
        """
        Ejecuta tests en un proyecto o solución
        
        Args:
            test_path: Directorio del proyecto/solución con tests
            filter_expression: Filtro para tests específicos
            collect_coverage: Si recopilar coverage
            
        Returns:
            Resultados de los tests
        """
        try:
            # Construir comando
            cmd = ["test", "--logger", "trx", "--logger", "console;verbosity=detailed"]
            
            if filter_expression:
                cmd.extend(["--filter", filter_expression])
            
            if collect_coverage:
                cmd.extend(["--collect", "XPlat Code Coverage"])
            
            # Ejecutar tests
            result = await self._run_dotnet_command(cmd, cwd=test_path)
            
            # Analizar resultados
            test_analysis = self._analyze_test_output(result.get("output", ""), result.get("error", ""))
            
            return {
                "success": result["success"],
                "message": "Tests ejecutados",
                "output": result["output"],
                "error": result.get("error", ""),
                "filter": filter_expression,
                "coverage": collect_coverage,
                "analysis": test_analysis
            }
                
        except Exception as e:
            raise CodeAnalysisError(f"Error ejecutando tests: {str(e)}")
    
    async def add_package(self, project_file: str, package_name: str, version: str = None) -> Dict[str, Any]:
        """
        Agrega un paquete NuGet a un proyecto con configuración mejorada
        
        Args:
            project_file: Ruta al archivo .csproj
            package_name: Nombre del paquete
            version: Versión específica (opcional)
            
        Returns:
            Resultado de la operación
        """
        try:
            # Validar parámetros
            if not project_file or not project_file.strip():
                raise CodeAnalysisError("La ruta del archivo de proyecto es requerida")
            
            if not package_name or not package_name.strip():
                raise CodeAnalysisError("El nombre del paquete es requerido")
            
            project_file = project_file.strip()
            package_name = package_name.strip()
            
            # Normalizar ruta usando rutas absolutas
            project_file = os.path.normpath(os.path.abspath(project_file))
            
            if not os.path.exists(project_file):
                raise CodeAnalysisError(f"Archivo de proyecto no encontrado: {project_file}")
            
            # Obtener el directorio del proyecto
            project_dir = os.path.dirname(project_file)
            project_filename = os.path.basename(project_file)
            
            # PASO 1: Configurar NuGet antes de agregar paquete
            nuget_config_result = await self._ensure_nuget_config(project_dir)
            
            # PASO 2: Limpiar artefactos previos si es necesario
            if not nuget_config_result["cache_valid"]:
                await self._clean_project_artifacts(project_dir)
                await self._clear_nuget_cache()
            
            # Construir comando relativo al directorio del proyecto
            cmd = ["add", project_filename, "package", package_name]
            if version and version.strip():
                cmd.extend(["--version", version.strip()])
            
            # Agregar configuración NuGet específica
            if (nuget_config_result["config_path"] != "default" and 
                nuget_config_result["config_path"] and 
                os.path.exists(nuget_config_result["config_path"])):
                cmd.extend(["--configfile", f'"{nuget_config_result["config_path"]}"'])
            
            # Agregar flags para mejor manejo
            cmd.extend(["--no-restore"])  # No restaurar automáticamente
            
            # PASO 3: Ejecutar comando con reintentos
            max_retries = 3
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    # Ejecutar comando desde el directorio del proyecto
                    result = await self._run_dotnet_command(cmd, cwd=project_dir)
                    
                    if result["success"]:
                        # PASO 4: Restaurar paquetes después de agregar
                        restore_result = await self.restore_packages(project_dir)
                        
                        return {
                            "success": True,
                            "message": f"Paquete {package_name} agregado exitosamente",
                            "package": package_name,
                            "version": version,
                            "output": result.get("output", ""),
                            "project_file": project_file,
                            "attempt": attempt + 1,
                            "nuget_config": nuget_config_result,
                            "restore_result": restore_result
                        }
                    else:
                        last_error = result.get("error", "Error desconocido")
                        
                        # Manejo de errores específicos
                        error_message = result.get("error", "") or result.get("output", "")
                        if "No se puede crear el archivo de gráfico de dependencias" in error_message:
                            # Problema con gráfico de dependencias - limpiar y reconfigurar
                            await self._clean_project_artifacts(project_dir)
                            await self._ensure_nuget_config(project_dir, force_recreate=True)
                        elif "Value cannot be null" in error_message:
                            # Problema con rutas NuGet
                            await self._clear_nuget_cache()
                            
                except Exception as e:
                    last_error = str(e)
                    
                # Esperar antes del siguiente intento
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
            
            # Si llegamos aquí, todos los intentos fallaron
            return {
                "success": False,
                "message": f"Error agregando paquete después de {max_retries} intentos",
                "package": package_name,
                "version": version,
                "last_error": last_error or "Error desconocido",
                "nuget_config": nuget_config_result,
                "project_file": project_file
            }
                
        except Exception as e:
            raise CodeAnalysisError(f"Error agregando paquete: {str(e)}")
    
    async def list_projects_in_solution(self, solution_file: str) -> Dict[str, Any]:
        """
        Lista los proyectos en una solución
        
        Args:
            solution_file: Ruta al archivo .sln
            
        Returns:
            Lista de proyectos
        """
        try:
            if not os.path.exists(solution_file):
                raise CodeAnalysisError(f"Archivo de solución no encontrado: {solution_file}")
            
            # Ejecutar dotnet sln list
            result = await self._run_dotnet_command(["sln", solution_file, "list"])
            
            if result["success"]:
                projects = self._parse_solution_projects(result["output"])
                return {
                    "success": True,
                    "projects": projects,
                    "total_projects": len(projects),
                    "output": result["output"]
                }
            else:
                raise CodeAnalysisError(f"Error listando proyectos: {result['error']}")
                
        except Exception as e:
            raise CodeAnalysisError(f"Error listando proyectos: {str(e)}")
    
    async def restore_packages(self, project_path: str) -> Dict[str, Any]:
        """
        Restaura paquetes NuGet de un proyecto/solución con configuración mejorada
        
        Args:
            project_path: Directorio del proyecto/solución
            
        Returns:
            Resultado de la operación
        """
        try:
            # Validar parámetros
            if not project_path or not project_path.strip():
                raise CodeAnalysisError("La ruta del proyecto es requerida")
            
            project_path = project_path.strip()
            
            # Normalizar ruta usando rutas absolutas
            project_path = os.path.normpath(os.path.abspath(project_path))
            
            if not os.path.exists(project_path):
                raise CodeAnalysisError(f"Directorio del proyecto no encontrado: {project_path}")
            
            # PASO 1: Configurar NuGet correctamente
            nuget_config_result = await self._ensure_nuget_config(project_path)
            
            # PASO 2: Limpiar caché NuGet si es necesario
            if not nuget_config_result["cache_valid"]:
                await self._clear_nuget_cache()
            
            # Verificar si es un archivo específico o un directorio
            if os.path.isfile(project_path):
                # Es un archivo .sln/.csproj específico
                work_dir = os.path.dirname(project_path)
                cmd = ["restore", os.path.basename(project_path)]
            else:
                # Es un directorio
                work_dir = project_path
                cmd = ["restore"]
            
            # Agregar flags para mejorar la estabilidad y diagnóstico
            cmd.extend([
                "--verbosity", "normal",
                "--disable-parallel",
                "--no-cache",  # Evitar problemas de caché
                "--force"      # Forzar restauración completa
            ])
            
            # Agregar configfile solo si es válido y no es "default"
            if (nuget_config_result["config_path"] != "default" and 
                nuget_config_result["config_path"] and 
                os.path.exists(nuget_config_result["config_path"])):
                cmd.extend(["--configfile", f'"{nuget_config_result["config_path"]}"'])
            
            # PASO 3: Intentar restauración con reintentos
            max_retries = 3
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    result = await self._run_dotnet_command(cmd, cwd=work_dir)
                    
                    if result["success"]:
                        # Verificar que se generó project.assets.json
                        assets_validation = await self._validate_project_assets(work_dir)
                        
                        return {
                            "success": True,
                            "message": "Restauración de paquetes completada exitosamente",
                            "attempt": attempt + 1,
                            "assets_generated": assets_validation["assets_found"],
                            "nuget_config": nuget_config_result,
                            "output": result["output"],
                            "validation": assets_validation
                        }
                    else:
                        last_error = result["error"]
                        
                        # Si es un error específico de NuGet, intentar solucionarlo
                        if "Value cannot be null" in result["error"]:
                            # Problema con rutas NuGet - limpiar y reconfigurar
                            await self._clear_nuget_cache()
                            await self._ensure_nuget_config(work_dir, force_recreate=True)
                        elif "project.assets.json" in result["error"]:
                            # Problema con assets - limpiar obj y bin
                            await self._clean_project_artifacts(work_dir)
                            
                except Exception as e:
                    last_error = str(e)
                    
                # Esperar antes del siguiente intento
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
            
            # Si llegamos aquí, todos los intentos fallaron
            return {
                "success": False,
                "message": f"Error en restauración después de {max_retries} intentos",
                "last_error": last_error,
                "nuget_config": nuget_config_result,
                "output": result["output"],
                "error": result.get("error", ""),
                "working_directory": work_dir
            }
                
        except Exception as e:
            raise CodeAnalysisError(f"Error restaurando paquetes: {str(e)}")
    
    # === Métodos auxiliares ===
    
    async def _run_dotnet_command(self, args: List[str], cwd: str = None) -> Dict[str, Any]:
        """
        Ejecuta un comando dotnet de forma asíncrona
        
        Args:
            args: Argumentos del comando dotnet
            cwd: Directorio de trabajo
            
        Returns:
            Resultado del comando
        """
        try:
            # Validar argumentos
            if not args:
                raise CodeAnalysisError("Los argumentos del comando son requeridos")
            
            # Información del directorio de trabajo
            current_dir = os.getcwd()
            
            # NO normalizar rutas absolutas en argumentos - mantener rutas relativas
            normalized_args = []
            for arg in args:
                # Solo normalizar si es una ruta que realmente existe
                if arg and os.path.exists(arg):
                    # Si el argumento es una ruta existente, normalizarla
                    normalized_args.append(os.path.normpath(arg))
                else:
                    # Para nombres de archivos relativos y otros argumentos, mantenerlos como están
                    normalized_args.append(arg)
            
            cmd = ["dotnet"] + normalized_args
            
            # Normalizar directorio de trabajo
            if cwd:
                cwd = os.path.normpath(os.path.abspath(cwd))
                # Verificar que el directorio existe
                if not os.path.exists(cwd):
                    raise CodeAnalysisError(f"Directorio de trabajo no existe: {cwd}")
            else:
                # Si no se especifica cwd, usar el directorio actual
                cwd = current_dir
            
            # Configurar environment variables para evitar problemas con NuGet
            env = os.environ.copy()
            env['DOTNET_CLI_TELEMETRY_OPTOUT'] = '1'
            env['DOTNET_SKIP_FIRST_TIME_EXPERIENCE'] = '1'
            env['DOTNET_NOLOGO'] = '1'
            
            # Crear directorio temporal para NuGet si no existe
            if 'NUGET_PACKAGES' not in env:
                temp_nuget = os.path.join(os.path.expanduser("~"), ".nuget", "packages")
                os.makedirs(temp_nuget, exist_ok=True)
                env['NUGET_PACKAGES'] = temp_nuget
            
            # Cambiar al directorio de trabajo ANTES de ejecutar el comando
            original_cwd = os.getcwd()
            try:
                if cwd and cwd != original_cwd:
                    os.chdir(cwd)
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                    env=env
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.dotnet_timeout
                )
                
                return {
                    "success": process.returncode == 0,
                    "output": stdout.decode('utf-8', errors='replace'),
                    "error": stderr.decode('utf-8', errors='replace'),
                    "return_code": process.returncode,
                    "command": " ".join(cmd),
                    "working_directory": cwd,
                    "debug_info": {
                        "original_cwd": original_cwd,
                        "requested_cwd": cwd,
                        "final_cwd": os.getcwd(),
                        "original_args": args,
                        "normalized_args": normalized_args
                    }
                }
                
            finally:
                # Restaurar directorio original
                if cwd and cwd != original_cwd:
                    os.chdir(original_cwd)
            
        except asyncio.TimeoutError:
            raise CodeAnalysisError(f"Timeout ejecutando comando dotnet: {' '.join(args)}")
        except FileNotFoundError:
            raise CodeAnalysisError("dotnet CLI no encontrado. Asegúrate de que esté instalado y en PATH")
        except Exception as e:
            raise CodeAnalysisError(f"Error ejecutando comando dotnet: {str(e)}")
    
    async def _get_dotnet_path(self) -> str:
        """Obtiene la ruta del ejecutable dotnet"""
        try:
            result = await self._run_dotnet_command(["--info"])
            if result["success"]:
                # Buscar la línea que contiene la ruta base
                for line in result["output"].split('\n'):
                    if 'Base Path:' in line:
                        return line.split('Base Path:')[1].strip()
            return "dotnet"
        except:
            return "dotnet"
    
    def _analyze_build_output(self, output: str, error: str) -> Dict[str, Any]:
        """
        Analiza la salida de compilación para extraer errores y warnings
        
        Args:
            output: Salida estándar
            error: Salida de error
            
        Returns:
            Análisis de la compilación
        """
        full_output = output + "\n" + error
        
        # Patrones para errores y warnings
        error_pattern = r'error\s+CS\d+:'
        warning_pattern = r'warning\s+CS\d+:'
        
        errors = re.findall(error_pattern + r'.*', full_output, re.IGNORECASE)
        warnings = re.findall(warning_pattern + r'.*', full_output, re.IGNORECASE)
        
        # Buscar resumen de build
        build_summary = {}
        if "Build succeeded." in full_output:
            build_summary["status"] = "success"
        elif "Build FAILED." in full_output:
            build_summary["status"] = "failed"
        else:
            build_summary["status"] = "unknown"
        
        return {
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "build_summary": build_summary,
            "has_errors": len(errors) > 0,
            "has_warnings": len(warnings) > 0
        }
    
    def _analyze_test_output(self, output: str, error: str) -> Dict[str, Any]:
        """
        Analiza la salida de tests para extraer resultados
        
        Args:
            output: Salida estándar
            error: Salida de error
            
        Returns:
            Análisis de los tests
        """
        full_output = output + "\n" + error
        
        # Buscar resumen de tests
        test_summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # Patrones para resultados de tests
        patterns = {
            "total": r'Total tests: (\d+)',
            "passed": r'Passed: (\d+)',
            "failed": r'Failed: (\d+)',
            "skipped": r'Skipped: (\d+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, full_output, re.IGNORECASE)
            if match:
                test_summary[key] = int(match.group(1))
        
        # Buscar tests fallidos específicos
        failed_tests = re.findall(r'Failed\s+([^\s]+)', full_output, re.IGNORECASE)
        
        return {
            "summary": test_summary,
            "failed_tests": failed_tests,
            "success_rate": (test_summary["passed"] / max(test_summary["total"], 1)) * 100,
            "has_failures": test_summary["failed"] > 0
        }
    
    def _parse_solution_projects(self, output: str) -> List[Dict[str, str]]:
        """
        Parsea la salida de 'dotnet sln list' para extraer proyectos
        
        Args:
            output: Salida del comando
            
        Returns:
            Lista de proyectos
        """
        projects = []
        lines = output.split('\n')
        
        # Buscar líneas que contienen rutas de proyectos
        for line in lines:
            line = line.strip()
            if line.endswith('.csproj') or line.endswith('.fsproj') or line.endswith('.vbproj'):
                project_path = line
                project_name = os.path.splitext(os.path.basename(project_path))[0]
                
                projects.append({
                    "name": project_name,
                    "path": project_path,
                    "full_path": os.path.abspath(project_path) if os.path.exists(project_path) else project_path
                })
        
        return projects
    
    async def _ensure_nuget_config(self, project_path: str, force_recreate: bool = False) -> Dict[str, Any]:
        """
        Asegura que existe una configuración NuGet válida
        
        Args:
            project_path: Ruta del proyecto
            force_recreate: Si forzar recreación del config
            
        Returns:
            Información sobre la configuración NuGet
        """
        try:
            # Normalizar ruta del proyecto
            project_path = os.path.normpath(os.path.abspath(project_path))
            
            # Buscar archivo nuget.config existente
            config_locations = [
                os.path.join(project_path, "nuget.config"),
                os.path.join(project_path, "NuGet.config")
            ]
            
            # Buscar config global solo si existe el directorio
            global_nuget_dir = os.path.join(os.path.expanduser("~"), ".nuget", "NuGet")
            if os.path.exists(global_nuget_dir):
                config_locations.append(os.path.join(global_nuget_dir, "NuGet.Config"))
            
            existing_config = None
            for config_path in config_locations:
                if os.path.exists(config_path):
                    existing_config = config_path
                    break
            
            # Si no existe config, se fuerza recreación, o el config existente no es válido
            should_create_config = (not existing_config or 
                                   force_recreate or 
                                   not self._is_valid_nuget_config(existing_config))
            
            if should_create_config:
                config_path = os.path.join(project_path, "nuget.config")
                await self._create_nuget_config(config_path)
                existing_config = config_path
            
            # Validar configuración NuGet
            nuget_cache_valid = await self._validate_nuget_cache()
            
            return {
                "config_path": existing_config or "default",
                "config_created": should_create_config,
                "cache_valid": nuget_cache_valid,
                "nuget_packages_path": os.path.join(os.path.expanduser("~"), ".nuget", "packages")
            }
            
        except Exception as e:
            # Si falla, usar configuración por defecto
            return {
                "config_path": "default",
                "config_created": False,
                "cache_valid": False,
                "error": str(e)
            }
    
    async def _create_nuget_config(self, config_path: str) -> None:
        """
        Crea un archivo nuget.config con configuración estándar
        
        Args:
            config_path: Ruta donde crear el archivo
        """
        nuget_config_content = """<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <add key="nuget.org" value="https://api.nuget.org/v3/index.json" protocolVersion="3" />
    <add key="Microsoft Visual Studio Offline Packages" value="C:\\Program Files (x86)\\Microsoft SDKs\\NuGetPackages\\" />
  </packageSources>
  <packageSourceCredentials />
  <apikeys />
  <disabledPackageSources />
  <config>
    <add key="globalPackagesFolder" value="%USERPROFILE%\\.nuget\\packages" />
    <add key="repositoryPath" value="packages" />
  </config>
</configuration>"""
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(nuget_config_content)
    
    async def _validate_nuget_cache(self) -> bool:
        """
        Valida que el caché NuGet esté en buen estado
        
        Returns:
            True si el caché es válido
        """
        try:
            # Verificar que el directorio de paquetes existe
            packages_dir = os.path.join(os.path.expanduser("~"), ".nuget", "packages")
            if not os.path.exists(packages_dir):
                return False
            
            # Ejecutar comando para listar fuentes
            result = await self._run_dotnet_command(["nuget", "list", "source"])
            return result["success"]
            
        except Exception:
            return False
    
    async def _clear_nuget_cache(self) -> Dict[str, Any]:
        """
        Limpia el caché NuGet
        
        Returns:
            Resultado de la operación
        """
        try:
            # Limpiar caché global
            result = await self._run_dotnet_command(["nuget", "locals", "all", "--clear"])
            
            return {
                "success": result["success"],
                "message": "Caché NuGet limpiado" if result["success"] else "Error limpiando caché",
                "output": result["output"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error limpiando caché NuGet: {str(e)}"
            }
    
    async def _validate_project_assets(self, work_dir: str) -> Dict[str, Any]:
        """
        Valida que se generaron los archivos project.assets.json
        
        Args:
            work_dir: Directorio de trabajo
            
        Returns:
            Resultado de la validación
        """
        try:
            assets_files = []
            
            # Buscar archivos project.assets.json en subdirectorios obj
            for root, dirs, files in os.walk(work_dir):
                for file in files:
                    if file == "project.assets.json":
                        assets_files.append(os.path.join(root, file))
            
            return {
                "assets_found": len(assets_files) > 0,
                "assets_count": len(assets_files),
                "assets_files": assets_files
            }
            
        except Exception as e:
            return {
                "assets_found": False,
                "assets_count": 0,
                "assets_files": [],
                "error": str(e)
            }
    
    async def _clean_project_artifacts(self, work_dir: str) -> Dict[str, Any]:
        """
        Limpia artefactos de compilación (obj, bin)
        
        Args:
            work_dir: Directorio de trabajo
            
        Returns:
            Resultado de la limpieza
        """
        try:
            # Ejecutar dotnet clean
            result = await self._run_dotnet_command(["clean"], cwd=work_dir)
            
            # Eliminar manualmente directorios obj y bin si existen
            artifacts_removed = []
            for root, dirs, files in os.walk(work_dir):
                for dir_name in dirs:
                    if dir_name in ["obj", "bin"]:
                        dir_path = os.path.join(root, dir_name)
                        try:
                            import shutil
                            shutil.rmtree(dir_path)
                            artifacts_removed.append(dir_path)
                        except Exception:
                            pass
            
            return {
                "success": result["success"],
                "message": "Artefactos limpiados",
                "artifacts_removed": artifacts_removed,
                "output": result["output"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error limpiando artefactos: {str(e)}"
            }
    
    async def diagnose_nuget_issues(self, project_path: str) -> Dict[str, Any]:
        """
        Diagnostica problemas comunes de NuGet en un proyecto
        
        Args:
            project_path: Ruta del proyecto a diagnosticar
            
        Returns:
            Diagnóstico completo de NuGet
        """
        try:
            project_path = os.path.normpath(os.path.abspath(project_path))
            
            # Verificar que el directorio existe
            if not os.path.exists(project_path):
                return {
                    "success": False,
                    "message": f"Directorio no encontrado: {project_path}"
                }
            
            diagnosis = {
                "project_path": project_path,
                "dotnet_info": {},
                "nuget_config": {},
                "nuget_cache": {},
                "project_assets": {},
                "nuget_sources": {},
                "recommendations": []
            }
            
            # 1. Verificar instalación de dotnet
            dotnet_check = await self.check_dotnet_installed()
            diagnosis["dotnet_info"] = dotnet_check
            
            # 2. Verificar configuración NuGet
            nuget_config = await self._ensure_nuget_config(project_path)
            diagnosis["nuget_config"] = nuget_config
            
            # 3. Verificar caché NuGet
            cache_valid = await self._validate_nuget_cache()
            diagnosis["nuget_cache"] = {
                "valid": cache_valid,
                "path": os.path.join(os.path.expanduser("~"), ".nuget", "packages")
            }
            
            # 4. Verificar archivos project.assets.json
            assets_validation = await self._validate_project_assets(project_path)
            diagnosis["project_assets"] = assets_validation
            
            # 5. Verificar fuentes NuGet
            try:
                sources_result = await self._run_dotnet_command(["nuget", "list", "source"])
                diagnosis["nuget_sources"] = {
                    "success": sources_result["success"],
                    "output": sources_result["output"],
                    "error": sources_result.get("error", "")
                }
            except Exception as e:
                diagnosis["nuget_sources"] = {
                    "success": False,
                    "error": str(e)
                }
            
            # 6. Generar recomendaciones
            recommendations = []
            
            if not dotnet_check["installed"]:
                recommendations.append("❌ .NET SDK no está instalado. Instalar .NET SDK.")
            
            if not cache_valid:
                recommendations.append("⚠️ Caché NuGet inválido. Ejecutar limpieza de caché.")
            
            if not nuget_config["cache_valid"]:
                recommendations.append("⚠️ Configuración NuGet problemática. Reconfigurar NuGet.")
            
            if not assets_validation["assets_found"]:
                recommendations.append("❌ Archivos project.assets.json no encontrados. Ejecutar restauración.")
            
            if not diagnosis["nuget_sources"]["success"]:
                recommendations.append("❌ Fuentes NuGet no configuradas. Configurar fuentes de paquetes.")
            
            if not recommendations:
                recommendations.append("✅ No se detectaron problemas obvios de NuGet.")
            
            diagnosis["recommendations"] = recommendations
            diagnosis["success"] = True
            
            return diagnosis
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error en diagnóstico: {str(e)}",
                "project_path": project_path
            }
    
    async def fix_nuget_issues(self, project_path: str) -> Dict[str, Any]:
        """
        Intenta resolver problemas comunes de NuGet automáticamente
        
        Args:
            project_path: Ruta del proyecto a reparar
            
        Returns:
            Resultado de las reparaciones
        """
        try:
            project_path = os.path.normpath(os.path.abspath(project_path))
            
            if not os.path.exists(project_path):
                return {
                    "success": False,
                    "message": f"Directorio no encontrado: {project_path}"
                }
            
            fix_results = {
                "project_path": project_path,
                "steps_executed": [],
                "success": True,
                "errors": []
            }
            
            # PASO 1: Limpiar artefactos existentes
            try:
                clean_result = await self._clean_project_artifacts(project_path)
                fix_results["steps_executed"].append({
                    "step": "clean_artifacts",
                    "success": clean_result["success"],
                    "message": clean_result["message"]
                })
            except Exception as e:
                fix_results["errors"].append(f"Error limpiando artefactos: {str(e)}")
            
            # PASO 2: Limpiar caché NuGet
            try:
                cache_result = await self._clear_nuget_cache()
                fix_results["steps_executed"].append({
                    "step": "clear_cache",
                    "success": cache_result["success"],
                    "message": cache_result["message"]
                })
            except Exception as e:
                fix_results["errors"].append(f"Error limpiando caché: {str(e)}")
            
            # PASO 3: Reconfigurar NuGet
            try:
                config_result = await self._ensure_nuget_config(project_path, force_recreate=True)
                fix_results["steps_executed"].append({
                    "step": "recreate_config",
                    "success": config_result["config_created"],
                    "message": f"Configuración NuGet recreada: {config_result['config_path']}"
                })
            except Exception as e:
                fix_results["errors"].append(f"Error configurando NuGet: {str(e)}")
            
            # PASO 4: Restaurar paquetes
            try:
                restore_result = await self.restore_packages(project_path)
                fix_results["steps_executed"].append({
                    "step": "restore_packages",
                    "success": restore_result["success"],
                    "message": restore_result["message"]
                })
            except Exception as e:
                fix_results["errors"].append(f"Error restaurando paquetes: {str(e)}")
            
            # Determinar éxito general
            fix_results["success"] = len(fix_results["errors"]) == 0
            
            return fix_results
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error en reparación automática: {str(e)}",
                "project_path": project_path
            }
