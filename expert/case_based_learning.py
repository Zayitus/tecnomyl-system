# expert/case_based_learning.py - Sistema de aprendizaje basado en casos
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import hashlib
import numpy as np
from collections import defaultdict

@dataclass
class Case:
    """Representa un caso de ausencia procesado"""
    case_id: str
    facts: Dict[str, Any]
    rules_applied: List[str]
    actions_taken: List[str]
    outcome: str  # 'approved', 'rejected', 'escalated', 'sanctioned'
    feedback: Optional[str] = None
    similarity_features: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    expert_validation: bool = False

@dataclass
class SimilarCase:
    """Caso similar con score de similitud"""
    case: Case
    similarity_score: float
    matching_features: List[str]

class CaseBasedLearning:
    """Sistema de aprendizaje basado en casos CBR"""
    
    def __init__(self, database_path: str = 'test.db'):
        self.database_path = database_path
        self.cases = []
        self.feature_weights = self._load_feature_weights()
        self._load_cases_from_db()
    
    def _load_feature_weights(self) -> Dict[str, float]:
        """Carga pesos de características para similitud"""
        return {
            'motivo': 0.25,
            'duracion': 0.20,
            'ausencias_ultimo_mes': 0.15,
            'validation_status': 0.10,
            'certificate_uploaded': 0.15,
            'sector': 0.10,
            'deadline_exceeded': 0.05
        }
    
    def _load_cases_from_db(self):
        """Carga casos existentes desde la base de datos"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Crear tabla de casos si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT UNIQUE NOT NULL,
                    facts TEXT NOT NULL,
                    rules_applied TEXT NOT NULL,
                    actions_taken TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    feedback TEXT,
                    similarity_features TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    expert_validation BOOLEAN DEFAULT 0
                );
            """)
            
            # Cargar casos existentes
            cursor.execute("SELECT * FROM cases ORDER BY timestamp DESC LIMIT 1000")
            rows = cursor.fetchall()
            
            for row in rows:
                case = Case(
                    case_id=row[1],
                    facts=json.loads(row[2]),
                    rules_applied=json.loads(row[3]),
                    actions_taken=json.loads(row[4]),
                    outcome=row[5],
                    feedback=row[6],
                    similarity_features=json.loads(row[7]),
                    timestamp=datetime.fromisoformat(row[8]),
                    expert_validation=bool(row[9])
                )
                self.cases.append(case)
            
            conn.close()
            print(f"[CBR] Cargados {len(self.cases)} casos desde BD")
            
        except Exception as e:
            print(f"[CBR] Error cargando casos: {e}")
            self.cases = []
    
    def extract_features(self, facts: Dict[str, Any]) -> Dict[str, float]:
        """Extrae características numéricas para comparación"""
        features = {}
        
        # Mapeo de motivos a números
        motivo_map = {
            'ART': 1.0, 'Licencia Enfermedad Personal': 2.0,
            'Licencia Enfermedad Familiar': 3.0, 'Licencia por Fallecimiento Familiar': 4.0,
            'Licencia por Matrimonio': 5.0, 'Licencia por Paternidad': 6.0,
            'Licencia por Nacimiento': 7.0, 'Permiso Gremial': 8.0
        }
        
        # Características principales
        features['motivo'] = motivo_map.get(facts.get('motivo', ''), 0.0)
        features['duracion'] = float(facts.get('duracion', 0))
        features['ausencias_ultimo_mes'] = float(facts.get('ausencias_ultimo_mes', 0))
        features['certificate_uploaded'] = 1.0 if facts.get('certificate_uploaded', False) else 0.0
        features['validation_status'] = 1.0 if facts.get('validation_status') == 'validated' else 0.5
        
        # Características derivadas
        cert_deadline = facts.get('certificate_deadline')
        if cert_deadline and isinstance(cert_deadline, datetime):
            hours_overdue = (datetime.now() - cert_deadline).total_seconds() / 3600
            features['deadline_exceeded'] = max(0.0, hours_overdue / 24.0)  # Días de retraso
        else:
            features['deadline_exceeded'] = 0.0
        
        # Sector (simplificado)
        sector_map = {'linea1': 1.0, 'linea2': 2.0, 'Mantenimiento': 3.0, 'RH': 4.0}
        features['sector'] = sector_map.get(facts.get('sector', ''), 0.0)
        
        return features
    
    def calculate_similarity(self, features1: Dict[str, float], 
                           features2: Dict[str, float]) -> float:
        """Calcula similitud entre dos conjuntos de características"""
        if not features1 or not features2:
            return 0.0
        
        similarity = 0.0
        total_weight = 0.0
        
        for feature, weight in self.feature_weights.items():
            if feature in features1 and feature in features2:
                val1, val2 = features1[feature], features2[feature]
                
                if feature == 'motivo':
                    # Similitud exacta para motivo
                    feature_sim = 1.0 if val1 == val2 else 0.0
                elif feature in ['certificate_uploaded', 'validation_status']:
                    # Similitud binaria/categórica
                    feature_sim = 1.0 if val1 == val2 else 0.0
                else:
                    # Similitud numérica normalizada
                    max_val = max(val1, val2, 1.0)  # Evitar división por 0
                    feature_sim = 1.0 - abs(val1 - val2) / max_val
                
                similarity += feature_sim * weight
                total_weight += weight
        
        return similarity / total_weight if total_weight > 0 else 0.0
    
    def find_similar_cases(self, current_facts: Dict[str, Any], 
                          top_k: int = 5, min_similarity: float = 0.3) -> List[SimilarCase]:
        """Encuentra casos similares al actual"""
        if not self.cases:
            return []
        
        current_features = self.extract_features(current_facts)
        similar_cases = []
        
        for case in self.cases:
            similarity = self.calculate_similarity(current_features, case.similarity_features)
            
            if similarity >= min_similarity:
                # Identificar características coincidentes
                matching_features = []
                for feature, weight in self.feature_weights.items():
                    if (feature in current_features and feature in case.similarity_features):
                        if feature == 'motivo':
                            if current_features[feature] == case.similarity_features[feature]:
                                matching_features.append(feature)
                        elif abs(current_features[feature] - case.similarity_features[feature]) < 0.1:
                            matching_features.append(feature)
                
                similar_cases.append(SimilarCase(
                    case=case,
                    similarity_score=similarity,
                    matching_features=matching_features
                ))
        
        # Ordenar por similitud descendente
        similar_cases.sort(key=lambda x: x.similarity_score, reverse=True)
        return similar_cases[:top_k]
    
    def store_case(self, facts: Dict[str, Any], rules_applied: List[str],
                   actions_taken: List[str], outcome: str) -> str:
        """Almacena un nuevo caso en el sistema"""
        
        # Preparar facts para serialización (convertir datetime a string)
        serializable_facts = {}
        for key, value in facts.items():
            if isinstance(value, datetime):
                serializable_facts[key] = value.isoformat()
            else:
                serializable_facts[key] = value
        
        # Generar ID único del caso
        case_content = json.dumps({
            'facts': serializable_facts,
            'rules': sorted(rules_applied),
            'actions': sorted(actions_taken)
        }, sort_keys=True)
        case_id = hashlib.md5(case_content.encode()).hexdigest()[:12]
        
        # Extraer características
        similarity_features = self.extract_features(facts)
        
        # Crear caso
        new_case = Case(
            case_id=case_id,
            facts=serializable_facts.copy(),
            rules_applied=rules_applied.copy(),
            actions_taken=actions_taken.copy(),
            outcome=outcome,
            similarity_features=similarity_features,
            timestamp=datetime.now()
        )
        
        # Almacenar en memoria
        self.cases.append(new_case)
        
        # Almacenar en BD
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO cases 
                (case_id, facts, rules_applied, actions_taken, outcome, 
                 similarity_features, timestamp, expert_validation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_id,
                json.dumps(serializable_facts),
                json.dumps(rules_applied),
                json.dumps(actions_taken),
                outcome,
                json.dumps(similarity_features),
                new_case.timestamp.isoformat(),
                False
            ))
            
            conn.commit()
            conn.close()
            print(f"[CBR] Caso almacenado: {case_id}")
            
        except Exception as e:
            print(f"[CBR] Error almacenando caso: {e}")
        
        return case_id
    
    def get_recommendations(self, current_facts: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene recomendaciones basadas en casos similares"""
        similar_cases = self.find_similar_cases(current_facts, top_k=5, min_similarity=0.4)
        
        if not similar_cases:
            return {
                'recommendations': [],
                'confidence': 0.0,
                'similar_cases_count': 0,
                'reasoning': 'No se encontraron casos similares suficientes'
            }
        
        # Análisis de patrones en casos similares
        outcome_counts = defaultdict(int)
        action_counts = defaultdict(int)
        rule_counts = defaultdict(int)
        
        total_similarity = 0.0
        for similar_case in similar_cases:
            weight = similar_case.similarity_score
            total_similarity += weight
            
            outcome_counts[similar_case.case.outcome] += weight
            
            for action in similar_case.case.actions_taken:
                action_counts[action] += weight
            
            for rule in similar_case.case.rules_applied:
                rule_counts[rule] += weight
        
        # Recomendación de outcome más probable
        most_likely_outcome = max(outcome_counts.items(), key=lambda x: x[1])
        confidence = most_likely_outcome[1] / total_similarity
        
        # Top acciones recomendadas
        top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Top reglas relevantes
        top_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        recommendations = []
        
        # Recomendación principal
        recommendations.append({
            'type': 'outcome_prediction',
            'suggestion': f"Outcome más probable: {most_likely_outcome[0]}",
            'confidence': confidence,
            'reasoning': f"Basado en {len(similar_cases)} casos similares"
        })
        
        # Recomendaciones de acciones
        if top_actions:
            recommendations.append({
                'type': 'action_suggestion',
                'suggestion': f"Acción recomendada: {top_actions[0][0]}",
                'confidence': top_actions[0][1] / total_similarity,
                'reasoning': f"Presente en casos similares con alta frecuencia"
            })
        
        # Alertas de patrones
        if confidence > 0.8:
            recommendations.append({
                'type': 'pattern_alert',
                'suggestion': "Patrón muy consistente detectado",
                'confidence': confidence,
                'reasoning': "Los casos similares muestran un resultado muy consistente"
            })
        
        return {
            'recommendations': recommendations,
            'confidence': confidence,
            'similar_cases_count': len(similar_cases),
            'reasoning': f'Análisis basado en {len(similar_cases)} casos con similitud promedio {total_similarity/len(similar_cases):.2f}',
            'similar_cases': [
                {
                    'case_id': sc.case.case_id,
                    'similarity': sc.similarity_score,
                    'outcome': sc.case.outcome,
                    'matching_features': sc.matching_features,
                    'timestamp': sc.case.timestamp.isoformat()
                }
                for sc in similar_cases
            ]
        }
    
    def update_case_feedback(self, case_id: str, feedback: str, 
                           expert_validation: bool = False):
        """Actualiza feedback de un caso para aprendizaje"""
        try:
            # Actualizar en memoria
            for case in self.cases:
                if case.case_id == case_id:
                    case.feedback = feedback
                    case.expert_validation = expert_validation
                    break
            
            # Actualizar en BD
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE cases 
                SET feedback = ?, expert_validation = ?
                WHERE case_id = ?
            """, (feedback, expert_validation, case_id))
            
            conn.commit()
            conn.close()
            print(f"[CBR] Feedback actualizado para caso: {case_id}")
            
        except Exception as e:
            print(f"[CBR] Error actualizando feedback: {e}")
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del aprendizaje"""
        if not self.cases:
            return {'total_cases': 0}
        
        outcome_dist = defaultdict(int)
        validated_cases = 0
        recent_cases = 0
        
        week_ago = datetime.now() - timedelta(days=7)
        
        for case in self.cases:
            outcome_dist[case.outcome] += 1
            if case.expert_validation:
                validated_cases += 1
            if case.timestamp >= week_ago:
                recent_cases += 1
        
        return {
            'total_cases': len(self.cases),
            'validated_cases': validated_cases,
            'validation_rate': validated_cases / len(self.cases),
            'recent_cases_week': recent_cases,
            'outcome_distribution': dict(outcome_dist),
            'feature_weights': self.feature_weights,
            'learning_active': len(self.cases) >= 10
        }

def test_case_based_learning():
    """Función de prueba del sistema CBR"""
    print("[TEST] Sistema de Aprendizaje Basado en Casos")
    print("=" * 55)
    
    cbr = CaseBasedLearning()
    
    # Casos de ejemplo para poblar el sistema
    sample_cases = [
        {
            'facts': {
                'motivo': 'ART', 'duracion': 5, 'ausencias_ultimo_mes': 1,
                'certificate_uploaded': False, 'validation_status': 'validated', 'sector': 'linea1'
            },
            'rules': ['cert_missing_critical'],
            'actions': ['add_observacion'],
            'outcome': 'approved_with_warning'
        },
        {
            'facts': {
                'motivo': 'ART', 'duracion': 10, 'ausencias_ultimo_mes': 3,
                'certificate_uploaded': False, 'validation_status': 'validated', 'sector': 'linea1'
            },
            'rules': ['cert_missing_critical', 'frequent_absences_pattern'],
            'actions': ['add_observacion', 'require_approval'],
            'outcome': 'escalated'
        },
        {
            'facts': {
                'motivo': 'Licencia Enfermedad Personal', 'duracion': 7, 'ausencias_ultimo_mes': 2,
                'certificate_uploaded': True, 'validation_status': 'validated', 'sector': 'RH'
            },
            'rules': [],
            'actions': [],
            'outcome': 'approved'
        }
    ]
    
    # Almacenar casos de ejemplo
    print("\n[STORAGE] Almacenando casos de ejemplo...")
    case_ids = []
    for i, case_data in enumerate(sample_cases):
        case_id = cbr.store_case(
            case_data['facts'],
            case_data['rules'],
            case_data['actions'],
            case_data['outcome']
        )
        case_ids.append(case_id)
        print(f"  Caso {i+1}: {case_id}")
    
    # Caso actual para análisis
    current_case = {
        'motivo': 'ART',
        'duracion': 8,
        'ausencias_ultimo_mes': 2,
        'certificate_uploaded': False,
        'validation_status': 'validated',
        'sector': 'linea1'
    }
    
    print(f"\n[ANALYSIS] Analizando caso actual:")
    print(f"  Motivo: {current_case['motivo']}")
    print(f"  Duración: {current_case['duracion']} días")
    print(f"  Ausencias recientes: {current_case['ausencias_ultimo_mes']}")
    
    # Obtener recomendaciones
    recommendations = cbr.get_recommendations(current_case)
    
    print(f"\n[RECOMMENDATIONS] Recomendaciones del sistema CBR:")
    print(f"  Casos similares encontrados: {recommendations['similar_cases_count']}")
    print(f"  Confianza general: {recommendations['confidence']:.2f}")
    print(f"  Razonamiento: {recommendations['reasoning']}")
    
    for i, rec in enumerate(recommendations['recommendations'], 1):
        print(f"  {i}. [{rec['type'].upper()}] {rec['suggestion']}")
        print(f"     Confianza: {rec['confidence']:.2f} | {rec['reasoning']}")
    
    if recommendations['similar_cases']:
        print(f"\n[SIMILAR_CASES] Casos más similares:")
        for sc in recommendations['similar_cases'][:3]:
            print(f"  • Caso {sc['case_id']}: similitud {sc['similarity']:.2f}")
            print(f"    Outcome: {sc['outcome']} | Features: {', '.join(sc['matching_features'])}")
    
    # Estadísticas del sistema
    stats = cbr.get_learning_stats()
    print(f"\n[STATS] Estadísticas del aprendizaje:")
    print(f"  Total casos: {stats['total_cases']}")
    print(f"  Casos validados: {stats['validated_cases']}")
    print(f"  Distribución outcomes: {stats['outcome_distribution']}")
    print(f"  Aprendizaje activo: {stats['learning_active']}")

if __name__ == "__main__":
    test_case_based_learning()