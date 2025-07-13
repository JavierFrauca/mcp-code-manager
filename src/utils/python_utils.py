"""
Utilidades para operaciones con Python y testing
"""
import os
import re
import platform
from typing import Dict, List, Any, Optional
from pathlib import Path

class PythonUtils:
    """Utilidades para trabajar con proyectos Python"""
    
    # Testing frameworks comunes
    TESTING_FRAMEWORKS = {
        "pytest": {
            "description": "Framework de testing moderno y popular",
            "install_cmd": "pip install pytest",
            "run_cmd": "pytest",
            "features": ["fixtures", "parametrize", "plugins", "coverage"]
        },
        "unittest": {
            "description": "Framework de testing incluido en Python estándar",
            "install_cmd": "built-in",
            "run_cmd": "python -m unittest",
            "features": ["built-in", "standard", "no-dependencies"]
        },
        "nose2": {
            "description": "Sucesor de nose, extensible",
            "install_cmd": "pip install nose2",
            "run_cmd": "nose2",
            "features": ["unittest-compatible", "plugins"]
        }
    }
    
    # Linters y herramientas de calidad
    QUALITY_TOOLS = {
        "flake8": {
            "description": "Linter que combina pycodestyle, pyflakes y mccabe",
            "install_cmd": "pip install flake8",
            "type": "linter"
        },
        "pylint": {
            "description": "Linter muy completo con muchas verificaciones",
            "install_cmd": "pip install pylint",
            "type": "linter"
        },
        "black": {
            "description": "Formateador de código Python opinionado",
            "install_cmd": "pip install black",
            "type": "formatter"
        },
        "autopep8": {
            "description": "Formateador que sigue PEP 8",
            "install_cmd": "pip install autopep8",
            "type": "formatter"
        },
        "isort": {
            "description": "Organizador de imports",
            "install_cmd": "pip install isort",
            "type": "formatter"
        },
        "mypy": {
            "description": "Type checker estático",
            "install_cmd": "pip install mypy",
            "type": "type_checker"
        }
    }
    
    # Patrones de archivos Python
    PYTHON_PATTERNS = {
        "test_files": [
            "test_*.py",
            "*_test.py",
            "tests.py"
        ],
        "config_files": [
            "setup.py",
            "setup.cfg",
            "pyproject.toml",
            "requirements.txt",
            "requirements-dev.txt",
            "Pipfile",
            "poetry.lock"
        ],
        "venv_names": [
            "venv",
            "env", 
            ".venv",
            ".env",
            "virtualenv"
        ]
    }
    
    @staticmethod
    def validate_project_name(name: str) -> str:
        """
        Valida y normaliza un nombre de proyecto Python
        
        Args:
            name: Nombre del proyecto
            
        Returns:
            Nombre validado
            
        Raises:
            ValueError: Si el nombre no es válido
        """
        if not name:
            raise ValueError("El nombre del proyecto no puede estar vacío")
        
        # Convertir a snake_case válido para Python
        name = re.sub(r'[^\w\-]', '_', name.strip().lower())
        name = re.sub(r'[-\s]+', '_', name)
        name = re.sub(r'_+', '_', name)
        name = name.strip('_')
        
        if not name:
            raise ValueError("El nombre del proyecto debe contener al menos un carácter válido")
        
        # No puede empezar con número
        if name[0].isdigit():
            name = f"project_{name}"
        
        # Nombres reservados de Python
        reserved_names = [
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del',
            'elif', 'else', 'except', 'exec', 'finally', 'for', 'from', 'global',
            'if', 'import', 'in', 'is', 'lambda', 'not', 'or', 'pass', 'print',
            'raise', 'return', 'try', 'while', 'with', 'yield'
        ]
        
        if name in reserved_names:
            name = f"{name}_project"
        
        return name
    
    @staticmethod
    def validate_venv_name(name: str) -> str:
        """
        Valida un nombre de entorno virtual
        
        Args:
            name: Nombre del entorno virtual
            
        Returns:
            Nombre validado
        """
        if not name:
            return "venv"  # Default
        
        # Eliminar caracteres problemáticos
        name = re.sub(r'[^\w\-\.]', '_', name.strip())
        
        if not name:
            return "venv"
        
        return name
    
    @staticmethod
    def get_venv_activation_command(venv_path: str) -> Dict[str, str]:
        """
        Obtiene los comandos de activación para diferentes shells
        
        Args:
            venv_path: Ruta del entorno virtual
            
        Returns:
            Comandos de activación por shell
        """
        is_windows = platform.system() == "Windows"
        
        if is_windows:
            return {
                "cmd": f"{venv_path}\\Scripts\\activate.bat",
                "powershell": f"{venv_path}\\Scripts\\Activate.ps1",
                "bash": f"source {venv_path}/Scripts/activate",  # Git Bash
                "description": "Windows activation commands"
            }
        else:
            return {
                "bash": f"source {venv_path}/bin/activate",
                "zsh": f"source {venv_path}/bin/activate",
                "fish": f"source {venv_path}/bin/activate.fish",
                "csh": f"source {venv_path}/bin/activate.csh",
                "description": "Unix activation commands"
            }
    
    @staticmethod
    def parse_requirements_file(requirements_path: str) -> Dict[str, Any]:
        """
        Parsea un archivo requirements.txt
        
        Args:
            requirements_path: Ruta al archivo requirements.txt
            
        Returns:
            Información parseada del archivo
        """
        requirements_info = {
            "packages": [],
            "total_packages": 0,
            "has_versions": 0,
            "has_git_packages": 0,
            "has_comments": 0
        }
        
        try:
            if not os.path.exists(requirements_path):
                return requirements_info
            
            with open(requirements_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    continue
                
                if line.startswith('#'):
                    requirements_info["has_comments"] += 1
                    continue
                
                if line.startswith('git+') or line.startswith('-e git+'):
                    requirements_info["has_git_packages"] += 1
                    package_name = "git_package"
                    version = "git"
                else:
                    # Parsear paquete normal
                    match = re.match(r'^([a-zA-Z0-9\-_\.]+)([>=<!=]+(.+))?', line)
                    if match:
                        package_name = match.group(1)
                        version = match.group(3) if match.group(3) else None
                        if version:
                            requirements_info["has_versions"] += 1
                    else:
                        package_name = line.split('=')[0].split('>')[0].split('<')[0]
                        version = None
                
                requirements_info["packages"].append({
                    "name": package_name,
                    "version": version,
                    "raw_line": line
                })
                requirements_info["total_packages"] += 1
        
        except Exception:
            pass  # Retornar info vacía si hay error
        
        return requirements_info
    
    @staticmethod
    def find_python_files(directory: str, include_tests: bool = True) -> Dict[str, List[str]]:
        """
        Busca archivos Python en un directorio
        
        Args:
            directory: Directorio a buscar
            include_tests: Si incluir archivos de test
            
        Returns:
            Archivos Python organizados por tipo
        """
        python_files = {
            "source_files": [],
            "test_files": [],
            "config_files": [],
            "other_files": []
        }
        
        try:
            for root, dirs, files in os.walk(directory):
                # Excluir directorios comunes que no queremos
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env']]
                
                for file in files:
                    if not file.endswith('.py'):
                        # Verificar archivos de configuración
                        if file in PythonUtils.PYTHON_PATTERNS["config_files"]:
                            python_files["config_files"].append(os.path.join(root, file))
                        continue
                    
                    file_path = os.path.join(root, file)
                    
                    # Determinar tipo de archivo
                    is_test = any(
                        file.startswith(pattern.replace('*', '')) or file.endswith(pattern.replace('*', ''))
                        for pattern in PythonUtils.PYTHON_PATTERNS["test_files"]
                    )
                    
                    if is_test and include_tests:
                        python_files["test_files"].append(file_path)
                    elif not is_test:
                        python_files["source_files"].append(file_path)
                    else:
                        python_files["other_files"].append(file_path)
        
        except Exception:
            pass
        
        return python_files
    
    @staticmethod
    def detect_testing_framework(project_path: str) -> Dict[str, Any]:
        """
        Detecta qué framework de testing usa el proyecto
        
        Args:
            project_path: Directorio del proyecto
            
        Returns:
            Información sobre el framework detectado
        """
        detected = {
            "primary_framework": None,
            "frameworks_found": [],
            "config_files_found": [],
            "confidence": 0
        }
        
        try:
            # Buscar archivos de configuración
            config_files = {
                "pytest.ini": "pytest",
                "pyproject.toml": "pytest",  # Puede tener config de pytest
                "setup.cfg": "pytest",      # Puede tener config de pytest
                "tox.ini": "pytest",        # Puede usar pytest
                ".pytest_cache": "pytest",   # Directorio
                "nose2.cfg": "nose2",
                "unittest.cfg": "unittest"
            }
            
            for config_file, framework in config_files.items():
                config_path = os.path.join(project_path, config_file)
                if os.path.exists(config_path):
                    detected["config_files_found"].append(config_file)
                    if framework not in detected["frameworks_found"]:
                        detected["frameworks_found"].append(framework)
            
            # Buscar imports en archivos de test
            python_files = PythonUtils.find_python_files(project_path)
            
            framework_imports = {
                "pytest": ["import pytest", "from pytest"],
                "unittest": ["import unittest", "from unittest"],
                "nose2": ["import nose2", "from nose2"]
            }
            
            framework_counts = {}
            
            for test_file in python_files["test_files"]:
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for framework, import_patterns in framework_imports.items():
                        for pattern in import_patterns:
                            if pattern in content:
                                framework_counts[framework] = framework_counts.get(framework, 0) + 1
                                if framework not in detected["frameworks_found"]:
                                    detected["frameworks_found"].append(framework)
                
                except Exception:
                    continue
            
            # Determinar framework principal
            if framework_counts:
                detected["primary_framework"] = max(framework_counts, key=framework_counts.get)
                detected["confidence"] = framework_counts[detected["primary_framework"]] / max(sum(framework_counts.values()), 1)
            elif detected["frameworks_found"]:
                detected["primary_framework"] = detected["frameworks_found"][0]
                detected["confidence"] = 0.5
            else:
                # Default a unittest si hay archivos de test
                if python_files["test_files"]:
                    detected["primary_framework"] = "unittest"
                    detected["confidence"] = 0.3
        
        except Exception:
            pass
        
        return detected
    
    @staticmethod
    def get_common_test_patterns() -> List[Dict[str, str]]:
        """
        Retorna patrones de test comunes
        
        Returns:
            Lista de patrones con ejemplos
        """
        return [
            {
                "name": "Todos los tests",
                "pattern": "",
                "description": "Ejecuta todos los tests disponibles",
                "framework": "both"
            },
            {
                "name": "Tests por nombre de función",
                "pattern": "test_calculate",
                "description": "Tests que contengan 'test_calculate' en el nombre",
                "framework": "pytest"
            },
            {
                "name": "Tests por nombre de clase",
                "pattern": "TestCalculator",
                "description": "Tests de la clase TestCalculator",
                "framework": "both"
            },
            {
                "name": "Tests marcados (pytest)",
                "pattern": "@pytest.mark.slow",
                "description": "Tests marcados como 'slow'",
                "framework": "pytest"
            },
            {
                "name": "Tests unitarios",
                "pattern": "unit",
                "description": "Tests que contengan 'unit' en el nombre",
                "framework": "both"
            },
            {
                "name": "Tests de integración",
                "pattern": "integration",
                "description": "Tests que contengan 'integration' en el nombre",
                "framework": "both"
            },
            {
                "name": "Archivo específico",
                "pattern": "test_models.py",
                "description": "Solo tests del archivo test_models.py",
                "framework": "both"
            }
        ]
    
    @staticmethod
    def format_test_output(output: str, framework: str = "pytest") -> str:
        """
        Formatea la salida de tests para mejor legibilidad
        
        Args:
            output: Salida cruda de los tests
            framework: Framework usado
            
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
            
            # Patrones comunes para pytest
            if framework == "pytest":
                if "PASSED" in line:
                    formatted_lines.append(f"✅ {line}")
                elif "FAILED" in line:
                    formatted_lines.append(f"❌ {line}")
                elif "SKIPPED" in line:
                    formatted_lines.append(f"⏭️ {line}")
                elif "ERROR" in line:
                    formatted_lines.append(f"💥 {line}")
                elif line.startswith("="):
                    formatted_lines.append(f"📋 {line}")
                elif "collected" in line:
                    formatted_lines.append(f"🔍 {line}")
                else:
                    formatted_lines.append(f"   {line}")
            
            # Patrones para unittest
            elif framework == "unittest":
                if line.startswith("OK"):
                    formatted_lines.append(f"✅ {line}")
                elif "FAIL:" in line or "ERROR:" in line:
                    formatted_lines.append(f"❌ {line}")
                elif line.startswith("Ran"):
                    formatted_lines.append(f"📊 {line}")
                else:
                    formatted_lines.append(f"   {line}")
            
            else:
                formatted_lines.append(f"   {line}")
        
        return '\n'.join(formatted_lines)
    
    @staticmethod
    def format_lint_output(output: str, linter: str = "flake8") -> str:
        """
        Formatea la salida de linting para mejor legibilidad
        
        Args:
            output: Salida cruda del linter
            linter: Linter usado
            
        Returns:
            Salida formateada
        """
        if not output:
            return "✅ No se encontraron problemas de linting"
        
        lines = output.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if linter == "flake8":
                # flake8 format: file:line:col: code message
                if re.match(r'.+:\d+:\d+: \w+ .+', line):
                    # Determinar severidad por código
                    if ' E' in line:  # Error
                        formatted_lines.append(f"❌ {line}")
                    elif ' W' in line:  # Warning
                        formatted_lines.append(f"⚠️ {line}")
                    else:
                        formatted_lines.append(f"ℹ️ {line}")
                else:
                    formatted_lines.append(f"   {line}")
            
            elif linter == "pylint":
                if line.startswith("*"):
                    formatted_lines.append(f"📁 {line}")
                elif "error" in line.lower():
                    formatted_lines.append(f"❌ {line}")
                elif "warning" in line.lower():
                    formatted_lines.append(f"⚠️ {line}")
                elif "convention" in line.lower():
                    formatted_lines.append(f"ℹ️ {line}")
                else:
                    formatted_lines.append(f"   {line}")
            
            else:
                formatted_lines.append(f"   {line}")
        
        return '\n'.join(formatted_lines)
