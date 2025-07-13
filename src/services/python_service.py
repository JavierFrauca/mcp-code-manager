"""
Servicio para operaciones con proyectos Python y testing
"""
import os
import subprocess
import json
import re
import sys
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import asyncio
import platform

from utils.exceptions import CodeAnalysisError

class PythonService:
    """Servicio para gestión de proyectos Python y testing"""
    
    def __init__(self):
        self.python_timeout = 300  # 5 minutos timeout para operaciones
        self.is_windows = platform.system() == "Windows"
        
    async def check_python_environment(self, project_path: str = None) -> Dict[str, Any]:
        """
        Verifica el entorno Python disponible
        
        Args:
            project_path: Ruta del proyecto (opcional)
            
        Returns:
            Información sobre el entorno Python
        """
        try:
            # Verificar Python principal
            python_info = await self._get_python_info()
            
            # Verificar pip
            pip_info = await self._get_pip_info()
            
            # Verificar herramientas de testing
            testing_tools = await self._check_testing_tools()
            
            # Verificar entornos virtuales si hay proyecto
            venv_info = {}
            if project_path:
                venv_info = await self._check_virtual_environments(project_path)
            
            return {
                "python": python_info,
                "pip": pip_info,
                "testing_tools": testing_tools,
                "virtual_environments": venv_info,
                "project_path": project_path
            }
            
        except Exception as e:
            raise CodeAnalysisError(f"Error verificando entorno Python: {str(e)}")
    
    async def create_virtual_environment(self, project_path: str, venv_name: str = "venv") -> Dict[str, Any]:
        """
        Crea un entorno virtual Python
        
        Args:
            project_path: Directorio donde crear el entorno
            venv_name: Nombre del entorno virtual
            
        Returns:
            Información del entorno creado
        """
        try:
            os.makedirs(project_path, exist_ok=True)
            venv_path = os.path.join(project_path, venv_name)
            
            # Crear entorno virtual
            result = await self._run_python_command(
                ["-m", "venv", venv_path],
                cwd=project_path
            )
            
            if result["success"]:
                # Obtener información del entorno creado
                venv_info = self._get_venv_info(venv_path)
                
                return {
                    "success": True,
                    "message": f"Entorno virtual creado: {venv_name}",
                    "venv_path": venv_path,
                    "venv_name": venv_name,
                    "activation_script": venv_info["activation_script"],
                    "python_executable": venv_info["python_executable"],
                    "output": result["output"]
                }
            else:
                raise CodeAnalysisError(f"Error creando entorno virtual: {result['error']}")
                
        except Exception as e:
            raise CodeAnalysisError(f"Error creando entorno virtual: {str(e)}")
    
    async def install_packages(self, packages: List[str], venv_path: str = None, 
                             requirements_file: str = None) -> Dict[str, Any]:
        """
        Instala paquetes Python usando pip
        
        Args:
            packages: Lista de paquetes a instalar
            venv_path: Ruta del entorno virtual (opcional)
            requirements_file: Archivo requirements.txt (opcional)
            
        Returns:
            Resultado de la instalación
        """
        try:
            if requirements_file and os.path.exists(requirements_file):
                # Instalar desde requirements.txt
                cmd = ["-m", "pip", "install", "-r", requirements_file]
                operation = f"requirements from {requirements_file}"
            elif packages:
                # Instalar paquetes específicos
                cmd = ["-m", "pip", "install"] + packages
                operation = f"packages: {', '.join(packages)}"
            else:
                raise CodeAnalysisError("No se especificaron paquetes ni archivo requirements")
            
            # Usar entorno virtual si se especifica
            python_cmd = self._get_python_executable(venv_path)
            
            result = await self._run_command(
                [python_cmd] + cmd,
                cwd=os.path.dirname(venv_path) if venv_path else None
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Paquetes instalados exitosamente: {operation}",
                    "packages": packages,
                    "venv_path": venv_path,
                    "output": result["output"]
                }
            else:
                raise CodeAnalysisError(f"Error instalando paquetes: {result['error']}")
                
        except Exception as e:
            raise CodeAnalysisError(f"Error instalando paquetes: {str(e)}")
    
    async def run_tests_pytest(self, test_path: str, venv_path: str = None, 
                             test_pattern: str = None, collect_coverage: bool = False,
                             verbose: bool = False) -> Dict[str, Any]:
        """
        Ejecuta tests usando pytest
        
        Args:
            test_path: Directorio o archivo de tests
            venv_path: Ruta del entorno virtual (opcional)
            test_pattern: Patrón de tests específicos
            collect_coverage: Si recopilar coverage
            verbose: Salida verbose
            
        Returns:
            Resultados de los tests
        """
        try:
            # Construir comando pytest
            cmd = ["-m", "pytest"]
            
            if verbose:
                cmd.append("-v")
            
            if collect_coverage:
                cmd.extend(["--cov=.", "--cov-report=term-missing"])
            
            if test_pattern:
                cmd.extend(["-k", test_pattern])
            
            # Agregar JSON reporter para parsing
            cmd.extend(["--json-report", "--json-report-file=test_results.json"])
            
            # Agregar directorio de tests
            cmd.append(test_path)
            
            # Usar entorno virtual si se especifica
            python_cmd = self._get_python_executable(venv_path)
            
            result = await self._run_command(
                [python_cmd] + cmd,
                cwd=os.path.dirname(test_path) if os.path.isfile(test_path) else test_path
            )
            
            # Analizar resultados
            test_analysis = self._analyze_pytest_output(result.get("output", ""), result.get("error", ""))
            
            return {
                "success": result["success"],
                "message": "Tests ejecutados con pytest",
                "test_path": test_path,
                "pattern": test_pattern,
                "coverage": collect_coverage,
                "verbose": verbose,
                "venv_path": venv_path,
                "output": result["output"],
                "error": result.get("error", ""),
                "analysis": test_analysis
            }
                
        except Exception as e:
            raise CodeAnalysisError(f"Error ejecutando tests pytest: {str(e)}")
    
    async def run_tests_unittest(self, test_path: str, venv_path: str = None, 
                               test_pattern: str = None, verbose: bool = False) -> Dict[str, Any]:
        """
        Ejecuta tests usando unittest
        
        Args:
            test_path: Directorio o módulo de tests
            venv_path: Ruta del entorno virtual (opcional)
            test_pattern: Patrón de tests específicos
            verbose: Salida verbose
            
        Returns:
            Resultados de los tests
        """
        try:
            # Construir comando unittest
            cmd = ["-m", "unittest"]
            
            if verbose:
                cmd.append("-v")
            
            # Descubrir tests si es directorio
            if os.path.isdir(test_path):
                cmd.extend(["discover", "-s", test_path])
                if test_pattern:
                    cmd.extend(["-p", f"*{test_pattern}*"])
            else:
                # Ejecutar módulo específico
                cmd.append(test_path)
            
            # Usar entorno virtual si se especifica
            python_cmd = self._get_python_executable(venv_path)
            
            result = await self._run_command(
                [python_cmd] + cmd,
                cwd=os.path.dirname(test_path) if os.path.isfile(test_path) else test_path
            )
            
            # Analizar resultados
            test_analysis = self._analyze_unittest_output(result.get("output", ""), result.get("error", ""))
            
            return {
                "success": result["success"],
                "message": "Tests ejecutados con unittest",
                "test_path": test_path,
                "pattern": test_pattern,
                "verbose": verbose,
                "venv_path": venv_path,
                "output": result["output"],
                "error": result.get("error", ""),
                "analysis": test_analysis
            }
                
        except Exception as e:
            raise CodeAnalysisError(f"Error ejecutando tests unittest: {str(e)}")
    
    async def run_linting(self, project_path: str, venv_path: str = None, 
                        linter: str = "flake8") -> Dict[str, Any]:
        """
        Ejecuta linting de código Python
        
        Args:
            project_path: Directorio del proyecto
            venv_path: Ruta del entorno virtual (opcional)
            linter: Herramienta de linting (flake8, pylint, etc.)
            
        Returns:
            Resultados del linting
        """
        try:
            # Construir comando según el linter
            if linter == "flake8":
                cmd = ["-m", "flake8", ".", "--max-line-length=88"]
            elif linter == "pylint":
                cmd = ["-m", "pylint", "**/*.py"]
            else:
                raise CodeAnalysisError(f"Linter no soportado: {linter}")
            
            # Usar entorno virtual si se especifica
            python_cmd = self._get_python_executable(venv_path)
            
            result = await self._run_command(
                [python_cmd] + cmd,
                cwd=project_path
            )
            
            # Analizar resultados de linting
            lint_analysis = self._analyze_lint_output(result.get("output", ""), result.get("error", ""), linter)
            
            return {
                "success": result["return_code"] == 0,  # flake8/pylint usan códigos de salida específicos
                "message": f"Linting completado con {linter}",
                "linter": linter,
                "project_path": project_path,
                "venv_path": venv_path,
                "output": result["output"],
                "error": result.get("error", ""),
                "analysis": lint_analysis
            }
                
        except Exception as e:
            raise CodeAnalysisError(f"Error ejecutando linting: {str(e)}")
    
    async def format_code(self, project_path: str, venv_path: str = None, 
                        formatter: str = "black") -> Dict[str, Any]:
        """
        Formatea código Python
        
        Args:
            project_path: Directorio del proyecto
            venv_path: Ruta del entorno virtual (opcional)
            formatter: Herramienta de formateo (black, autopep8)
            
        Returns:
            Resultado del formateo
        """
        try:
            # Construir comando según el formateador
            if formatter == "black":
                cmd = ["-m", "black", ".", "--line-length=88"]
            elif formatter == "autopep8":
                cmd = ["-m", "autopep8", "--in-place", "--recursive", "."]
            else:
                raise CodeAnalysisError(f"Formateador no soportado: {formatter}")
            
            # Usar entorno virtual si se especifica
            python_cmd = self._get_python_executable(venv_path)
            
            result = await self._run_command(
                [python_cmd] + cmd,
                cwd=project_path
            )
            
            return {
                "success": result["success"],
                "message": f"Código formateado con {formatter}",
                "formatter": formatter,
                "project_path": project_path,
                "venv_path": venv_path,
                "output": result["output"],
                "error": result.get("error", "")
            }
                
        except Exception as e:
            raise CodeAnalysisError(f"Error formateando código: {str(e)}")
    
    async def generate_requirements(self, project_path: str, venv_path: str = None) -> Dict[str, Any]:
        """
        Genera archivo requirements.txt
        
        Args:
            project_path: Directorio del proyecto
            venv_path: Ruta del entorno virtual (opcional)
            
        Returns:
            Resultado de la generación
        """
        try:
            # Usar entorno virtual si se especifica
            python_cmd = self._get_python_executable(venv_path)
            
            result = await self._run_command(
                [python_cmd, "-m", "pip", "freeze"],
                cwd=project_path
            )
            
            if result["success"]:
                # Escribir requirements.txt
                requirements_file = os.path.join(project_path, "requirements.txt")
                with open(requirements_file, 'w', encoding='utf-8') as f:
                    f.write(result["output"])
                
                # Contar paquetes
                package_count = len([line for line in result["output"].split('\n') if line.strip() and not line.startswith('#')])
                
                return {
                    "success": True,
                    "message": f"requirements.txt generado con {package_count} paquetes",
                    "requirements_file": requirements_file,
                    "package_count": package_count,
                    "venv_path": venv_path,
                    "content": result["output"]
                }
            else:
                raise CodeAnalysisError(f"Error generando requirements: {result['error']}")
                
        except Exception as e:
            raise CodeAnalysisError(f"Error generando requirements: {str(e)}")
    
    # === Métodos auxiliares ===
    
    async def _run_python_command(self, args: List[str], cwd: str = None) -> Dict[str, Any]:
        """Ejecuta un comando Python"""
        return await self._run_command([sys.executable] + args, cwd)
    
    async def _run_command(self, cmd: List[str], cwd: str = None) -> Dict[str, Any]:
        """
        Ejecuta un comando de forma asíncrona
        
        Args:
            cmd: Comando a ejecutar
            cwd: Directorio de trabajo
            
        Returns:
            Resultado del comando
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=self.python_timeout
            )
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8', errors='replace'),
                "error": stderr.decode('utf-8', errors='replace'),
                "return_code": process.returncode,
                "command": " ".join(cmd)
            }
            
        except asyncio.TimeoutError:
            raise CodeAnalysisError(f"Timeout ejecutando comando: {' '.join(cmd)}")
        except FileNotFoundError:
            raise CodeAnalysisError(f"Comando no encontrado: {cmd[0]}")
        except Exception as e:
            raise CodeAnalysisError(f"Error ejecutando comando: {str(e)}")
    
    async def _get_python_info(self) -> Dict[str, Any]:
        """Obtiene información de Python"""
        try:
            result = await self._run_python_command(["--version"])
            if result["success"]:
                version = result["output"].strip()
                
                # Obtener información adicional
                info_result = await self._run_python_command(["-c", "import sys; print(sys.executable); print(sys.version)"])
                
                return {
                    "installed": True,
                    "version": version,
                    "executable": info_result["output"].split('\n')[0] if info_result["success"] else sys.executable,
                    "full_version": info_result["output"].split('\n')[1] if info_result["success"] else ""
                }
            else:
                return {"installed": False, "error": result.get("error", "Python not found")}
        except Exception as e:
            return {"installed": False, "error": str(e)}
    
    async def _get_pip_info(self) -> Dict[str, Any]:
        """Obtiene información de pip"""
        try:
            result = await self._run_python_command(["-m", "pip", "--version"])
            if result["success"]:
                return {
                    "installed": True,
                    "version": result["output"].strip()
                }
            else:
                return {"installed": False, "error": result.get("error", "pip not found")}
        except Exception as e:
            return {"installed": False, "error": str(e)}
    
    async def _check_testing_tools(self) -> Dict[str, Any]:
        """Verifica herramientas de testing disponibles"""
        tools = {}
        
        # Verificar pytest
        try:
            result = await self._run_python_command(["-m", "pytest", "--version"])
            tools["pytest"] = {
                "installed": result["success"],
                "version": result["output"].strip() if result["success"] else None,
                "error": result.get("error") if not result["success"] else None
            }
        except:
            tools["pytest"] = {"installed": False, "error": "Not available"}
        
        # Verificar unittest (siempre disponible en Python estándar)
        tools["unittest"] = {"installed": True, "version": "built-in"}
        
        # Verificar coverage
        try:
            result = await self._run_python_command(["-m", "coverage", "--version"])
            tools["coverage"] = {
                "installed": result["success"],
                "version": result["output"].strip() if result["success"] else None
            }
        except:
            tools["coverage"] = {"installed": False}
        
        # Verificar linters
        for linter in ["flake8", "pylint", "black"]:
            try:
                result = await self._run_python_command(["-m", linter, "--version"])
                tools[linter] = {
                    "installed": result["success"],
                    "version": result["output"].strip() if result["success"] else None
                }
            except:
                tools[linter] = {"installed": False}
        
        return tools
    
    async def _check_virtual_environments(self, project_path: str) -> Dict[str, Any]:
        """Busca entornos virtuales en el proyecto"""
        venvs = []
        common_venv_names = ["venv", "env", ".venv", ".env", "virtualenv"]
        
        for venv_name in common_venv_names:
            venv_path = os.path.join(project_path, venv_name)
            if os.path.exists(venv_path):
                venv_info = self._get_venv_info(venv_path)
                if venv_info["is_valid"]:
                    venvs.append(venv_info)
        
        return {
            "found_environments": venvs,
            "total_environments": len(venvs)
        }
    
    def _get_venv_info(self, venv_path: str) -> Dict[str, Any]:
        """Obtiene información de un entorno virtual"""
        try:
            if self.is_windows:
                python_exe = os.path.join(venv_path, "Scripts", "python.exe")
                activation_script = os.path.join(venv_path, "Scripts", "activate.bat")
            else:
                python_exe = os.path.join(venv_path, "bin", "python")
                activation_script = os.path.join(venv_path, "bin", "activate")
            
            is_valid = os.path.exists(python_exe)
            
            return {
                "name": os.path.basename(venv_path),
                "path": venv_path,
                "python_executable": python_exe,
                "activation_script": activation_script,
                "is_valid": is_valid,
                "platform": "Windows" if self.is_windows else "Unix"
            }
        except Exception:
            return {"is_valid": False, "error": "Could not analyze venv"}
    
    def _get_python_executable(self, venv_path: str = None) -> str:
        """Obtiene el ejecutable Python apropiado"""
        if venv_path:
            venv_info = self._get_venv_info(venv_path)
            if venv_info["is_valid"]:
                return venv_info["python_executable"]
        
        return sys.executable
    
    def _analyze_pytest_output(self, output: str, error: str) -> Dict[str, Any]:
        """Analiza la salida de pytest"""
        full_output = output + "\n" + error
        
        # Buscar resumen de tests
        summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0
        }
        
        # Patrón para resultado final de pytest
        result_pattern = r'=+ (.+) =+'
        matches = re.findall(result_pattern, full_output)
        
        if matches:
            result_line = matches[-1]  # Última línea de resultado
            
            # Extraer números
            if "passed" in result_line:
                passed_match = re.search(r'(\d+) passed', result_line)
                if passed_match:
                    summary["passed"] = int(passed_match.group(1))
            
            if "failed" in result_line:
                failed_match = re.search(r'(\d+) failed', result_line)
                if failed_match:
                    summary["failed"] = int(failed_match.group(1))
            
            if "skipped" in result_line:
                skipped_match = re.search(r'(\d+) skipped', result_line)
                if skipped_match:
                    summary["skipped"] = int(skipped_match.group(1))
            
            if "error" in result_line:
                error_match = re.search(r'(\d+) error', result_line)
                if error_match:
                    summary["errors"] = int(error_match.group(1))
        
        summary["total"] = summary["passed"] + summary["failed"] + summary["skipped"] + summary["errors"]
        
        # Buscar tests fallidos
        failed_tests = re.findall(r'FAILED (.+?) -', full_output)
        
        return {
            "summary": summary,
            "failed_tests": failed_tests,
            "success_rate": (summary["passed"] / max(summary["total"], 1)) * 100,
            "has_failures": summary["failed"] > 0 or summary["errors"] > 0
        }
    
    def _analyze_unittest_output(self, output: str, error: str) -> Dict[str, Any]:
        """Analiza la salida de unittest"""
        full_output = output + "\n" + error
        
        # Buscar línea de resultado
        result_match = re.search(r'Ran (\d+) tests? in', full_output)
        total_tests = int(result_match.group(1)) if result_match else 0
        
        # Buscar fallos y errores
        failures = len(re.findall(r'FAIL:', full_output))
        errors = len(re.findall(r'ERROR:', full_output))
        
        summary = {
            "total": total_tests,
            "passed": total_tests - failures - errors,
            "failed": failures,
            "errors": errors,
            "skipped": 0  # unittest no separa skipped fácilmente
        }
        
        # Buscar tests fallidos específicos
        failed_tests = re.findall(r'FAIL: (.+)', full_output)
        error_tests = re.findall(r'ERROR: (.+)', full_output)
        
        return {
            "summary": summary,
            "failed_tests": failed_tests + error_tests,
            "success_rate": (summary["passed"] / max(summary["total"], 1)) * 100,
            "has_failures": failures > 0 or errors > 0
        }
    
    def _analyze_lint_output(self, output: str, error: str, linter: str) -> Dict[str, Any]:
        """Analiza la salida de linting"""
        full_output = output + "\n" + error
        
        if linter == "flake8":
            # flake8 format: filename:line:col: error_code message
            issues = re.findall(r'([^:]+):(\d+):(\d+): (\w+) (.+)', full_output)
            
            issue_types = {}
            for file, line, col, code, message in issues:
                issue_type = code[0]  # E=error, W=warning, etc.
                if issue_type not in issue_types:
                    issue_types[issue_type] = 0
                issue_types[issue_type] += 1
            
            return {
                "total_issues": len(issues),
                "issue_types": issue_types,
                "issues": [
                    {
                        "file": file,
                        "line": int(line),
                        "column": int(col),
                        "code": code,
                        "message": message
                    }
                    for file, line, col, code, message in issues[:20]  # Limitar a 20
                ]
            }
        
        return {
            "total_issues": 0,
            "issue_types": {},
            "issues": [],
            "raw_output": full_output
        }
