# expert/integrated_expert_system.py - Sistema experto integrado
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from expert.inference_engine import InferenceEngine, InferenceResult
from expert.explanation_system import ExplanationGenerator, ExplanationContext, explain_absence_processing
from expert.case_based_learning import CaseBasedLearning

class IntegratedExpertSystem:
    """Sistema experto completo que integra inferencia, explicaciones y aprendizaje"""
    
    def __init__(self, rules_file: str = 'expert/advanced_rules.json', 
                 database_path: str = 'test.db'):
        self.inference_engine = InferenceEngine(rules_file)
        self.explanation_generator = ExplanationGenerator()
        self.cbr_system = CaseBasedLearning(database_path)
        self.processing_history = []
    
    def process_absence_request(self, absence_facts: Dict[str, Any], 
                              user_type: str = 'employee') -> Dict[str, Any]:
        """Procesa una solicitud de ausencia completa con todas las funcionalidades"""
        
        print(f"[EXPERT] Procesando solicitud de ausencia...")
        processing_start = datetime.now()
        
        # 1. Obtener recomendaciones del sistema CBR
        cbr_recommendations = self.cbr_system.get_recommendations(absence_facts)
        print(f"[CBR] Encontrados {cbr_recommendations['similar_cases_count']} casos similares")
        
        # 2. Ejecutar motor de inferencia
        inference_result = self.inference_engine.forward_chaining(absence_facts)
        print(f"[INFERENCE] {len(inference_result.steps)} reglas disparadas")
        
        # 3. Determinar outcome basado en reglas e inferencia
        outcome = self._determine_outcome(inference_result, absence_facts)
        
        # 4. Generar explicación adaptada al usuario
        explanation_context = ExplanationContext(
            user_type=user_type,
            detail_level='medium' if user_type == 'employee' else 'detailed',
            include_technical=(user_type in ['admin', 'developer'])
        )
        explanation = self.explanation_generator.generate_explanation(
            inference_result, explanation_context
        )
        
        # 5. Almacenar caso para aprendizaje futuro
        case_id = self.cbr_system.store_case(
            facts=absence_facts,
            rules_applied=[step.rule_id for step in inference_result.steps],
            actions_taken=inference_result.actions_taken,
            outcome=outcome
        )
        
        # 6. Compilar resultado completo
        result = {
            'case_id': case_id,
            'outcome': outcome,
            'processing_time': (datetime.now() - processing_start).total_seconds(),
            'inference_result': {
                'rules_triggered': len(inference_result.steps),
                'conclusions': inference_result.conclusions,
                'actions_taken': inference_result.actions_taken,
                'execution_time': inference_result.execution_time
            },
            'cbr_analysis': {
                'similar_cases_found': cbr_recommendations['similar_cases_count'],
                'confidence': cbr_recommendations['confidence'],
                'recommendations': cbr_recommendations['recommendations'][:2],  # Top 2
                'predicted_outcome': cbr_recommendations['recommendations'][0]['suggestion'] if cbr_recommendations['recommendations'] else None
            },
            'explanation': explanation,
            'system_observations': self._extract_observations(inference_result.final_facts),
            'requires_human_review': self._requires_human_review(inference_result, cbr_recommendations),
            'risk_level': self._assess_risk_level(inference_result.final_facts),
            'next_actions': self._suggest_next_actions(outcome, inference_result.final_facts)
        }
        
        # 7. Registrar en historial
        self.processing_history.append({
            'timestamp': processing_start,
            'case_id': case_id,
            'outcome': outcome,
            'user_type': user_type
        })
        
        print(f"[EXPERT] Procesamiento completado: {outcome}")
        return result
    
    def _determine_outcome(self, inference_result: InferenceResult, 
                         facts: Dict[str, Any]) -> str:
        """Determina el outcome basado en reglas e inferencia"""
        
        final_facts = inference_result.final_facts
        
        # Outcome basado en sanciones y aprobaciones
        if final_facts.get('sancion_aplicada', False):
            return 'sanctioned'
        elif final_facts.get('requiere_aprobacion', False):
            return 'requires_approval'
        elif len(inference_result.steps) == 0:
            return 'auto_approved'
        elif any('error' in step.rule_name.lower() or 'crítico' in step.rule_name.lower() 
                for step in inference_result.steps):
            return 'rejected'
        elif len(inference_result.steps) > 0:
            return 'approved_with_conditions'
        else:
            return 'approved'
    
    def _extract_observations(self, final_facts: Dict[str, Any]) -> List[str]:
        """Extrae observaciones del sistema del estado final"""
        observations = []
        
        observaciones_list = final_facts.get('observaciones', [])
        if isinstance(observaciones_list, list):
            for obs in observaciones_list:
                if isinstance(obs, dict) and 'message' in obs:
                    severity = obs.get('severity', 'info')
                    message = obs['message']
                    observations.append(f"[{severity.upper()}] {message}")
                elif isinstance(obs, str):
                    observations.append(f"[INFO] {obs}")
        
        # Agregar otras observaciones relevantes
        if final_facts.get('sancion_aplicada'):
            motivo = final_facts.get('sancion_motivo', 'Regla del sistema')
            observations.append(f"[SANCTION] Sanción aplicada: {motivo}")
        
        if final_facts.get('requiere_aprobacion'):
            motivo = final_facts.get('aprobacion_motivo', 'Regla del sistema')
            observations.append(f"[APPROVAL] Requiere aprobación: {motivo}")
        
        return observations
    
    def _requires_human_review(self, inference_result: InferenceResult, 
                             cbr_recommendations: Dict[str, Any]) -> bool:
        """Determina si requiere revisión humana"""
        
        # Si hay sanciones o aprobaciones requeridas
        if inference_result.final_facts.get('sancion_aplicada', False):
            return True
        if inference_result.final_facts.get('requiere_aprobacion', False):
            return True
        
        # Si el CBR tiene baja confianza
        if cbr_recommendations['confidence'] < 0.5:
            return True
        
        # Si hay muchas reglas disparadas (caso complejo)
        if len(inference_result.steps) >= 4:
            return True
        
        return False
    
    def _assess_risk_level(self, final_facts: Dict[str, Any]) -> str:
        """Evalúa el nivel de riesgo del caso"""
        
        risk_score = 0
        
        # Factores de riesgo
        if final_facts.get('sancion_aplicada', False):
            risk_score += 3
        
        if final_facts.get('riesgo_empleado') == 'alto':
            risk_score += 2
        
        ausencias = final_facts.get('ausencias_ultimo_mes', 0)
        if ausencias >= 4:
            risk_score += 2
        elif ausencias >= 3:
            risk_score += 1
        
        if not final_facts.get('certificate_uploaded', True):
            risk_score += 1
        
        # Clasificación de riesgo
        if risk_score >= 5:
            return 'HIGH'
        elif risk_score >= 3:
            return 'MEDIUM'
        elif risk_score >= 1:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _suggest_next_actions(self, outcome: str, final_facts: Dict[str, Any]) -> List[str]:
        """Sugiere próximas acciones basadas en el outcome"""
        
        actions = []
        
        if outcome == 'sanctioned':
            actions.append("Notificar sanción al empleado y RRHH")
            actions.append("Documentar en expediente personal")
        
        elif outcome == 'requires_approval':
            actions.append("Escalar a supervisor para aprobación")
            actions.append("Establecer plazo para decisión")
        
        elif outcome == 'rejected':
            actions.append("Notificar rechazo con explicación detallada")
            actions.append("Ofrecer alternativas si aplica")
        
        elif outcome == 'approved_with_conditions':
            actions.append("Aprobar con observaciones indicadas")
            if not final_facts.get('certificate_uploaded', True):
                actions.append("Solicitar certificado médico pendiente")
        
        elif outcome == 'auto_approved':
            actions.append("Procesar aprobación automática")
            actions.append("Enviar confirmación al empleado")
        
        # Acciones adicionales por contexto
        if final_facts.get('ausencias_ultimo_mes', 0) >= 3:
            actions.append("Programar seguimiento con RRHH")
        
        return actions
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema integrado"""
        
        # Estadísticas CBR
        cbr_stats = self.cbr_system.get_learning_stats()
        
        # Estadísticas de procesamiento reciente
        recent_processing = len(self.processing_history)
        
        # Distribución de outcomes recientes
        outcomes = [entry['outcome'] for entry in self.processing_history[-50:]]
        outcome_dist = {outcome: outcomes.count(outcome) for outcome in set(outcomes)}
        
        return {
            'system_version': '2.0',
            'components': {
                'inference_engine': 'active',
                'explanation_system': 'active', 
                'case_based_learning': 'active' if cbr_stats['learning_active'] else 'training'
            },
            'processing_stats': {
                'total_processed': recent_processing,
                'outcome_distribution': outcome_dist
            },
            'learning_stats': cbr_stats,
            'system_health': 'operational'
        }
    
    def provide_feedback(self, case_id: str, feedback: str, 
                        expert_validation: bool = False) -> bool:
        """Proporciona feedback sobre un caso para mejorar el aprendizaje"""
        try:
            self.cbr_system.update_case_feedback(case_id, feedback, expert_validation)
            print(f"[EXPERT] Feedback registrado para caso {case_id}")
            return True
        except Exception as e:
            print(f"[EXPERT] Error registrando feedback: {e}")
            return False

def test_integrated_system():
    """Prueba del sistema experto integrado"""
    print("[TEST] Sistema Experto Integrado")
    print("=" * 50)
    
    expert_system = IntegratedExpertSystem()
    
    # Caso de prueba complejo
    test_case = {
        'motivo': 'ART',
        'duracion': 12,
        'ausencias_ultimo_mes': 3,
        'certificate_uploaded': False,
        'certificate_deadline': datetime.now() - timedelta(hours=48),
        'validation_status': 'validated',
        'sector': 'linea1'
    }
    
    print(f"\n[INPUT] Procesando caso de prueba:")
    print(f"  Motivo: {test_case['motivo']}")
    print(f"  Duración: {test_case['duracion']} días")
    print(f"  Ausencias recientes: {test_case['ausencias_ultimo_mes']}")
    print(f"  Certificado: {'Subido' if test_case['certificate_uploaded'] else 'Faltante'}")
    
    # Procesar con diferentes tipos de usuario
    for user_type in ['employee', 'hr', 'admin']:
        print(f"\n[PROCESSING] Procesando para usuario: {user_type}")
        print("-" * 40)
        
        result = expert_system.process_absence_request(test_case, user_type)
        
        print(f"  Caso ID: {result['case_id']}")
        print(f"  Outcome: {result['outcome']}")
        print(f"  Nivel de riesgo: {result['risk_level']}")
        print(f"  Requiere revisión: {result['requires_human_review']}")
        print(f"  Tiempo procesamiento: {result['processing_time']:.3f}s")
        
        print(f"  Análisis CBR:")
        print(f"    - Casos similares: {result['cbr_analysis']['similar_cases_found']}")
        print(f"    - Confianza: {result['cbr_analysis']['confidence']:.2f}")
        
        print(f"  Observaciones del sistema:")
        for obs in result['system_observations'][:3]:  # Top 3
            print(f"    - {obs}")
        
        print(f"  Próximas acciones:")
        for action in result['next_actions'][:2]:  # Top 2
            print(f"    > {action}")
    
    # Estadísticas del sistema
    print(f"\n[STATS] Estadísticas del sistema:")
    stats = expert_system.get_system_stats()
    print(f"  Versión: {stats['system_version']}")
    print(f"  Componentes activos: {list(stats['components'].keys())}")
    print(f"  Salud del sistema: {stats['system_health']}")
    print(f"  Casos procesados: {stats['processing_stats']['total_processed']}")

if __name__ == "__main__":
    from datetime import timedelta
    test_integrated_system()