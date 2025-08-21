# 🧠 Módulo de Adquisición de Conocimiento - Documentación

## 📖 Resumen

Sistema implementado para permitir a **usuarios no técnicos** (ej: personal de RRHH) agregar, editar y gestionar reglas del sistema experto sin necesidad de modificar archivos JSON manualmente.

---

## ✅ Componentes Implementados

### 1. 🔧 **Gestor de Reglas Backend** (`expert/rules_manager.py`)

**Funcionalidades principales:**
- ✅ **Validación completa** de reglas antes de guardar
- ✅ **Sistema de backups automáticos** antes de cada cambio
- ✅ **CRUD completo** (Crear, Leer, Actualizar, Eliminar)
- ✅ **Validaciones de seguridad** para prevenir código malicioso
- ✅ **Sugerencias inteligentes** para usuarios no técnicos

**Validaciones implementadas:**
- **ID único**: No permite IDs duplicados
- **Sintaxis de condiciones**: Valida expresiones lógicas con AST
- **Acciones permitidas**: Solo funciones whitelistadas
- **Prioridades válidas**: Rango 1-100
- **Severidad correcta**: info, warning, error

### 2. 🌐 **Interfaz Web Completa**

#### **Formulario de Creación** (`templates/rules_form.html`)
- ✅ Interfaz intuitiva con ayudas contextuales
- ✅ **Ejemplos dinámicos** de condiciones y acciones
- ✅ **Validación en tiempo real** con JavaScript
- ✅ **Tooltips y guías** para cada campo
- ✅ **Diseño responsive** para mobile/desktop

#### **Lista y Gestión** (`templates/rules_list.html`)
- ✅ **Dashboard completo** con estadísticas en tiempo real
- ✅ **Búsqueda avanzada** por ID, nombre, condición
- ✅ **Filtros** por severidad y prioridad
- ✅ **Edición inline** con modal dinámico
- ✅ **Eliminación segura** con confirmación

### 3. 🔌 **API REST Completa** (`api/rules_endpoints.py`)

**Endpoints disponibles:**
- `GET /rules` - Página de lista de reglas
- `GET /rules/new` - Formulario de nueva regla
- `GET /api/rules` - Obtener todas las reglas (JSON)
- `POST /api/rules` - Crear nueva regla
- `PUT /api/rules/{id}` - Actualizar regla existente
- `DELETE /api/rules/{id}` - Eliminar regla
- `GET /api/rules/suggestions` - Obtener sugerencias

**Características:**
- ✅ **Manejo de formularios HTML** y JSON
- ✅ **Validación robusta** antes de guardar
- ✅ **Respuestas estructuradas** con códigos HTTP apropiados
- ✅ **Integración con sistema de seguridad**

### 4. 🔗 **Integración con Sistema Principal**

- ✅ **Enlaces en dashboard principal** (main.py)
- ✅ **Rutas configuradas automáticamente**
- ✅ **Sistema de backups integrado**
- ✅ **Compatible con sistema experto existente**

---

## 🚀 Cómo Usar el Sistema

### Para Usuarios No Técnicos (RRHH):

#### **Crear Nueva Regla:**
1. Acceder a: `http://localhost:8000/rules/new`
2. Completar formulario intuitivo:
   - **ID único**: ej. `cert_missing_personal`
   - **Nombre**: ej. `Certificado Personal Faltante`
   - **Condición**: ej. `motivo == 'Licencia Enfermedad Personal' and duracion > 3`
   - **Acción**: ej. `add_observacion('Certificado requerido')`
   - **Prioridad**: 1-100 (menor = mayor prioridad)
   - **Severidad**: info/warning/error

#### **Gestionar Reglas Existentes:**
1. Acceder a: `http://localhost:8000/rules`
2. **Buscar** reglas por texto
3. **Filtrar** por severidad o prioridad
4. **Editar** haciendo clic en el botón de lápiz
5. **Eliminar** con confirmación de seguridad

#### **Ver Estadísticas:**
- Dashboard muestra total de reglas
- Distribución por severidad
- Backups disponibles
- Última actualización

---

## 📋 Variables y Funciones Disponibles

### **Variables del Sistema:**
```javascript
motivo                  // Tipo de ausencia
duracion               // Días de ausencia  
ausencias_ultimo_mes   // Ausencias previas
certificate_uploaded   // Si subió certificado
validation_status      // 'validated' o 'provisional'
sector                // Departamento del empleado
current_hour          // Hora actual (0-23)
```

### **Funciones Temporales:**
```javascript
hours_since(fecha)     // Horas transcurridas desde fecha
days_since(fecha)      // Días transcurridos desde fecha
is_weekend()          // True si es fin de semana
```

### **Acciones Permitidas:**
```javascript
add_observacion('mensaje')           // Agregar observación
mark_sanction()                     // Aplicar sanción automática
require_approval()                  // Requiere aprobación supervisor
set_fact('nombre', 'valor')         // Establecer hecho personalizado
```

---

## 🛡️ Seguridad y Validaciones

### **Prevención de Código Malicioso:**
- ✅ **Whitelist de acciones** - Solo funciones permitidas
- ✅ **AST parsing seguro** - Sin eval() directo
- ✅ **Validación de sintaxis** antes de guardar
- ✅ **Sandboxing** de expresiones lógicas

