# 🧠 Sistema Experto Avanzado - Documentación Técnica

## 📖 Descripción General

Sistema experto avanzado de gestión de ausencias laborales que combina **inteligencia artificial**, **aprendizaje automático** y **razonamiento lógico** para automatizar la validación, procesamiento y toma de decisiones sobre solicitudes de ausencias de empleados.

### ✨ Características Principales

- 🔍 **Motor de Inferencia Avanzado** con encadenamiento de reglas
- 🧠 **Sistema de Aprendizaje Basado en Casos (CBR)**
- 📝 **Explicaciones Detalladas** en lenguaje natural
- 🔐 **Sistema de Seguridad y Autenticación** robusto
- 📊 **Análisis Predictivo** basado en casos históricos
- ⚡ **Procesamiento en Tiempo Real** con alta performance

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                     SISTEMA EXPERTO AVANZADO                     │
├─────────────────┬─────────────────┬─────────────────┬─────────────┤
│                 │                 │                 │             │
│  MOTOR DE       │  SISTEMA CBR    │  EXPLICACIONES  │ SEGURIDAD   │
│  INFERENCIA     │  (Aprendizaje)  │  DETALLADAS     │ & AUTH      │
│                 │                 │                 │             │
│ • Encadenamiento│ • Casos Similares│ • Multi-nivel  │ • JWT       │
│ • AST Parsing   │ • Recomendaciones│ • Contextuales │ • API Keys  │
│ • Prioridades   │ • Patrones      │ • Adaptativas   │ • Permisos  │
└─────────────────┴─────────────────┴─────────────────┴─────────────┘
         │                   │                   │             │
         └───────────────────┼───────────────────┼─────────────┘
                             │                   │
         ┌───────────────────▼───────────────────▼─────────────┐
         │            SISTEMA INTEGRADO                        │
         │          (IntegratedExpertSystem)                   │
         └─────────────────────────────────────────────────────┘
                             │
         ┌───────────────────▼───────────────────────────────┐
         │                TELEGRAM BOT                       │
         │              +  FastAPI Server                    │
         └───────────────────────────────────────────────────┘
                             │
         ┌───────────────────▼───────────────────────────────┐
         │                SQLite Database                     │
         │       (Empleados + Ausencias + Casos + Seguridad) │
         └───────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

### 1. Motor de Inferencia Avanzado (`expert/inference_engine.py`)

**Características principales:**
- ✅ Evaluación segura de expresiones con **AST parsing**
- ✅ **Encadenamiento hacia adelante** con detección de loops
- ✅ Sistema de **prioridades** en reglas
- ✅ **Funciones temporales** especializadas
- ✅ Tracking completo de pasos de razonamiento

```python
# Ejemplo de uso
engine = InferenceEngine('expert/advanced_rules.json')
result = engine.forward_chaining(absence_facts)
print(f"Reglas disparadas: {len(result.steps)}")
```

**Reglas soportadas (12 reglas activas):**
1. **Certificado Faltante - Crítico** (Prioridad 1)
2. **Certificado Vencido** (Prioridad 2)  
3. **Duración Excesiva - ART** (Prioridad 3)
4. **Patrón de Ausencias Frecuentes** (Prioridad 4)
5. **Empleado Provisional - Ausencia Extendida** (Prioridad 5)
6. **ART en Fin de Semana** (Prioridad 6)
7. **Reporte Nocturno** (Prioridad 7)
8. **Certificado Recomendado** (Prioridad 8)
9. **Documentación Matrimonio** (Prioridad 9)
10. **Paternidad Extendida** (Prioridad 10)
11. **Regla Encadenada - Certificado y Duración** (Prioridad 11)
12. **Evaluación de Riesgo Integral** (Prioridad 12)

### 2. Sistema de Aprendizaje Basado en Casos (`expert/case_based_learning.py`)

**Funcionalidades CBR:**
- 🔍 **Búsqueda de casos similares** con algoritmo de similitud ponderada
- 📊 **Análisis predictivo** basado en patrones históricos
- 🎯 **Recomendaciones contextuales** con niveles de confianza
- 💾 **Almacenamiento persistente** de casos y feedback
- 📈 **Aprendizaje continuo** con validación experta

