import sys
from typing import List
from mcp.types import TextContent

class PythonAdapterMixin:
    async def _python_check_environment(self, repo_url: str = None) -> List[TextContent]:
        """Conecta python_check_environment con el handler Python"""
        try:
            result = await self.python_handler.check_python_environment(repo_url)
            response_text = f"✅ Entorno Python verificado:\n\n"
            response_text += f"🐍 **Python:** {result['environment'].get('python_version', 'N/A')}\n"
            response_text += f"📦 **Pip:** {result['environment'].get('pip_version', 'N/A')}\n"
            if result['project']:
                response_text += f"📁 **Archivos Python:** {result['project']['file_summary']['source_files']}\n"
                response_text += f"🧪 **Framework de testing:** {result['project']['testing_framework']}\n"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error verificando entorno Python: {str(e)}")]
    
    async def _python_create_venv(self, repo_url: str, venv_name: str = "venv", base_path: str = "") -> List[TextContent]:
        """Conecta python_create_venv con el handler Python"""
        try:
            result = await self.python_handler.create_virtual_environment(repo_url, venv_name, base_path)
            return [TextContent(type="text", text=f"✅ Entorno virtual Python creado:\n\n📁 **Nombre:** {result['venv_name']}\n📂 **Ubicación:** {result['venv_path']}\n🐍 **Python:** {result['python_executable']}\n\n📋 **Comandos de activación:**\n{result['activation_commands']}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error creando entorno virtual: {str(e)}")]
    
    async def _python_install_packages(self, repo_url: str, packages: List[str], venv_name: str = None, base_path: str = "") -> List[TextContent]:
        """Conecta python_install_packages con el handler Python"""
        try:
            result = await self.python_handler.install_packages(repo_url, packages, venv_name, base_path)
            return [TextContent(type="text", text=f"✅ Paquetes Python instalados:\n\n📦 **Paquetes:** {', '.join(result['packages'])}\n🐍 **Entorno:** {result['venv_name'] or 'Sistema'}\n\n📋 **Output:**\n{result['output']}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error instalando paquetes: {str(e)}")]
    
    async def _python_install_requirements(self, repo_url: str, requirements_file: str = "requirements.txt", venv_name: str = None, base_path: str = "") -> List[TextContent]:
        """Conecta python_install_requirements con el handler Python"""
        try:
            result = await self.python_handler.install_requirements(repo_url, requirements_file, venv_name, base_path)
            return [TextContent(type="text", text=f"✅ Requirements instalados:\n\n📄 **Archivo:** {result['requirements_file']}\n📦 **Paquetes:** {result['packages_installed']}\n🐍 **Entorno:** {result['venv_name'] or 'Sistema'}\n\n📋 **Output:**\n{result['output']}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error instalando requirements: {str(e)}")]
    
    async def _python_freeze(self, repo_url: str, venv_name: str = None, base_path: str = "") -> List[TextContent]:
        """Conecta python_freeze con el handler Python"""
        try:
            result = await self.python_handler.generate_requirements(repo_url, venv_name, base_path)
            return [TextContent(type="text", text=f"✅ Requirements.txt generado:\n\n📄 **Archivo:** {result['requirements_file']}\n📦 **Paquetes:** {result['package_count']}\n🐍 **Entorno:** {result['venv_name'] or 'Sistema'}\n\n📋 **Contenido:**\n{result['content']}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error generando requirements: {str(e)}")]
    
    async def _python_run_pytest(self, repo_url: str, test_path: str = ".", venv_name: str = None, test_pattern: str = None, collect_coverage: bool = False, verbose: bool = False) -> List[TextContent]:
        """Conecta python_run_pytest con el handler Python"""
        try:
            result = await self.python_handler.run_tests_pytest(repo_url, test_path, venv_name, test_pattern, collect_coverage, verbose)
            if result['success']:
                response_text = f"✅ Tests pytest ejecutados:\n\n"
                response_text += f"📁 **Path:** {result['test_path']}\n"
                response_text += f"🔍 **Patrón:** {result['pattern'] or 'Todos'}\n"
                response_text += f"📊 **Resumen:** {result['test_summary']}\n"
                response_text += f"📈 **Tasa de éxito:** {result['success_rate']}%\n"
                if result['failed_tests']:
                    response_text += f"❌ **Tests fallidos:** {len(result['failed_tests'])}\n"
                response_text += f"\n📋 **Salida:**\n{result['output']}"
            else:
                response_text = f"❌ Error ejecutando pytest:\n\n{result['output']}"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando pytest: {str(e)}")]
    
    async def _python_run_unittest(self, repo_url: str, test_path: str = ".", venv_name: str = None, test_pattern: str = None, verbose: bool = False) -> List[TextContent]:
        """Conecta python_run_unittest con el handler Python"""
        try:
            result = await self.python_handler.run_tests_unittest(repo_url, test_path, venv_name, test_pattern, verbose)
            if result['success']:
                response_text = f"✅ Tests unittest ejecutados:\n\n"
                response_text += f"📁 **Path:** {result['test_path']}\n"
                response_text += f"🔍 **Patrón:** {result['pattern'] or 'Todos'}\n"
                response_text += f"📊 **Resumen:** {result['test_summary']}\n"
                response_text += f"📈 **Tasa de éxito:** {result['success_rate']}%\n"
                response_text += f"\n📋 **Salida:**\n{result['output']}"
            else:
                response_text = f"❌ Error ejecutando unittest:\n\n{result['output']}"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando unittest: {str(e)}")]
    
    async def _python_lint(self, repo_url: str, linter: str = "flake8", venv_name: str = None, base_path: str = "") -> List[TextContent]:
        """Conecta python_lint con el handler Python"""
        try:
            result = await self.python_handler.run_linting(repo_url, linter, venv_name, base_path)
            if result['success']:
                response_text = f"✅ Linting ejecutado ({result['linter']}):\n\n"
                response_text += f"📁 **Path:** {result['project_path']}\n"
                response_text += f"🐍 **Entorno:** {result['venv_name'] or 'Sistema'}\n"
                response_text += f"🔍 **Issues:** {result['total_issues']}\n"
                response_text += f"\n📋 **Salida:**\n{result['output']}"
            else:
                response_text = f"❌ Error ejecutando linting:\n\n{result['output']}"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando linting: {str(e)}")]
    
    async def _python_format(self, repo_url: str, formatter: str = "black", venv_name: str = None, base_path: str = "") -> List[TextContent]:
        """Conecta python_format con el handler Python"""
        try:
            result = await self.python_handler.format_code(repo_url, formatter, venv_name, base_path)
            if result['success']:
                response_text = f"✅ Código formateado ({result['formatter']}):\n\n"
                response_text += f"📁 **Path:** {result['project_path']}\n"
                response_text += f"🐍 **Entorno:** {result['venv_name'] or 'Sistema'}\n"
                response_text += f"\n📋 **Output:**\n{result['output']}"
            else:
                response_text = f"❌ Error formateando código:\n\n{result['output']}"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error formateando código: {str(e)}")]
    
    async def _python_detect_project(self, repo_url: str) -> List[TextContent]:
        """Conecta python_detect_project con el handler Python"""
        try:
            result = await self.python_handler.detect_project_structure(repo_url)
            response_text = f"📋 **Estructura del proyecto Python:**\n\n"
            response_text += f"📁 **Archivos fuente:** {result['file_summary']['source_files']}\n"
            response_text += f"🧪 **Archivos de test:** {result['file_summary']['test_files']}\n"
            response_text += f"⚙️ **Archivos de config:** {result['file_summary']['config_files']}\n"
            response_text += f"🔧 **Framework de testing:** {result['testing_framework']}\n"
            response_text += f"📦 **Requirements:** {result['requirements']['total_packages']} paquetes\n"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error analizando estructura: {str(e)}")]
    
    async def _python_get_test_patterns(self) -> List[TextContent]:
        """Conecta python_get_test_patterns con el handler Python"""
        try:
            result = await self.python_handler.get_test_patterns()
            response_text = f"📋 **Patrones de test Python ({result['total']} disponibles):**\n\n"
            for pattern in result['patterns']:
                response_text += f"🔍 **{pattern['name']}**: {pattern['description']}\n"
                response_text += f"   📝 Patrón: `{pattern['pattern'] or 'Todos'}`\n\n"
            response_text += f"\n💡 **Ejemplos de uso:**\n"
            for example in result['usage_examples']:
                response_text += f"   • {example}\n"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error obteniendo patrones: {str(e)}")]
    
    async def _python_get_tools_info(self) -> List[TextContent]:
        """Conecta python_get_tools_info con el handler Python"""
        try:
            result = await self.python_handler.get_quality_tools_info()
            response_text = f"🔧 **Herramientas de calidad Python:**\n\n"
            response_text += f"📋 **Linting:** {', '.join([tool['name'] for tool in result['quality_tools']['linting']])}\n"
            response_text += f"✨ **Formateo:** {', '.join([tool['name'] for tool in result['quality_tools']['formatting']])}\n"
            response_text += f"🧪 **Testing:** {', '.join([fw['name'] for fw in result['testing_frameworks']])}\n\n"
            response_text += f"💡 **Workflow recomendado:**\n"
            for step in result['recommended_workflow']:
                response_text += f"   {step}\n"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error obteniendo información de herramientas: {str(e)}")]
