# 📋 Sistema de Registro de Ausencias - Manual Completo

## 🎯 ¿Qué es este sistema?

Es un **bot de Telegram** que permite a los empleados registrar sus ausencias laborales de manera fácil y automática. Los datos se almacenan en una base de datos y pueden ser consultados por administradores.

## 🏗️ Arquitectura del Sistema

### **Componentes principales:**

- **Bot de Telegram** → Interfaz con usuarios
- **API FastAPI** → Servidor web y endpoints
- **Base de datos SQLite** → Almacenamiento de datos
- **Sistema de archivos** → Guardado de certificados médicos

### **Tecnologías:**

- Python 3.11+
- FastAPI (servidor web)
- python-telegram-bot (integración Telegram)
- SQLAlchemy (ORM base de datos)
- SQLite (base de datos)
- Ngrok (túnel público)

---

## 📁 Estructura de Archivos

```
tecnomyl-system/
├── main.py                 # Archivo principal del servidor
├── config.py              # Configuración (token, BD)
├── setup_webhook.py       # Configurar webhook de ngrok
├── view_records.py        # Consultar registros desde consola
├── db_query.py            # Herramienta de consulta BD
├── test_save.py           # Probar guardado manual
├── test.db                # Base de datos SQLite
├── requirements.txt       # Dependencias Python
├── models/
│   ├── __init__.py
│   ├── database.py        # Modelos de base de datos
│   └── config.py          # Configuración adicional
├── bot/
│   ├── __init__.py
│   └── handlers.py        # Manejadores del bot (vacío)
├── expert/
│   ├── __init__.py
│   ├── rules.json         # Reglas de negocio
│   └── engine.py          # Motor de reglas (no usado)
└── certificados/          # Carpeta para guardar imágenes
```

---

## 🚀 Instalación y Configuración

### **1. Requisitos previos:**

- Python 3.11 o superior
- Token de bot de Telegram (obtener de @BotFather)
- Ngrok instalado

### **2. Instalación:**

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar ngrok (ejemplo)
ngrok http 8000
```

### **3. Configuración del webhook:**

```bash
# Ejecutar script de configuración
python setup_webhook.py
# Ingresar URL de ngrok cuando se solicite
```

### **4. Iniciar el sistema:**

```bash
# Iniciar servidor principal
python main.py
```

---

## 👤 Uso del Sistema (Para Empleados)

### **Comandos disponibles:**

- `/start` → Iniciar registro de ausencia
- `/registros` → Ver mis ausencias registradas
- `/help` → Mostrar ayuda

### **Flujo de registro:**

1. **Iniciar:** Enviar `/start` al bot
2. **Nombre:** Escribir apellido y nombre completo
3. **Legajo:** Escribir número de legajo
4. **Motivo:** Seleccionar del 1 al 8:
   - 1. ART
   - 2. Licencia Enfermedad Familiar
   - 3. Licencia Enfermedad Personal
   - 4. Licencia por Fallecimiento Familiar
   - 5. Licencia por Matrimonio
   - 6. Licencia por Nacimiento
   - 7. Licencia por Paternidad
   - 8. Permiso Gremial
5. **Duración:** Escribir cantidad de días (número)
6. **Certificado** (si aplica):
   - Responder "si" o "no"
   - Si es "si": Enviar foto del certificado o escribir "saltar"
7. **Confirmación:** ✅ Ausencia registrada exitosamente

### **¿Qué motivos requieren certificado?**

- ✅ ART
- ✅ Licencia Enfermedad Familiar
- ✅ Licencia Enfermedad Personal
- ❌ Todos los demás NO requieren certificado

---

## 🔧 Administración del Sistema

### **1. Ver registros desde consola:**

```bash
python view_records.py
```

**Opciones:**

- Ver todos los registros
- Buscar por legajo específico
- Consultas SQL personalizadas

### **2. Dashboard web:**

**URL:** `http://localhost:8000` (o URL de ngrok)

- Ver todos los registros con estadísticas
- Enlaces directos a certificados guardados
- Interfaz visual amigable

### **3. API REST:**

```bash
# Ver todos los registros (JSON)
GET http://localhost:8000/api/registros

# Listar certificados
GET http://localhost:8000/certificados

# Ver certificado específico
GET http://localhost:8000/certificados/cert_12345_20240120_143052.jpg
```

### **4. Base de datos directa:**

```bash
# Usando el script de consultas
python db_query.py

# O usando SQLite directamente
sqlite3 test.db "SELECT * FROM absences ORDER BY created_at DESC LIMIT 10;"
```

---

## 🗃️ Estructura de Base de Datos

