"""
Servicio para análisis de código C#
"""
import re
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

from utils.exceptions import CodeAnalysisError

class CodeAnalyzer:
    """Analizador de código C# para extraer información estructural"""
    
    def __init__(self):
        # Patrones regex para elementos C#
        self.patterns = {
            'namespace': r'namespace\s+([A-Za-z_][\w\.]*)',
            'using': r'using\s+([A-Za-z_][\w\.]*);',
            'class': r'(?:public|private|protected|internal)?\s*(?:static|abstract|sealed)?\s*class\s+([A-Za-z_]\w*)',
            'interface': r'(?:public|private|protected|internal)?\s*interface\s+([A-Za-z_]\w*)',
            'enum': r'(?:public|private|protected|internal)?\s*enum\s+([A-Za-z_]\w*)',
            'record': r'(?:public|private|protected|internal)?\s*record\s+([A-Za-z_]\w*)',
            'struct': r'(?:public|private|protected|internal)?\s*struct\s+([A-Za-z_]\w*)',
            'method': r'(?:public|private|protected|internal|static|virtual|override|abstract)\s+(?:\w+\s+)*(\w+)\s*\([^)]*\)',
            'property': r'(?:public|private|protected|internal)\s+(\w+)\s+(\w+)\s*{\s*(?:get|set)',
            'field': r'(?:public|private|protected|internal|readonly|static)\s+(\w+)\s+(\w+);'
        }
    
    async def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analiza un archivo C# y extrae información estructural
        
        Args:
            file_path: Ruta del archivo a analizar
            
        Returns:
            Información del análisis
        """
        try:
            if not os.path.exists(file_path):
                raise CodeAnalysisError(f"Archivo no encontrado: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'size': len(content),
                'lines': len(content.splitlines()),
                'namespace': self._extract_namespace(content),
                'usings': self._extract_usings(content),
                'elements': self._extract_elements(content),
                'methods': self._extract_methods(content),
                'properties': self._extract_properties(content),
                'fields': self._extract_fields(content),
                'summary': self._generate_summary(content)
            }
            
            return analysis
            
        except Exception as e:
            raise CodeAnalysisError(f"Error analizando archivo '{file_path}': {str(e)}")
    
    async def analyze_solution(self, solution_path: str) -> Dict[str, Any]:
        """
        Analiza una solución completa
        
        Args:
            solution_path: Ruta de la solución
            
        Returns:
            Análisis de la solución
        """
        try:
            cs_files = self._find_cs_files(solution_path)
            
            solution_analysis = {
                'solution_path': solution_path,
                'total_files': len(cs_files),
                'files': [],
                'summary': {
                    'total_classes': 0,
                    'total_interfaces': 0,
                    'total_enums': 0,
                    'total_records': 0,
                    'total_methods': 0,
                    'total_properties': 0,
                    'namespaces': set()
                }
            }
            
            for file_path in cs_files:
                try:
                    file_analysis = await self.analyze_file(file_path)
                    solution_analysis['files'].append(file_analysis)
                    
                    # Actualizar resumen
                    self._update_solution_summary(solution_analysis['summary'], file_analysis)
                    
                except Exception:
                    # Continuar con otros archivos si uno falla
                    continue
            
            # Convertir set a lista para serialización
            solution_analysis['summary']['namespaces'] = list(solution_analysis['summary']['namespaces'])
            
            return solution_analysis
            
        except Exception as e:
            raise CodeAnalysisError(f"Error analizando solución: {str(e)}")
    
    def _extract_namespace(self, content: str) -> Optional[str]:
        """Extrae el namespace principal del archivo"""
        match = re.search(self.patterns['namespace'], content, re.MULTILINE)
        return match.group(1) if match else None
    
    def _extract_usings(self, content: str) -> List[str]:
        """Extrae las declaraciones using"""
        matches = re.findall(self.patterns['using'], content, re.MULTILINE)
        return sorted(set(matches))
    
    def _extract_elements(self, content: str) -> List[Dict[str, Any]]:
        """Extrae elementos principales (clases, interfaces, etc.)"""
        elements = []
        lines = content.splitlines()
        
        element_types = ['class', 'interface', 'enum', 'record', 'struct']
        
        for element_type in element_types:
            pattern = self.patterns[element_type]
            
            for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                line_number = content[:match.start()].count('\n') + 1
                
                # Extraer modificadores y información adicional
                line_content = lines[line_number - 1] if line_number <= len(lines) else ""
                modifiers = self._extract_modifiers(line_content)
                
                element = {
                    'name': match.group(1),
                    'type': element_type,
                    'line_number': line_number,
                    'modifiers': modifiers,
                    'summary': self._extract_element_summary(content, line_number)
                }
                
                # Información específica por tipo
                if element_type == 'class':
                    element['inheritance'] = self._extract_inheritance(line_content)
                elif element_type == 'interface':
                    element['inheritance'] = self._extract_interface_inheritance(line_content)
                
                elements.append(element)
        
        return elements
    
    def _extract_methods(self, content: str) -> List[Dict[str, Any]]:
        """Extrae métodos del archivo"""
        methods = []
        
        # Patrón más específico para métodos
        method_pattern = r'(?:public|private|protected|internal|static|virtual|override|abstract|async)\s+(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*(?:{|;)'
        
        for match in re.finditer(method_pattern, content, re.MULTILINE):
            line_number = content[:match.start()].count('\n') + 1
            
            # Extraer información del método
            method_line = content.splitlines()[line_number - 1] if line_number <= len(content.splitlines()) else ""
            
            method = {
                'name': match.group(1),
                'line_number': line_number,
                'modifiers': self._extract_modifiers(method_line),
                'return_type': self._extract_return_type(method_line),
                'parameters': self._extract_parameters(method_line),
                'is_async': 'async' in method_line.lower(),
                'summary': self._extract_element_summary(content, line_number)
            }
            
            methods.append(method)
        
        return methods
    
    def _extract_properties(self, content: str) -> List[Dict[str, Any]]:
        """Extrae propiedades del archivo"""
        properties = []
        
        for match in re.finditer(self.patterns['property'], content, re.MULTILINE):
            line_number = content[:match.start()].count('\n') + 1
            property_line = content.splitlines()[line_number - 1] if line_number <= len(content.splitlines()) else ""
            
            property_info = {
                'name': match.group(2),
                'type': match.group(1),
                'line_number': line_number,
                'modifiers': self._extract_modifiers(property_line),
                'has_getter': 'get' in property_line.lower(),
                'has_setter': 'set' in property_line.lower(),
                'summary': self._extract_element_summary(content, line_number)
            }
            
            properties.append(property_info)
        
        return properties
    
    def _extract_fields(self, content: str) -> List[Dict[str, Any]]:
        """Extrae campos del archivo"""
        fields = []
        
        for match in re.finditer(self.patterns['field'], content, re.MULTILINE):
            line_number = content[:match.start()].count('\n') + 1
            field_line = content.splitlines()[line_number - 1] if line_number <= len(content.splitlines()) else ""
            
            field_info = {
                'name': match.group(2),
                'type': match.group(1),
                'line_number': line_number,
                'modifiers': self._extract_modifiers(field_line),
                'is_readonly': 'readonly' in field_line.lower(),
                'is_static': 'static' in field_line.lower(),
                'summary': self._extract_element_summary(content, line_number)
            }
            
            fields.append(field_info)
        
        return fields
    
    def _extract_modifiers(self, line: str) -> List[str]:
        """Extrae modificadores de acceso y otros"""
        modifiers = []
        modifier_patterns = ['public', 'private', 'protected', 'internal', 'static', 'virtual', 'override', 'abstract', 'sealed', 'readonly', 'async']
        
        line_lower = line.lower()
        for modifier in modifier_patterns:
            if modifier in line_lower:
                modifiers.append(modifier)
        
        return modifiers
    
    def _extract_inheritance(self, line: str) -> List[str]:
        """Extrae información de herencia para clases"""
        inheritance = []
        
        # Buscar patrón ": BaseClass, IInterface1, IInterface2"
        match = re.search(r':\s*([^{]+)', line)
        if match:
            inheritance_text = match.group(1).strip()
            # Dividir por comas y limpiar espacios
            inheritance = [item.strip() for item in inheritance_text.split(',')]
        
        return inheritance
    
    def _extract_interface_inheritance(self, line: str) -> List[str]:
        """Extrae información de herencia para interfaces"""
        return self._extract_inheritance(line)
    
    def _extract_return_type(self, method_line: str) -> Optional[str]:
        """Extrae el tipo de retorno de un método"""
        # Simplificado - buscar patrón antes del nombre del método
        parts = method_line.strip().split()
        if len(parts) >= 2:
            # Buscar el tipo antes del nombre del método
            for i, part in enumerate(parts):
                if '(' in part:  # Encontró el nombre del método con parámetros
                    if i > 0:
                        return parts[i-1]
        return None
    
    def _extract_parameters(self, method_line: str) -> List[Dict[str, str]]:
        """Extrae parámetros de un método"""
        parameters = []
        
        # Buscar contenido entre paréntesis
        match = re.search(r'\(([^)]*)\)', method_line)
        if match and match.group(1).strip():
            param_text = match.group(1).strip()
            
            # Dividir por comas (simple)
            for param in param_text.split(','):
                param = param.strip()
                if param:
                    parts = param.split()
                    if len(parts) >= 2:
                        parameters.append({
                            'type': parts[-2],
                            'name': parts[-1]
                        })
        
        return parameters
    
    def _extract_element_summary(self, content: str, line_number: int) -> Optional[str]:
        """Extrae el comentario XML summary si existe"""
        lines = content.splitlines()
        
        # Buscar hacia atrás desde la línea del elemento
        for i in range(line_number - 2, max(0, line_number - 10), -1):
            if i < len(lines):
                line = lines[i].strip()
                if '<summary>' in line.lower():
                    # Extraer contenido del summary
                    summary_match = re.search(r'<summary>\s*(.*?)\s*</summary>', line, re.IGNORECASE)
                    if summary_match:
                        return summary_match.group(1).strip()
        
        return None
    
    def _generate_summary(self, content: str) -> Dict[str, Any]:
        """Genera un resumen del archivo"""
        lines = content.splitlines()
        
        return {
            'total_lines': len(lines),
            'code_lines': len([line for line in lines if line.strip() and not line.strip().startswith('//')]),
            'comment_lines': len([line for line in lines if line.strip().startswith('//')]),
            'blank_lines': len([line for line in lines if not line.strip()]),
            'has_xml_docs': '<summary>' in content.lower(),
            'complexity_estimate': self._estimate_complexity(content)
        }
    
    def _estimate_complexity(self, content: str) -> str:
        """Estima la complejidad del código"""
        # Contadores simples para estimar complejidad
        if_count = len(re.findall(r'\bif\s*\(', content, re.IGNORECASE))
        for_count = len(re.findall(r'\bfor\s*\(', content, re.IGNORECASE))
        while_count = len(re.findall(r'\bwhile\s*\(', content, re.IGNORECASE))
        switch_count = len(re.findall(r'\bswitch\s*\(', content, re.IGNORECASE))
        
        complexity_score = if_count + for_count + while_count + switch_count
        
        if complexity_score < 5:
            return "Low"
        elif complexity_score < 15:
            return "Medium"
        else:
            return "High"
    
    def _find_cs_files(self, directory: str) -> List[str]:
        """Encuentra todos los archivos .cs en un directorio"""
        cs_files = []
        
        for root, dirs, files in os.walk(directory):
            # Excluir directorios irrelevantes
            dirs[:] = [d for d in dirs if d not in {'.git', 'bin', 'obj', 'packages', 'node_modules'}]
            
            for file in files:
                if file.endswith('.cs'):
                    cs_files.append(os.path.join(root, file))
        
        return cs_files
    
    def _update_solution_summary(self, summary: Dict[str, Any], file_analysis: Dict[str, Any]) -> None:
        """Actualiza el resumen de la solución con información de un archivo"""
        for element in file_analysis.get('elements', []):
            element_type = element['type']
            
            if element_type == 'class':
                summary['total_classes'] += 1
            elif element_type == 'interface':
                summary['total_interfaces'] += 1
            elif element_type == 'enum':
                summary['total_enums'] += 1
            elif element_type == 'record':
                summary['total_records'] += 1
        
        summary['total_methods'] += len(file_analysis.get('methods', []))
        summary['total_properties'] += len(file_analysis.get('properties', []))
        
        # Añadir namespace si existe
        if file_analysis.get('namespace'):
            summary['namespaces'].add(file_analysis['namespace'])