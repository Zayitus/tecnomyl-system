# expert/rules_preview.py - Sistema de preview de reglas
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from expert.inference_engine import InferenceEngine, SafeExpressionEvaluator

class RulesPreview:
    """Sistema para probar reglas antes de guardarlas"""
    
    def __init__(self):
        self.test_scenarios = self._generate_test_scenarios()
    
    def _generate_test_scenarios(self) -> List[Dict[str, Any]]:
        """Genera escenarios de prueba típicos"""
        base_date = datetime.now()
        
        return [
            {
                "name": "ART Normal",
                "description": "Ausencia ART típica con certificado",
                "facts": {
                    "motivo": "ART",
                    "duracion": 5,
                    "ausencias_ultimo_mes": 0,
                    "certificate_uploaded": True,
                    "certificate_deadline": base_date + timedelta(hours=24),
                    "validation_status": "validated",
                    "sector": "linea1",
                    "current_hour": 14
                }
            },
            {
                "name": "ART Sin Certificado",
                "description": "ART crítica sin certificado",
                "facts": {
                    "motivo": "ART",
                    "duracion": 8,
                    "ausencias_ultimo_mes": 1,
                    "certificate_uploaded": False,
                    "certificate_deadline": base_date - timedelta(hours=2),
                    "validation_status": "validated",
                    "sector": "linea1",
                    "current_hour": 10
                }
            },
            {
                "name": "Enfermedad Personal",
                "description": "Licencia enfermedad personal corta",
                "facts": {
                    "motivo": "Licencia Enfermedad Personal",
                    "duracion": 3,
                    "ausencias_ultimo_mes": 2,
                    "certificate_uploaded": False,
                    "certificate_deadline": base_date + timedelta(hours=48),
                    "validation_status": "validated",
                    "sector": "RH",
                    "current_hour": 9
                }
            },
            {
                "name": "Patrón Sospechoso",
                "description": "Empleado con muchas ausencias",
                "facts": {
                    "motivo": "Licencia Enfermedad Familiar",
                    "duracion": 2,
                    "ausencias_ultimo_mes": 5,
                    "certificate_uploaded": True,
                    "certificate_deadline": base_date + timedelta(hours=24),
                    "validation_status": "validated",
                    "sector": "linea2",
                    "current_hour": 15
                }
            },
            {
                "name": "Empleado Provisional",
                "description": "Empleado no validado",
                "facts": {
                    "motivo": "Permiso Gremial",
                    "duracion": 6,
                    "ausencias_ultimo_mes": 0,
                    "certificate_uploaded": False,
                    "certificate_deadline": None,
                    "validation_status": "provisional",
                    "sector": "Mantenimiento",
                    "current_hour": 11
                }
            },
            {
                "name": "Fin de Semana",
                "description": "Reporte en fin de semana",
                "facts": {
                    "motivo": "ART",
                    "duracion": 1,
                    "ausencias_ultimo_mes": 0,
                    "certificate_uploaded": False,
                    "certificate_deadline": base_date + timedelta(hours=24),
                    "validation_status": "validated",
                    "sector": "linea1",
                    "current_hour": 22  # Simular hora nocturna
                }
            }
        ]
    
    def preview_single_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prueba una regla individual contra escenarios"""
        results = {}
        
        for scenario in self.test_scenarios:
            # Crear facts con funciones especiales
            test_facts = scenario["facts"].copy()
            test_facts['hours_since'] = lambda date: (datetime.now() - date).total_seconds() / 3600 if date else 999
            test_facts['days_since'] = lambda date: (datetime.now() - date).days if date else 999
            test_facts['is_weekend'] = lambda: datetime.now().weekday() >= 5
            
            try:
                # Evaluar solo la condición de esta regla
                evaluator = SafeExpressionEvaluator(test_facts)
                condition_result = evaluator.evaluate(rule_data["condition"])
                
                results[scenario["name"]] = {
                    "description": scenario["description"],
                    "condition_met": bool(condition_result),
                    "would_fire": bool(condition_result),
                    "action_would_execute": rule_data.get("action", "") if condition_result else None,
                    "severity": rule_data.get("severity", "info") if condition_result else None
                }
                
            except Exception as e:
                results[scenario["name"]] = {
                    "description": scenario["description"],
                    "condition_met": False,
                    "would_fire": False,
                    "error": str(e)[:100]
                }
        
        return results
    
    def preview_rule_with_existing(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prueba una regla nueva junto con las existentes"""
        
        # Crear un motor temporal con todas las reglas incluyendo la nueva
        engine = InferenceEngine()
        
        # Cargar reglas existentes
        existing_rules = engine.rules.copy()
        
        # Agregar regla temporal
        temp_rule = {
            "id": rule_data.get("id", "temp_rule"),
            "name": rule_data.get("name", "Regla Temporal"),
            "condition": rule_data.get("condition", "true"),
            "action": rule_data.get("action", "add_observacion('temp')"),
            "priority": rule_data.get("priority", 999),
            "severity": rule_data.get("severity", "info"),
            "explanation": rule_data.get("explanation", "")
        }
        
        # Agregar a la lista
        all_rules = existing_rules + [temp_rule]
        
        # Simular motor temporal
        class TempEngine(InferenceEngine):
            def __init__(self, temp_rules):
                self.rules = sorted(temp_rules, key=lambda x: x.get('priority', 999))
                self.facts = {}
                self.inference_steps = []
        
        temp_engine = TempEngine(all_rules)
        
        scenario_results = {}
        
        for scenario in self.test_scenarios:
            try:
                # Ejecutar inferencia completa
                result = temp_engine.forward_chaining(scenario["facts"])
                
                # Verificar si nuestra regla se disparó
                our_rule_fired = any(
                    step.rule_id == temp_rule["id"] for step in result.steps
                )
                
                scenario_results[scenario["name"]] = {
                    "description": scenario["description"],
                    "total_rules_fired": len(result.steps),
                    "our_rule_fired": our_rule_fired,
                    "final_outcome": self._determine_outcome_preview(result.final_facts),
                    "conclusions": result.conclusions[:3],  # Top 3
                    "execution_time": result.execution_time
                }
                
            except Exception as e:
                scenario_results[scenario["name"]] = {
                    "description": scenario["description"],
                    "error": str(e)[:100]
                }
        
        return scenario_results
    
    def _determine_outcome_preview(self, final_facts: Dict[str, Any]) -> str:
        """Determina outcome para preview"""
        if final_facts.get('sancion_aplicada', False):
            return 'sanctioned'
        elif final_facts.get('requiere_aprobacion', False):
            return 'requires_approval'
        elif final_facts.get('observaciones', []):
            return 'approved_with_conditions'
        else:
            return 'auto_approved'
    
    def analyze_rule_conflicts(self, rule_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analiza posibles conflictos con reglas existentes"""
        engine = InferenceEngine()
        conflicts = []
        
        new_priority = rule_data.get("priority", 999)
        new_severity = rule_data.get("severity", "info")
        new_condition = rule_data.get("condition", "")
        
        for existing_rule in engine.rules:
            # Conflicto de prioridad
            if existing_rule.get("priority") == new_priority:
                conflicts.append({
                    "type": "priority_conflict",
                    "message": f"Misma prioridad que regla '{existing_rule.get('name')}'",
                    "severity": "warning",
                    "rule_id": existing_rule.get("id")
                })
            
            # Condiciones muy similares
            if self._conditions_similar(new_condition, existing_rule.get("condition", "")):
                conflicts.append({
                    "type": "similar_condition",
                    "message": f"Condición similar a regla '{existing_rule.get('name')}'",
                    "severity": "info",
                    "rule_id": existing_rule.get("id")
                })
            
            # Severidad inconsistente para condiciones similares
            if (self._conditions_overlap(new_condition, existing_rule.get("condition", "")) and
                new_severity != existing_rule.get("severity")):
                conflicts.append({
                    "type": "severity_inconsistency",
                    "message": f"Severidad diferente para caso similar: '{existing_rule.get('name')}'",
                    "severity": "warning",
                    "rule_id": existing_rule.get("id")
                })
        
        return conflicts
    
    def _conditions_similar(self, cond1: str, cond2: str) -> bool:
        """Verifica si dos condiciones son similares"""
        # Análisis básico de similitud
        if not cond1 or not cond2:
            return False
        
        # Extraer variables de ambas condiciones
        import re
        vars1 = set(re.findall(r'\b(motivo|duracion|ausencias_ultimo_mes|certificate_uploaded|validation_status)\b', cond1))
        vars2 = set(re.findall(r'\b(motivo|duracion|ausencias_ultimo_mes|certificate_uploaded|validation_status)\b', cond2))
        
        # Si comparten más del 70% de las variables, son similares
        if len(vars1.union(vars2)) > 0:
            similarity = len(vars1.intersection(vars2)) / len(vars1.union(vars2))
            return similarity > 0.7
        
        return False
    
    def _conditions_overlap(self, cond1: str, cond2: str) -> bool:
        """Verifica si dos condiciones podrían solaparse"""
        # Análisis básico de solapamiento
        # Por ejemplo, si ambas mencionan el mismo motivo
        import re
        
        motivos1 = re.findall(r"motivo\s*==\s*['\"]([^'\"]+)['\"]", cond1)
        motivos2 = re.findall(r"motivo\s*==\s*['\"]([^'\"]+)['\"]", cond2)
        
        return bool(set(motivos1).intersection(set(motivos2)))
    
    def get_recommendation(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera recomendaciones para mejorar la regla"""
        recommendations = []
        
        condition = rule_data.get("condition", "")
        priority = rule_data.get("priority", 999)
        severity = rule_data.get("severity", "info")
        
        # Recomendaciones de condición
        if "motivo" not in condition:
            recommendations.append({
                "type": "condition_improvement",
                "message": "Consider incluir 'motivo' en la condición para mayor especificidad",
                "severity": "info"
            })
        
        if "and" not in condition and "or" not in condition:
            recommendations.append({
                "type": "condition_complexity",
                "message": "Condición muy simple, considera agregar más criterios",
                "severity": "info"
            })
        
        # Recomendaciones de prioridad
        if priority > 80:
            recommendations.append({
                "type": "priority_suggestion",
                "message": "Prioridad muy baja (>80), esta regla se ejecutará al final",
                "severity": "warning"
            })
        elif priority < 5:
            recommendations.append({
                "type": "priority_suggestion", 
                "message": "Prioridad muy alta (<5), asegúrate de que es crítica",
                "severity": "warning"
            })
        
        # Recomendaciones de severidad
        if "certificado" in condition.lower() and severity != "error":
            recommendations.append({
                "type": "severity_suggestion",
                "message": "Reglas sobre certificados suelen ser 'error' por compliance",
                "severity": "info"
            })
        
        return {
            "recommendations": recommendations,
            "rule_quality_score": self._calculate_quality_score(rule_data),
            "estimated_frequency": self._estimate_firing_frequency(rule_data)
        }
    
    def _calculate_quality_score(self, rule_data: Dict[str, Any]) -> float:
        """Calcula un score de calidad de la regla (0-1)"""
        score = 0.5  # Base score
        
        condition = rule_data.get("condition", "")
        
        # Bonus por complejidad apropiada
        if "and" in condition or "or" in condition:
            score += 0.1
        
        # Bonus por incluir variables importantes
        important_vars = ["motivo", "duracion", "certificate_uploaded"]
        for var in important_vars:
            if var in condition:
                score += 0.1
        
        # Bonus por tener explicación
        if rule_data.get("explanation", "").strip():
            score += 0.1
        
        # Penalización por prioridad extrema
        priority = rule_data.get("priority", 50)
        if priority < 5 or priority > 90:
            score -= 0.1
        
        return min(1.0, max(0.0, score))
    
    def _estimate_firing_frequency(self, rule_data: Dict[str, Any]) -> str:
        """Estima con qué frecuencia se disparará la regla"""
        condition = rule_data.get("condition", "")
        
        # Análisis heurístico básico
        if "motivo" in condition and "ART" in condition:
            return "Media (ART representa ~20% de ausencias)"
        elif "ausencias_ultimo_mes >= 4" in condition:
            return "Baja (pocos empleados con 4+ ausencias)"
        elif "certificate_uploaded" in condition:
            return "Alta (muchas ausencias requieren certificado)"
        elif "validation_status == 'provisional'" in condition:
            return "Muy baja (pocos empleados no validados)"
        else:
            return "Desconocida (requiere más análisis)"

def test_rules_preview():
    """Función de prueba del sistema de preview"""
    print("[TEST] Sistema de Preview de Reglas")
    print("=" * 45)
    
    preview = RulesPreview()
    
    # Regla de prueba
    test_rule = {
        "id": "test_preview_rule",
        "name": "Prueba de Preview",
        "condition": "motivo == 'ART' and duracion > 3 and not certificate_uploaded",
        "action": "add_observacion('Certificado requerido para ART > 3 días')",
        "priority": 15,
        "severity": "error",
        "explanation": "Regla de prueba para el sistema de preview"
    }
    
    # 1. Preview individual
    print("\n[1] PREVIEW INDIVIDUAL:")
    individual_results = preview.preview_single_rule(test_rule)
    
    for scenario_name, result in individual_results.items():
        status = "[FIRE]" if result.get("would_fire", False) else "[SKIP]"
        print(f"  {status} {scenario_name}: {result.get('description', 'N/A')}")
        if result.get("error"):
            print(f"       ERROR: {result['error']}")
    
    # 2. Análisis de conflictos
    print("\n[2] ANÁLISIS DE CONFLICTOS:")
    conflicts = preview.analyze_rule_conflicts(test_rule)
    if conflicts:
        for conflict in conflicts:
            print(f"  [CONFLICT] {conflict['type']}: {conflict['message']}")
    else:
        print("  [OK] No se detectaron conflictos")
    
    # 3. Recomendaciones
    print("\n[3] RECOMENDACIONES:")
    recommendations = preview.get_recommendation(test_rule)
    print(f"  Score de calidad: {recommendations['rule_quality_score']:.2f}")
    print(f"  Frecuencia estimada: {recommendations['estimated_frequency']}")
    
    for rec in recommendations['recommendations']:
        print(f"  [{rec['severity'].upper()}] {rec['message']}")
    
    # 4. Preview con reglas existentes
    print("\n[4] PREVIEW CON SISTEMA COMPLETO:")
    full_results = preview.preview_rule_with_existing(test_rule)
    
    for scenario_name, result in full_results.items():
        if "error" not in result:
            fired = "[FIRED]" if result.get("our_rule_fired", False) else "[NOT FIRED]"
            total = result.get("total_rules_fired", 0)
            outcome = result.get("final_outcome", "unknown")
            print(f"  {fired} {scenario_name}: {total} reglas total, outcome: {outcome}")

if __name__ == "__main__":
    test_rules_preview()