```python
# Ejemplo de uso
cbr = CaseBasedLearning()
recommendations = cbr.get_recommendations(current_facts)
case_id = cbr.store_case(facts, rules, actions, outcome)
```

**Características de similitud evaluadas:**
- **Motivo de ausencia** (peso: 25%)
- **Duración** (peso: 20%)
- **Ausencias último mes** (peso: 15%)
- **Estado de certificado** (peso: 15%)
- **Estado de validación** (peso: 10%)
- **Sector** (peso: 10%)
- **Plazo excedido** (peso: 5%)

### 3. Sistema de Explicaciones Detalladas (`expert/explanation_system.py`)

**Niveles de explicación:**
- **Básico**: Para empleados (resultado simple)
- **Medio**: Para RRHH (con contexto)
- **Detallado**: Para supervisores (con técnico)
- **Técnico**: Para administradores (completo + debugging)

```python
# Ejemplo de uso
generator = ExplanationGenerator()
explanation = generator.generate_explanation(
    inference_result, 
    ExplanationContext(user_type='hr', detail_level='detailed')
)
```

**Características:**
- ✅ **Multiidioma** (español/inglés)
- ✅ **Adaptativo** según tipo de usuario
- ✅ **Detección de encadenamiento** automática
- ✅ **Análisis de hechos utilizados**
- ✅ **Resumen ejecutivo** personalizable

### 4. Sistema de Seguridad y Autenticación (`security/auth_system.py`)

**Componentes de seguridad:**
- 🔐 **Autenticación JWT** con expiración configurable
- 🗝️ **Claves API** con permisos granulares
- 👤 **Gestión de usuarios** y roles
- 📝 **Auditoría completa** de eventos de seguridad
- 🛡️ **Protección contra ataques** (rate limiting, intentos fallidos)

```python
# Ejemplo de uso
security = SecurityManager()
success, user = security.authenticate_user('admin', 'password')
token = security.create_jwt_token(user)
api_key = security.create_api_key(user.user_id, 'My API Key', permissions)
```

**Roles y permisos:**
- **Admin**: Acceso completo (`all`)
- **HR Manager**: Gestión empleados, reportes (`view_absences`, `manage_employees`, `generate_reports`)
- **Supervisor**: Aprobaciones, validaciones
- **Employee**: Solo consulta personal

### 5. Sistema Experto Integrado (`expert/integrated_expert_system.py`)

**Funcionalidad principal:**
```python
expert_system = IntegratedExpertSystem()
result = expert_system.process_absence_request(absence_facts, user_type='hr')
```

**Salida completa del procesamiento:**
```json
{
    "case_id": "a2c17194fe8b",
    "outcome": "sanctioned",
    "processing_time": 0.006,
    "inference_result": {
        "rules_triggered": 5,
        "conclusions": ["Certificado Faltante - Crítico", "Certificado Vencido", ...],
        "actions_taken": ["Observación agregada: ...", "Sanción aplicada", ...],
        "execution_time": 0.002
    },
    "cbr_analysis": {
        "similar_cases_found": 3,
        "confidence": 0.56,
        "recommendations": [
            {
                "type": "outcome_prediction",
                "suggestion": "Outcome más probable: sanctioned",
                "confidence": 0.56,
                "reasoning": "Basado en 3 casos similares"
            }
        ]
    },
    "explanation": "[ENGINE] El sistema analizó 5 reglas...",
    "system_observations": [
        "[ERROR] Certificado médico obligatorio para ausencias > 3 días",
        "[WARNING] Patrón de ausencias frecuentes detectado - Revisar con RRHH"
    ],
    "requires_human_review": true,
    "risk_level": "HIGH",
    "next_actions": [
        "Notificar sanción al empleado y RRHH",
        "Documentar en expediente personal"
    ]
}
```

---

## 📊 Base de Datos Extendida

### Tablas del Sistema Experto

