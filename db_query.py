# db_query.py - Consultas directas a la base de datos
import sqlite3
from datetime import datetime

def connect_db():
    """Conecta a la base de datos SQLite"""
    return sqlite3.connect('test.db')

def show_tables():
    """Muestra todas las tablas"""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("📋 TABLAS EN LA BASE DE DATOS:")
    for table in tables:
        print(f"- {table[0]}")
    
    conn.close()

def show_table_structure(table_name):
    """Muestra la estructura de una tabla"""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    print(f"\n🏗️ ESTRUCTURA DE LA TABLA '{table_name}':")
    print("Columna | Tipo | Nulo | Clave | Valor por defecto")
    print("-" * 60)
    for col in columns:
        print(f"{col[1]} | {col[2]} | {'No' if col[3] else 'Sí'} | {'Sí' if col[5] else 'No'} | {col[4] or 'Ninguno'}")
    
    conn.close()

def count_records():
    """Cuenta registros en cada tabla"""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Ausencias
    cursor.execute("SELECT COUNT(*) FROM absences;")
    absences_count = cursor.fetchone()[0]
    
    # Estados de conversación
    cursor.execute("SELECT COUNT(*) FROM conversation_states;")
    conversations_count = cursor.fetchone()[0]
    
    print(f"\n📊 CONTEO DE REGISTROS:")
    print(f"- Ausencias: {absences_count}")
    print(f"- Estados de conversación: {conversations_count}")
    
    conn.close()

def execute_custom_query(query):
    """Ejecuta una consulta SQL personalizada"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"\n🔍 RESULTADO DE: {query}")
        print("-" * 50)
        for row in results:
            print(row)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

def show_recent_absences(limit=5):
    """Muestra las ausencias más recientes"""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, legajo, motivo, duracion, created_at 
        FROM absences 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (limit,))
    
    records = cursor.fetchall()
    
    print(f"\n📅 ÚLTIMAS {limit} AUSENCIAS:")
    print("-" * 80)
    for record in records:
        print(f"ID: {record[0]} | {record[1]} | Legajo: {record[2]} | {record[3]} | {record[4]} días | {record[5]}")
    
    conn.close()

def main():
    while True:
        print("\n🗄️ CONSULTOR DE BASE DE DATOS")
        print("1. Mostrar tablas")
        print("2. Ver estructura de tabla")
        print("3. Contar registros")
        print("4. Últimas ausencias")
        print("5. Consulta personalizada")
        print("6. Salir")
        
        choice = input("\nSelecciona opción (1-6): ").strip()
        
        if choice == "1":
            show_tables()
        elif choice == "2":
            table = input("Nombre de la tabla: ").strip()
            show_table_structure(table)
        elif choice == "3":
            count_records()
        elif choice == "4":
            limit = input("¿Cuántos registros? (default 5): ").strip()
            limit = int(limit) if limit.isdigit() else 5
            show_recent_absences(limit)
        elif choice == "5":
            query = input("Ingresa tu consulta SQL: ").strip()
            if query:
                execute_custom_query(query)
        elif choice == "6":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()