# 🤖 Sistema Experto de Registro de Ausencias

## 📖 Descripción

Sistema inteligente de gestión de ausencias laborales que combina un **bot de Telegram** con un **sistema experto** para automatizar la validación, registro y control de ausencias de empleados.

### ✨ Características principales

- 🔍 **Validación automática** de empleados contra base de datos
- 📋 **Códigos únicos** de registro para trazabilidad
- ⏰ **Control de deadlines** para certificados médicos
- 🤖 **Sistema experto** con reglas de negocio automatizadas
- 📊 **Dashboard web** con estadísticas y reportes
- 📱 **Interfaz Telegram** intuitiva y conversacional

---

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│  Bot Telegram   │◄──►│   FastAPI        │◄──►│  Sistema        │
│  (Interface)    │    │   (Server)       │    │  Experto        │
│                 │    │                  │    │  (Rules Engine) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│  Usuarios       │    │  SQLite          │    │  Reglas JSON    │
│  Telegram       │    │  Database        │    │  (Configurable) │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 🛠️ Tecnologías

- **Backend**: Python 3.11+ con FastAPI
- **Bot**: python-telegram-bot
- **Base de datos**: SQLite con SQLAlchemy ORM
- **Sistema experto**: Motor de reglas JSON configurable
- **Frontend**: Dashboard web HTML/CSS integrado

---

## 🚀 Instalación

### 1. Requisitos previos

- Python 3.11 o superior
- Token de bot de Telegram (obtener de @BotFather)
- Ngrok para túnel público

### 2. Instalación de dependencias

```bash
pip install -r requirements.txt
```

### 3. Configuración

Edita `config.py` con tu token:
```python
TELEGRAM_TOKEN = "tu_token_aqui"
DATABASE_URL = "sqlite:///./test.db"
```

### 4. Cargar empleados

```bash
python load_employees.py load "ruta/a/empleados.csv"
```

El CSV debe tener formato:
```csv
legajo,nombre,sector
890001,Juan Pérez,linea1
890002,María García,RH
```

### 5. Migrar base de datos (si actualizas)

```bash
python migrate_database.py
```

### 6. Configurar webhook

```bash
# Iniciar ngrok
ngrok http 8000

# Configurar webhook con la URL de ngrok
python setup_webhook.py
```

### 7. Iniciar sistema

```bash
python main.py
```

---

## 👤 Uso del Sistema

### Comandos del bot

- `/start` - Registrar nueva ausencia
- `/registros` - Ver mis ausencias
- `/help` - Ayuda y comandos

### Flujo de registro

1. **Inicio**: `/start`
2. **Nombre**: Ingresa apellido y nombre
3. **Legajo**: 🔥 **Validación automática**
   - ✅ **Validado**: Confirma datos del empleado
   - ⚠️ **No encontrado**: Registro provisional
   - ❌ **Inactivo**: Bloquea registro
4. **Motivo**: Selecciona del 1 al 8
5. **Duración**: Días de ausencia
6. **Certificado**: Si es requerido
7. **Confirmación**: 🤖 **Sistema experto activo**

### Tipos de ausencias

| Motivo | Requiere Certificado | Duración Máxima |
|--------|:-------------------:|:---------------:|
| ART | ✅ | 365 días |
| Licencia Enfermedad Familiar | ✅ | 30 días |
| Licencia Enfermedad Personal | ✅ | 90 días |
| Licencia por Fallecimiento Familiar | ❌ | 5 días |
| Licencia por Matrimonio | ❌ | 10 días |
| Licencia por Nacimiento | ❌ | 2 días |
| Licencia por Paternidad | ❌ | 15 días |
| Permiso Gremial | ❌ | Sin límite |

---

## 🤖 Sistema Experto

### Reglas automáticas

El sistema evalúa cada registro contra 5 reglas:

1. **Certificado Obligatorio** - Detecta certificados faltantes
2. **Vencimiento de Certificado** - Marca sanciones por deadlines
3. **Duración Excesiva** - Identifica ausencias que exceden límites
4. **Empleado No Validado** - Señala registros provisionales
5. **Ausencias Frecuentes** - Detecta patrones sospechosos (>3 en 30 días)

### Códigos de registro

- **Validados**: `REG-890001-20250820-A1B2`
- **Provisionales**: `PROV-123456-20250820-C3D4`

