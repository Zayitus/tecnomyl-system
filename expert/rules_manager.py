# expert/rules_manager.py - Gestor de reglas con validaciones
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from expert.inference_engine import SafeExpressionEvaluator

class RulesManager:
    """Gestor para crear, editar y validar reglas del sistema experto"""
    
    def __init__(self, rules_file: str = 'expert/advanced_rules.json'):
        self.rules_file = rules_file
        self.backup_dir = 'expert/backups'
        self._ensure_backup_dir()
        
        # Acciones permitidas para usuarios no técnicos
        self.allowed_actions = [
            'add_observacion',
            'mark_sanction', 
            'require_approval',
            'set_fact'
        ]
        
        # Variables permitidas en condiciones
        self.allowed_variables = [
            'motivo', 'duracion', 'ausencias_ultimo_mes', 'certificate_uploaded',
            'certificate_deadline', 'validation_status', 'sector', 'current_hour',
            'is_weekend', 'hours_since', 'days_since'
        ]
        
        # Valores válidos para motivo
        self.valid_motivos = [
            'ART', 'Licencia Enfermedad Personal', 'Licencia Enfermedad Familiar',
            'Licencia por Fallecimiento Familiar', 'Licencia por Matrimonio',
            'Licencia por Nacimiento', 'Licencia por Paternidad', 'Permiso Gremial'
        ]
    
    def _ensure_backup_dir(self):
        """Asegura que el directorio de backups existe"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def _create_backup(self) -> str:
        """Crea backup del archivo de reglas actual"""
        if not os.path.exists(self.rules_file):
            return None
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"rules_backup_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        shutil.copy2(self.rules_file, backup_path)
        return backup_path
    
    def load_rules(self) -> Dict[str, Any]:
        """Carga las reglas desde el archivo JSON"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando reglas: {e}")
            return {"rules": [], "metadata": {}}
    
    def save_rules(self, rules_data: Dict[str, Any]) -> bool:
        """Guarda las reglas al archivo JSON con backup"""
        try:
            # Crear backup antes de guardar
            backup_path = self._create_backup()
            if backup_path:
                print(f"[RULES] Backup creado: {backup_path}")
            
            # Actualizar metadata
            rules_data["metadata"]["last_updated"] = datetime.now().strftime('%Y-%m-%d')
            rules_data["metadata"]["total_rules"] = len(rules_data.get("rules", []))
            
            # Guardar archivo
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
            
            print(f"[RULES] Reglas guardadas exitosamente")
            return True
        
        except Exception as e:
            print(f"[RULES] Error guardando reglas: {e}")
            return False
    
    def validate_rule_id(self, rule_id: str, existing_rules: List[Dict]) -> Tuple[bool, str]:
        """Valida que el ID de regla sea único y válido"""
        if not rule_id or not rule_id.strip():
            return False, "ID de regla no puede estar vacío"
        
        if not rule_id.replace('_', '').replace('-', '').isalnum():
            return False, "ID debe contener solo letras, números, guiones y guiones bajos"
        
        if len(rule_id) > 50:
            return False, "ID no puede exceder 50 caracteres"
        
        # Verificar unicidad
        if any(rule.get("id") == rule_id for rule in existing_rules):
            return False, f"Ya existe una regla con ID '{rule_id}'"
        
        return True, "ID válido"
    
    def validate_condition(self, condition: str) -> Tuple[bool, str]:
        """Valida la sintaxis y seguridad de una condición"""
        if not condition or not condition.strip():
            return False, "Condición no puede estar vacía"
        
        # Test facts para validación
        test_facts = {
            'motivo': 'ART',
            'duracion': 5,
            'ausencias_ultimo_mes': 2,
            'certificate_uploaded': False,
            'certificate_deadline': datetime.now(),
            'validation_status': 'validated',
            'sector': 'linea1',
            'current_hour': 14
        }
        
        # Agregar funciones especiales para testing
        test_facts['hours_since'] = lambda x: 24
        test_facts['days_since'] = lambda x: 1
        test_facts['is_weekend'] = lambda: False
        
        try:
            # Intentar evaluar la condición
            evaluator = SafeExpressionEvaluator(test_facts)
            result = evaluator.evaluate(condition)
            
            if result is False:  # False es un resultado válido
                return True, "Condición válida (evalúa a False)"
            elif result is True:  # True es un resultado válido
                return True, "Condición válida (evalúa a True)"
            elif isinstance(result, bool):  # Cualquier otro booleano
                return True, "Condición válida"
            else:
                return False, "La condición debe evaluar a True/False"
            
        except Exception as e:
            return False, f"Error en condición: {str(e)[:100]}"
    
    def validate_action(self, action: str) -> Tuple[bool, str]:
        """Valida que la acción sea segura y permitida"""
        if not action or not action.strip():
            return False, "Acción no puede estar vacía"
        
        # Verificar formato función(argumentos)
        if '(' not in action or ')' not in action:
            return False, "Acción debe tener formato: función('argumentos')"
        
        # Extraer nombre de función
        func_name = action.split('(')[0].strip()
        
        if func_name not in self.allowed_actions:
            return False, f"Acción '{func_name}' no permitida. Permitidas: {', '.join(self.allowed_actions)}"
        
        # Validaciones específicas por acción
        if func_name == 'add_observacion':
            if not ("'" in action or '"' in action):
                return False, "add_observacion requiere un mensaje entre comillas"
        
        elif func_name == 'set_fact':
            # set_fact('nombre_hecho', 'valor')
            if action.count(',') != 1:
                return False, "set_fact requiere exactamente 2 argumentos: nombre y valor"
        
        return True, "Acción válida"
    
    def validate_priority(self, priority: int, existing_rules: List[Dict]) -> Tuple[bool, str]:
        """Valida la prioridad de la regla"""
        if not isinstance(priority, int):
            return False, "Prioridad debe ser un número entero"
        
        if priority < 1 or priority > 100:
            return False, "Prioridad debe estar entre 1 y 100"
        
        # Advertir si hay conflicto de prioridades
        existing_priorities = [rule.get("priority", 999) for rule in existing_rules]
        if priority in existing_priorities:
            return True, f"Advertencia: Ya existe una regla con prioridad {priority}"
        
        return True, "Prioridad válida"
    
    def validate_severity(self, severity: str) -> Tuple[bool, str]:
        """Valida el nivel de severidad"""
        valid_severities = ['info', 'warning', 'error']
        
        if severity not in valid_severities:
            return False, f"Severidad debe ser una de: {', '.join(valid_severities)}"
        
        return True, "Severidad válida"
    
    def add_rule(self, rule_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Agrega una nueva regla con validaciones completas"""
        
        # Cargar reglas existentes
        rules_json = self.load_rules()
        existing_rules = rules_json.get("rules", [])
        
        # Validar todos los campos
        validations = [
            self.validate_rule_id(rule_data.get("id", ""), existing_rules),
            self.validate_condition(rule_data.get("condition", "")),
            self.validate_action(rule_data.get("action", "")),
            self.validate_priority(rule_data.get("priority", 0), existing_rules),
            self.validate_severity(rule_data.get("severity", ""))
        ]
        
        # Verificar si hay errores
        for valid, message in validations:
            if not valid:
                return False, message
        
        # Crear nueva regla
        new_rule = {
            "id": rule_data["id"].strip(),
            "name": rule_data.get("name", "").strip(),
            "condition": rule_data["condition"].strip(),
            "action": rule_data["action"].strip(),
            "priority": int(rule_data["priority"]),
            "severity": rule_data["severity"],
            "explanation": rule_data.get("explanation", "").strip(),
            "created_by": rule_data.get("created_by", "system"),
            "created_at": datetime.now().isoformat()
        }
        
        # Agregar a la lista
        rules_json["rules"].append(new_rule)
        
        # Ordenar por prioridad
        rules_json["rules"].sort(key=lambda x: x.get("priority", 999))
        
        # Guardar
        if self.save_rules(rules_json):
            return True, f"Regla '{new_rule['id']}' agregada exitosamente"
        else:
            return False, "Error al guardar el archivo de reglas"
    
    def edit_rule(self, rule_id: str, updated_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Edita una regla existente"""
        
        # Cargar reglas
        rules_json = self.load_rules()
        rules = rules_json.get("rules", [])
        
        # Buscar regla a editar
        rule_index = None
        for i, rule in enumerate(rules):
            if rule.get("id") == rule_id:
                rule_index = i
                break
        
        if rule_index is None:
            return False, f"Regla con ID '{rule_id}' no encontrada"
        
        # Validar cambios (excluyendo ID actual de validación de unicidad)
        other_rules = rules[:rule_index] + rules[rule_index + 1:]
        
        validations = []
        if "condition" in updated_data:
            validations.append(self.validate_condition(updated_data["condition"]))
        if "action" in updated_data:
            validations.append(self.validate_action(updated_data["action"]))
        if "priority" in updated_data:
            validations.append(self.validate_priority(updated_data["priority"], other_rules))
        if "severity" in updated_data:
            validations.append(self.validate_severity(updated_data["severity"]))
        
        # Verificar errores
        for valid, message in validations:
            if not valid:
                return False, message
        
        # Actualizar regla
        rules[rule_index].update(updated_data)
        rules[rule_index]["updated_at"] = datetime.now().isoformat()
        
        # Reordenar por prioridad si cambió
        if "priority" in updated_data:
            rules.sort(key=lambda x: x.get("priority", 999))
        
        # Guardar
        if self.save_rules(rules_json):
            return True, f"Regla '{rule_id}' actualizada exitosamente"
        else:
            return False, "Error al guardar cambios"
    
    def delete_rule(self, rule_id: str) -> Tuple[bool, str]:
        """Elimina una regla"""
        
        # Cargar reglas
        rules_json = self.load_rules()
        rules = rules_json.get("rules", [])
        
        # Buscar y eliminar regla
        initial_count = len(rules)
        rules_json["rules"] = [rule for rule in rules if rule.get("id") != rule_id]
        
        if len(rules_json["rules"]) == initial_count:
            return False, f"Regla con ID '{rule_id}' no encontrada"
        
        # Guardar
        if self.save_rules(rules_json):
            return True, f"Regla '{rule_id}' eliminada exitosamente"
        else:
            return False, "Error al guardar cambios"
    
    def get_rule_suggestions(self) -> Dict[str, Any]:
        """Proporciona sugerencias para crear reglas"""
        return {
            "motivos_validos": self.valid_motivos,
            "variables_disponibles": self.allowed_variables,
            "acciones_permitidas": self.allowed_actions,
            "ejemplos_condiciones": [
                "motivo == 'ART'",
                "duracion > 5",
                "ausencias_ultimo_mes >= 3",
                "not certificate_uploaded",
                "motivo in ['ART', 'Licencia Enfermedad Personal']",
                "duracion > 3 and not certificate_uploaded",
                "hours_since(certificate_deadline) > 0"
            ],
            "ejemplos_acciones": [
                "add_observacion('Certificado requerido')",
                "mark_sanction()",
                "require_approval()",
                "set_fact('riesgo_empleado', 'alto')"
            ]
        }
    
    def get_rules_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de las reglas"""
        rules_json = self.load_rules()
        rules = rules_json.get("rules", [])
        
        if not rules:
            return {"total": 0}
        
        severity_count = {}
        priority_range = []
        
        for rule in rules:
            severity = rule.get("severity", "unknown")
            severity_count[severity] = severity_count.get(severity, 0) + 1
            priority_range.append(rule.get("priority", 999))
        
        return {
            "total": len(rules),
            "severity_distribution": severity_count,
            "priority_range": {
                "min": min(priority_range) if priority_range else 0,
                "max": max(priority_range) if priority_range else 0
            },
            "last_updated": rules_json.get("metadata", {}).get("last_updated", "unknown"),
            "backups_available": len([f for f in os.listdir(self.backup_dir) 
                                    if f.startswith("rules_backup_")])
        }

def test_rules_manager():
    """Función de prueba del gestor de reglas"""
    print("[TEST] Gestor de Reglas")
    print("=" * 40)
    
    manager = RulesManager()
    
    # Test 1: Agregar regla válida
    print("\n[ADD] Probando agregar regla válida...")
    test_rule = {
        "id": "test_rule_demo",
        "name": "Regla de Prueba",
        "condition": "motivo == 'ART' and duracion > 5",
        "action": "add_observacion('Regla de prueba disparada')",
        "priority": 99,
        "severity": "info",
        "explanation": "Regla creada para testing del sistema",
        "created_by": "test_user"
    }
    
    success, message = manager.add_rule(test_rule)
    print(f"  Resultado: {message}")
    
    # Test 2: Intentar agregar regla con ID duplicado
    print("\n[ADD] Probando regla con ID duplicado...")
    success, message = manager.add_rule(test_rule)
    print(f"  Resultado: {message}")
    
    # Test 3: Validar condición inválida
    print("\n[VALIDATE] Probando condición inválida...")
    invalid_rule = test_rule.copy()
    invalid_rule["id"] = "test_invalid"
    invalid_rule["condition"] = "motivo === 'ART'"  # Sintaxis incorrecta
    
    success, message = manager.add_rule(invalid_rule)
    print(f"  Resultado: {message}")
    
    # Test 4: Editar regla
    print("\n[EDIT] Probando editar regla...")
    success, message = manager.edit_rule("test_rule_demo", {
        "name": "Regla de Prueba Editada",
        "priority": 95
    })
    print(f"  Resultado: {message}")
    
    # Test 5: Obtener estadísticas
    print("\n[STATS] Estadísticas de reglas:")
    stats = manager.get_rules_stats()
    print(f"  Total reglas: {stats['total']}")
    print(f"  Distribución severidad: {stats['severity_distribution']}")
    print(f"  Backups disponibles: {stats['backups_available']}")
    
    # Test 6: Obtener sugerencias
    print("\n[SUGGESTIONS] Sugerencias para usuarios:")
    suggestions = manager.get_rule_suggestions()
    print(f"  Acciones permitidas: {suggestions['acciones_permitidas']}")
    print(f"  Ejemplos de condiciones:")
    for example in suggestions['ejemplos_condiciones'][:3]:
        print(f"    - {example}")
    
    # Cleanup - eliminar regla de prueba
    print("\n[CLEANUP] Eliminando regla de prueba...")
    success, message = manager.delete_rule("test_rule_demo")
    print(f"  Resultado: {message}")

if __name__ == "__main__":
    test_rules_manager()