# expert/rules_monitoring.py - Sistema de monitoreo de reglas
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import json
from expert.rules_manager import RulesManager

class RulesMonitoring:
    """Sistema de monitoreo y análisis de reglas activas"""
    
    def __init__(self, database_path: str = 'test.db'):
        self.database_path = database_path
        self.rules_manager = RulesManager()
        self._ensure_monitoring_tables()
    
    def _ensure_monitoring_tables(self):
        """Crea tablas de monitoreo si no existen"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Tabla de ejecuciones de reglas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rule_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                executed_at DATETIME NOT NULL,
                case_facts TEXT NOT NULL,              -- JSON con los hechos del caso
                condition_result BOOLEAN NOT NULL,
                action_executed TEXT,
                execution_time_ms REAL NOT NULL,
                absence_id INTEGER,                    -- FK a tabla absences si existe
                FOREIGN KEY (absence_id) REFERENCES absences (id)
            )
        """)
        
        # Tabla de estadísticas agregadas de reglas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rule_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                date DATE NOT NULL,
                executions_count INTEGER DEFAULT 0,
                successful_executions INTEGER DEFAULT 0,
                avg_execution_time_ms REAL DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(rule_id, date)
            )
        """)
        
        conn.commit()
        conn.close()
        print("[MONITORING] Tablas de monitoreo inicializadas")
    
    def log_rule_execution(self, rule_id: str, rule_name: str, 
                          case_facts: Dict[str, Any], condition_result: bool,
                          action_executed: str, execution_time_ms: float,
                          absence_id: Optional[int] = None):
        """Registra la ejecución de una regla"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO rule_executions 
                (rule_id, rule_name, executed_at, case_facts, condition_result, 
                 action_executed, execution_time_ms, absence_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule_id, rule_name, datetime.now().isoformat(),
                json.dumps(case_facts), condition_result, action_executed,
                execution_time_ms, absence_id
            ))
            
            # Actualizar estadísticas agregadas
            today = datetime.now().date().isoformat()
            cursor.execute("""
                INSERT OR REPLACE INTO rule_stats 
                (rule_id, date, executions_count, successful_executions, avg_execution_time_ms, last_updated)
                VALUES (
                    ?, ?, 
                    COALESCE((SELECT executions_count FROM rule_stats WHERE rule_id = ? AND date = ?), 0) + 1,
                    COALESCE((SELECT successful_executions FROM rule_stats WHERE rule_id = ? AND date = ?), 0) + ?,
                    (COALESCE((SELECT avg_execution_time_ms * executions_count FROM rule_stats WHERE rule_id = ? AND date = ?), 0) + ?) / 
                     (COALESCE((SELECT executions_count FROM rule_stats WHERE rule_id = ? AND date = ?), 0) + 1),
                    ?
                )
            """, (
                rule_id, today, rule_id, today, rule_id, today,
                1 if condition_result else 0, rule_id, today,
                execution_time_ms, rule_id, today, datetime.now().isoformat()
            ))
            
            conn.commit()
        
        except Exception as e:
            print(f"[MONITORING] Error registrando ejecución: {e}")
        finally:
            conn.close()
    
    def get_rules_dashboard(self, days: int = 7) -> Dict[str, Any]:
        """Obtiene dashboard completo de reglas"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "overview": self._get_overview_stats(start_date, end_date),
            "top_rules": self._get_top_firing_rules(start_date, end_date),
            "performance": self._get_performance_stats(start_date, end_date),
            "patterns": self._get_execution_patterns(start_date, end_date),
            "alerts": self._get_system_alerts(start_date, end_date),
            "rule_health": self._get_rule_health_status()
        }
    
    def _get_overview_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Obtiene estadísticas generales"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Total reglas activas
        rules_data = self.rules_manager.load_rules()
        total_rules = len(rules_data.get("rules", []))
        
        # Execuciones en el período
        cursor.execute("""
            SELECT 
                COUNT(*) as total_executions,
                SUM(CASE WHEN condition_result = 1 THEN 1 ELSE 0 END) as successful_executions,
                COUNT(DISTINCT rule_id) as active_rules,
                AVG(execution_time_ms) as avg_execution_time
            FROM rule_executions 
            WHERE executed_at BETWEEN ? AND ?
        """, (start_date.isoformat(), end_date.isoformat()))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return {
                "total_rules": total_rules,
                "active_rules": result[2] or 0,
                "inactive_rules": total_rules - (result[2] or 0),
                "total_executions": result[0] or 0,
                "successful_executions": result[1] or 0,
                "success_rate": (result[1] or 0) / (result[0] or 1) * 100,
                "avg_execution_time": round(result[3] or 0, 2)
            }
        
        return {
            "total_rules": total_rules,
            "active_rules": 0,
            "inactive_rules": total_rules,
            "total_executions": 0,
            "successful_executions": 0,
            "success_rate": 0,
            "avg_execution_time": 0
        }
    
    def _get_top_firing_rules(self, start_date: datetime, end_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene las reglas que más se ejecutan"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                rule_id,
                rule_name,
                COUNT(*) as total_executions,
                SUM(CASE WHEN condition_result = 1 THEN 1 ELSE 0 END) as successful_executions,
                AVG(execution_time_ms) as avg_execution_time,
                MAX(executed_at) as last_execution
            FROM rule_executions 
            WHERE executed_at BETWEEN ? AND ?
            GROUP BY rule_id, rule_name
            ORDER BY total_executions DESC
            LIMIT ?
        """, (start_date.isoformat(), end_date.isoformat(), limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "rule_id": row[0],
                "rule_name": row[1],
                "total_executions": row[2],
                "successful_executions": row[3],
                "success_rate": (row[3] / row[2] * 100) if row[2] > 0 else 0,
                "avg_execution_time": round(row[4], 2),
                "last_execution": row[5]
            })
        
        conn.close()
        return results
    
    def _get_performance_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Obtiene estadísticas de performance"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                MIN(execution_time_ms) as min_time,
                MAX(execution_time_ms) as max_time,
                AVG(execution_time_ms) as avg_time,
                COUNT(CASE WHEN execution_time_ms > 100 THEN 1 END) as slow_executions
            FROM rule_executions 
            WHERE executed_at BETWEEN ? AND ?
        """, (start_date.isoformat(), end_date.isoformat()))
        
        result = cursor.fetchone()
        
        if result and result[0] is not None:
            total_executions = cursor.execute("""
                SELECT COUNT(*) FROM rule_executions 
                WHERE executed_at BETWEEN ? AND ?
            """, (start_date.isoformat(), end_date.isoformat())).fetchone()[0]
            
            conn.close()
            
            return {
                "min_execution_time": round(result[0], 2),
                "max_execution_time": round(result[1], 2),
                "avg_execution_time": round(result[2], 2),
                "slow_executions": result[3] or 0,
                "slow_execution_rate": ((result[3] or 0) / (total_executions or 1)) * 100
            }
        
        conn.close()
        return {
            "min_execution_time": 0,
            "max_execution_time": 0,
            "avg_execution_time": 0,
            "slow_executions": 0,
            "slow_execution_rate": 0
        }
    
    def _get_execution_patterns(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analiza patrones de ejecución"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Execuciones por hora del día
        cursor.execute("""
            SELECT 
                strftime('%H', executed_at) as hour,
                COUNT(*) as executions
            FROM rule_executions 
            WHERE executed_at BETWEEN ? AND ?
            GROUP BY hour
            ORDER BY hour
        """, (start_date.isoformat(), end_date.isoformat()))
        
        hourly_pattern = {str(i).zfill(2): 0 for i in range(24)}
        for hour, count in cursor.fetchall():
            hourly_pattern[hour] = count
        
        # Execuciones por día de la semana
        cursor.execute("""
            SELECT 
                strftime('%w', executed_at) as day_of_week,
                COUNT(*) as executions
            FROM rule_executions 
            WHERE executed_at BETWEEN ? AND ?
            GROUP BY day_of_week
        """, (start_date.isoformat(), end_date.isoformat()))
        
        days_names = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        weekly_pattern = {day: 0 for day in days_names}
        
        for day_num, count in cursor.fetchall():
            day_name = days_names[int(day_num)]
            weekly_pattern[day_name] = count
        
        conn.close()
        
        return {
            "hourly_distribution": hourly_pattern,
            "weekly_distribution": weekly_pattern,
            "peak_hour": max(hourly_pattern.items(), key=lambda x: x[1])[0] if any(hourly_pattern.values()) else "00",
            "peak_day": max(weekly_pattern.items(), key=lambda x: x[1])[0] if any(weekly_pattern.values()) else "N/A"
        }
    
    def _get_system_alerts(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Genera alertas del sistema"""
        alerts = []
        
        # Alertas de performance
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Reglas muy lentas
        cursor.execute("""
            SELECT rule_id, rule_name, AVG(execution_time_ms) as avg_time
            FROM rule_executions 
            WHERE executed_at BETWEEN ? AND ?
            GROUP BY rule_id, rule_name
            HAVING AVG(execution_time_ms) > 50
        """, (start_date.isoformat(), end_date.isoformat()))
        
        for rule_id, rule_name, avg_time in cursor.fetchall():
            alerts.append({
                "type": "performance",
                "severity": "warning",
                "message": f"Regla '{rule_name}' ejecutándose lentamente ({avg_time:.1f}ms promedio)",
                "rule_id": rule_id,
                "timestamp": datetime.now().isoformat()
            })
        
        # Reglas que nunca se ejecutan
        rules_data = self.rules_manager.load_rules()
        active_rule_ids = set()
        
        cursor.execute("""
            SELECT DISTINCT rule_id FROM rule_executions 
            WHERE executed_at BETWEEN ? AND ?
        """, (start_date.isoformat(), end_date.isoformat()))
        
        active_rule_ids = {row[0] for row in cursor.fetchall()}
        
        for rule in rules_data.get("rules", []):
            if rule.get("id") not in active_rule_ids:
                alerts.append({
                    "type": "unused_rule",
                    "severity": "info",
                    "message": f"Regla '{rule.get('name')}' no se ha ejecutado en {(end_date - start_date).days} días",
                    "rule_id": rule.get("id"),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Reglas con baja tasa de éxito
        cursor.execute("""
            SELECT 
                rule_id, rule_name,
                COUNT(*) as total,
                SUM(CASE WHEN condition_result = 1 THEN 1 ELSE 0 END) as successful
            FROM rule_executions 
            WHERE executed_at BETWEEN ? AND ?
            GROUP BY rule_id, rule_name
            HAVING COUNT(*) > 10 AND 
                   (SUM(CASE WHEN condition_result = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) < 0.1
        """, (start_date.isoformat(), end_date.isoformat()))
        
        for rule_id, rule_name, total, successful in cursor.fetchall():
            success_rate = (successful / total) * 100
            alerts.append({
                "type": "low_success_rate",
                "severity": "warning",
                "message": f"Regla '{rule_name}' con baja tasa de éxito ({success_rate:.1f}%)",
                "rule_id": rule_id,
                "timestamp": datetime.now().isoformat()
            })
        
        conn.close()
        return sorted(alerts, key=lambda x: x["severity"] == "warning", reverse=True)
    
    def _get_rule_health_status(self) -> Dict[str, Any]:
        """Obtiene estado de salud general del sistema de reglas"""
        rules_data = self.rules_manager.load_rules()
        total_rules = len(rules_data.get("rules", []))
        
        # Análisis de configuración
        priority_conflicts = self._check_priority_conflicts()
        syntax_issues = self._check_syntax_issues()
        
        # Score de salud general
        health_score = 100
        
        if priority_conflicts:
            health_score -= len(priority_conflicts) * 5
        
        if syntax_issues:
            health_score -= len(syntax_issues) * 10
        
        health_score = max(0, min(100, health_score))
        
        # Estado general
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 75:
            status = "good"
        elif health_score >= 50:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "overall_health_score": health_score,
            "status": status,
            "total_rules": total_rules,
            "priority_conflicts": len(priority_conflicts),
            "syntax_issues": len(syntax_issues),
            "last_backup": self._get_last_backup_date(),
            "recommendations": self._generate_health_recommendations()
        }
    
    def _check_priority_conflicts(self) -> List[Dict[str, Any]]:
        """Verifica conflictos de prioridad"""
        rules_data = self.rules_manager.load_rules()
        rules = rules_data.get("rules", [])
        
        priority_map = defaultdict(list)
        for rule in rules:
            priority = rule.get("priority", 999)
            priority_map[priority].append(rule.get("id", "unknown"))
        
        conflicts = []
        for priority, rule_ids in priority_map.items():
            if len(rule_ids) > 1:
                conflicts.append({
                    "priority": priority,
                    "rule_ids": rule_ids,
                    "count": len(rule_ids)
                })
        
        return conflicts
    
    def _check_syntax_issues(self) -> List[Dict[str, Any]]:
        """Verifica problemas de sintaxis en reglas"""
        rules_data = self.rules_manager.load_rules()
        issues = []
        
        for rule in rules_data.get("rules", []):
            # Verificar con el validador
            valid, message = self.rules_manager.validate_condition(rule.get("condition", ""))
            if not valid:
                issues.append({
                    "rule_id": rule.get("id"),
                    "rule_name": rule.get("name"),
                    "issue": message
                })
        
        return issues
    
    def _get_last_backup_date(self) -> str:
        """Obtiene fecha del último backup"""
        import os
        backup_dir = "expert/backups"
        
        if not os.path.exists(backup_dir):
            return "never"
        
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("rules_backup_")]
        
        if not backup_files:
            return "never"
        
        latest_backup = max(backup_files)
        # Extraer fecha del nombre del archivo
        try:
            date_part = latest_backup.replace("rules_backup_", "").replace(".json", "")
            return datetime.strptime(date_part, "%Y%m%d_%H%M%S").isoformat()
        except:
            return "unknown"
    
    def _generate_health_recommendations(self) -> List[str]:
        """Genera recomendaciones para mejorar la salud del sistema"""
        recommendations = []
        
        # Verificar backups recientes
        last_backup = self._get_last_backup_date()
        if last_backup == "never":
            recommendations.append("Realizar backup del sistema de reglas")
        
        # Verificar conflictos de prioridad
        conflicts = self._check_priority_conflicts()
        if conflicts:
            recommendations.append(f"Resolver {len(conflicts)} conflictos de prioridad")
        
        # Verificar sintaxis
        syntax_issues = self._check_syntax_issues()
        if syntax_issues:
            recommendations.append(f"Corregir {len(syntax_issues)} problemas de sintaxis")
        
        if not recommendations:
            recommendations.append("Sistema en buen estado - mantener monitoreo regular")
        
        return recommendations

