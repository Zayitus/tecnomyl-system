# expert/explanation_system.py - Sistema de explicaciones detalladas
from typing import List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from expert.inference_engine import InferenceResult, InferenceStep

@dataclass
class ExplanationContext:
    """Contexto para generar explicaciones personalizadas"""
    user_type: str = "employee"  # employee, hr, supervisor, admin
    detail_level: str = "medium"  # basic, medium, detailed, technical
    language: str = "es"  # es, en
    include_technical: bool = False

class ExplanationGenerator:
    """Generador de explicaciones en lenguaje natural"""
    
    def __init__(self):
        self.templates = self._load_explanation_templates()
    
    def _load_explanation_templates(self) -> Dict[str, Dict[str, str]]:
        """Carga plantillas de explicaciones por idioma y nivel"""
        return {
            "es": {
                "rule_fired": "[OK] Se aplicó la regla '{rule_name}' porque {explanation}",
                "condition_met": "[COND] La condición '{condition}' se cumplió",
                "action_taken": "[ACTION] Acción ejecutada: {action_description}",
                "fact_used": "[DATA] Se utilizó el dato: {fact_name} = {fact_value}",
                "inference_summary": "[ENGINE] El sistema analizó {total_rules} reglas en {execution_time:.2f}s",
                "no_rules_fired": "[INFO] No se aplicaron reglas adicionales - el registro es normal",
                "chain_detected": "[CHAIN] Se detectó encadenamiento: regla {first_rule} activó {second_rule}",
                
                # Plantillas específicas por tipo de regla
                "cert_missing": "Se requiere certificado médico para este tipo de ausencia",
                "deadline_overdue": "El plazo para entregar documentos ha vencido",
                "duration_excessive": "La duración solicitada excede los límites normales",
                "pattern_detected": "Se detectó un patrón que requiere atención especial",
                "provisional_user": "El usuario no está completamente validado en el sistema",
                "approval_required": "Esta solicitud requiere aprobación adicional"
            },
            "en": {
                "rule_fired": "✅ Applied rule '{rule_name}' because {explanation}",
                "condition_met": "📋 Condition '{condition}' was satisfied",
                "action_taken": "⚡ Action executed: {action_description}",
                "fact_used": "📊 Used data: {fact_name} = {fact_value}",
                "inference_summary": "🧠 System analyzed {total_rules} rules in {execution_time:.2f}s",
                "no_rules_fired": "ℹ️ No additional rules applied - record is normal",
                "chain_detected": "🔗 Chain detected: rule {first_rule} triggered {second_rule}"
            }
        }
    
    def generate_explanation(self, 
                           inference_result: InferenceResult, 
                           context: ExplanationContext = None) -> str:
        """Genera explicación completa del razonamiento"""
        
        if context is None:
            context = ExplanationContext()
        
        templates = self.templates.get(context.language, self.templates["es"])
        explanation_parts = []
        
        # Resumen general
        if context.detail_level in ["medium", "detailed", "technical"]:
            summary = templates["inference_summary"].format(
                total_rules=len(inference_result.steps),
                execution_time=inference_result.execution_time
            )
            explanation_parts.append(summary)
        
        # Explicar cada paso
        if inference_result.steps:
            explanation_parts.append("\n[ANALYSIS] **Análisis detallado:**")
            
            for i, step in enumerate(inference_result.steps, 1):
                step_explanation = self._explain_step(step, context, templates, i)
                explanation_parts.append(step_explanation)
        else:
            explanation_parts.append(templates["no_rules_fired"])
        
        # Detectar encadenamiento
        chain_info = self._detect_rule_chaining(inference_result.steps)
        if chain_info and context.detail_level in ["detailed", "technical"]:
            explanation_parts.append(f"\n[CHAIN] **Encadenamiento detectado:**")
            for chain in chain_info:
                explanation_parts.append(f"   • {chain}")
        
        # Hechos finales relevantes (solo para nivel técnico)
        if context.detail_level == "technical" and context.include_technical:
            explanation_parts.append(self._explain_final_facts(inference_result.final_facts))
        
        return "\n".join(explanation_parts)
    
    def _explain_step(self, step: InferenceStep, context: ExplanationContext, 
                     templates: Dict[str, str], step_number: int) -> str:
        """Explica un paso individual del razonamiento"""
        
        explanation_parts = []
        
        # Título del paso
        explanation_parts.append(f"\n**{step_number}. {step.rule_name}**")
        
        # Explicación de la condición (adaptada al nivel de detalle)
        if context.detail_level == "basic":
            explanation_parts.append(f"   • Resultado: {'[OK] Aplicada' if step.condition_result else '[NO] No aplicada'}")
        
        elif context.detail_level == "medium":
            if step.condition_result:
                explanation_parts.append(f"   • [OK] Condición cumplida")
                explanation_parts.append(f"   • [ACTION] Acción: {self._humanize_action(step.action)}")
        
        elif context.detail_level in ["detailed", "technical"]:
            explanation_parts.append(f"   • [COND] Condición evaluada: `{step.condition}`")
            explanation_parts.append(f"   • [RESULT] Resultado: {step.condition_result}")
            
            if step.condition_result:
                explanation_parts.append(f"   • [ACTION] Acción ejecutada: `{step.action}`")
                explanation_parts.append(f"   • [TIME] Momento: {step.timestamp.strftime('%H:%M:%S')}")
                
                # Mostrar hechos utilizados (solo nivel técnico)
                if context.detail_level == "technical" and step.facts_used:
                    relevant_facts = self._get_relevant_facts(step.facts_used, step.condition)
                    if relevant_facts:
                        explanation_parts.append("   • [DATA] Datos utilizados:")
                        for fact, value in relevant_facts.items():
                            explanation_parts.append(f"     - {fact}: {value}")
        
        return "\n".join(explanation_parts)
    
    def _humanize_action(self, action: str) -> str:
        """Convierte acciones técnicas a lenguaje natural"""
        action_translations = {
            "add_observacion": "Agregar observación",
            "mark_sanction": "Marcar sanción",
            "require_approval": "Requerir aprobación",
            "set_fact": "Establecer dato",
        }
        
        action_type = action.split('(')[0].strip()
        return action_translations.get(action_type, action)
    
    def _get_relevant_facts(self, facts: Dict[str, Any], condition: str) -> Dict[str, Any]:
        """Extrae hechos relevantes para una condición específica"""
        # Identificar variables mencionadas en la condición
        import re
        variables = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', condition)
        
        relevant = {}
        for var in variables:
            if var in facts and not callable(facts[var]):
                relevant[var] = facts[var]
        
        return relevant
    
    def _detect_rule_chaining(self, steps: List[InferenceStep]) -> List[str]:
        """Detecta encadenamiento entre reglas"""
        chains = []
        
        for i, step in enumerate(steps[:-1]):
            # Buscar si esta regla estableció un hecho que activó la siguiente
            next_step = steps[i + 1]
            
            # Ejemplo de detección: si una regla establece rule_X_executed
            if f"rule_{step.rule_id}_executed" in next_step.condition:
                chains.append(f"'{step.rule_name}' activó '{next_step.rule_name}'")
            
            # Detección más sofisticada: si una acción establece un hecho usado en la siguiente regla
            if "set_fact" in step.action:
                # Extraer el nombre del hecho establecido
                fact_match = re.search(r"set_fact\(['\"](\w+)['\"]", step.action)
                if fact_match:
                    fact_name = fact_match.group(1)
                    if fact_name in next_step.condition:
                        chains.append(f"'{step.rule_name}' estableció '{fact_name}' usado por '{next_step.rule_name}'")
        
        return chains
    
    def _explain_final_facts(self, final_facts: Dict[str, Any]) -> str:
        """Explica el estado final de los hechos (nivel técnico)"""
        explanation = ["\n[SYSTEM] **Estado final del sistema:**"]
        
        # Filtrar hechos relevantes (no funciones ni datos internos)
        relevant_facts = {
            k: v for k, v in final_facts.items() 
            if not k.startswith('rule_') and not callable(v) and k not in ['now']
        }
        
        for fact, value in sorted(relevant_facts.items()):
            if isinstance(value, list) and value:  # Observaciones
                explanation.append(f"   • {fact}: {len(value)} elementos")
                for item in value:
                    if isinstance(item, dict) and 'message' in item:
                        explanation.append(f"     - {item['message']}")
            elif value is not None and value != "":
                explanation.append(f"   • {fact}: {value}")
        
        return "\n".join(explanation)
    
    def generate_summary(self, inference_result: InferenceResult, context: ExplanationContext = None) -> str:
        """Genera un resumen ejecutivo de las decisiones"""
        if context is None:
            context = ExplanationContext()
        
        if not inference_result.steps:
            return "[OK] El registro no requiere acciones especiales."
        
        summary_parts = []
        
        # Contar tipos de acciones
        warnings = sum(1 for step in inference_result.steps if any("warning" in str(fact) for fact in step.facts_used.values()))
        errors = sum(1 for step in inference_result.steps if any("error" in str(fact) for fact in step.facts_used.values()))
        
        # Mensaje principal
        if errors > 0:
            summary_parts.append(f"[ERROR] **{errors} problema(s) crítico(s) detectado(s)**")
        elif warnings > 0:
            summary_parts.append(f"[WARNING] **{warnings} observación(es) identificada(s)**")
        else:
            summary_parts.append("[INFO] **Registro procesado con observaciones menores**")
        
        # Lista de acciones tomadas
        if inference_result.actions_taken:
            summary_parts.append("**Acciones tomadas:**")
            for action in inference_result.actions_taken:
                summary_parts.append(f"• {action}")
        
        return "\n".join(summary_parts)

