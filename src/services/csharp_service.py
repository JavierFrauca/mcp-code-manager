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
        Compila una solución C#
        
        Args:
            solution_path: Directorio de la solución o archivo .sln
            configuration: Configuración (Debug/Release)
            
        Returns:
            Resultado de la compilación
        """
        try:
            # Ejecutar dotnet build
            result = await self._run_dotnet_command(
                ["build", "--configuration", configuration, "--verbosity", "normal"],
                cwd=solution_path
            )
            
            # Analizar errores y warnings
            build_analysis = self._analyze_build_output(result.get("output", ""), result.get("error", ""))
            
            return {
                "success": result["success"],
                "message": "Compilación completada" if result["success"] else "Compilación falló",
                "output": result["output"],
                "error": result.get("error", ""),
                "configuration": configuration,
                "analysis": build_analysis
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
        Agrega un paquete NuGet a un proyecto
        
        Args:
            project_file: Ruta al archivo .csproj
            package_name: Nombre del paquete
            version: Versión específica (opcional)
            
        Returns:
            Resultado de la operación
        """
        try:
            if not os.path.exists(project_file):
                raise CodeAnalysisError(f"Archivo de proyecto no encontrado: {project_file}")
            
            # Construir comando
            cmd = ["add", project_file, "package", package_name]
            if version:
                cmd.extend(["--version", version])
            
            # Ejecutar comando
            result = await self._run_dotnet_command(cmd)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Paquete {package_name} agregado exitosamente",
                    "package": package_name,
                    "version": version,
                    "output": result["output"]
                }
            else:
                raise CodeAnalysisError(f"Error agregando paquete: {result['error']}")
                
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
        Restaura paquetes NuGet de un proyecto/solución
        
        Args:
            project_path: Directorio del proyecto/solución
            
        Returns:
            Resultado de la operación
        """
        try:
            result = await self._run_dotnet_command(["restore"], cwd=project_path)
            
            return {
                "success": result["success"],
                "message": "Restauración de paquetes completada" if result["success"] else "Error en restauración",
                "output": result["output"],
                "error": result.get("error", "")
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
            cmd = ["dotnet"] + args
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
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
                "command": " ".join(cmd)
            }
            
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
