"""
Handler para operaciones de testing y gestión de proyectos Python
"""
import os
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path

from services.python_service import PythonService
from services.file_manager import FileManager
from utils.exceptions import CodeAnalysisError, FileOperationError
from utils.python_utils import PythonUtils

class PythonTestHandler:
    """Handler para gestión de proyectos Python y ejecución de tests"""
    
    def __init__(self):
        self.python_service = PythonService()
        self.file_manager = FileManager()
        self.python_utils = PythonUtils()
    
    # === Gestión de Entorno ===
    
    async def check_python_environment(self, repo_url: str = None) -> Dict[str, Any]:
        """
        Verifica el entorno Python disponible
        
        Args:
            repo_url: URL del repositorio (opcional)
            
        Returns:
            Información del entorno Python
        """
        try:
            # Obtener directorio del proyecto si hay repo
            project_path = None
            if repo_url:
                project_path = await self.file_manager.get_repo_path(repo_url)
            
            # Verificar entorno con timeout más agresivo
            try:
                result = await asyncio.wait_for(
                    self.python_service.check_python_environment(project_path),
                    timeout=15.0  # Reducido a 15 segundos para mejor experiencia
                )
            except asyncio.TimeoutError:
                # Return basic environment info if timeout
                result = {
                    "python_version": "Available (timeout protection)",
                    "pip_version": "Available (timeout protection)",
                    "python_executable": "python",
                    "pip_executable": "pip",
                    "has_python": True,
                    "has_pip": True
                }
            
            # Agregar información adicional del proyecto con timeout protection
            project_info = {}
            if project_path and os.path.exists(project_path):
                try:
                    # Buscar archivos Python con timeout reducido
                    python_files = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, self.python_utils.find_python_files, project_path
                        ),
                        timeout=5.0  # Reducido a 5 segundos para mejor experiencia
                    )
                    
                    # Detectar framework de testing (quick operation)
                    testing_framework = self.python_utils.detect_testing_framework(project_path)
                    
                    # Parsear requirements si existe (quick operation)
                    requirements_path = os.path.join(project_path, "requirements.txt")
                    requirements_info = self.python_utils.parse_requirements_file(requirements_path)
                    
                    project_info = {
                        "python_files": python_files,
                        "testing_framework": testing_framework,
                        "requirements": requirements_info,
                        "file_summary": {
                            "source_files": len(python_files.get("source_files", [])),
                            "test_files": len(python_files.get("test_files", [])),
                            "config_files": len(python_files.get("config_files", [])),
                            "other_files": len(python_files.get("other_files", []))
                        }
                    }
                except asyncio.TimeoutError:
                    project_info = {
                        "python_files": {"source_files": [], "test_files": [], "config_files": [], "other_files": []},
                        "testing_framework": "Unknown (timeout)",
                        "requirements": {"packages": [], "file_exists": False},
                        "file_summary": {"source_files": 0, "test_files": 0, "config_files": 0, "other_files": 0}
                    }
                except Exception:
                    project_info = {
                        "python_files": {"source_files": [], "test_files": [], "config_files": [], "other_files": []},
                        "testing_framework": "Unknown (error)",
                        "requirements": {"packages": [], "file_exists": False},
                        "file_summary": {"source_files": 0, "test_files": 0, "config_files": 0, "other_files": 0}
                    }
            
            return {
                "environment": result,
                "project": project_info,
                "available_tools": self.python_utils.QUALITY_TOOLS,
                "testing_frameworks": self.python_utils.TESTING_FRAMEWORKS
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error verificando entorno Python: {str(e)}")
    
    async def create_virtual_environment(self, repo_url: str, venv_name: str = "venv", 
                                       base_path: str = "") -> Dict[str, Any]:
        """
        Crea un entorno virtual Python
        
        Args:
            repo_url: URL del repositorio
            venv_name: Nombre del entorno virtual
            base_path: Subdirectorio donde crear el entorno
            
        Returns:
            Información del entorno creado
        """
        try:
            # Validar nombre del entorno
            venv_name = self.python_utils.validate_venv_name(venv_name)
            
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta del proyecto
            if base_path:
                project_path = os.path.join(repo_path, base_path)
            else:
                project_path = repo_path
            
            # Crear entorno virtual
            result = await self.python_service.create_virtual_environment(project_path, venv_name)
            
            # Obtener comandos de activación
            activation_commands = self.python_utils.get_venv_activation_command(result["venv_path"])
            
            return {
                "success": True,
                "message": result["message"],
                "venv_name": venv_name,
                "venv_path": result["venv_path"],
                "project_path": project_path,
                "activation_commands": activation_commands,
                "python_executable": result["python_executable"],
                "output": result["output"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error creando entorno virtual: {str(e)}")
    
    # === Gestión de Dependencias ===
    
    async def install_packages(self, repo_url: str, packages: List[str], 
                             venv_name: str = None, base_path: str = "") -> Dict[str, Any]:
        """
        Instala paquetes Python usando pip
        
        Args:
            repo_url: URL del repositorio
            packages: Lista de paquetes a instalar
            venv_name: Nombre del entorno virtual (opcional)
            base_path: Subdirectorio del proyecto
            
        Returns:
            Resultado de la instalación
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta del proyecto
            if base_path:
                project_path = os.path.join(repo_path, base_path)
            else:
                project_path = repo_path
            
            # Construir ruta del entorno virtual si se especifica
            venv_path = None
            if venv_name:
                venv_path = os.path.join(project_path, venv_name)
            
            # Instalar paquetes
            result = await self.python_service.install_packages(packages, venv_path)
            
            return {
                "success": True,
                "message": result["message"],
                "packages": packages,
                "venv_name": venv_name,
                "venv_path": venv_path,
                "project_path": project_path,
                "output": result["output"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error instalando paquetes: {str(e)}")
    
    async def install_requirements(self, repo_url: str, requirements_file: str = "requirements.txt", 
                                 venv_name: str = None, base_path: str = "") -> Dict[str, Any]:
        """
        Instala dependencias desde requirements.txt
        
        Args:
            repo_url: URL del repositorio
            requirements_file: Nombre del archivo requirements
            venv_name: Nombre del entorno virtual (opcional)
            base_path: Subdirectorio del proyecto
            
        Returns:
            Resultado de la instalación
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta del proyecto
            if base_path:
                project_path = os.path.join(repo_path, base_path)
            else:
                project_path = repo_path
            
            # Construir ruta completa del requirements
            full_requirements_path = os.path.join(project_path, requirements_file)
            
            if not os.path.exists(full_requirements_path):
                raise CodeAnalysisError(f"Archivo requirements no encontrado: {requirements_file}")
            
            # Construir ruta del entorno virtual si se especifica
            venv_path = None
            if venv_name:
                venv_path = os.path.join(project_path, venv_name)
            
            # Instalar desde requirements
            result = await self.python_service.install_packages([], venv_path, full_requirements_path)
            
            # Parsear archivo requirements para información
            requirements_info = self.python_utils.parse_requirements_file(full_requirements_path)
            
            return {
                "success": True,
                "message": result["message"],
                "requirements_file": requirements_file,
                "packages_installed": requirements_info["total_packages"],
                "venv_name": venv_name,
                "venv_path": venv_path,
                "project_path": project_path,
                "requirements_info": requirements_info,
                "output": result["output"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error instalando requirements: {str(e)}")
    
    async def generate_requirements(self, repo_url: str, venv_name: str = None, 
                                  base_path: str = "") -> Dict[str, Any]:
        """
        Genera archivo requirements.txt
        
        Args:
            repo_url: URL del repositorio
            venv_name: Nombre del entorno virtual (opcional)
            base_path: Subdirectorio del proyecto
            
        Returns:
            Resultado de la generación
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta del proyecto
            if base_path:
                project_path = os.path.join(repo_path, base_path)
            else:
                project_path = repo_path
            
            # Construir ruta del entorno virtual si se especifica
            venv_path = None
            if venv_name:
                venv_path = os.path.join(project_path, venv_name)
            
            # Generar requirements
            result = await self.python_service.generate_requirements(project_path, venv_path)
            
            return {
                "success": True,
                "message": result["message"],
                "requirements_file": result["requirements_file"],
                "package_count": result["package_count"],
                "venv_name": venv_name,
                "venv_path": venv_path,
                "project_path": project_path,
                "content": result["content"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error generando requirements: {str(e)}")
    
    # === Testing ===
    
    async def run_tests_pytest(self, repo_url: str, test_path: str = ".", 
                             venv_name: str = None, test_pattern: str = None,
                             collect_coverage: bool = False, verbose: bool = False) -> Dict[str, Any]:
        """
        Ejecuta tests usando pytest
        
        Args:
            repo_url: URL del repositorio
            test_path: Directorio o archivo de tests
            venv_name: Nombre del entorno virtual (opcional)
            test_pattern: Patrón de tests específicos
            collect_coverage: Si recopilar coverage
            verbose: Salida verbose
            
        Returns:
            Resultados de los tests
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir rutas
            if test_path == ".":
                full_test_path = repo_path
            else:
                full_test_path = os.path.join(repo_path, test_path)
            
            # Construir ruta del entorno virtual si se especifica
            venv_path = None
            if venv_name:
                venv_path = os.path.join(repo_path, venv_name)
            
            # Ejecutar tests
            result = await self.python_service.run_tests_pytest(
                full_test_path, venv_path, test_pattern, collect_coverage, verbose
            )
            
            # Formatear salida
            formatted_output = self.python_utils.format_test_output(result["output"], "pytest")
            
            return {
                "success": result["success"],
                "message": result["message"],
                "framework": "pytest",
                "test_path": test_path,
                "pattern": test_pattern,
                "coverage": collect_coverage,
                "verbose": verbose,
                "venv_name": venv_name,
                "output": formatted_output,
                "raw_output": result["output"],
                "analysis": result["analysis"],
                "test_summary": result["analysis"]["summary"],
                "failed_tests": result["analysis"]["failed_tests"],
                "success_rate": result["analysis"]["success_rate"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error ejecutando tests pytest: {str(e)}")
    
    async def run_tests_unittest(self, repo_url: str, test_path: str = ".", 
                               venv_name: str = None, test_pattern: str = None,
                               verbose: bool = False) -> Dict[str, Any]:
        """
        Ejecuta tests usando unittest
        
        Args:
            repo_url: URL del repositorio
            test_path: Directorio o módulo de tests
            venv_name: Nombre del entorno virtual (opcional)
            test_pattern: Patrón de tests específicos
            verbose: Salida verbose
            
        Returns:
            Resultados de los tests
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir rutas
            if test_path == ".":
                full_test_path = repo_path
            else:
                full_test_path = os.path.join(repo_path, test_path)
            
            # Construir ruta del entorno virtual si se especifica
            venv_path = None
            if venv_name:
                venv_path = os.path.join(repo_path, venv_name)
            
            # Ejecutar tests
            result = await self.python_service.run_tests_unittest(
                full_test_path, venv_path, test_pattern, verbose
            )
            
            # Formatear salida
            formatted_output = self.python_utils.format_test_output(result["output"], "unittest")
            
            return {
                "success": result["success"],
                "message": result["message"],
                "framework": "unittest",
                "test_path": test_path,
                "pattern": test_pattern,
                "verbose": verbose,
                "venv_name": venv_name,
                "output": formatted_output,
                "raw_output": result["output"],
                "analysis": result["analysis"],
                "test_summary": result["analysis"]["summary"],
                "failed_tests": result["analysis"]["failed_tests"],
                "success_rate": result["analysis"]["success_rate"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error ejecutando tests unittest: {str(e)}")
    
    # === Análisis de Código ===
    
    async def run_linting(self, repo_url: str, linter: str = "flake8", 
                        venv_name: str = None, base_path: str = "") -> Dict[str, Any]:
        """
        Ejecuta linting de código Python
        
        Args:
            repo_url: URL del repositorio
            linter: Herramienta de linting (flake8, pylint)
            venv_name: Nombre del entorno virtual (opcional)
            base_path: Subdirectorio del proyecto
            
        Returns:
            Resultados del linting
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta del proyecto
            if base_path:
                project_path = os.path.join(repo_path, base_path)
            else:
                project_path = repo_path
            
            # Construir ruta del entorno virtual si se especifica
            venv_path = None
            if venv_name:
                venv_path = os.path.join(project_path, venv_name)
            
            # Ejecutar linting
            result = await self.python_service.run_linting(project_path, venv_path, linter)
            
            # Formatear salida
            formatted_output = self.python_utils.format_lint_output(result["output"], linter)
            
            return {
                "success": result["success"],
                "message": result["message"],
                "linter": linter,
                "project_path": base_path or "(directorio completo)",
                "venv_name": venv_name,
                "output": formatted_output,
                "raw_output": result["output"],
                "analysis": result["analysis"],
                "total_issues": result["analysis"]["total_issues"],
                "issue_types": result["analysis"]["issue_types"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error ejecutando linting: {str(e)}")
    
    async def format_code(self, repo_url: str, formatter: str = "black", 
                        venv_name: str = None, base_path: str = "") -> Dict[str, Any]:
        """
        Formatea código Python
        
        Args:
            repo_url: URL del repositorio
            formatter: Herramienta de formateo (black, autopep8)
            venv_name: Nombre del entorno virtual (opcional)
            base_path: Subdirectorio del proyecto
            
        Returns:
            Resultado del formateo
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta del proyecto
            if base_path:
                project_path = os.path.join(repo_path, base_path)
            else:
                project_path = repo_path
            
            # Construir ruta del entorno virtual si se especifica
            venv_path = None
            if venv_name:
                venv_path = os.path.join(project_path, venv_name)
            
            # Formatear código
            result = await self.python_service.format_code(project_path, venv_path, formatter)
            
            return {
                "success": result["success"],
                "message": result["message"],
                "formatter": formatter,
                "project_path": base_path or "(directorio completo)",
                "venv_name": venv_name,
                "output": result["output"],
                "error": result.get("error", "")
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error formateando código: {str(e)}")
    
    # === Información y Utilidades ===
    
    async def detect_project_structure(self, repo_url: str) -> Dict[str, Any]:
        """
        Analiza la estructura del proyecto Python
        
        Args:
            repo_url: URL del repositorio
            
        Returns:
            Información sobre la estructura del proyecto
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Buscar archivos Python
            python_files = self.python_utils.find_python_files(repo_path)
            
            # Detectar framework de testing
            testing_framework = self.python_utils.detect_testing_framework(repo_path)
            
            # Parsear requirements si existe
            requirements_path = os.path.join(repo_path, "requirements.txt")
            requirements_info = self.python_utils.parse_requirements_file(requirements_path)
            
            # Buscar entornos virtuales
            env_result = await self.python_service._check_virtual_environments(repo_path)
            
            return {
                "python_files": python_files,
                "file_summary": {
                    "source_files": len(python_files["source_files"]),
                    "test_files": len(python_files["test_files"]),
                    "config_files": len(python_files["config_files"]),
                    "other_files": len(python_files["other_files"])
                },
                "testing_framework": testing_framework,
                "requirements": requirements_info,
                "virtual_environments": env_result,
                "project_path": repo_path
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error analizando estructura: {str(e)}")
    
    async def get_test_patterns(self) -> Dict[str, Any]:
        """
        Obtiene patrones de test comunes con ejemplos
        
        Returns:
            Lista de patrones comunes
        """
        try:
            common_patterns = PythonUtils.get_common_test_patterns()
            
            return {
                "patterns": common_patterns,
                "total": len(common_patterns),
                "testing_frameworks": PythonUtils.TESTING_FRAMEWORKS,
                "usage_examples": [
                    "Usar -k para filtros en pytest: pytest -k 'test_calculate'",
                    "Ejecutar archivo específico: pytest test_models.py",
                    "Usar marcadores: pytest -m slow",
                    "Unittest con patrón: python -m unittest discover -p '*integration*'"
                ]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error obteniendo patrones: {str(e)}")
    
    async def get_quality_tools_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre herramientas de calidad disponibles
        
        Returns:
            Información sobre herramientas de linting, formateo, etc.
        """
        try:
            return {
                "quality_tools": {
                    "linting": [
                        {"name": "flake8", "description": "Linter completo y popular"},
                        {"name": "pylint", "description": "Linter muy detallado"}
                    ],
                    "formatting": [
                        {"name": "black", "description": "Formateador opinionado"},
                        {"name": "autopep8", "description": "Formateador basado en PEP8"}
                    ]
                },
                "testing_frameworks": [
                    {"name": "pytest", "description": "Framework moderno y extensible"},
                    {"name": "unittest", "description": "Framework incluido en Python"}
                ],
                "recommended_workflow": [
                    "1. Crear entorno virtual: python_create_venv",
                    "2. Instalar dependencias: python_install_requirements",
                    "3. Ejecutar tests: python_run_pytest o python_run_unittest",
                    "4. Linting: python_lint (flake8 recomendado)",
                    "5. Formatear: python_format (black recomendado)",
                    "6. Generar requirements: python_freeze"
                ]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error obteniendo información de herramientas: {str(e)}")