# Funciones de utilidad para integración
def explain_absence_processing(inference_result: InferenceResult, 
                             user_type: str = "employee") -> str:
    """Función de conveniencia para explicar el procesamiento de una ausencia"""
    
    context = ExplanationContext(
        user_type=user_type,
        detail_level="medium" if user_type == "employee" else "detailed",
        include_technical=(user_type in ["admin", "developer"])
    )
    
    generator = ExplanationGenerator()
    return generator.generate_explanation(inference_result, context)

def get_processing_summary(inference_result: InferenceResult) -> str:
    """Función de conveniencia para obtener un resumen ejecutivo"""
    generator = ExplanationGenerator()
    return generator.generate_summary(inference_result)

# Test del sistema de explicaciones
def test_explanation_system():
    """Prueba del sistema de explicaciones"""
    from expert.inference_engine import InferenceEngine
    from datetime import datetime, timedelta
    
    # Crear datos de prueba
    test_facts = {
        'motivo': 'ART',
        'duracion': 8,
        'certificate_uploaded': False,
        'certificate_deadline': datetime.now() - timedelta(hours=25),
        'validation_status': 'validated',
        'ausencias_ultimo_mes': 4
    }
    
    print("[TEST] Sistema de Explicaciones")
    print("=" * 50)
    
    # Ejecutar inferencia
    engine = InferenceEngine('expert/advanced_rules.json')
    result = engine.forward_chaining(test_facts)
    
    # Generar explicaciones para diferentes contextos
    contexts = [
        ("Empleado", ExplanationContext(user_type="employee", detail_level="medium")),
        ("RRHH", ExplanationContext(user_type="hr", detail_level="detailed")),
        ("Técnico", ExplanationContext(user_type="admin", detail_level="technical", include_technical=True))
    ]
    
    generator = ExplanationGenerator()
    
    for context_name, context in contexts:
        print(f"\n[{context_name.upper()}] Explicacion para {context_name}:")
        print("-" * 40)
        explanation = generator.generate_explanation(result, context)
        print(explanation)
    
    print(f"\n[RESUMEN] Resumen Ejecutivo:")
    print("-" * 40)
    summary = generator.generate_summary(result)
    print(summary)

if __name__ == "__main__":
    test_explanation_system()