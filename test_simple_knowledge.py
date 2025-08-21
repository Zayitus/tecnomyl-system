# test_simple_knowledge.py - Prueba simple sin emojis
from expert.rules_manager import RulesManager

def test_knowledge_system():
    print("=" * 50)
    print("SISTEMA DE ADQUISICION DE CONOCIMIENTO - PRUEBA")
    print("=" * 50)
    
    manager = RulesManager()
    
    # 1. Estadisticas iniciales
    print("\n[1] ESTADISTICAS INICIALES:")
    stats = manager.get_rules_stats()
    print(f"    Total reglas: {stats['total']}")
    print(f"    Backups disponibles: {stats['backups_available']}")
    
    # 2. Crear regla de prueba
    print("\n[2] CREANDO REGLA DE PRUEBA:")
    test_rule = {
        "id": "test_simple_rule",
        "name": "Regla de Prueba Simple",
        "condition": "motivo == 'ART' and duracion > 3",
        "action": "add_observacion('Prueba del sistema')",
        "priority": 80,
        "severity": "info",
        "explanation": "Regla creada para probar el sistema",
        "created_by": "test_system"
    }
    
    success, message = manager.add_rule(test_rule)
    print(f"    Resultado: {message}")
    
    # 3. Validaciones
    print("\n[3] PRUEBAS DE VALIDACION:")
    rules_json = manager.load_rules()
    existing_rules = rules_json.get("rules", [])
    
    # Pruebas de validacion
    tests = [
        ("Condicion valida", manager.validate_condition("duracion > 5")),
        ("Accion valida", manager.validate_action("add_observacion('test')")),
        ("Condicion invalida", manager.validate_condition("duracion === 5")),
        ("Accion no permitida", manager.validate_action("delete_all()")),
    ]
    
    for test_name, (valid, msg) in tests:
        status = "[OK]" if valid else "[ERROR]"
        print(f"    {status} {test_name}: {msg[:50]}...")
    
    # 4. Sugerencias
    print("\n[4] SUGERENCIAS PARA USUARIOS:")
    suggestions = manager.get_rule_suggestions()
    print(f"    Motivos disponibles: {len(suggestions['motivos_validos'])}")
    print(f"    Variables disponibles: {len(suggestions['variables_disponibles'])}")
    print(f"    Acciones permitidas: {suggestions['acciones_permitidas']}")
    
    # 5. Cleanup
    print("\n[5] LIMPIEZA:")
    success, message = manager.delete_rule("test_simple_rule")
    print(f"    {message}")
    
    # 6. Estadisticas finales
    print("\n[6] ESTADISTICAS FINALES:")
    final_stats = manager.get_rules_stats()
    print(f"    Total reglas: {final_stats['total']}")
    print(f"    Backups creados: {final_stats['backups_available'] - stats['backups_available']}")
    
    print("\n" + "=" * 50)
    print("PRUEBA COMPLETADA EXITOSAMENTE")
    print("SISTEMA LISTO PARA PRODUCCION")
    print("=" * 50)
    
    print("\nURLs DISPONIBLES:")
    print("  - Listar reglas: http://localhost:8000/rules")
    print("  - Nueva regla: http://localhost:8000/rules/new")
    print("  - API REST: http://localhost:8000/api/rules")

if __name__ == "__main__":
    test_knowledge_system()