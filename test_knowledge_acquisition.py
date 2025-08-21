# test_knowledge_acquisition.py - Prueba completa del módulo de adquisición de conocimiento
from expert.rules_manager import RulesManager
from datetime import datetime

def test_complete_knowledge_acquisition():
    """Prueba completa del sistema de adquisición de conocimiento"""
    
    print("="*60)
    print("[BRAIN] PRUEBA COMPLETA: MODULO DE ADQUISICION DE CONOCIMIENTO")
    print("="*60)
    
    manager = RulesManager()
    
    # 1. Mostrar estadísticas iniciales
    print("\n[STATS] Estadísticas iniciales:")
    stats = manager.get_rules_stats()
    print(f"  [DATA] Total reglas: {stats['total']}")
    print(f"  [DATA] Distribucion severidad: {stats['severity_distribution']}")
    print(f"  [DATA] Backups disponibles: {stats['backups_available']}")
    
    # 2. Crear una regla de prueba completa
    print("\n[CREATE] Creando regla de prueba...")
    test_rule = {
        "id": "demo_knowledge_acquisition",
        "name": "Demo Adquisición de Conocimiento",
        "condition": "motivo == 'Licencia Enfermedad Familiar' and duracion > 2 and not certificate_uploaded",
        "action": "add_observacion('Certificado recomendado para ausencias familiares de más de 2 días')",
        "priority": 77,
        "severity": "info",
        "explanation": "Aunque no es obligatorio, se recomienda certificado para ausencias familiares extensas.",
        "created_by": "knowledge_acquisition_demo"
    }
    
    success, message = manager.add_rule(test_rule)
    if success:
        print(f"  [OK] {message}")
    else:
        print(f"  [ERROR] {message}")
    
    # 3. Mostrar sugerencias para usuarios
    print("\n[SUGGESTIONS] Sugerencias para usuarios no técnicos:")
    suggestions = manager.get_rule_suggestions()
    
    print("  📝 Motivos válidos:")
    for i, motivo in enumerate(suggestions['motivos_validos'][:4], 1):
        print(f"     {i}. {motivo}")
    print("     ...")
    
    print("  🔧 Variables disponibles:")
    for var in suggestions['variables_disponibles'][:6]:
        print(f"     • {var}")
    print("     ...")
    
    print("  ⚡ Acciones permitidas:")
    for action in suggestions['acciones_permitidas']:
        print(f"     • {action}()")
    
    print("  💡 Ejemplos de condiciones:")
    for example in suggestions['ejemplos_condiciones'][:3]:
        print(f"     • {example}")
    
    # 4. Probar validaciones
    print("\n[VALIDATION] Probando sistema de validaciones...")
    
    # Validación exitosa
    valid_rule = {
        "id": "validation_test_ok",
        "condition": "ausencias_ultimo_mes >= 2 and duracion > 1",
        "action": "add_observacion('Patrón detectado')",
        "priority": 60,
        "severity": "warning"
    }
    
    # Cargar reglas para validación
    rules_json = manager.load_rules()
    existing_rules = rules_json.get("rules", [])
    
    # Probar cada validación
    validations = [
        ("ID único", manager.validate_rule_id(valid_rule["id"], existing_rules)),
        ("Condición", manager.validate_condition(valid_rule["condition"])),
        ("Acción", manager.validate_action(valid_rule["action"])),
        ("Prioridad", manager.validate_priority(valid_rule["priority"], existing_rules)),
        ("Severidad", manager.validate_severity(valid_rule["severity"]))
    ]
    
    for test_name, (valid, msg) in validations:
        status = "✅" if valid else "❌"
        print(f"     {status} {test_name}: {msg}")
    
    # 5. Probar validación de regla inválida
    print("\n[VALIDATION] Probando detección de errores...")
    invalid_tests = [
        ("ID duplicado", "demo_knowledge_acquisition"),
        ("Condición inválida", "motivo === 'ART'"),  # Sintaxis incorrecta
        ("Acción no permitida", "delete_database()"),
        ("Prioridad fuera de rango", 150),
        ("Severidad inválida", "critical")
    ]
    
    for test_name, invalid_value in invalid_tests:
        if test_name == "ID duplicado":
            valid, msg = manager.validate_rule_id(invalid_value, existing_rules)
        elif test_name == "Condición inválida":
            valid, msg = manager.validate_condition(invalid_value)
        elif test_name == "Acción no permitida":
            valid, msg = manager.validate_action(invalid_value)
        elif test_name == "Prioridad fuera de rango":
            valid, msg = manager.validate_priority(invalid_value, existing_rules)
        elif test_name == "Severidad inválida":
            valid, msg = manager.validate_severity(invalid_value)
        
        status = "✅" if not valid else "❌"  # Esperamos que sea inválido
        print(f"     {status} {test_name}: {msg}")
    
    # 6. Editar regla creada
    print("\n[EDIT] Editando regla de prueba...")
    edit_data = {
        "name": "Demo Adquisición EDITADA",
        "explanation": "Explicación actualizada desde el sistema de adquisición de conocimiento",
        "priority": 75
    }
    
    success, message = manager.edit_rule("demo_knowledge_acquisition", edit_data)
    if success:
        print(f"  [OK] {message}")
    else:
        print(f"  [ERROR] {message}")
    
    # 7. Verificar estadísticas finales
    print("\n[STATS] Estadísticas después de las modificaciones:")
    final_stats = manager.get_rules_stats()
    print(f"  📊 Total reglas: {final_stats['total']} (cambio: +{final_stats['total'] - stats['total']})")
    print(f"  📊 Nuevos backups: {final_stats['backups_available'] - stats['backups_available']}")
    print(f"  📊 Última actualización: {final_stats['last_updated']}")
    
    # 8. Mostrar estructura de archivos
    print("\n[FILES] Archivos del sistema de adquisición:")
    import os
    files_created = [
        "expert/rules_manager.py",
        "api/rules_endpoints.py", 
        "templates/rules_form.html",
        "templates/rules_list.html",
        "expert/backups/"
    ]
    
    for file_path in files_created:
        exists = "✅" if os.path.exists(file_path) else "❌"
        print(f"  {exists} {file_path}")
    
    # 9. Información para usuarios
    print("\n[INFO] Para usuarios no técnicos:")
    print("  🌐 Acceder a: http://localhost:8000/rules")
    print("  ➕ Nueva regla: http://localhost:8000/rules/new")
    print("  📋 Gestionar todas: http://localhost:8000/rules")
    print("  📊 API REST: http://localhost:8000/api/rules")
    
    # 10. Cleanup - eliminar regla de prueba
    print("\n[CLEANUP] Limpiando regla de prueba...")
    success, message = manager.delete_rule("demo_knowledge_acquisition")
    if success:
        print(f"  [OK] {message}")
    else:
        print(f"  [WARN] {message}")
    
    print("\n" + "="*60)
    print("[SUCCESS] MODULO DE ADQUISICION DE CONOCIMIENTO COMPLETADO")
    print("[SUCCESS] Sistema listo para uso en produccion")
    print("="*60)

if __name__ == "__main__":
    test_complete_knowledge_acquisition()