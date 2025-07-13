"""
Handler para operaciones de testing y gestión de proyectos C#
"""
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

from services.csharp_service import CSharpService
from services.file_manager import FileManager
from utils.exceptions import CodeAnalysisError, FileOperationError
from utils.dotnet_utils import DotNetUtils

class CSharpTestHandler:
    """Handler para gestión de proyectos C# y ejecución de tests"""
    
    def __init__(self):
        self.csharp_service = CSharpService()
        self.file_manager = FileManager()
        self.dotnet_utils = DotNetUtils()
    
    # === Gestión de Soluciones ===
    
    async def create_solution(self, repo_url: str, solution_name: str, base_path: str = "") -> Dict[str, Any]:
        """
        Crea una nueva solución C#
        
        Args:
            repo_url: URL del repositorio (para obtener el directorio base)
            solution_name: Nombre de la solución
            base_path: Subdirectorio dentro del repo (opcional)
            
        Returns:
            Información de la solución creada
        """
        try:
            # Validar nombre de solución
            solution_name = self.dotnet_utils.validate_project_name(solution_name)
            
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta completa
            if base_path:
                solution_path = os.path.join(repo_path, base_path)
            else:
                solution_path = repo_path
            
            # Crear solución
            result = await self.csharp_service.create_solution(solution_path, solution_name)
            
            return {
                "success": True,
                "message": result["message"],
                "solution_name": solution_name,
                "solution_file": result["solution_file"],
                "solution_path": solution_path,
                "output": result["output"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error creando solución: {str(e)}")
    
    async def add_project_to_solution(self, repo_url: str, solution_file: str, project_file: str) -> Dict[str, Any]:
        """
        Agrega un proyecto a una solución existente
        
        Args:
            repo_url: URL del repositorio
            solution_file: Ruta relativa al archivo .sln
            project_file: Ruta relativa al archivo .csproj
            
        Returns:
            Resultado de la operación
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir rutas absolutas
            full_solution_path = os.path.join(repo_path, solution_file)
            full_project_path = os.path.join(repo_path, project_file)
            
            # Agregar proyecto a solución
            result = await self.csharp_service.add_project_to_solution(full_solution_path, full_project_path)
            
            return {
                "success": True,
                "message": result["message"],
                "solution_file": solution_file,
                "project_file": project_file,
                "output": result["output"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error agregando proyecto a solución: {str(e)}")
    
    async def list_solution_projects(self, repo_url: str, solution_file: str) -> Dict[str, Any]:
        """
        Lista los proyectos en una solución
        
        Args:
            repo_url: URL del repositorio
            solution_file: Ruta relativa al archivo .sln
            
        Returns:
            Lista de proyectos en la solución
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta absoluta
            full_solution_path = os.path.join(repo_path, solution_file)
            
            # Listar proyectos
            result = await self.csharp_service.list_projects_in_solution(full_solution_path)
            
            # Agregar información adicional de cada proyecto
            enhanced_projects = []
            for project in result["projects"]:
                project_info = self.dotnet_utils.parse_csproj_info(
                    os.path.join(repo_path, project["path"])
                )
                enhanced_projects.append({
                    **project,
                    "info": project_info
                })
            
            return {
                "success": True,
                "solution_file": solution_file,
                "total_projects": result["total_projects"],
                "projects": enhanced_projects,
                "output": result["output"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error listando proyectos: {str(e)}")
    
    # === Gestión de Proyectos ===
    
    async def create_project(self, repo_url: str, project_name: str, template: str = "console", 
                           base_path: str = "", framework: str = None) -> Dict[str, Any]:
        """
        Crea un nuevo proyecto C#
        
        Args:
            repo_url: URL del repositorio
            project_name: Nombre del proyecto
            template: Tipo de proyecto (console, classlib, web, etc.)
            base_path: Subdirectorio donde crear el proyecto
            framework: Target framework (opcional)
            
        Returns:
            Información del proyecto creado
        """
        try:
            # Validar parámetros
            project_name = self.dotnet_utils.validate_project_name(project_name)
            template = self.dotnet_utils.validate_template(template)
            
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta del proyecto
            if base_path:
                project_path = os.path.join(repo_path, base_path)
            else:
                project_path = repo_path
            
            # Crear proyecto
            result = await self.csharp_service.create_project(project_path, project_name, template)
            
            # Si se especifica framework, modificar el .csproj
            if framework:
                validated_framework = self.dotnet_utils.validate_framework(framework)
                if validated_framework:
                    await self._update_project_framework(result["project_file"], validated_framework)
            
            # Obtener información del proyecto creado
            project_info = self.dotnet_utils.parse_csproj_info(result["project_file"])
            
            return {
                "success": True,
                "message": result["message"],
                "project_name": project_name,
                "project_file": result["project_file"],
                "template": template,
                "framework": framework,
                "project_info": project_info,
                "output": result["output"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error creando proyecto: {str(e)}")
    
    async def add_package_to_project(self, repo_url: str, project_file: str, package_name: str, 
                                   version: str = None) -> Dict[str, Any]:
        """
        Agrega un paquete NuGet a un proyecto
        
        Args:
            repo_url: URL del repositorio
            project_file: Ruta relativa al archivo .csproj
            package_name: Nombre del paquete
            version: Versión específica (opcional)
            
        Returns:
            Resultado de la operación
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta absoluta
            full_project_path = os.path.join(repo_path, project_file)
            
            # Agregar paquete
            result = await self.csharp_service.add_package(full_project_path, package_name, version)
            
            return {
                "success": True,
                "message": result["message"],
                "project_file": project_file,
                "package": package_name,
                "version": version or "latest",
                "output": result["output"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error agregando paquete: {str(e)}")
    
    # === Compilación ===
    
    async def build_solution(self, repo_url: str, solution_file: str = None, 
                           configuration: str = "Debug") -> Dict[str, Any]:
        """
        Compila una solución o directorio completo
        
        Args:
            repo_url: URL del repositorio
            solution_file: Archivo .sln específico (opcional)
            configuration: Configuración (Debug/Release)
            
        Returns:
            Resultado de la compilación
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Determinar qué compilar
            if solution_file:
                build_path = os.path.join(repo_path, solution_file)
            else:
                build_path = repo_path
            
            # Compilar
            result = await self.csharp_service.build_solution(build_path, configuration)
            
            # Formatear salida
            formatted_output = self.dotnet_utils.format_build_output(result["output"])
            
            return {
                "success": result["success"],
                "message": result["message"],
                "configuration": configuration,
                "solution_file": solution_file or "(directorio completo)",
                "output": formatted_output,
                "raw_output": result["output"],
                "analysis": result["analysis"],
                "has_errors": result["analysis"]["has_errors"],
                "has_warnings": result["analysis"]["has_warnings"],
                "error_count": result["analysis"]["error_count"],
                "warning_count": result["analysis"]["warning_count"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error compilando: {str(e)}")
    
    async def build_project(self, repo_url: str, project_file: str, 
                          configuration: str = "Debug") -> Dict[str, Any]:
        """
        Compila un proyecto específico
        
        Args:
            repo_url: URL del repositorio
            project_file: Ruta relativa al archivo .csproj
            configuration: Configuración (Debug/Release)
            
        Returns:
            Resultado de la compilación
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta absoluta
            full_project_path = os.path.join(repo_path, project_file)
            
            # Compilar proyecto específico
            result = await self.csharp_service.build_solution(full_project_path, configuration)
            
            # Formatear salida
            formatted_output = self.dotnet_utils.format_build_output(result["output"])
            
            return {
                "success": result["success"],
                "message": result["message"],
                "configuration": configuration,
                "project_file": project_file,
                "output": formatted_output,
                "raw_output": result["output"],
                "analysis": result["analysis"],
                "has_errors": result["analysis"]["has_errors"],
                "has_warnings": result["analysis"]["has_warnings"],
                "error_count": result["analysis"]["error_count"],
                "warning_count": result["analysis"]["warning_count"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error compilando proyecto: {str(e)}")
    
    # === Testing ===
    
    async def run_all_tests(self, repo_url: str, test_path: str = "", 
                          collect_coverage: bool = False) -> Dict[str, Any]:
        """
        Ejecuta todos los tests en una solución o proyecto
        
        Args:
            repo_url: URL del repositorio
            test_path: Subdirectorio específico con tests (opcional)
            collect_coverage: Si recopilar coverage
            
        Returns:
            Resultados de los tests
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta de tests
            if test_path:
                full_test_path = os.path.join(repo_path, test_path)
            else:
                full_test_path = repo_path
            
            # Ejecutar tests
            result = await self.csharp_service.run_tests(full_test_path, None, collect_coverage)
            
            # Formatear salida
            formatted_output = self.dotnet_utils.format_test_output(result["output"])
            
            return {
                "success": result["success"],
                "message": result["message"],
                "test_path": test_path or "(directorio completo)",
                "coverage": collect_coverage,
                "output": formatted_output,
                "raw_output": result["output"],
                "analysis": result["analysis"],
                "test_summary": result["analysis"]["summary"],
                "failed_tests": result["analysis"]["failed_tests"],
                "success_rate": result["analysis"]["success_rate"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error ejecutando tests: {str(e)}")
    
    async def run_filtered_tests(self, repo_url: str, filter_expression: str, 
                               test_path: str = "", collect_coverage: bool = False) -> Dict[str, Any]:
        """
        Ejecuta tests con filtro específico
        
        Args:
            repo_url: URL del repositorio
            filter_expression: Expresión de filtro para tests
            test_path: Subdirectorio específico con tests (opcional)
            collect_coverage: Si recopilar coverage
            
        Returns:
            Resultados de los tests filtrados
        """
        try:
            # Validar filtro
            filter_info = self.dotnet_utils.parse_test_filter(filter_expression)
            if not filter_info["valid"]:
                raise CodeAnalysisError(f"Expresión de filtro inválida: {filter_expression}")
            
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta de tests
            if test_path:
                full_test_path = os.path.join(repo_path, test_path)
            else:
                full_test_path = repo_path
            
            # Ejecutar tests con filtro
            result = await self.csharp_service.run_tests(full_test_path, filter_expression, collect_coverage)
            
            # Formatear salida
            formatted_output = self.dotnet_utils.format_test_output(result["output"])
            
            return {
                "success": result["success"],
                "message": result["message"],
                "filter": filter_expression,
                "filter_info": filter_info,
                "test_path": test_path or "(directorio completo)",
                "coverage": collect_coverage,
                "output": formatted_output,
                "raw_output": result["output"],
                "analysis": result["analysis"],
                "test_summary": result["analysis"]["summary"],
                "failed_tests": result["analysis"]["failed_tests"],
                "success_rate": result["analysis"]["success_rate"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error ejecutando tests filtrados: {str(e)}")
    
    # === Información y Utilidades ===
    
    async def check_dotnet_environment(self, repo_url: str = None) -> Dict[str, Any]:
        """
        Verifica el entorno dotnet disponible
        
        Args:
            repo_url: URL del repositorio (opcional, para contexto)
            
        Returns:
            Información del entorno dotnet
        """
        try:
            # Verificar dotnet
            dotnet_info = await self.csharp_service.check_dotnet_installed()
            
            # Si hay repo, buscar proyectos existentes
            projects_info = {}
            if repo_url:
                try:
                    repo_path = await self.file_manager.get_repo_path(repo_url)
                    
                    # Buscar archivos de solución y proyecto
                    solution_files = self.dotnet_utils.find_solution_files(repo_path)
                    project_files = self.dotnet_utils.find_project_files(repo_path)
                    
                    projects_info = {
                        "solution_files": solution_files,
                        "project_files": project_files,
                        "total_solutions": len(solution_files),
                        "total_projects": len(project_files)
                    }
                except Exception:
                    projects_info = {"error": "No se pudo analizar el repositorio"}
            
            return {
                "dotnet": dotnet_info,
                "projects": projects_info,
                "common_templates": self.dotnet_utils.COMMON_TEMPLATES,
                "common_frameworks": self.dotnet_utils.COMMON_FRAMEWORKS
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error verificando entorno: {str(e)}")
    
    async def get_common_test_filters(self) -> Dict[str, Any]:
        """
        Obtiene filtros de test comunes con ejemplos
        
        Returns:
            Lista de filtros comunes
        """
        try:
            common_filters = self.dotnet_utils.get_common_test_filters()
            
            return {
                "filters": common_filters,
                "total": len(common_filters),
                "usage_examples": [
                    "Usar filtros para ejecutar solo tests unitarios",
                    "Combinar filtros: TestCategory=Unit&Priority=1",
                    "Usar comodines: Name~Calculator*",
                    "Filtros por namespace: FullyQualifiedName~MyProject.Tests.*"
                ]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error obteniendo filtros: {str(e)}")
    
    async def restore_packages(self, repo_url: str, project_path: str = "") -> Dict[str, Any]:
        """
        Restaura paquetes NuGet de un proyecto o solución
        
        Args:
            repo_url: URL del repositorio
            project_path: Subdirectorio específico (opcional)
            
        Returns:
            Resultado de la restauración
        """
        try:
            # Obtener directorio del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Construir ruta de restauración
            if project_path:
                full_project_path = os.path.join(repo_path, project_path)
            else:
                full_project_path = repo_path
            
            # Restaurar paquetes
            result = await self.csharp_service.restore_packages(full_project_path)
            
            return {
                "success": result["success"],
                "message": result["message"],
                "project_path": project_path or "(directorio completo)",
                "output": result["output"]
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error restaurando paquetes: {str(e)}")
    
    # === Métodos auxiliares ===
    
    async def _update_project_framework(self, project_file: str, framework: str):
        """
        Actualiza el target framework de un proyecto
        
        Args:
            project_file: Ruta al archivo .csproj
            framework: Nuevo target framework
        """
        try:
            if not os.path.exists(project_file):
                return
            
            with open(project_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Reemplazar o agregar TargetFramework
            import re
            if '<TargetFramework>' in content:
                content = re.sub(
                    r'<TargetFramework>[^<]+</TargetFramework>',
                    f'<TargetFramework>{framework}</TargetFramework>',
                    content
                )
            else:
                # Agregar después de <PropertyGroup>
                content = content.replace(
                    '<PropertyGroup>',
                    f'<PropertyGroup>\n    <TargetFramework>{framework}</TargetFramework>'
                )
            
            with open(project_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception:
            pass  # Ignorar errores al modificar framework
