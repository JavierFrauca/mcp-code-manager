"""
Utilidades para operaciones con dotnet CLI
"""
import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

class DotNetUtils:
    """Utilidades para trabajar con dotnet CLI y proyectos C#"""
    
    # Templates disponibles comunes
    COMMON_TEMPLATES = {
        "console": "Console App",
        "classlib": "Class Library", 
        "web": "ASP.NET Core Web App",
        "webapi": "ASP.NET Core Web API",
        "mvc": "ASP.NET Core Web App (Model-View-Controller)",
        "razor": "ASP.NET Core Web App",
        "blazorserver": "Blazor Server App",
        "blazorwasm": "Blazor WebAssembly App",
        "wpf": "WPF Application",
        "winforms": "Windows Forms App",
        "worker": "Worker Service",
        "mstest": "MSTest Test Project",
        "nunit": "NUnit 3 Test Project",
        "xunit": "xUnit Test Project"
    }
    
    # Frameworks comunes
    COMMON_FRAMEWORKS = [
        "net8.0",
        "net7.0", 
        "net6.0",
        "net48",
        "net472",
        "netstandard2.1",
        "netstandard2.0"
    ]
    
    @staticmethod
    def validate_project_name(name: str) -> str:
        """
        Valida y normaliza un nombre de proyecto
        
        Args:
            name: Nombre del proyecto
            
        Returns:
            Nombre validado
            
        Raises:
            ValueError: Si el nombre no es válido
        """
        if not name:
            raise ValueError("El nombre del proyecto no puede estar vacío")
        
        # Eliminar espacios y caracteres no válidos
        name = re.sub(r'[^\w\-\.]', '', name.strip())
        
        if not name:
            raise ValueError("El nombre del proyecto debe contener al menos un carácter válido")
        
        # No puede empezar con número
        if name[0].isdigit():
            raise ValueError("El nombre del proyecto no puede empezar con un número")
        
        # Nombres reservados de Windows
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        
        if name.upper() in reserved_names:
            raise ValueError(f"'{name}' es un nombre reservado del sistema")
        
        return name
    
    @staticmethod
    def validate_template(template: str) -> str:
        """
        Valida un template de proyecto
        
        Args:
            template: Nombre del template
            
        Returns:
            Template validado
        """
        if not template:
            return "console"  # Default
        
        template = template.lower().strip()
        
        # Si es un template conocido, retornarlo
        if template in DotNetUtils.COMMON_TEMPLATES:
            return template
        
        # Si no, retornar tal como está (puede ser un template personalizado)
        return template
    
    @staticmethod
    def validate_framework(framework: str) -> Optional[str]:
        """
        Valida un target framework
        
        Args:
            framework: Framework target
            
        Returns:
            Framework validado o None si no es válido
        """
        if not framework:
            return None
        
        framework = framework.lower().strip()
        
        if framework in [f.lower() for f in DotNetUtils.COMMON_FRAMEWORKS]:
            return framework
        
        # Validar formato netX.X o netstandard2.X
        if re.match(r'^net\d+\.\d+$', framework) or re.match(r'^netstandard\d+\.\d+$', framework):
            return framework
        
        return None
    
    @staticmethod
    def parse_csproj_info(csproj_path: str) -> Dict[str, Any]:
        """
        Extrae información básica de un archivo .csproj
        
        Args:
            csproj_path: Ruta al archivo .csproj
            
        Returns:
            Información del proyecto
        """
        info = {
            "project_name": "",
            "target_framework": "",
            "output_type": "",
            "package_references": [],
            "project_references": []
        }
        
        try:
            if not os.path.exists(csproj_path):
                return info
            
            with open(csproj_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraer información básica
            info["project_name"] = os.path.splitext(os.path.basename(csproj_path))[0]
            
            # Target Framework
            framework_match = re.search(r'<TargetFramework>([^<]+)</TargetFramework>', content)
            if framework_match:
                info["target_framework"] = framework_match.group(1)
            
            # Output Type
            output_match = re.search(r'<OutputType>([^<]+)</OutputType>', content)
            if output_match:
                info["output_type"] = output_match.group(1)
            
            # Package References
            package_pattern = r'<PackageReference\s+Include="([^"]+)"\s+Version="([^"]+)"'
            package_matches = re.findall(package_pattern, content)
            info["package_references"] = [
                {"name": name, "version": version} 
                for name, version in package_matches
            ]
            
            # Project References
            project_pattern = r'<ProjectReference\s+Include="([^"]+)"'
            project_matches = re.findall(project_pattern, content)
            info["project_references"] = project_matches
            
        except Exception:
            pass  # Retornar info vacía si hay error
        
        return info
    
    @staticmethod
    def find_solution_files(directory: str) -> List[str]:
        """
        Busca archivos .sln en un directorio
        
        Args:
            directory: Directorio a buscar
            
        Returns:
            Lista de archivos .sln encontrados
        """
        solution_files = []
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.sln'):
                        solution_files.append(os.path.join(root, file))
        except Exception:
            pass
        
        return solution_files
    
    @staticmethod
    def find_project_files(directory: str) -> List[str]:
        """
        Busca archivos de proyecto C# en un directorio
        
        Args:
            directory: Directorio a buscar
            
        Returns:
            Lista de archivos de proyecto encontrados
        """
        project_files = []
        project_extensions = ['.csproj', '.fsproj', '.vbproj']
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in project_extensions):
                        project_files.append(os.path.join(root, file))
        except Exception:
            pass
        
        return project_files
    
    @staticmethod
    def parse_test_filter(filter_expression: str) -> Dict[str, Any]:
        """
        Valida y parsea una expresión de filtro para tests
        
        Args:
            filter_expression: Expresión de filtro
            
        Returns:
            Información del filtro parseado
        """
        if not filter_expression:
            return {"valid": True, "type": "all", "expression": ""}
        
        filter_info = {
            "valid": True,
            "type": "custom",
            "expression": filter_expression,
            "examples": []
        }
        
        # Detectar tipos comunes de filtros
        if "FullyQualifiedName" in filter_expression:
            filter_info["type"] = "method_name"
            filter_info["examples"] = ["FullyQualifiedName=MyProject.Tests.TestClass.TestMethod"]
        elif "TestCategory" in filter_expression:
            filter_info["type"] = "category"
            filter_info["examples"] = ["TestCategory=Unit", "TestCategory=Integration"]
        elif "Priority" in filter_expression:
            filter_info["type"] = "priority"
            filter_info["examples"] = ["Priority=1", "Priority=High"]
        elif "Name" in filter_expression:
            filter_info["type"] = "name_pattern"
            filter_info["examples"] = ["Name~Unit", "Name=SpecificTest"]
        
        return filter_info
    
    @staticmethod
    def get_common_test_filters() -> List[Dict[str, str]]:
        """
        Retorna filtros de test comunes
        
        Returns:
            Lista de filtros comunes con ejemplos
        """
        return [
            {
                "name": "Todos los tests",
                "filter": "",
                "description": "Ejecuta todos los tests disponibles"
            },
            {
                "name": "Tests unitarios",
                "filter": "TestCategory=Unit",
                "description": "Solo tests marcados como Unit"
            },
            {
                "name": "Tests de integración",
                "filter": "TestCategory=Integration",
                "description": "Solo tests marcados como Integration"
            },
            {
                "name": "Tests por prioridad alta",
                "filter": "Priority=1",
                "description": "Tests con prioridad 1 (alta)"
            },
            {
                "name": "Tests por nombre",
                "filter": "Name~Calculator",
                "description": "Tests que contengan 'Calculator' en el nombre"
            },
            {
                "name": "Clase específica",
                "filter": "FullyQualifiedName~MyProject.Tests.CalculatorTests",
                "description": "Todos los tests de una clase específica"
            },
            {
                "name": "Método específico",
                "filter": "FullyQualifiedName=MyProject.Tests.CalculatorTests.AddTest",
                "description": "Un test específico"
            }
        ]
    
    @staticmethod
    def format_build_output(output: str) -> str:
        """
        Formatea la salida de build para mejor legibilidad
        
        Args:
            output: Salida cruda del build
            
        Returns:
            Salida formateada
        """
        if not output:
            return ""
        
        lines = output.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Resaltar errores
            if 'error CS' in line.lower():
                formatted_lines.append(f"❌ {line}")
            # Resaltar warnings
            elif 'warning CS' in line.lower():
                formatted_lines.append(f"⚠️ {line}")
            # Resaltar éxito
            elif 'Build succeeded' in line:
                formatted_lines.append(f"✅ {line}")
            # Resaltar fallo
            elif 'Build FAILED' in line:
                formatted_lines.append(f"❌ {line}")
            else:
                formatted_lines.append(f"   {line}")
        
        return '\n'.join(formatted_lines)
    
    @staticmethod
    def format_test_output(output: str) -> str:
        """
        Formatea la salida de tests para mejor legibilidad
        
        Args:
            output: Salida cruda de los tests
            
        Returns:
            Salida formateada
        """
        if not output:
            return ""
        
        lines = output.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Resaltar resultados de tests
            if 'Passed!' in line or 'Passed:' in line:
                formatted_lines.append(f"✅ {line}")
            elif 'Failed!' in line or 'Failed:' in line:
                formatted_lines.append(f"❌ {line}")
            elif 'Skipped:' in line:
                formatted_lines.append(f"⏭️ {line}")
            elif 'Total tests:' in line:
                formatted_lines.append(f"📊 {line}")
            elif line.startswith('Test run for'):
                formatted_lines.append(f"🔍 {line}")
            else:
                formatted_lines.append(f"   {line}")
        
        return '\n'.join(formatted_lines)
