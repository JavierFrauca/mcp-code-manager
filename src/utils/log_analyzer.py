"""
Utilidades para gestión y análisis de logs
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class LogEntry:
    """Representa una entrada de log"""
    timestamp: datetime
    level: str
    logger_name: str
    message: str
    raw_line: str
    parsed_data: Optional[Dict[str, Any]] = None

class LogAnalyzer:
    """Analizador de logs para MCP Code Manager"""
    
    def __init__(self, logs_dir: str = None):
        """
        Inicializa el analizador de logs
        
        Args:
            logs_dir: Directorio de logs. Si es None, usa ./logs
        """
        if logs_dir is None:
            # Obtener directorio del proyecto
            project_root = Path(__file__).parent.parent.parent
            logs_dir = project_root / "logs"
        
        self.logs_dir = Path(logs_dir)
    
    def parse_log_line(self, line: str) -> Optional[LogEntry]:
        """Parsea una línea de log"""
        # Patrón para logs: timestamp | level | logger | message
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s* \| ([\w.]+)\s* \| (.+)'
        
        match = re.match(pattern, line.strip())
        if not match:
            return None
        
        timestamp_str, level, logger_name, message = match.groups()
        
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None
        
        # Intentar parsear datos JSON en el mensaje
        parsed_data = None
        json_match = re.search(r'\{.*\}$', message)
        if json_match:
            try:
                parsed_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            logger_name=logger_name,
            message=message,
            raw_line=line,
            parsed_data=parsed_data
        )
    
    def read_log_file(self, filename: str, max_lines: int = None) -> List[LogEntry]:
        """Lee un archivo de log y devuelve las entradas parseadas"""
        log_file = self.logs_dir / filename
        
        if not log_file.exists():
            return []
        
        entries = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                if max_lines:
                    lines = lines[-max_lines:]  # Últimas N líneas
                
                for line in lines:
                    entry = self.parse_log_line(line)
                    if entry:
                        entries.append(entry)
        
        except Exception as e:
            print(f"Error leyendo archivo de log {filename}: {e}")
        
        return entries
    
    def get_recent_errors(self, hours: int = 24) -> List[LogEntry]:
        """Obtiene errores recientes"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        entries = self.read_log_file('errors.log')
        
        return [entry for entry in entries if entry.timestamp >= cutoff_time]
    
    def get_tool_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Obtiene estadísticas de ejecución de herramientas"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        entries = self.read_log_file('tools_execution.log')
        
        recent_entries = [entry for entry in entries if entry.timestamp >= cutoff_time]
        
        stats = {
            'total_executions': len(recent_entries),
            'successful_executions': 0,
            'failed_executions': 0,
            'tools_usage': {},
            'average_execution_time': 0,
            'slowest_tools': [],
            'most_used_tools': []
        }
        
        execution_times = []
        
        for entry in recent_entries:
            if entry.parsed_data:
                tool_name = entry.parsed_data.get('tool_name', 'unknown')
                success = entry.parsed_data.get('success', False)
                exec_time = entry.parsed_data.get('execution_time_ms', 0)
                
                if success:
                    stats['successful_executions'] += 1
                else:
                    stats['failed_executions'] += 1
                
                # Estadísticas por herramienta
                if tool_name not in stats['tools_usage']:
                    stats['tools_usage'][tool_name] = {
                        'count': 0,
                        'successes': 0,
                        'failures': 0,
                        'avg_time': 0,
                        'total_time': 0
                    }
                
                tool_stats = stats['tools_usage'][tool_name]
                tool_stats['count'] += 1
                tool_stats['total_time'] += exec_time
                
                if success:
                    tool_stats['successes'] += 1
                else:
                    tool_stats['failures'] += 1
                
                execution_times.append((tool_name, exec_time))
        
        # Calcular promedios
        if execution_times:
            stats['average_execution_time'] = sum(time for _, time in execution_times) / len(execution_times)
            
            # Herramientas más lentas
            execution_times.sort(key=lambda x: x[1], reverse=True)
            stats['slowest_tools'] = execution_times[:5]
        
        # Calcular promedios por herramienta
        for tool_name, tool_stats in stats['tools_usage'].items():
            if tool_stats['count'] > 0:
                tool_stats['avg_time'] = tool_stats['total_time'] / tool_stats['count']
        
        # Herramientas más usadas
        most_used = sorted(stats['tools_usage'].items(), key=lambda x: x[1]['count'], reverse=True)
        stats['most_used_tools'] = [(name, data['count']) for name, data in most_used[:10]]
        
        return stats
    
    def get_mcp_request_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Obtiene estadísticas de peticiones MCP"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        entries = self.read_log_file('mcp_requests.log')
        
        recent_entries = [entry for entry in entries if entry.timestamp >= cutoff_time]
        
        stats = {
            'total_requests': 0,
            'total_responses': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'methods_usage': {},
            'average_response_time': 0
        }
        
        response_times = []
        
        for entry in recent_entries:
            if entry.parsed_data:
                entry_type = entry.parsed_data.get('type')
                method = entry.parsed_data.get('method', 'unknown')
                
                if entry_type == 'request':
                    stats['total_requests'] += 1
                elif entry_type == 'response':
                    stats['total_responses'] += 1
                    success = entry.parsed_data.get('success', False)
                    exec_time = entry.parsed_data.get('execution_time_ms', 0)
                    
                    if success:
                        stats['successful_responses'] += 1
                    else:
                        stats['failed_responses'] += 1
                    
                    if exec_time:
                        response_times.append(exec_time)
                
                # Estadísticas por método
                if method not in stats['methods_usage']:
                    stats['methods_usage'][method] = 0
                stats['methods_usage'][method] += 1
        
        # Calcular tiempo promedio de respuesta
        if response_times:
            stats['average_response_time'] = sum(response_times) / len(response_times)
        
        return stats
    
    def search_logs(self, query: str, log_files: List[str] = None, max_results: int = 100) -> List[LogEntry]:
        """Busca en los logs por un término específico"""
        if log_files is None:
            log_files = ['mcp_requests.log', 'tools_execution.log', 'errors.log', 'debug.log']
        
        results = []
        query_lower = query.lower()
        
        for log_file in log_files:
            entries = self.read_log_file(log_file)
            
            for entry in entries:
                if query_lower in entry.message.lower():
                    results.append(entry)
                    
                    if len(results) >= max_results:
                        return results
        
        return results
    
    def export_log_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Exporta un resumen completo de los logs"""
        return {
            'timestamp': datetime.now().isoformat(),
            'period_hours': hours,
            'tool_stats': self.get_tool_stats(hours),
            'mcp_stats': self.get_mcp_request_stats(hours),
            'recent_errors': [
                {
                    'timestamp': entry.timestamp.isoformat(),
                    'message': entry.message,
                    'data': entry.parsed_data
                }
                for entry in self.get_recent_errors(hours)
            ]
        }

def get_log_analyzer(logs_dir: str = None) -> LogAnalyzer:
    """Obtiene una instancia del analizador de logs"""
    return LogAnalyzer(logs_dir)