Formato: `TIPO-LEGAJO-FECHA-UUID`

### Observaciones automáticas

```
[WARNING] Falta certificado médico obligatorio
[ERROR] Certificado no entregado en plazo - SANCIÓN aplicada
[INFO] Registro provisional - Requiere validación de RRHH
```

---

## 🔧 Administración

### Dashboard web

**URL**: `http://localhost:8000` (o URL de ngrok)

Funciones:
- 📊 Estadísticas en tiempo real
- 📋 Lista completa de registros
- 🔍 Enlaces a certificados
- ⚠️ Alertas del sistema experto

### API REST

```bash
# Todos los registros
GET /api/registros

# Lista de certificados
GET /certificados

# Certificado específico
GET /certificados/cert_890001_20250820_143052.jpg
```

### Consultas de base de datos

```bash
# Ver empleados
python load_employees.py list

# Buscar empleado
python load_employees.py search 890001

# Consultas personalizadas
python db_query.py
```

### Reportes del sistema experto

```python
from expert.engine import ExpertSystem
expert = ExpertSystem()
print(expert.generate_report())
```

Resultado:
```json
{
  "total_registros": 25,
  "validados": 20,
  "provisionales": 5,
  "con_sancion": 2,
  "certificados_vencidos": 1,
  "fecha_reporte": "2025-08-20 15:30:00"
}
```

---

## 📁 Estructura del Proyecto

```
tecnomyl-system/
├── main.py                    # Servidor principal
├── config.py                  # Configuración
├── utils.py                   # Utilidades (códigos, etc.)
├── requirements.txt           # Dependencias
├── test.db                    # Base de datos SQLite
├── migrate_database.py        # Migrador de BD
├── setup_webhook.py           # Configurador de webhook
├── load_employees.py          # Cargador de empleados
├── view_records.py            # Visualizador de registros
├── db_query.py               # Consultor de BD
├── models/
│   ├── __init__.py
│   ├── database.py           # Modelos SQLAlchemy
│   └── config.py
├── expert/
│   ├── __init__.py
│   ├── rules.json            # Reglas del sistema experto
│   └── engine.py             # Motor de reglas
├── bot/
│   ├── __init__.py
│   └── handlers.py           # Manejadores (vacío)
└── certificados/             # Archivos de certificados
```

---

## 🗄️ Base de Datos

### Tabla `employees` (40 empleados)

```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    legajo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    sector TEXT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Tabla `absences` (con sistema experto)

```sql
CREATE TABLE absences (
    id INTEGER PRIMARY KEY,
    chat_id INTEGER,
    name TEXT,
    legajo TEXT,
    motivo TEXT,
    duracion INTEGER,
    certificado TEXT,
    created_at DATETIME,
    -- Campos del sistema experto
    employee_id INTEGER,
    registration_code TEXT UNIQUE,
    validation_status TEXT DEFAULT 'provisional',
    certificate_deadline DATETIME,
    certificate_uploaded BOOLEAN DEFAULT FALSE,
    observaciones TEXT DEFAULT '',
    sancion_aplicada BOOLEAN DEFAULT FALSE
);
```

### Sectores disponibles

- **linea1**: Línea de Producción 1 (15 empleados)
- **linea2**: Línea de Producción 2 (12 empleados)
- **Mantenimiento**: Mantenimiento (6 empleados)
- **RH**: Recursos Humanos (7 empleados)

---

## ⚙️ Configuración Avanzada

### Variables de entorno

```bash
export TELEGRAM_TOKEN="tu_token_aqui"
export DATABASE_URL="sqlite:///./test.db"
export NGROK_AUTH_TOKEN="tu_token_ngrok"
```

### Personalizar reglas del sistema experto

Edita `expert/rules.json`:

```json
{
  "rules": [
    {
      "id": "custom_rule",
      "name": "Regla Personalizada",
      "condition": {...},
      "action": "custom_action",
      "message": "Mensaje personalizado",
      "priority": 6,
      "severity": "info"
    }
  ]
}
```

### Configurar deadlines personalizados

En `expert/rules.json` → `motivo_rules`:

```json
"ART": {
  "descripcion": "Accidente de trabajo",
  "requiere_certificado": true,
  "duracion_maxima": 365,
  "deadline_horas": 24
}
```

---

## 🚨 Solución de Problemas

### Bot no responde

1. Verificar servidor activo: `python main.py`
2. Verificar ngrok: `ngrok http 8000`
3. Reconfigurar webhook: `python setup_webhook.py`

### Error en base de datos

1. Hacer backup: `cp test.db backup.db`
2. Migrar: `python migrate_database.py`
3. Verificar estructura: `python db_query.py`

### Sistema experto no funciona

1. Verificar reglas: `cat expert/rules.json`
2. Probar motor: `python -c "from expert.engine import ExpertSystem; ExpertSystem().generate_report()"`
3. Verificar columnas nuevas en BD

### Webhooks con ngrok

```bash
# Problema: URL de ngrok cambia
# Solución: Reconfigurar webhook
python setup_webhook.py