#### `cases` - Casos de aprendizaje CBR
```sql
CREATE TABLE cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT UNIQUE NOT NULL,
    facts TEXT NOT NULL,                 -- JSON con hechos del caso
    rules_applied TEXT NOT NULL,         -- JSON con reglas disparadas
    actions_taken TEXT NOT NULL,         -- JSON con acciones ejecutadas
    outcome TEXT NOT NULL,               -- Resultado final
    feedback TEXT,                       -- Feedback experto
    similarity_features TEXT NOT NULL,   -- JSON con características de similitud
    timestamp DATETIME NOT NULL,
    expert_validation BOOLEAN DEFAULT 0
);
```

#### `users` - Usuarios del sistema
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,         -- Hash PBKDF2 + salt
    role TEXT NOT NULL,                  -- admin, hr, supervisor, employee
    permissions TEXT NOT NULL,           -- JSON array de permisos
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME NOT NULL,
    last_login DATETIME,
    failed_attempts INTEGER DEFAULT 0
);
```

#### `api_keys` - Claves API
```sql
CREATE TABLE api_keys (
    key_id TEXT PRIMARY KEY,
    key_hash TEXT UNIQUE NOT NULL,       -- Hash SHA256 de la clave
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    permissions TEXT NOT NULL,           -- JSON array de permisos específicos
    created_at DATETIME NOT NULL,
    expires_at DATETIME,
    is_active BOOLEAN DEFAULT 1,
    usage_count INTEGER DEFAULT 0,
    last_used DATETIME
);
```

#### `security_logs` - Auditoría de seguridad
```sql
CREATE TABLE security_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    user_id TEXT,
    action TEXT NOT NULL,               -- login_success, api_key_created, etc.
    ip_address TEXT,
    success BOOLEAN NOT NULL,
    details TEXT
);
```

### Tablas Existentes Actualizadas

#### `absences` - Ausencias con campos del sistema experto
```sql
-- Campos originales
id, chat_id, name, legajo, motivo, duracion, certificado, created_at

-- Campos del sistema experto
employee_id INTEGER,              -- FK a tabla employees
registration_code TEXT UNIQUE,   -- Código único del registro
validation_status TEXT DEFAULT 'provisional',  -- validated/provisional
certificate_deadline DATETIME,   -- Deadline para entrega certificado
certificate_uploaded BOOLEAN DEFAULT FALSE,
observaciones TEXT DEFAULT '',   -- Observaciones del sistema experto
sancion_aplicada BOOLEAN DEFAULT FALSE
```

---

## 🚀 Instalación y Configuración

### 1. Dependencias nuevas requeridas
```bash
pip install PyJWT numpy
```

### 2. Migración de base de datos
```bash
python migrate_database.py
```

### 3. Configuración del sistema experto
Archivo `expert/advanced_rules.json` contiene todas las reglas configurables del sistema.

### 4. Usuarios por defecto creados automáticamente:
- **admin** / admin123 (rol: admin, permisos: all)
- **hr_manager** / hr123 (rol: hr, permisos: view_absences, manage_employees, generate_reports)

---

## 🔄 Flujo de Procesamiento Avanzado

### Procesamiento de una solicitud de ausencia:

1. **📥 Recepción**: Datos de ausencia del bot Telegram
2. **🔍 Análisis CBR**: Búsqueda de casos similares y recomendaciones
3. **⚡ Inferencia**: Motor de reglas evalúa y encadena reglas
4. **🎯 Decisión**: Determina outcome basado en reglas + CBR
5. **📝 Explicación**: Genera explicación adaptada al usuario
6. **💾 Almacenamiento**: Guarda caso para aprendizaje futuro
7. **📊 Respuesta**: Retorna resultado completo con recomendaciones

### Posibles Outcomes:
- `auto_approved` - Aprobación automática sin problemas
- `approved_with_conditions` - Aprobado con observaciones
- `requires_approval` - Requiere aprobación supervisor
- `sanctioned` - Sanción aplicada automáticamente  
- `rejected` - Rechazado por incumplimiento crítico

### Niveles de Riesgo:
- **MINIMAL** (0 puntos) - Sin factores de riesgo
- **LOW** (1-2 puntos) - Riesgo bajo, seguimiento normal
- **MEDIUM** (3-4 puntos) - Riesgo medio, atención requerida
- **HIGH** (5+ puntos) - Alto riesgo, revisión inmediata

---

## 📈 Métricas y KPIs del Sistema Experto

### Métricas de Inferencia:
- **Reglas disparadas por caso**: Promedio y distribución
- **Tiempo de procesamiento**: < 50ms objetivo
- **Encadenamientos detectados**: Casos complejos identificados
- **Distribución de outcomes**: Patrones de decisiones

### Métricas de CBR:
- **Casos almacenados**: Base de conocimiento acumulada
- **Similitud promedio**: Calidad de matches encontrados
- **Confianza de recomendaciones**: Precisión predictiva
- **Tasa de validación experta**: Casos confirmados por humanos

### Métricas de Seguridad:
- **Intentos de login fallidos**: Detección de ataques
- **Uso de API keys**: Patrones de consumo
- **Eventos de seguridad**: Monitoreo de incidentes
- **Sesiones activas**: Carga del sistema

---

## 🛠️ APIs y Endpoints

### API del Sistema Experto:
```python
# Procesar ausencia con sistema experto
result = expert_system.process_absence_request(
    absence_facts={
        'motivo': 'ART',
        'duracion': 10,
        'ausencias_ultimo_mes': 3,
        'certificate_uploaded': False,
        'validation_status': 'validated'
    },
    user_type='hr'
)
```

### API de Seguridad:
```python
# Autenticación y autorización
@require_auth('view_absences')
def get_absence_data(auth_token=None, current_user=None):
    # Función protegida por autenticación JWT
    return absence_data

