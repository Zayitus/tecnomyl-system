# test_save.py - Probar guardado manual
import asyncio
from models.database import SessionLocal, Absence

async def test_save():
    print("Probando guardado manual...")
    
    # Datos de prueba
    test_data = {
        "name": "Juan Perez TEST",
        "legajo": "12345",
        "motivo": "Licencia Enfermedad Personal",
        "duracion": 3,
        "certificado": "Test - No aplica"
    }
    
    # Importar función
    import sys
    sys.path.append('.')
    from main import save_absence_data
    
    # Guardar
    await save_absence_data(chat_id=999999, data=test_data)
    
    # Verificar
    db = SessionLocal()
    try:
        count = db.query(Absence).count()
        print(f"Total registros después del test: {count}")
        
        if count > 0:
            last_record = db.query(Absence).order_by(Absence.id.desc()).first()
            print(f"Último registro: {last_record.name} - {last_record.motivo}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_save())