# Problema: Error 429 Too Many Requests  
# Solución: Esperar o usar otro túnel
```

---

## 🔄 Mantenimiento

### Backup automático

```bash
# Backup diario
cp test.db backups/test_$(date +%Y%m%d).db

# Limpiar certificados antiguos (opcional)
find certificados/ -name "*.jpg" -mtime +365 -delete
```

### Monitoreo

```bash
# Ver logs del servidor
tail -f server.log

# Estadísticas del sistema experto
python -c "from expert.engine import ExpertSystem; print(ExpertSystem().generate_report())"

# Empleados activos
python load_employees.py list
```

### Actualizar empleados

```bash
# Cargar nuevos empleados
python load_employees.py load nuevos_empleados.csv

# Desactivar empleado (manual en BD)
sqlite3 test.db "UPDATE employees SET activo = 0 WHERE legajo = '890001'"
```

---

## 📊 Métricas y KPIs

El sistema proporciona las siguientes métricas:

- **Tasa de validación**: Empleados validados vs provisionales
- **Cumplimiento de certificados**: % de certificados entregados a tiempo
- **Patrones de ausencias**: Detección de comportamientos anómalos
- **Eficiencia del sistema**: Tiempo de respuesta y disponibilidad
- **Uso por sector**: Distribución de ausencias por departamento

---

## 🛡️ Seguridad

- ✅ **Tokens seguros** en variables de entorno
- ✅ **Validación de entrada** en todos los campos
- ✅ **Backup automático** antes de migraciones
- ✅ **Logs de auditoría** para todas las acciones
- ✅ **Control de acceso** por empleado validado

---

## 🤝 Contribuir

### Agregar nueva regla al sistema experto

1. Editar `expert/rules.json`
2. Agregar lógica en `expert/engine.py`
3. Probar con registros existentes
4. Documentar comportamiento esperado

### Agregar nuevo tipo de ausencia

1. Actualizar lista en `main.py`
2. Agregar reglas en `expert/rules.json`  
3. Actualizar documentación
4. Probar flujo completo

---

## 📈 Roadmap

- [ ] **Dashboard avanzado** con gráficos interactivos
- [ ] **Notificaciones automáticas** por WhatsApp/Email
- [ ] **Integración ERP** para sincronización de empleados
- [ ] **Machine Learning** para predicción de ausencias
- [ ] **API móvil** para app nativa
- [ ] **Reportes PDF** automáticos
- [ ] **Múltiples empresas** (multi-tenant)

---

## 📞 Soporte

- **Documentación técnica**: `MANUAL_SISTEMA.md`
- **Logs del sistema**: Consola del servidor
- **Verificación de salud**: `http://localhost:8000/api/registros`
- **Respaldo de emergencia**: Scripts de migración incluidos

---

## 📄 Licencia

Sistema desarrollado para gestión interna de ausencias laborales.

**Versión**: 2.0 (Sistema Experto)  
**Última actualización**: 2025-08-20  
**Estado**: ✅ Producción

---

## 🎯 Resumen Ejecutivo

**Sistema completo y funcional** que combina:

- 📱 **Interfaz conversacional** en Telegram
- 🤖 **Inteligencia artificial** para validación automática  
- 📊 **Dashboard web** para administración
- 🔍 **Trazabilidad completa** con códigos únicos
- ⚡ **Reglas de negocio** automatizadas
- 📈 **Métricas** y reportes en tiempo real

**¡Listo para usar en producción!** 🚀