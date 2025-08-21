# migrate_database.py - Migra la base de datos a la nueva estructura
import sqlite3
import os
from datetime import datetime

def backup_database():
    """Crear backup de la base de datos actual"""
    if os.path.exists('test.db'):
        backup_name = f"test_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.system(f'copy "test.db" "{backup_name}"')
        print(f"[BACKUP] Base de datos respaldada como: {backup_name}")
        return backup_name
    return None

def migrate_database():
    """Migra la base de datos agregando las nuevas columnas"""
    
    # Backup first
    backup_file = backup_database()
    
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    
    try:
        print("[MIGRATE] Iniciando migración de base de datos...")
        
        # Verificar columnas existentes
        cursor.execute("PRAGMA table_info(absences);")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"[INFO] Columnas existentes: {existing_columns}")
        
        # Nuevas columnas a agregar
        new_columns = [
            ('employee_id', 'INTEGER'),
            ('registration_code', 'TEXT'),
            ('validation_status', 'TEXT DEFAULT "provisional"'),
            ('certificate_deadline', 'DATETIME'),
            ('certificate_uploaded', 'BOOLEAN DEFAULT 0'),
            ('observaciones', 'TEXT DEFAULT ""'),
            ('sancion_aplicada', 'BOOLEAN DEFAULT 0')
        ]
        
        # Agregar columnas que no existen
        added_columns = []
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE absences ADD COLUMN {column_name} {column_type};")
                    added_columns.append(column_name)
                    print(f"[ADD] Columna agregada: {column_name}")
                except Exception as e:
                    print(f"[ERROR] No se pudo agregar {column_name}: {e}")
        
        # Crear tabla employees si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                legajo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                sector TEXT NOT NULL,
                activo BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("[CREATE] Tabla employees verificada/creada")
        
        conn.commit()
        
        # Verificar el resultado
        cursor.execute("PRAGMA table_info(absences);")
        final_columns = [column[1] for column in cursor.fetchall()]
        
        print(f"[SUCCESS] Migración completada!")
        print(f"[INFO] Columnas finales: {final_columns}")
        print(f"[INFO] Columnas agregadas: {added_columns}")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM absences;")
        absence_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM employees;")
        employee_count = cursor.fetchone()[0]
        
        print(f"[INFO] Registros preservados:")
        print(f"  - Ausencias: {absence_count}")
        print(f"  - Empleados: {employee_count}")
        
    except Exception as e:
        print(f"[ERROR] Error en migración: {e}")
        if backup_file:
            print(f"[RESTORE] Puedes restaurar desde: {backup_file}")
    finally:
        conn.close()

def verify_migration():
    """Verifica que la migración fue exitosa"""
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    
    try:
        # Verificar estructura de absences
        cursor.execute("PRAGMA table_info(absences);")
        columns = cursor.fetchall()
        
        required_columns = [
            'employee_id', 'registration_code', 'validation_status',
            'certificate_deadline', 'certificate_uploaded', 
            'observaciones', 'sancion_aplicada'
        ]
        
        existing_columns = [col[1] for col in columns]
        missing = [col for col in required_columns if col not in existing_columns]
        
        if missing:
            print(f"[VERIFY] FALTAN COLUMNAS: {missing}")
            return False
        else:
            print("[VERIFY] ✅ Todas las columnas requeridas están presentes")
            return True
            
    finally:
        conn.close()

if __name__ == "__main__":
    print("[DATABASE] MIGRADOR DE BASE DE DATOS")
    print("=" * 50)
    
    migrate_database()
    
    print("\n[VERIFY] VERIFICANDO MIGRACION...")
    print("=" * 50)
    
    if verify_migration():
        print("\n[SUCCESS] MIGRACION EXITOSA")
        print("La base de datos esta lista para el sistema experto")
    else:
        print("\n[ERROR] MIGRACION INCOMPLETA")
        print("Revisa los errores arriba")