def test_rules_monitoring():
    """Función de prueba del sistema de monitoreo"""
    print("[TEST] Sistema de Monitoreo de Reglas")
    print("=" * 45)
    
    monitoring = RulesMonitoring()
    
    # Simular algunas ejecuciones
    print("\n[1] SIMULANDO EJECUCIONES DE REGLAS:")
    import random
    from datetime import datetime, timedelta
    
    rules_data = monitoring.rules_manager.load_rules()
    rules = rules_data.get("rules", [])[:5]  # Tomar 5 reglas
    
    for i in range(20):  # Simular 20 ejecuciones
        rule = random.choice(rules)
        monitoring.log_rule_execution(
            rule_id=rule.get("id"),
            rule_name=rule.get("name"),
            case_facts={"motivo": "ART", "duracion": random.randint(1, 10)},
            condition_result=random.choice([True, False]),
            action_executed=rule.get("action", ""),
            execution_time_ms=random.uniform(1, 50)
        )
    
    print("  20 ejecuciones simuladas")
    
    # Obtener dashboard
    print("\n[2] DASHBOARD DE MONITOREO:")
    dashboard = monitoring.get_rules_dashboard(days=1)
    
    overview = dashboard["overview"]
    print(f"  Total reglas: {overview['total_rules']}")
    print(f"  Reglas activas: {overview['active_rules']}")
    print(f"  Ejecuciones totales: {overview['total_executions']}")
    print(f"  Tasa de éxito: {overview['success_rate']:.1f}%")
    print(f"  Tiempo promedio: {overview['avg_execution_time']:.2f}ms")
    
    # Top reglas
    print("\n[3] REGLAS MÁS EJECUTADAS:")
    for rule in dashboard["top_rules"][:3]:
        print(f"  • {rule['rule_name']}: {rule['total_executions']} ejecuciones")
    
    # Alertas
    print("\n[4] ALERTAS DEL SISTEMA:")
    alerts = dashboard["alerts"]
    if alerts:
        for alert in alerts[:3]:
            print(f"  [{alert['severity'].upper()}] {alert['message']}")
    else:
        print("  No hay alertas activas")
    
    # Salud del sistema
    print("\n[5] SALUD DEL SISTEMA:")
    health = dashboard["rule_health"]
    print(f"  Score: {health['overall_health_score']}/100")
    print(f"  Estado: {health['status']}")
    print(f"  Recomendaciones: {len(health['recommendations'])}")

if __name__ == "__main__":
    test_rules_monitoring()