"""
Handler para operaciones de código C#
"""
import os
import re
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from services.code_analyzer import CodeAnalyzer
from services.file_manager import FileManager
from utils.exceptions import CodeAnalysisError, FileOperationError
from utils.validators import validate_class_name, validate_element_type, validate_search_type

class CodeHandler:
    """Handler para gestión y análisis de código C#"""
    
    def __init__(self):
        self.code_analyzer = CodeAnalyzer()
        self.file_manager = FileManager()
    
    async def find_class(
        self, 
        repo_url: str, 
        class_name: str, 
        search_type: str = "direct"
    ) -> Dict[str, Any]:
        """
        Localiza una clase específica en el repositorio
        
        Args:
            repo_url: URL del repositorio
            class_name: Nombre de la clase a buscar
            search_type: Tipo de búsqueda ("direct" o "deep")
            
        Returns:
            Información de la clase encontrada
        """
        try:
            # Validar parámetros
            class_name = validate_class_name(class_name)
            search_type = validate_search_type(search_type)
            
            # Obtener directorio local del repositorio
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Búsqueda directa por nombre de archivo
            if search_type == "direct":
                result = await self._direct_search(repo_path, class_name)
                if result:
                    return result
            
            # Búsqueda profunda en toda la solución
            return await self._deep_search(repo_path, class_name)
            
        except Exception as e:
            raise CodeAnalysisError(f"Error buscando clase '{class_name}': {str(e)}")
    
    async def get_file_content(self, repo_url: str, file_path: str) -> Dict[str, Any]:
        """
        Obtiene el contenido completo de un archivo
        
        Args:
            repo_url: URL del repositorio
            file_path: Ruta relativa del archivo
            
        Returns:
            Contenido del archivo y metadatos
        """
        try:
            repo_path = await self.file_manager.get_repo_path(repo_url)
            full_path = os.path.join(repo_path, file_path)
            
            if not os.path.exists(full_path):
                raise FileOperationError(f"Archivo no encontrado: {file_path}")
            
            content = await self.file_manager.read_file(full_path)
            
            # Analizar el archivo si es C#
            analysis = None
            if file_path.endswith('.cs'):
                analysis = await self.code_analyzer.analyze_file(full_path)
            
            return {
                "file_path": file_path,
                "full_path": full_path,
                "content": content,
                "size": len(content),
                "lines": len(content.splitlines()),
                "analysis": analysis,
                "encoding": "utf-8"
            }
            
        except Exception as e:
            raise FileOperationError(f"Error obteniendo contenido de '{file_path}': {str(e)}")
    
    async def find_elements(
        self, 
        repo_url: str, 
        element_type: str, 
        element_name: str
    ) -> List[Dict[str, Any]]:
        """
        Busca elementos específicos (DTOs, Services, Controllers, etc.)
        
        Args:
            repo_url: URL del repositorio
            element_type: Tipo de elemento a buscar
            element_name: Nombre del elemento
            
        Returns:
            Lista de elementos encontrados
        """
        try:
            # Validar parámetros
            element_type = validate_element_type(element_type)
            element_name = validate_class_name(element_name)
            
            repo_path = await self.file_manager.get_repo_path(repo_url)
            
            # Buscar archivos C# en el repositorio
            cs_files = await self._find_cs_files(repo_path)
            
            results = []
            for file_path in cs_files:
                try:
                    analysis = await self.code_analyzer.analyze_file(file_path)
                    matches = self._filter_elements_by_type(analysis, element_type, element_name)
                    
                    for match in matches:
                        relative_path = os.path.relpath(file_path, repo_path)
                        results.append({
                            "element_name": match["name"],
                            "element_type": match["type"],
                            "file_path": relative_path,
                            "full_path": file_path,
                            "line_number": match.get("line_number", 0),
                            "namespace": match.get("namespace"),
                            "modifiers": match.get("modifiers", []),
                            "summary": match.get("summary")
                        })
                        
                except Exception as e:
                    # Continuar con otros archivos si uno falla
                    continue
            
            return results
            
        except Exception as e:
            raise CodeAnalysisError(f"Error buscando elementos '{element_name}': {str(e)}")
    
    async def get_solution_structure(self, repo_url: str) -> Dict[str, Any]:
        """
        Obtiene la estructura completa de la solución C#
        
        Args:
            repo_url: URL del repositorio
            
        Returns:
            Estructura organizada de la solución
        """
        try:
            repo_path = await self.file_manager.get_repo_path(repo_url)
            cs_files = await self._find_cs_files(repo_path)
            
            structure = {
                "solution_path": repo_path,
                "total_cs_files": len(cs_files),
                "namespaces": {},
                "projects": {},
                "file_types": {
                    "controllers": [],
                    "services": [],
                    "models": [],
                    "dtos": [],
                    "interfaces": [],
                    "enums": [],
                    "configurations": [],
                    "others": []
                },
                "summary": {
                    "total_classes": 0,
                    "total_interfaces": 0,
                    "total_enums": 0,
                    "total_records": 0
                }
            }
            
            # Analizar cada archivo C#
            for file_path in cs_files:
                try:
                    relative_path = os.path.relpath(file_path, repo_path)
                    analysis = await self.code_analyzer.analyze_file(file_path)
                    
                    # Organizar por namespace
                    namespace = analysis.get('namespace', 'Global')
                    if namespace not in structure["namespaces"]:
                        structure["namespaces"][namespace] = []
                    
                    file_info = {
                        "path": relative_path.replace(os.sep, '/'),
                        "name": os.path.basename(file_path),
                        "namespace": namespace,
                        "elements": analysis.get('elements', []),
                        "methods_count": len(analysis.get('methods', [])),
                        "properties_count": len(analysis.get('properties', [])),
                        "lines": analysis.get('lines', 0)
                    }
                    
                    structure["namespaces"][namespace].append(file_info)
                    
                    # Categorizar por tipo de archivo
                    self._categorize_file(file_info, structure["file_types"])
                    
                    # Actualizar resumen
                    for element in analysis.get('elements', []):
                        element_type = element['type']
                        if element_type == 'class':
                            structure["summary"]['total_classes'] += 1
                        elif element_type == 'interface':
                            structure["summary"]['total_interfaces'] += 1
                        elif element_type == 'enum':
                            structure["summary"]['total_enums'] += 1
                        elif element_type == 'record':
                            structure["summary"]['total_records'] += 1
                    
                    # Detectar archivos de proyecto
                    if file_path.endswith('.csproj'):
                        project_name = os.path.splitext(os.path.basename(file_path))[0]
                        structure["projects"][project_name] = {
                            "path": relative_path.replace(os.sep, '/'),
                            "directory": os.path.dirname(relative_path).replace(os.sep, '/'),
                            "files": []
                        }
                    
                except Exception:
                    # Continuar con otros archivos si uno falla
                    continue
            
            # Asignar archivos a proyectos
            self._assign_files_to_projects(structure)
            
            return structure
            
        except Exception as e:
            raise CodeAnalysisError(f"Error obteniendo estructura de la solución: {str(e)}")
    
    def _categorize_file(self, file_info: Dict[str, Any], file_types: Dict[str, List]) -> None:
        """
        Categoriza un archivo según su tipo
        
        Args:
            file_info: Información del archivo
            file_types: Diccionario de tipos de archivo
        """
        file_name = file_info["name"].lower()
        file_path = file_info["path"].lower()
        
        # Verificar por nombre y ruta
        if "controller" in file_name or "/controllers/" in file_path:
            file_types["controllers"].append(file_info)
        elif "service" in file_name or "/services/" in file_path:
            file_types["services"].append(file_info)
        elif "dto" in file_name or "/dtos/" in file_path or "/models/dto" in file_path:
            file_types["dtos"].append(file_info)
        elif "/models/" in file_path and "dto" not in file_name:
            file_types["models"].append(file_info)
        elif file_name.startswith("i") and any(e["type"] == "interface" for e in file_info["elements"]):
            file_types["interfaces"].append(file_info)
        elif any(e["type"] == "enum" for e in file_info["elements"]):
            file_types["enums"].append(file_info)
        elif "config" in file_name or "/configuration/" in file_path:
            file_types["configurations"].append(file_info)
        else:
            file_types["others"].append(file_info)
    
    def _assign_files_to_projects(self, structure: Dict[str, Any]) -> None:
        """
        Asigna archivos a sus proyectos correspondientes
        
        Args:
            structure: Estructura de la solución
        """
        # Simplificado: asignar archivos al proyecto más cercano
        for namespace, files in structure["namespaces"].items():
            for file_info in files:
                file_path = file_info["path"]
                
                # Buscar el proyecto más específico
                best_project = None
                best_match_length = 0
                
                for project_name, project_info in structure["projects"].items():
                    project_dir = project_info["directory"]
                    
                    if file_path.startswith(project_dir) and len(project_dir) > best_match_length:
                        best_project = project_name
                        best_match_length = len(project_dir)
                
                if best_project:
                    structure["projects"][best_project]["files"].append(file_info)
                    file_info["project"] = best_project
    
    async def _direct_search(self, repo_path: str, class_name: str) -> Optional[Dict[str, Any]]:
        """
        Búsqueda directa por nombre de archivo
        
        Args:
            repo_path: Ruta del repositorio
            class_name: Nombre de la clase
            
        Returns:
            Resultado de la búsqueda o None
        """
        # Patrones de archivo a buscar
        patterns = [
            f"{class_name}.cs",
            f"I{class_name}.cs",  # Interfaces
            f"{class_name}Dto.cs",  # DTOs
            f"{class_name}Service.cs",  # Services
            f"{class_name}Controller.cs",  # Controllers
        ]
        
        for pattern in patterns:
            for root, dirs, files in os.walk(repo_path):
                # Excluir directorios comunes que no contienen código fuente
                dirs[:] = [d for d in dirs if d not in {'.git', 'bin', 'obj', 'packages', 'node_modules'}]
                
                for file in files:
                    if file.lower() == pattern.lower():
                        file_path = os.path.join(root, file)
                        
                        # Verificar si contiene la clase buscada
                        if await self._file_contains_class(file_path, class_name):
                            relative_path = os.path.relpath(file_path, repo_path)
                            analysis = await self.code_analyzer.analyze_file(file_path)
                            
                            return {
                                "class_name": class_name,
                                "file_path": relative_path,
                                "full_path": file_path,
                                "search_type": "direct",
                                "analysis": analysis
                            }
        
        return None
    
    async def _deep_search(self, repo_path: str, class_name: str) -> Dict[str, Any]:
        """
        Búsqueda profunda en toda la solución
        
        Args:
            repo_path: Ruta del repositorio
            class_name: Nombre de la clase
            
        Returns:
            Resultado de la búsqueda
        """
        cs_files = await self._find_cs_files(repo_path)
        
        for file_path in cs_files:
            if await self._file_contains_class(file_path, class_name):
                relative_path = os.path.relpath(file_path, repo_path)
                analysis = await self.code_analyzer.analyze_file(file_path)
                
                return {
                    "class_name": class_name,
                    "file_path": relative_path,
                    "full_path": file_path,
                    "search_type": "deep",
                    "analysis": analysis
                }
        
        raise CodeAnalysisError(f"Clase '{class_name}' no encontrada en el repositorio")
    
    async def _find_cs_files(self, repo_path: str) -> List[str]:
        """
        Encuentra todos los archivos .cs en el repositorio
        
        Args:
            repo_path: Ruta del repositorio
            
        Returns:
            Lista de rutas de archivos .cs
        """
        cs_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Excluir directorios irrelevantes
            dirs[:] = [d for d in dirs if d not in {'.git', 'bin', 'obj', 'packages', 'node_modules'}]
            
            for file in files:
                if file.endswith('.cs'):
                    cs_files.append(os.path.join(root, file))
        
        return cs_files
    
    async def _file_contains_class(self, file_path: str, class_name: str) -> bool:
        """
        Verifica si un archivo contiene una clase específica
        
        Args:
            file_path: Ruta del archivo
            class_name: Nombre de la clase
            
        Returns:
            True si el archivo contiene la clase
        """
        try:
            content = await self.file_manager.read_file(file_path)
            
            # Patrones para buscar definiciones de clase
            patterns = [
                rf'\bclass\s+{re.escape(class_name)}\b',
                rf'\binterface\s+{re.escape(class_name)}\b',
                rf'\brecord\s+{re.escape(class_name)}\b',
                rf'\benum\s+{re.escape(class_name)}\b',
                rf'\bstruct\s+{re.escape(class_name)}\b'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _filter_elements_by_type(
        self, 
        analysis: Dict[str, Any], 
        element_type: str, 
        element_name: str
    ) -> List[Dict[str, Any]]:
        """
        Filtra elementos por tipo y nombre
        
        Args:
            analysis: Análisis del archivo
            element_type: Tipo de elemento
            element_name: Nombre del elemento
            
        Returns:
            Lista de elementos que coinciden
        """
        if not analysis or "elements" not in analysis:
            return []
        
        matches = []
        
        for element in analysis["elements"]:
            # Verificar tipo
            if element_type == "dto" and not element["name"].lower().endswith("dto"):
                continue
            elif element_type == "service" and not element["name"].lower().endswith("service"):
                continue
            elif element_type == "controller" and not element["name"].lower().endswith("controller"):
                continue
            elif element_type == "interface" and element["type"] != "interface":
                continue
            elif element_type == "enum" and element["type"] != "enum":
                continue
            elif element_type == "class" and element["type"] not in ["class", "record"]:
                continue
            
            # Verificar nombre (búsqueda parcial)
            if element_name.lower() in element["name"].lower():
                matches.append(element)
        
        return matches