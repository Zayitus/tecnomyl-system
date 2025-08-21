# expert/engine.py - Motor del sistema experto mejorado
import json
from datetime import datetime, timedelta
from models.database import SessionLocal, Absence

class ExpertSystem:
    def __init__(self):
        self.rules_data = self.load_rules()
        self.rules = self.rules_data.get('rules', [])
        self.motivo_rules = self.rules_data.get('motivo_rules', {})
    
    def load_rules(self):
        """Carga las reglas desde el archivo JSON"""
        try:
            with open('expert/rules.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando reglas: {e}")
            return {'rules': [], 'motivo_rules': {}}
    
    def evaluate_absence(self, absence):
        """Evalúa una ausencia contra todas las reglas del sistema experto"""
        findings = []
        
        for rule in sorted(self.rules, key=lambda x: x['priority']):
            result = self._check_rule(rule, absence)
            if result:
                findings.append(result)
        
        return findings
    
    def _check_rule(self, rule, absence):
        """Verifica si una regla específica aplica a una ausencia"""
        condition = rule['condition']
        
        # Regla: Certificado obligatorio
        if rule['id'] == 'certificate_required':
            if (absence.motivo in condition['motivo'] and 
                not absence.certificate_uploaded):
                return {
                    'rule_id': rule['id'],
                    'rule_name': rule['name'],
                    'message': rule['message'],
                    'severity': rule['severity'],
                    'action': rule['action']
                }
        
        # Regla: Deadline de certificado vencido
        elif rule['id'] == 'certificate_deadline':
            if (absence.certificate_deadline and 
                datetime.now() > absence.certificate_deadline and
                not absence.certificate_uploaded):
                return {
                    'rule_id': rule['id'],
                    'rule_name': rule['name'],
                    'message': rule['message'],
                    'severity': rule['severity'],
                    'action': rule['action']
                }
        
        # Regla: Duración excesiva
        elif rule['id'] == 'excessive_duration':
            max_duration = condition.get(absence.motivo)
            if max_duration and absence.duracion > max_duration:
                return {
                    'rule_id': rule['id'],
                    'rule_name': rule['name'],
                    'message': f"{rule['message']} (máximo: {max_duration} días, actual: {absence.duracion})",
                    'severity': rule['severity'],
                    'action': rule['action']
                }
        
        # Regla: Empleado provisional
        elif rule['id'] == 'provisional_employee':
            if absence.validation_status == 'provisional':
                return {
                    'rule_id': rule['id'],
                    'rule_name': rule['name'],
                    'message': rule['message'],
                    'severity': rule['severity'],
                    'action': rule['action']
                }
        
        # Regla: Ausencias frecuentes
        elif rule['id'] == 'frequent_absences':
            count = self._count_recent_absences(absence.chat_id)
            if count > 3:
                return {
                    'rule_id': rule['id'],
                    'rule_name': rule['name'],
                    'message': f"{rule['message']} ({count} ausencias en 30 días)",
                    'severity': rule['severity'],
                    'action': rule['action']
                }
        
        return None
    
    def _count_recent_absences(self, chat_id):
        """Cuenta ausencias recientes de un usuario"""
        db = SessionLocal()
        try:
            fecha_limite = datetime.now() - timedelta(days=30)
            return db.query(Absence).filter(
                Absence.chat_id == chat_id,
                Absence.created_at >= fecha_limite
            ).count()
        finally:
            db.close()
    
    def apply_expert_rules(self, absence_id):
        """Aplica las reglas del sistema experto a una ausencia y actualiza observaciones"""
        db = SessionLocal()
        try:
            absence = db.query(Absence).filter(Absence.id == absence_id).first()
            if not absence:
                return []
            
            findings = self.evaluate_absence(absence)
            
            # Actualizar observaciones en la base de datos
            observations = []
            sanctions = False
            
            for finding in findings:
                observations.append(f"[{finding['severity'].upper()}] {finding['message']}")
                
                if finding['action'] == 'mark_sanction':
                    sanctions = True
            
            if observations:
                absence.observaciones = " | ".join(observations)
                absence.sancion_aplicada = sanctions
                db.commit()
                
                print(f"[EXPERT] Reglas aplicadas a ausencia {absence_id}:")
                for obs in observations:
                    print(f"  - {obs}")
            
            return findings
            
        except Exception as e:
            print(f"Error aplicando reglas: {e}")
            return []
        finally:
            db.close()
    
    def validate_motivo_rules(self, motivo, duracion):
        """Valida una ausencia contra las reglas de motivo"""
        if motivo not in self.motivo_rules:
            return {
                'valid': False,
                'errors': [f'Motivo desconocido: {motivo}'],
                'warnings': []
            }
        
        rule = self.motivo_rules[motivo]
        errors = []
        warnings = []
        
        # Validar duración máxima
        max_duration = rule.get('duracion_maxima')
        if max_duration and duracion > max_duration:
            errors.append(f"Duración excede el máximo permitido: {max_duration} días")
        
        # Validar requisito de certificado
        if rule.get('requiere_certificado', False):
            warnings.append("Recuerda subir el certificado médico")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'rule': rule
        }
    
    def generate_report(self):
        """Genera un reporte del estado del sistema"""
        db = SessionLocal()
        try:
            # Estadísticas generales
            total_absences = db.query(Absence).count()
            validated = db.query(Absence).filter(Absence.validation_status == 'validated').count()
            provisional = db.query(Absence).filter(Absence.validation_status == 'provisional').count()
            with_sanctions = db.query(Absence).filter(Absence.sancion_aplicada == True).count()
            
            # Ausencias con certificado vencido
            overdue_certificates = db.query(Absence).filter(
                Absence.certificate_deadline < datetime.now(),
                Absence.certificate_uploaded == False
            ).count()
            
            return {
                'total_registros': total_absences,
                'validados': validated,
                'provisionales': provisional,
                'con_sancion': with_sanctions,
                'certificados_vencidos': overdue_certificates,
                'fecha_reporte': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        finally:
            db.close()

def test_expert_system():
    """Función de prueba del sistema experto"""
    expert = ExpertSystem()
    
    print("[EXPERT] Prueba del Sistema Experto")
    print("=" * 50)
    
    # Prueba validación de motivos
    result = expert.validate_motivo_rules("ART", 5)
    print(f"ART 5 días: {result}")
    
    result = expert.validate_motivo_rules("Licencia por Matrimonio", 15)
    print(f"Matrimonio 15 días: {result}")
    
    # Generar reporte
    report = expert.generate_report()
    print(f"Reporte del sistema: {report}")

if __name__ == "__main__":
    test_expert_system()