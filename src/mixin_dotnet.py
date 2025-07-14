
import sys
import json
from typing import List
from mcp.types import TextContent

class DotnetAdapterMixin:
    async def _dotnet_check_environment(self, repo_url: str = None) -> List[TextContent]:
        """Conecta dotnet_check_environment con el handler C#"""
        try:
            result = await self.csharp_handler.check_dotnet_environment(repo_url)
            return [TextContent(type="text", text=f"✅ Entorno .NET verificado:\n\n{json.dumps(result, indent=2, ensure_ascii=False)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error verificando entorno .NET: {str(e)}")]
    
    async def _dotnet_create_solution(self, repo_url: str, solution_name: str, base_path: str = "") -> List[TextContent]:
        """Conecta dotnet_create_solution con el handler C#"""
        try:
            result = await self.csharp_handler.create_solution(repo_url, solution_name, base_path)
            return [TextContent(type="text", text=f"✅ Solución C# creada:\n\n📁 **Solución:** {result['solution_name']}\n📄 **Archivo:** {result['solution_file']}\n📂 **Ubicación:** {result['solution_path']}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error creando solución: {str(e)}")]
    
    async def _dotnet_create_project(self, repo_url: str, project_name: str, template: str = "console", base_path: str = "", framework: str = None) -> List[TextContent]:
        """Conecta dotnet_create_project con el handler C#"""
        try:
            result = await self.csharp_handler.create_project(repo_url, project_name, template, base_path, framework)
            return [TextContent(type="text", text=f"✅ Proyecto C# creado:\n\n📁 **Proyecto:** {result['project_name']}\n🏗️ **Template:** {result['template']}\n📄 **Archivo:** {result['project_file']}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error creando proyecto: {str(e)}")]
    
    async def _dotnet_add_project_to_solution(self, repo_url: str, solution_file: str, project_file: str) -> List[TextContent]:
        """Conecta dotnet_add_project_to_solution con el handler C#"""
        try:
            result = await self.csharp_handler.add_project_to_solution(repo_url, solution_file, project_file)
            return [TextContent(type="text", text=f"✅ Proyecto agregado a solución:\n\n📋 **Solución:** {result['solution_file']}\n📁 **Proyecto:** {result['project_file']}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error agregando proyecto a solución: {str(e)}")]
    
    async def _dotnet_list_solution_projects(self, repo_url: str, solution_file: str) -> List[TextContent]:
        """Conecta dotnet_list_solution_projects con el handler C#"""
        try:
            result = await self.csharp_handler.list_solution_projects(repo_url, solution_file)
            response_text = f"📋 **Proyectos en solución '{result['solution_file']}':**\n\n"
            response_text += f"🔢 **Total:** {result['total_projects']} proyectos\n\n"
            for project in result['projects']:
                response_text += f"📁 **{project['name']}** ({project['path']})\n"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error listando proyectos: {str(e)}")]
    
    async def _dotnet_add_package(self, repo_url: str, project_file: str, package_name: str, version: str = None) -> List[TextContent]:
        """Conecta dotnet_add_package con el handler C#"""
        try:
            result = await self.csharp_handler.add_package_to_project(repo_url, project_file, package_name, version)
            return [TextContent(type="text", text=f"✅ Paquete NuGet agregado:\n\n📦 **Paquete:** {result['package']} (v{result['version']})\n📁 **Proyecto:** {result['project_file']}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error agregando paquete: {str(e)}")]
    
    async def _dotnet_build_solution(self, repo_url: str, solution_file: str = None, configuration: str = "Debug") -> List[TextContent]:
        """Conecta dotnet_build_solution con el handler C#"""
        try:
            result = await self.csharp_handler.build_solution(repo_url, solution_file, configuration)
            if result['success']:
                response_text = f"✅ Compilación exitosa:\n\n"
                response_text += f"🔧 **Configuración:** {result['configuration']}\n"
                response_text += f"📁 **Target:** {result['solution_file']}\n"
                if result['has_warnings']:
                    response_text += f"⚠️ **Warnings:** {result['warning_count']}\n"
                response_text += f"\n📋 **Salida:**\n{result['output']}"
            else:
                response_text = f"❌ Error en compilación:\n\n{result['output']}"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error compilando solución: {str(e)}")]
    
    async def _dotnet_build_project(self, repo_url: str, project_file: str, configuration: str = "Debug") -> List[TextContent]:
        """Conecta dotnet_build_project con el handler C#"""
        try:
            result = await self.csharp_handler.build_project(repo_url, project_file, configuration)
            if result['success']:
                response_text = f"✅ Proyecto compilado exitosamente:\n\n"
                response_text += f"🔧 **Configuración:** {result['configuration']}\n"
                response_text += f"📁 **Proyecto:** {result['project_file']}\n"
                if result['has_warnings']:
                    response_text += f"⚠️ **Warnings:** {result['warning_count']}\n"
                response_text += f"\n📋 **Salida:**\n{result['output']}"
            else:
                response_text = f"❌ Error compilando proyecto:\n\n{result['output']}"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error compilando proyecto: {str(e)}")]
    
    async def _dotnet_restore_packages(self, repo_url: str, project_path: str = "") -> List[TextContent]:
        """Conecta dotnet_restore_packages con el handler C#"""
        try:
            result = await self.csharp_handler.restore_packages(repo_url, project_path)
            return [TextContent(type="text", text=f"✅ Paquetes NuGet restaurados:\n\n📁 **Path:** {result['project_path']}\n📋 **Output:**\n{result['output']}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error restaurando paquetes: {str(e)}")]
    
    async def _dotnet_test_all(self, repo_url: str, test_path: str = "", collect_coverage: bool = False) -> List[TextContent]:
        """Conecta dotnet_test_all con el handler C#"""
        try:
            result = await self.csharp_handler.run_all_tests(repo_url, test_path, collect_coverage)
            if result['success']:
                response_text = f"✅ Tests ejecutados:\n\n"
                response_text += f"📁 **Path:** {result['test_path']}\n"
                response_text += f"📊 **Resumen:** {result['test_summary']}\n"
                response_text += f"📈 **Tasa de éxito:** {result['success_rate']}%\n"
                if result['failed_tests']:
                    response_text += f"❌ **Tests fallidos:** {len(result['failed_tests'])}\n"
                response_text += f"\n📋 **Salida:**\n{result['output']}"
            else:
                response_text = f"❌ Error ejecutando tests:\n\n{result['output']}"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando tests: {str(e)}")]
    
    async def _dotnet_test_filter(self, repo_url: str, filter_expression: str, test_path: str = "", collect_coverage: bool = False) -> List[TextContent]:
        """Conecta dotnet_test_filter con el handler C#"""
        try:
            result = await self.csharp_handler.run_filtered_tests(repo_url, filter_expression, test_path, collect_coverage)
            if result['success']:
                response_text = f"✅ Tests filtrados ejecutados:\n\n"
                response_text += f"🔍 **Filtro:** {result['filter']}\n"
                response_text += f"📁 **Path:** {result['test_path']}\n"
                response_text += f"📊 **Resumen:** {result['test_summary']}\n"
                response_text += f"📈 **Tasa de éxito:** {result['success_rate']}%\n"
                response_text += f"\n📋 **Salida:**\n{result['output']}"
            else:
                response_text = f"❌ Error ejecutando tests filtrados:\n\n{result['output']}"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error ejecutando tests filtrados: {str(e)}")]
    
    async def _dotnet_get_test_filters(self) -> List[TextContent]:
        """Conecta dotnet_get_test_filters con el handler C#"""
        try:
            result = await self.csharp_handler.get_common_test_filters()
            response_text = f"📋 **Filtros de test comunes ({result['total']} disponibles):**\n\n"
            for filter_info in result['filters']:
                response_text += f"🔍 **{filter_info['name']}**: {filter_info['description']}\n"
                response_text += f"   📝 Filtro: `{filter_info['filter']}`\n\n"  # ✅ 'filter' sí existe
            response_text += f"\n💡 **Ejemplos de uso:**\n"
            for example in result['usage_examples']:
                response_text += f"   • {example}\n"
            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error obteniendo filtros: {str(e)}")]
    