### **Sistema de Backups:**
- ✅ **Backup automático** antes de cada cambio
- ✅ **Nombres con timestamp** para trazabilidad
- ✅ **Recuperación fácil** en caso de errores
- ✅ **Almacenamiento en** `expert/backups/`

### **Validaciones de Entrada:**
- ✅ **IDs únicos** obligatorios
- ✅ **Sintaxis correcta** en condiciones
- ✅ **Rangos válidos** en prioridades (1-100)
- ✅ **Valores permitidos** en severidad
- ✅ **Longitud máxima** en campos de texto

---

## 📊 Ejemplos de Uso Real

### **Ejemplo 1: Certificado Personal Obligatorio**
```json
{
  "id": "cert_personal_obligatorio",
  "name": "Certificado Personal Obligatorio",
  "condition": "motivo == 'Licencia Enfermedad Personal' and duracion > 3 and not certificate_uploaded",
  "action": "add_observacion('Certificado médico obligatorio para ausencias > 3 días')",
  "priority": 5,
  "severity": "error"
}
```

### **Ejemplo 2: Patrón de Ausencias Sospechoso**
```json
{
  "id": "patron_ausencias_viernes",
  "name": "Patrón Ausencias en Viernes",
  "condition": "ausencias_ultimo_mes >= 3 and is_weekend()",
  "action": "add_observacion('Patrón sospechoso - Revisar ausencias en viernes')",
  "priority": 15,
  "severity": "warning"
}
```

### **Ejemplo 3: Escalamiento Automático**
```json
{
  "id": "escalamiento_duracion_extrema",
  "name": "Escalamiento por Duración Extrema",
  "condition": "duracion > 30 and validation_status == 'validated'",
  "action": "require_approval()",
  "priority": 8,
  "severity": "warning"
}
```

---

## 🔧 Configuración Técnica

### **Archivos Creados:**
```
expert/
├── rules_manager.py          # Gestor backend de reglas
└── backups/                  # Backups automáticos
    ├── rules_backup_20250821_070813.json
    └── ...

api/
└── rules_endpoints.py        # API REST endpoints

templates/
├── rules_form.html          # Formulario de creación
└── rules_list.html          # Lista y gestión

main.py                      # Integración con servidor principal
```

### **Dependencias Agregadas:**
```bash
pip install python-multipart  # Para manejo de formularios HTML
```

### **Configuración en main.py:**
```python
from api.rules_endpoints import RulesAPI

# Configurar API de reglas
rules_api = RulesAPI()
rules_api.setup_routes(app)
```

---

## 📈 Métricas y Monitoreo

### **Estadísticas Disponibles:**
- **Total de reglas activas**
- **Distribución por severidad** (error/warning/info)
- **Rango de prioridades** (min/max)
- **Backups disponibles**
- **Fecha última actualización**

### **Logs Automáticos:**
```
[RULES] Backup creado: expert/backups/rules_backup_20250821_070813.json
[RULES] Reglas guardadas exitosamente
[RULES] Error en validación: Condición inválida
```

---

## 🚨 Solución de Problemas

### **Error: "Regla con ID ya existe"**
- **Causa**: Intentar crear regla con ID duplicado
- **Solución**: Usar ID único diferente

### **Error: "Condición inválida"**
- **Causa**: Sintaxis incorrecta en expresión lógica
- **Solución**: Revisar ejemplos y usar operadores válidos

### **Error: "Acción no permitida"**
- **Causa**: Usar función no whitelistada
- **Solución**: Usar solo acciones permitidas del sistema

### **Error: "No se puede guardar archivo"**
- **Causa**: Permisos de escritura o archivo en uso
- **Solución**: Verificar permisos y cerrar editores de texto

---

## 📱 URLs de Acceso

### **Para Usuarios Finales:**
- 🏠 **Dashboard Principal**: `http://localhost:8000/`
- 📋 **Lista de Reglas**: `http://localhost:8000/rules`
- ➕ **Nueva Regla**: `http://localhost:8000/rules/new`

### **Para Desarrolladores:**
- 📊 **API Reglas**: `http://localhost:8000/api/rules`
- 💡 **Sugerencias**: `http://localhost:8000/api/rules/suggestions`
- ✅ **Validación**: `http://localhost:8000/api/rules/validate`

---

## ✅ Estado del Sistema

**🎯 COMPLETAMENTE IMPLEMENTADO Y FUNCIONAL**

- ✅ Backend de gestión con validaciones robustas
- ✅ Interfaz web intuitiva para usuarios no técnicos
- ✅ API REST completa para integraciones
- ✅ Sistema de backups automáticos
- ✅ Integración con sistema experto existente
- ✅ Pruebas exitosas y validaciones funcionando
- ✅ Documentación completa

**🚀 LISTO PARA PRODUCCIÓN**

El sistema permite a personal de RRHH gestionar reglas del sistema experto de forma segura e intuitiva, sin conocimientos técnicos, con validaciones automáticas y backups de seguridad.

---

## 🎓 Próximos Pasos Recomendados

1. **Capacitación del personal** en el uso de la interfaz web
2. **Configuración de reglas específicas** según políticas de la empresa
3. **Monitoreo inicial** de reglas creadas por usuarios
4. **Feedback y mejoras** basadas en uso real
5. **Integración con Power BI** para dashboards ejecutivos

---

*Sistema desarrollado para democratizar la gestión de conocimiento en el sistema experto de ausencias laborales.*