@require_api_key('manage_employees')  
def create_employee(api_key=None, current_user=None):
    # Función protegida por API key
    return result
```

---

## 🔧 Configuración Avanzada

### Archivo `expert/advanced_rules.json`:
```json
{
  "rules": [
    {
      "id": "cert_missing_critical",
      "name": "Certificado Faltante - Crítico", 
      "condition": "motivo in ['ART', 'Licencia Enfermedad Personal'] and not certificate_uploaded and duracion > 3",
      "action": "add_observacion('Certificado médico obligatorio para ausencias > 3 días')",
      "priority": 1,
      "severity": "error"
    }
  ]
}
```

### Variables de configuración:
- **JWT_SECRET**: Clave secreta para tokens (auto-generada)
- **SESSION_TIMEOUT**: 8 horas por defecto
- **MAX_FAILED_ATTEMPTS**: 5 intentos antes de bloqueo
- **CBR_MIN_SIMILARITY**: 0.3 umbral mínimo de similitud
- **INFERENCE_MAX_ITERATIONS**: 100 iteraciones máximas

---

## 🧪 Testing y Validación

### Tests incluidos:
```bash
# Test motor de inferencia
python -m expert.inference_engine

# Test sistema CBR  
python -m expert.case_based_learning

# Test explicaciones
python -m expert.explanation_system

# Test sistema integrado
python -m expert.integrated_expert_system

# Test seguridad
python -m security.auth_system
```

### Validaciones automáticas:
- ✅ **Consistencia de reglas**: Sin conflictos lógicos
- ✅ **Seguridad de expresiones**: Solo operadores permitidos
- ✅ **Integridad de datos**: Validación de tipos y rangos
- ✅ **Performance**: Tiempo de respuesta < 50ms
- ✅ **Encadenamientos**: Detección de loops infinitos

---

## 🚨 Monitoreo y Alertas

### Eventos críticos monitoreados:
- **Intentos de login sospechosos** (múltiples fallos)
- **API keys comprometidas** (uso anómalo)
- **Reglas con alta frecuencia de disparo** (posibles problemas)
- **Casos con baja confianza CBR** (requieren revisión)
- **Sanciones automáticas** (notificación inmediata)

### Logs de auditoría:
```sql
-- Ver eventos de seguridad recientes
SELECT * FROM security_logs 
WHERE timestamp > datetime('now', '-1 hour')
ORDER BY timestamp DESC;

