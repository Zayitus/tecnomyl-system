# load_employees.py - Carga empleados desde CSV
import pandas as pd
from models.database import SessionLocal, Employee, Base, engine

def load_employees_from_csv(csv_path):
    """Carga empleados desde archivo CSV"""
    
    # Crear tablas si no existen
    print("Creando tablas en base de datos...")
    Base.metadata.create_all(bind=engine)
    
    print(f"Leyendo archivo CSV: {csv_path}")
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        # Intentar con diferentes codificaciones
        df = pd.read_csv(csv_path, encoding='latin1')
    
    print(f"Encontrados {len(df)} empleados en el CSV")
    
    session = SessionLocal()
    added_count = 0
    skipped_count = 0
    
    try:
        for index, row in df.iterrows():
            legajo = str(row['legajo']).strip()
            nombre = str(row['nombre']).strip()
            sector = str(row['sector']).strip()
            
            # Verificar si ya existe
            existing = session.query(Employee).filter(Employee.legajo == legajo).first()
            
            if existing:
                print(f"SKIP: Empleado {legajo} - {nombre} ya existe")
                skipped_count += 1
                continue
            
            # Crear nuevo empleado
            employee = Employee(
                legajo=legajo,
                nombre=nombre,
                sector=sector,
                activo=True
            )
            
            session.add(employee)
            print(f"ADD: {legajo} - {nombre} ({sector})")
            added_count += 1
        
        # Guardar cambios
        session.commit()
        print(f"\n[SUCCESS] RESUMEN:")
        print(f"- Empleados agregados: {added_count}")
        print(f"- Empleados existentes (omitidos): {skipped_count}")
        print(f"- Total en base de datos: {session.query(Employee).count()}")
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR]: {e}")
        raise
    finally:
        session.close()

def list_employees():
    """Lista todos los empleados en la base de datos"""
    session = SessionLocal()
    try:
        employees = session.query(Employee).order_by(Employee.legajo).all()
        
        print(f"\n[EMPLOYEES] BASE DE DATOS ({len(employees)} total):")
        print("-" * 60)
        
        sectores = {}
        for emp in employees:
            sector = emp.sector
            if sector not in sectores:
                sectores[sector] = []
            sectores[sector].append(emp)
        
        for sector, empleados in sectores.items():
            print(f"\n[SECTOR] {sector.upper()} ({len(empleados)} empleados):")
            for emp in empleados:
                status = "Activo" if emp.activo else "Inactivo"
                print(f"  {emp.legajo} - {emp.nombre} ({status})")
        
    finally:
        session.close()

def search_employee(legajo):
    """Busca un empleado por legajo"""
    session = SessionLocal()
    try:
        employee = session.query(Employee).filter(Employee.legajo == legajo).first()
        
        if employee:
            print(f"\n[FOUND] EMPLEADO ENCONTRADO:")
            print(f"ID: {employee.id}")
            print(f"Legajo: {employee.legajo}")
            print(f"Nombre: {employee.nombre}")
            print(f"Sector: {employee.sector}")
            print(f"Activo: {'Si' if employee.activo else 'No'}")
            print(f"Registrado: {employee.created_at}")
            return employee
        else:
            print(f"[NOT FOUND] No se encontro empleado con legajo: {legajo}")
            return None
            
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso del script:")
        print("  python load_employees.py load <ruta_csv>     # Cargar empleados")
        print("  python load_employees.py list               # Listar empleados")
        print("  python load_employees.py search <legajo>    # Buscar empleado")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "load":
        if len(sys.argv) < 3:
            print("[ERROR] Falta especificar la ruta del archivo CSV")
            sys.exit(1)
        csv_path = sys.argv[2]
        load_employees_from_csv(csv_path)
        
    elif command == "list":
        list_employees()
        
    elif command == "search":
        if len(sys.argv) < 3:
            print("[ERROR] Falta especificar el legajo a buscar")
            sys.exit(1)
        legajo = sys.argv[2]
        search_employee(legajo)
        
    else:
        print(f"[ERROR] Comando desconocido: {command}")
        print("Comandos disponibles: load, list, search")