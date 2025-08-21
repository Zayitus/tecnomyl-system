# models/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import config 

Base = declarative_base()

# Modelo para empleados
class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    legajo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    sector = Column(String(50), nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

# Modelo para ausencias
class Absence(Base):
    __tablename__ = "absences"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer)  # ID de Telegram del usuario
    name = Column(String)
    legajo = Column(String)
    motivo = Column(String)
    duracion = Column(Integer)
    certificado = Column(Text, nullable=True)  # Puede ser un path o base64
    created_at = Column(DateTime, server_default=func.now())
    
    # Nuevos campos del sistema experto
    employee_id = Column(Integer, nullable=True)  # FK a Employee (si está validado)
    registration_code = Column(String(50), unique=True)  # Código único de registro
    validation_status = Column(String(20), default="provisional")  # 'validated' / 'provisional'
    certificate_deadline = Column(DateTime, nullable=True)  # Deadline para certificado
    certificate_uploaded = Column(Boolean, default=False)  # Si subió certificado
    observaciones = Column(Text, default="")  # Observaciones del sistema experto
    sancion_aplicada = Column(Boolean, default=False)  # Si tiene sanción por incumplimiento

# Modelo para el estado de la conversación
class ConversationState(Base):
    __tablename__ = "conversation_states"
    
    chat_id = Column(Integer, primary_key=True)
    state = Column(String)  # JSON con el estado actual
    last_updated = Column(DateTime, server_default=func.now())

# Inicializar la base de datos
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)