-- Casos procesados con alto riesgo
SELECT case_id, outcome, similarity_features 
FROM cases 
WHERE outcome IN ('sanctioned', 'rejected')
ORDER BY timestamp DESC;
```

---

## 📚 Documentación de Desarrollo

### Agregar nueva regla:
1. Editar `expert/advanced_rules.json`
2. Definir condición, acción y prioridad
3. Probar con casos de prueba
4. Validar no genera loops infinitos

### Agregar nuevo permiso:
1. Definir permiso en `SecurityManager`
2. Asignar a roles apropiados  
3. Usar decorador `@require_auth('nuevo_permiso')`
4. Probar autenticación y autorización

### Personalizar explicaciones:
1. Editar templates en `ExplanationGenerator`
2. Agregar lógica específica por tipo de regla
3. Probar con diferentes niveles de detalle
4. Validar multiidioma si aplica

---

## 📊 Ejemplos de Casos Reales

### Caso 1: ART con certificado vencido
```json
{
  "facts": {
    "motivo": "ART",
    "duracion": 12,
    "ausencias_ultimo_mes": 3,
    "certificate_uploaded": false,
    "certificate_deadline": "2025-08-18T10:00:00",
    "validation_status": "validated"
  },
  "outcome": "sanctioned",
  "rules_triggered": 5,
  "cbr_confidence": 0.84,
  "risk_level": "HIGH"
}
```

### Caso 2: Ausencia familiar simple
```json
{
  "facts": {
    "motivo": "Licencia por Nacimiento",
    "duracion": 2,
    "ausencias_ultimo_mes": 0,
    "certificate_uploaded": true,
    "validation_status": "validated"
  },
  "outcome": "auto_approved",
  "rules_triggered": 0,
  "cbr_confidence": 0.95,
  "risk_level": "MINIMAL"
}
```

---

## 🔮 Capacidades Futuras

### Próximas mejoras planificadas:
- **Machine Learning avanzado** con scikit-learn
- **Integración Power BI** para dashboards ejecutivos
- **API REST completa** con FastAPI
- **Notificaciones automáticas** WhatsApp/Email
- **Multitenancy** para múltiples empresas
- **Interfaz web administrativa** completa

### Extensibilidad:
El sistema está diseñado para ser fácilmente extensible:
- **Nuevas reglas** mediante JSON
- **Nuevos tipos de casos** con minimal coding
- **Nuevos algoritmos CBR** intercambiables
- **Nuevos métodos de autenticación** (OAuth, LDAP)
- **Nuevas fuentes de datos** (APIs externas)

---

## 📞 Soporte Técnico

### Archivos de configuración críticos:
- `expert/advanced_rules.json` - Reglas del sistema experto
- `test.db` - Base de datos principal
- `config.py` - Configuración general del sistema

### Comandos de diagnóstico:
```bash
# Verificar salud del sistema experto
python -c "from expert.integrated_expert_system import IntegratedExpertSystem; print(IntegratedExpertSystem().get_system_stats())"

# Verificar seguridad
python -c "from security.auth_system import SecurityManager; print(SecurityManager().get_security_stats())"

# Ver casos CBR recientes
python -c "from expert.case_based_learning import CaseBasedLearning; cbr = CaseBasedLearning(); print(f'Casos: {len(cbr.cases)}')"
```

### Respaldos recomendados:
- **Base de datos**: `test.db` (diario)
- **Reglas**: `expert/advanced_rules.json` (antes de cambios)
- **Logs de seguridad**: Tabla `security_logs` (semanal)

---

## 📄 Versión y Estado

**Versión actual**: 2.0 (Sistema Experto Avanzado)  
**Fecha**: 2025-08-20  
**Estado**: ✅ **Producción - Completamente Funcional**

**Componentes implementados:**
- ✅ Motor de inferencia avanzado con AST parsing
- ✅ Sistema CBR de aprendizaje automático  
- ✅ Explicaciones detalladas multi-nivel
- ✅ Seguridad y autenticación robusta
- ✅ Integración completa con sistema existente
- ✅ Base de datos extendida y migrada
- ✅ Tests automatizados y validaciones

**Listo para:**
- 🚀 Integración con bot Telegram existente
- 📊 Conexión con Power BI para dashboards
- 🔌 APIs REST para sistemas externos  
- 📈 Escalado a mayor volumen de datos
- 🎯 Implementación en producción

---

*Sistema desarrollado para automatizar completamente la gestión inteligente de ausencias laborales con capacidades de inteligencia artificial y aprendizaje automático.*