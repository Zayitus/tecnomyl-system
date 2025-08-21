# view_records.py
from models.database import SessionLocal, Absence
from datetime import datetime

def view_all_records():
    """Muestra todos los registros de ausencias"""
    db = SessionLocal()
    try:
        absences = db.query(Absence).order_by(Absence.created_at.desc()).all()
        
        if not absences:
            print("📝 No hay registros de ausencias.")
            return
        
        print(f"\n📋 REGISTROS DE AUSENCIAS ({len(absences)} total)")
        print("=" * 80)
        
        for absence in absences:
            print(f"ID: {absence.id}")
            print(f"👤 Nombre: {absence.name}")
            print(f"🆔 Legajo: {absence.legajo}")
            print(f"📅 Motivo: {absence.motivo}")
            print(f"⏰ Duración: {absence.duracion} días")
            print(f"🏥 Certificado: {absence.certificado}")
            print(f"📆 Registrado: {absence.created_at}")
            print(f"💬 Chat ID: {absence.chat_id}")
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

def search_by_legajo(legajo):
    """Busca registros por legajo"""
    db = SessionLocal()
    try:
        absences = db.query(Absence).filter(Absence.legajo == legajo).order_by(Absence.created_at.desc()).all()
        
        if not absences:
            print(f"📝 No se encontraron registros para el legajo: {legajo}")
            return
            
        print(f"\n📋 REGISTROS PARA LEGAJO: {legajo}")
        print("=" * 60)
        
        for absence in absences:
            print(f"📅 {absence.created_at.strftime('%d/%m/%Y %H:%M')}")
            print(f"👤 {absence.name}")
            print(f"📋 {absence.motivo} - {absence.duracion} días")
            print(f"🏥 {absence.certificado}")
            print("-" * 60)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

def main():
    while True:
        print("\n🏢 SISTEMA DE CONSULTA DE AUSENCIAS")
        print("1. Ver todos los registros")
        print("2. Buscar por legajo")
        print("3. Salir")
        
        choice = input("\nSelecciona una opción (1-3): ").strip()
        
        if choice == "1":
            view_all_records()
        elif choice == "2":
            legajo = input("Ingresa el legajo a buscar: ").strip()
            if legajo:
                search_by_legajo(legajo)
            else:
                print("❌ Legajo no puede estar vacío")
        elif choice == "3":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()