### **Tabla: `absences`**

```sql
CREATE TABLE absences (
    id INTEGER PRIMARY KEY,
    chat_id INTEGER,           -- ID de Telegram del usuario
    name TEXT,                 -- Apellido y nombre
    legajo TEXT,               -- Número de legajo
    motivo TEXT,               -- Tipo de ausencia
    duracion INTEGER,          -- Días de ausencia
    certificado TEXT,          -- Estado del certificado
    created_at DATETIME        -- Fecha de registro
);
```

### **Tabla: `conversation_states`**

```sql
CREATE TABLE conversation_states (
    chat_id INTEGER PRIMARY KEY,
    state TEXT,                -- Estado actual de la conversación
    last_updated DATETIME      -- Última actualización
);
```

---

## 📎 Sistema de Certificados

### **¿Cómo funciona?**

1. El usuario envía una **foto** al bot
2. Se guarda automáticamente en `/certificados/`
3. Nombre del archivo: `cert_[legajo]_[fecha]_[hora].jpg`
4. Se registra la ruta en la base de datos

### **Acceso a certificados:**

- **Dashboard web:** Enlaces clicables
- **API:** `GET /certificados/nombre_archivo.jpg`
- **Carpeta local:** `./certificados/`

---

## 🛠️ Configuración Técnica

### **archivo `config.py`:**

```python
TELEGRAM_TOKEN = "TU_TOKEN_AQUI"  # Token del bot
DATABASE_URL = "sqlite:///./test.db"  # Ruta de la BD
```

### **Puertos utilizados:**

- **8000:** Servidor FastAPI (webhook de Telegram)
- **4040:** Ngrok web interface (opcional)

### **Variables de entorno** (opcional):

```bash
export TELEGRAM_TOKEN="tu_token"
export DATABASE_URL="sqlite:///./test.db"
```

---

## 🚨 Solución de Problemas

### **El bot no responde:**

1. ✅ Verificar que el servidor esté ejecutándose
2. ✅ Verificar que ngrok esté activo
3. ✅ Verificar configuración del webhook: `python setup_webhook.py`

### **No se guardan registros:**

1. ✅ Verificar permisos de escritura en la BD
2. ✅ Verificar logs en la consola del servidor
3. ✅ Probar guardado manual: `python test_save.py`

### **Error con certificados:**

1. ✅ Verificar que existe la carpeta `certificados/`
2. ✅ Verificar permisos de escritura
3. ✅ El archivo debe ser una imagen (JPG/PNG)

### **Webhook desconfigurado:**

```bash
# Reconfigurar webhook
python setup_webhook.py
# Ingresar nueva URL de ngrok
```

---

## 📊 Monitoreo y Logs

### **Logs del servidor:**

- ✅ Guardado exitoso: `✅ Ausencia guardada para Juan Perez (Legajo: 12345)`
- ❌ Error de guardado: `❌ Error guardando ausencia: [detalle]`
- 📋 Estado de webhook: Se muestra al configurar

### **Estadísticas disponibles:**

- Total de registros por motivo
- Registros por empleado
- Ausencias por período
- Certificados guardados

---

## 🔄 Mantenimiento

### **Tareas regulares:**

1. **Backup de base de datos:**

   ```bash
   cp test.db backup_$(date +%Y%m%d).db
   ```
2. **Limpiar certificados antiguos** (opcional):

   ```bash
   find certificados/ -name "*.jpg" -mtime +365 -delete
   ```
3. **Verificar espacio en disco:**

   ```bash
   du -sh certificados/ test.db
   ```

### **Actualización del sistema:**

```bash
# Detener servidor
# Ctrl+C en la terminal donde corre main.py

# Actualizar código
git pull  # si usas git

# Reiniciar servidor  
python main.py
```

---

## 📞 Soporte Técnico

### **Información del sistema:**

- **Versión:** 1.0
- **Desarrollado con:** Python 3.11, FastAPI, SQLAlchemy
- **Compatibilidad:** Windows, Linux, macOS

### **Contacto:**

- Revisar logs en consola para diagnóstico
- Verificar archivos de configuración
- Probar scripts de diagnóstico incluidos

---

## 📝 Notas Adicionales

- El sistema mantiene el estado de conversación en memoria, se pierde al reiniciar
- Los certificados se almacenan localmente en la carpeta del proyecto
- La base de datos SQLite es un solo archivo, fácil de respaldar
- Ngrok genera URLs diferentes cada vez, reconfigurar webhook si es necesario
- El sistema funciona 24/7 mientras el servidor esté activo

¡Sistema listo para usar! 🚀
