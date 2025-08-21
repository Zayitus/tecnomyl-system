# api/rules_endpoints.py - Endpoints para gestión de reglas
from fastapi import HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any, Optional
import json
from pathlib import Path
from datetime import datetime

from expert.rules_manager import RulesManager
from expert.rules_preview import RulesPreview
from expert.rules_monitoring import RulesMonitoring
from security.auth_system import SecurityManager, require_api_key

class RulesAPI:
    """API para gestión de reglas del sistema experto"""
    
    def __init__(self):
        self.rules_manager = RulesManager()
        self.rules_preview = RulesPreview()
        self.rules_monitoring = RulesMonitoring()
        self.security_manager = SecurityManager()
        
    def setup_routes(self, app):
        """Configura las rutas en la aplicación FastAPI"""
        
        # Páginas web
        app.add_api_route("/rules", self.show_rules_list, methods=["GET"], response_class=HTMLResponse)
        app.add_api_route("/rules/new", self.show_rules_form, methods=["GET"], response_class=HTMLResponse)
        
        # API endpoints
        app.add_api_route("/api/rules", self.get_rules, methods=["GET"])
        app.add_api_route("/api/rules", self.create_rule_form, methods=["POST"])  # Formulario HTML
        app.add_api_route("/api/rules/{rule_id}", self.update_rule, methods=["PUT"])
        app.add_api_route("/api/rules/{rule_id}", self.delete_rule, methods=["DELETE"])
        app.add_api_route("/api/rules/suggestions", self.get_suggestions, methods=["GET"])
        app.add_api_route("/api/rules/validate", self.validate_rule_data, methods=["POST"])
        
        # API JSON endpoints
        app.add_api_route("/api/rules/json", self.create_rule, methods=["POST"])  # JSON
        
        # Nuevos endpoints avanzados
        app.add_api_route("/api/rules/preview", self.preview_rule, methods=["POST"])
        app.add_api_route("/api/rules/monitoring", self.get_monitoring_dashboard, methods=["GET"])
        app.add_api_route("/api/rules/{rule_id}/conflicts", self.check_rule_conflicts, methods=["GET"])
        app.add_api_route("/api/rules/health", self.get_system_health, methods=["GET"])
    
    async def show_rules_list(self) -> HTMLResponse:
        """Muestra la página de lista de reglas"""
        template_path = Path("templates/rules_list.html")
        
        if not template_path.exists():
            raise HTTPException(status_code=404, detail="Template no encontrado")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return HTMLResponse(content=content)
    
    async def show_rules_form(self) -> HTMLResponse:
        """Muestra el formulario para crear nuevas reglas"""
        template_path = Path("templates/rules_form.html")
        
        if not template_path.exists():
            raise HTTPException(status_code=404, detail="Template no encontrado")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return HTMLResponse(content=content)
    
    async def get_rules(self) -> JSONResponse:
        """Obtiene todas las reglas con estadísticas"""
        try:
            rules_data = self.rules_manager.load_rules()
            stats = self.rules_manager.get_rules_stats()
            
            return JSONResponse({
                "rules": rules_data.get("rules", []),
                "stats": stats,
                "metadata": rules_data.get("metadata", {})
            })
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error cargando reglas: {str(e)}")
    
    async def create_rule(self, rule_data: Dict[str, Any]) -> JSONResponse:
        """Crea una nueva regla"""
        try:
            # Si viene de formulario HTML
            if isinstance(rule_data, dict) and 'rule_id' in rule_data:
                # Convertir priority a int si es string
                if 'priority' in rule_data:
                    rule_data['priority'] = int(rule_data['priority'])
                
                success, message = self.rules_manager.add_rule(rule_data)
                
                if success:
                    return JSONResponse({"message": message}, status_code=201)
                else:
                    return JSONResponse({"error": message}, status_code=400)
            else:
                return JSONResponse({"error": "Datos de regla inválidos"}, status_code=400)
                
        except Exception as e:
            return JSONResponse({"error": f"Error interno: {str(e)}"}, status_code=500)
    
    async def create_rule_form(
        self,
        rule_id: str = Form(...),
        rule_name: str = Form(...),
        condition: str = Form(...),
        action: str = Form(...),
        priority: int = Form(...),
        severity: str = Form(...),
        explanation: str = Form(""),
        created_by: str = Form("web_user")
    ) -> JSONResponse:
        """Maneja el formulario HTML para crear reglas"""
        
        rule_data = {
            "id": rule_id,
            "name": rule_name,
            "condition": condition,
            "action": action,
            "priority": priority,
            "severity": severity,
            "explanation": explanation,
            "created_by": created_by
        }
        
        return await self.create_rule(rule_data)
    
    async def update_rule(self, rule_id: str, updated_data: Dict[str, Any]) -> JSONResponse:
        """Actualiza una regla existente"""
        try:
            # Convertir priority a int si es string
            if 'priority' in updated_data:
                updated_data['priority'] = int(updated_data['priority'])
            
            success, message = self.rules_manager.edit_rule(rule_id, updated_data)
            
            if success:
                return JSONResponse({"message": message})
            else:
                return JSONResponse({"error": message}, status_code=400)
                
        except Exception as e:
            return JSONResponse({"error": f"Error interno: {str(e)}"}, status_code=500)
    
    async def delete_rule(self, rule_id: str) -> JSONResponse:
        """Elimina una regla"""
        try:
            success, message = self.rules_manager.delete_rule(rule_id)
            
            if success:
                return JSONResponse({"message": message})
            else:
                return JSONResponse({"error": message}, status_code=404)
                
        except Exception as e:
            return JSONResponse({"error": f"Error interno: {str(e)}"}, status_code=500)
    
    async def get_suggestions(self) -> JSONResponse:
        """Obtiene sugerencias para crear reglas"""
        try:
            suggestions = self.rules_manager.get_rule_suggestions()
            return JSONResponse(suggestions)
            
        except Exception as e:
            return JSONResponse({"error": f"Error obteniendo sugerencias: {str(e)}"}, status_code=500)
    
    async def validate_rule_data(self, rule_data: Dict[str, Any]) -> JSONResponse:
        """Valida datos de una regla sin guardarla"""
        try:
            # Validar cada campo individualmente
            rules_json = self.rules_manager.load_rules()
            existing_rules = rules_json.get("rules", [])
            
            results = {}
            
            if 'rule_id' in rule_data:
                valid, message = self.rules_manager.validate_rule_id(
                    rule_data['rule_id'], existing_rules
                )
                results['rule_id'] = {"valid": valid, "message": message}
            
            if 'condition' in rule_data:
                valid, message = self.rules_manager.validate_condition(rule_data['condition'])
                results['condition'] = {"valid": valid, "message": message}
            
            if 'action' in rule_data:
                valid, message = self.rules_manager.validate_action(rule_data['action'])
                results['action'] = {"valid": valid, "message": message}
            
            if 'priority' in rule_data:
                priority = int(rule_data['priority']) if isinstance(rule_data['priority'], str) else rule_data['priority']
                valid, message = self.rules_manager.validate_priority(priority, existing_rules)
                results['priority'] = {"valid": valid, "message": message}
            
            if 'severity' in rule_data:
                valid, message = self.rules_manager.validate_severity(rule_data['severity'])
                results['severity'] = {"valid": valid, "message": message}
            
            # Determinar si todos son válidos
            all_valid = all(result['valid'] for result in results.values())
            
            return JSONResponse({
                "valid": all_valid,
                "results": results,
                "message": "Todos los campos son válidos" if all_valid else "Algunos campos requieren corrección"
            })
            
        except Exception as e:
            return JSONResponse({"error": f"Error en validación: {str(e)}"}, status_code=500)
    
    async def preview_rule(self, rule_data: Dict[str, Any]) -> JSONResponse:
        """Previsualiza una regla contra escenarios de prueba"""
        try:
            # Preview individual
            individual_results = self.rules_preview.preview_single_rule(rule_data)
            
            # Preview con sistema completo
            full_results = self.rules_preview.preview_rule_with_existing(rule_data)
            
            # Análisis de conflictos
            conflicts = self.rules_preview.analyze_rule_conflicts(rule_data)
            
            # Recomendaciones
            recommendations = self.rules_preview.get_recommendation(rule_data)
            
            return JSONResponse({
                "individual_preview": individual_results,
                "full_system_preview": full_results,
                "conflicts": conflicts,
                "recommendations": recommendations,
                "preview_timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return JSONResponse({"error": f"Error en preview: {str(e)}"}, status_code=500)
    
    async def get_monitoring_dashboard(self, days: int = 7) -> JSONResponse:
        """Obtiene dashboard de monitoreo de reglas"""
        try:
            dashboard_data = self.rules_monitoring.get_rules_dashboard(days)
            return JSONResponse(dashboard_data)
            
        except Exception as e:
            return JSONResponse({"error": f"Error obteniendo dashboard: {str(e)}"}, status_code=500)
    
    async def check_rule_conflicts(self, rule_id: str) -> JSONResponse:
        """Verifica conflictos para una regla específica"""
        try:
            # Cargar regla específica
            rules_data = self.rules_manager.load_rules()
            target_rule = None
            
            for rule in rules_data.get("rules", []):
                if rule.get("id") == rule_id:
                    target_rule = rule
                    break
            
            if not target_rule:
                return JSONResponse({"error": "Regla no encontrada"}, status_code=404)
            
            conflicts = self.rules_preview.analyze_rule_conflicts(target_rule)
            
            return JSONResponse({
                "rule_id": rule_id,
                "conflicts": conflicts,
                "conflict_count": len(conflicts),
                "analysis_timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return JSONResponse({"error": f"Error verificando conflictos: {str(e)}"}, status_code=500)
    
    async def get_system_health(self) -> JSONResponse:
        """Obtiene información de salud del sistema de reglas"""
        try:
            health_data = self.rules_monitoring.get_system_health()
            return JSONResponse(health_data)
            
        except Exception as e:
            return JSONResponse({"error": f"Error obteniendo salud del sistema: {str(e)}"}, status_code=500)


def test_rules_api():
    """Función de prueba para los endpoints de reglas"""
    print("[TEST] API de Reglas")
    print("=" * 30)
    
    # Simular datos de una nueva regla
    test_rule = {
        "rule_id": "api_test_rule",
        "rule_name": "Regla de Prueba API",
        "condition": "motivo == 'ART' and duracion > 7",
        "action": "add_observacion('Prueba desde API')",
        "priority": 88,
        "severity": "info",
        "explanation": "Regla creada para probar la API",
        "created_by": "api_test"
    }
    
    # Crear instancia de la API
    api = RulesAPI()
    
    # Test 1: Obtener reglas existentes
    print("\n[GET] Probando obtener reglas...")
    import asyncio
    
    async def test_get_rules():
        try:
            response = await api.get_rules()
            data = json.loads(response.body.decode())
            print(f"  Total reglas: {len(data.get('rules', []))}")
            print(f"  Estadísticas: {data.get('stats', {})}")
            return True
        except Exception as e:
            print(f"  Error: {e}")
            return False
    
    # Test 2: Validar regla
    print("\n[VALIDATE] Probando validación...")
    async def test_validation():
        try:
            response = await api.validate_rule_data(test_rule)
            data = json.loads(response.body.decode())
            print(f"  Válida: {data.get('valid', False)}")
            print(f"  Resultados: {len(data.get('results', {}))}")
            return data.get('valid', False)
        except Exception as e:
            print(f"  Error: {e}")
            return False
    
    # Test 3: Crear regla
    print("\n[CREATE] Probando crear regla...")
    async def test_create():
        try:
            response = await api.create_rule(test_rule)
            data = json.loads(response.body.decode())
            if 'message' in data:
                print(f"  Éxito: {data['message']}")
                return True
            else:
                print(f"  Error: {data.get('error', 'Desconocido')}")
                return False
        except Exception as e:
            print(f"  Error: {e}")
            return False
    
    # Test 4: Eliminar regla
    print("\n[DELETE] Probando eliminar regla...")
    async def test_delete():
        try:
            response = await api.delete_rule("api_test_rule")
            data = json.loads(response.body.decode())
            if 'message' in data:
                print(f"  Éxito: {data['message']}")
                return True
            else:
                print(f"  Error: {data.get('error', 'Desconocido')}")
                return False
        except Exception as e:
            print(f"  Error: {e}")
            return False
    
    # Ejecutar tests
    async def run_all_tests():
        test1 = await test_get_rules()
        test2 = await test_validation()
        test3 = await test_create()
        test4 = await test_delete()
        
        print(f"\n[SUMMARY] Resultados:")
        print(f"  GET rules: {'✅' if test1 else '❌'}")
        print(f"  Validation: {'✅' if test2 else '❌'}")
        print(f"  Create rule: {'✅' if test3 else '❌'}")
        print(f"  Delete rule: {'✅' if test4 else '❌'}")
    
    asyncio.run(run_all_tests())

if __name__ == "__main__":
    test_rules_api()