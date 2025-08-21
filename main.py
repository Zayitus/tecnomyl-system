# main.py
from models.database import Base 
from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import uvicorn
from pydantic import BaseModel
import json
import os
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import config
from models.database import engine, SessionLocal, Absence, ConversationState, Employee
from utils import generate_registration_code, get_sector_display_name

# Importar módulos del sistema experto
from api.rules_endpoints import RulesAPI

app = FastAPI()
bot = Bot(token=config.TELEGRAM_TOKEN)

# Inicializar la base de datos (crea tablas si no existen)
Base.metadata.create_all(bind=engine)

# Diccionario para mantener el estado de las conversaciones en memoria
conversation_states = {}


async def handle_update(update: Update):
    if not update.message:
        return
    
    chat_id = update.effective_chat.id
    text = update.message.text if update.message.text else ""
    
    # Manejar fotos (certificados)
    if update.message.photo:
        await handle_certificate_photo(update, chat_id)
        return
    
    # Obtener o inicializar el estado
    if chat_id not in conversation_states:
        conversation_states[chat_id] = {
            "step": "start",
            "data": {}
        }
    
    state = conversation_states[chat_id]
    
    # Flujo de la conversación
    if state["step"] == "start":
        await bot.send_message(chat_id=chat_id, text="Apellido y Nombre:")
        state["step"] = "name"
    
    elif state["step"] == "name":
        # Guardar el nombre
        state["data"]["name"] = text
        await bot.send_message(chat_id=chat_id, text="Legajo:")
        state["step"] = "legajo"
    
    elif state["step"] == "legajo":
        legajo = text.strip()
        
        # Validar formato de legajo
        if not legajo.isdigit() or len(legajo) < 4:
            await bot.send_message(
                chat_id=chat_id,
                text="❌ Formato de legajo inválido. Debe ser un número de al menos 4 dígitos.\n\nIntenta nuevamente:"
            )
            return
        
        # Buscar empleado en base de datos
        db = SessionLocal()
        try:
            employee = db.query(Employee).filter(Employee.legajo == legajo).first()
            
            if employee and employee.activo:
                # Empleado VALIDADO
                state["data"]["legajo"] = legajo
                state["data"]["employee_id"] = employee.id
                state["data"]["validated"] = True
                state["data"]["employee_name"] = employee.nombre
                state["data"]["sector"] = employee.sector
                
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ **Legajo validado**\n\n"
                         f"👤 **Empleado:** {employee.nombre}\n"
                         f"🏢 **Sector:** {get_sector_display_name(employee.sector)}\n"
                         f"🆔 **Legajo:** {employee.legajo}\n\n"
                         f"¿El nombre es correcto? Responde **'si'** para continuar o **'no'** para corregir:"
                )
                state["step"] = "confirm_employee"
                
            elif employee and not employee.activo:
                # Empleado INACTIVO
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ **Empleado inactivo**\n\n"
                         f"El legajo {legajo} corresponde a {employee.nombre} pero está marcado como inactivo.\n\n"
                         f"Contacta a Recursos Humanos para más información."
                )
                # Reiniciar conversación
                del conversation_states[chat_id]
                return
                
            else:
                # Empleado NO ENCONTRADO
                state["data"]["legajo"] = legajo
                state["data"]["validated"] = False
                state["data"]["employee_id"] = None
                
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ **Legajo no encontrado**\n\n"
                         f"El legajo **{legajo}** no está registrado en el sistema.\n\n"
                         f"¿Deseas continuar como **registro provisional**?\n"
                         f"- **'si'** → Continuar (se requerirá validación posterior)\n"
                         f"- **'no'** → Cancelar y verificar el legajo"
                )
                state["step"] = "confirm_provisional"
                
        finally:
            db.close()
    
    elif state["step"] == "confirm_employee":
        # Confirmar datos del empleado validado
        if text.lower().strip() in ["si", "sí", "s", "yes"]:
            await bot.send_message(
                chat_id=chat_id,
                text="✅ Perfecto. Ahora selecciona el motivo de tu ausencia:"
            )
            state["step"] = "show_motivos"
        else:
            await bot.send_message(
                chat_id=chat_id,
                text="❌ Datos incorrectos. Por favor, ingresa tu nombre completo manualmente:"
            )
            state["step"] = "manual_name"
    
    elif state["step"] == "confirm_provisional":
        # Confirmar registro provisional
        if text.lower().strip() in ["si", "sí", "s", "yes"]:
            await bot.send_message(
                chat_id=chat_id,
                text="⚠️ **Registro Provisional Activado**\n\n"
                     "Tu ausencia se registrará como **provisional** y requerirá validación posterior por RRHH.\n\n"
                     "Ingresa tu nombre completo:"
            )
            state["step"] = "manual_name"
        else:
            await bot.send_message(
                chat_id=chat_id,
                text="❌ Registro cancelado.\n\n"
                     "Verifica tu legajo con Recursos Humanos y vuelve a intentar.\n\n"
                     "Usa /start para comenzar nuevamente."
            )
            del conversation_states[chat_id]
    
    elif state["step"] == "manual_name":
        # Guardar nombre ingresado manualmente
        state["data"]["name"] = text
        await bot.send_message(
            chat_id=chat_id,
            text="✅ Nombre registrado. Ahora selecciona el motivo de tu ausencia:"
        )
        state["step"] = "show_motivos"
    
    elif state["step"] == "show_motivos":
        # Mostrar opciones de motivos
        options = [
            "ART",
            "Licencia Enfermedad Familiar",
            "Licencia Enfermedad Personal",
            "Licencia por Fallecimiento Familiar",
            "Licencia por Matrimonio",
            "Licencia por Nacimiento",
            "Licencia por Paternidad",
            "Permiso Gremial"
        ]
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
        
        await bot.send_message(
            chat_id=chat_id,
            text=f"¿Cuál es el motivo de tu ausencia?\n{options_text}"
        )
        state["step"] = "motivo"
    
    elif state["step"] == "motivo":
        # Procesar la selección del motivo
        try:
            choice_num = int(text) - 1
            options = [
                "ART",
                "Licencia Enfermedad Familiar", 
                "Licencia Enfermedad Personal",
                "Licencia por Fallecimiento Familiar",
                "Licencia por Matrimonio",
                "Licencia por Nacimiento",
                "Licencia por Paternidad",
                "Permiso Gremial"
            ]
            
            if 0 <= choice_num < len(options):
                state["data"]["motivo"] = options[choice_num]
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"Motivo seleccionado: {options[choice_num]}\n\n¿Cuántos días durará la ausencia?"
                )
                state["step"] = "duracion"
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text="Por favor, selecciona un número válido (1-8):"
                )
        except ValueError:
            await bot.send_message(
                chat_id=chat_id,
                text="Por favor, ingresa solo el número de la opción (1-8):"
            )
    
    elif state["step"] == "duracion":
        # Validar y guardar la duración
        try:
            duracion = int(text)
            if duracion <= 0:
                await bot.send_message(
                    chat_id=chat_id,
                    text="La duración debe ser mayor a 0 días. Intenta nuevamente:"
                )
                return
                
            state["data"]["duracion"] = duracion
            
            # Preguntar por certificado si es necesario
            motivo = state["data"]["motivo"]
            if motivo in ["ART", "Licencia Enfermedad Familiar", "Licencia Enfermedad Personal"]:
                await bot.send_message(
                    chat_id=chat_id,
                    text="¿Tienes certificado médico? (Responde 'si' o 'no')"
                )
                state["step"] = "certificado"
            else:
                # Guardar directamente si no necesita certificado
                await save_absence_data(chat_id, state["data"])
                # Limpiar estado
                del conversation_states[chat_id]
                
        except ValueError:
            await bot.send_message(
                chat_id=chat_id,
                text="Por favor, ingresa un número válido de días:"
            )
    
    elif state["step"] == "certificado":
        # Manejar respuesta sobre certificado
        respuesta = text.lower().strip()
        if respuesta in ["si", "sí", "s"]:
            state["data"]["certificado"] = "Pendiente de envío"
            await bot.send_message(
                chat_id=chat_id,
                text="📎 Por favor, envía una foto del certificado médico o escribe 'saltar' para continuar sin certificado."
            )
            state["step"] = "upload_certificado"
        elif respuesta in ["no", "n"]:
            state["data"]["certificado"] = "No aplica"
            await save_absence_data(chat_id, state["data"])
            # Limpiar estado
            del conversation_states[chat_id]
        else:
            await bot.send_message(
                chat_id=chat_id,
                text="Por favor, responde 'si' o 'no':"
            )
    
    elif state["step"] == "upload_certificado":
        # Manejar upload de certificado o saltar
        if text.lower().strip() == "saltar":
            state["data"]["certificado"] = "No enviado"
        else:
            # Aquí podrías manejar la foto del certificado
            state["data"]["certificado"] = f"Recibido: {text}"
        
        await save_absence_data(chat_id, state["data"])
        # Limpiar estado
        del conversation_states[chat_id]

async def save_absence_data(chat_id, data):
    """Guarda los datos de ausencia en la base de datos"""
    from datetime import timedelta
    
    db = SessionLocal()
    try:
        # Generar código de registro
        validated = data.get("validated", False)
        registration_code = generate_registration_code(data["legajo"], validated)
        
        # Calcular deadline para certificado si es necesario
        certificate_deadline = None
        motivo = data["motivo"]
        if motivo in ["ART", "Licencia Enfermedad Familiar", "Licencia Enfermedad Personal"]:
            certificate_deadline = datetime.now() + timedelta(hours=24)
        
        # Usar nombre del empleado validado si está disponible
        final_name = data.get("employee_name", data.get("name", "Nombre no especificado"))
        
        absence = Absence(
            chat_id=chat_id,
            name=final_name,
            legajo=data["legajo"],
            motivo=data["motivo"],
            duracion=data["duracion"],
            certificado=data.get("certificado", "No aplica"),
            created_at=datetime.now(),
            
            # Nuevos campos del sistema experto
            employee_id=data.get("employee_id"),
            registration_code=registration_code,
            validation_status="validated" if validated else "provisional",
            certificate_deadline=certificate_deadline,
            certificate_uploaded=("Archivo guardado:" in data.get("certificado", "")),
            observaciones="",
            sancion_aplicada=False
        )
        
        db.add(absence)
        db.commit()
        
        # Obtener el ID de la ausencia recién creada
        db.refresh(absence)
        absence_id = absence.id
        
        # Aplicar reglas del sistema experto
        from expert.engine import ExpertSystem
        expert = ExpertSystem()
        expert_findings = expert.apply_expert_rules(absence_id)
        
        # Mensaje mejorado con código de registro
        status = "VALIDADO" if validated else "PROVISIONAL"
        print(f"✅ Ausencia guardada: {final_name} (Legajo: {data['legajo']}) - {status} - Código: {registration_code}")
        
        # Preparar mensaje con alertas del sistema experto
        base_message = (f"✅ **Ausencia registrada exitosamente**\n\n"
                       f"📋 **Código de registro:** `{registration_code}`\n"
                       f"👤 **Empleado:** {final_name}\n"
                       f"🆔 **Legajo:** {data['legajo']}\n"
                       f"📅 **Motivo:** {data['motivo']}\n"
                       f"⏰ **Duración:** {data['duracion']} días\n"
                       f"🔍 **Estado:** {status}\n")
        
        # Agregar alertas del sistema experto si las hay
        if expert_findings:
            base_message += "\n🤖 **Sistema Experto:**\n"
            for finding in expert_findings:
                if finding['severity'] == 'error':
                    base_message += f"❌ {finding['message']}\n"
                elif finding['severity'] == 'warning':
                    base_message += f"⚠️ {finding['message']}\n"
                elif finding['severity'] == 'info':
                    base_message += f"ℹ️ {finding['message']}\n"
        
        base_message += f"\nEscribe /start para registrar otra ausencia."
        
        # Enviar mensaje al usuario
        await bot.send_message(chat_id=chat_id, text=base_message)
        
    except Exception as e:
        print(f"❌ Error guardando ausencia: {e}")
        db.rollback()
        await bot.send_message(
            chat_id=chat_id,
            text="❌ Error al guardar la ausencia. Intenta nuevamente o contacta a soporte."
        )
    finally:
        db.close()

async def show_records(chat_id):
    """Muestra los registros de ausencias del usuario actual"""
    db = SessionLocal()
    try:
        # Buscar registros de este chat
        absences = db.query(Absence).filter(Absence.chat_id == chat_id).order_by(Absence.created_at.desc()).limit(10).all()
        
        if not absences:
            await bot.send_message(
                chat_id=chat_id,
                text="📝 No tienes registros de ausencias aún.\n\nUsa /start para registrar tu primera ausencia."
            )
            return
        
        # Formatear registros
        records_text = f"📋 **Tus últimos {len(absences)} registros:**\n\n"
        
        for i, absence in enumerate(absences, 1):
            date_str = absence.created_at.strftime('%d/%m/%Y %H:%M')
            records_text += f"**{i}.** {absence.name}\n"
            records_text += f"🆔 Legajo: {absence.legajo}\n"
            records_text += f"📅 Motivo: {absence.motivo}\n"
            records_text += f"⏰ Duración: {absence.duracion} días\n"
            records_text += f"🏥 Certificado: {absence.certificado}\n"
            records_text += f"📆 Fecha: {date_str}\n"
            records_text += "─" * 30 + "\n\n"
        
        # Telegram tiene límite de caracteres, dividir si es muy largo
        if len(records_text) > 4000:
            # Enviar en partes
            parts = [records_text[i:i+4000] for i in range(0, len(records_text), 4000)]
            for part in parts:
                await bot.send_message(chat_id=chat_id, text=part)
        else:
            await bot.send_message(chat_id=chat_id, text=records_text)
            
    except Exception as e:
        print(f"❌ Error mostrando registros: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text="❌ Error al consultar registros. Intenta nuevamente."
        )
    finally:
        db.close()

async def handle_certificate_photo(update: Update, chat_id):
    """Maneja la recepción de fotos de certificados"""
    if chat_id not in conversation_states:
        await bot.send_message(
            chat_id=chat_id,
            text="❌ No hay una conversación activa. Usa /start para comenzar."
        )
        return
    
    state = conversation_states[chat_id]
    
    if state["step"] != "upload_certificado":
        await bot.send_message(
            chat_id=chat_id,
            text="❌ No esperaba un certificado en este momento."
        )
        return
    
    try:
        # Obtener la foto de mayor resolución
        photo = update.message.photo[-1]
        
        # Generar nombre único para el archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        legajo = state["data"].get("legajo", "unknown")
        filename = f"cert_{legajo}_{timestamp}.jpg"
        filepath = os.path.join("certificados", filename)
        
        # Descargar la foto
        file = await bot.get_file(photo.file_id)
        await file.download_to_drive(filepath)
        
        # Guardar la ruta en el estado
        state["data"]["certificado"] = f"Archivo guardado: {filename}"
        
        await bot.send_message(
            chat_id=chat_id,
            text="✅ Certificado recibido y guardado.\n\nProcesando tu registro..."
        )
        
        # Guardar y finalizar
        await save_absence_data(chat_id, state["data"])
        
        # Limpiar estado
        del conversation_states[chat_id]
        
    except Exception as e:
        print(f"❌ Error guardando certificado: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text="❌ Error al guardar el certificado. Escribe 'saltar' para continuar sin certificado."
        )

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Página web para ver todos los registros"""
    db = SessionLocal()
    try:
        absences = db.query(Absence).order_by(Absence.created_at.desc()).all()
        
        # Generar HTML
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>📋 Sistema de Ausencias - Dashboard</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                .record { background-color: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .record h3 { margin: 0 0 10px 0; color: #2c3e50; }
                .field { margin: 5px 0; }
                .label { font-weight: bold; color: #34495e; }
                .no-records { text-align: center; color: #7f8c8d; font-style: italic; }
                .stats { background-color: #3498db; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏢 Sistema de Registro de Ausencias</h1>
                <p>Dashboard administrativo - Todos los registros</p>
                <div style="margin-top: 15px;">
                    <a href="/rules" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">🧠 Gestionar Reglas</a>
                    <a href="/rules/new" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">➕ Nueva Regla</a>
                    <a href="/api/registros" style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">📊 API JSON</a>
                </div>
            </div>
        """
        
        if absences:
            # Estadísticas
            total_registros = len(absences)
            motivos = {}
            for absence in absences:
                motivos[absence.motivo] = motivos.get(absence.motivo, 0) + 1
            
            html_content += f"""
            <div class="stats">
                <h3>📊 Estadísticas</h3>
                <p><strong>Total de registros:</strong> {total_registros}</p>
                <p><strong>Motivos más comunes:</strong></p>
                <ul>
            """
            
            for motivo, count in sorted(motivos.items(), key=lambda x: x[1], reverse=True)[:5]:
                html_content += f"<li>{motivo}: {count} registros</li>"
            
            html_content += "</ul></div>"
            
            # Registros
            for absence in absences:
                date_str = absence.created_at.strftime('%d/%m/%Y a las %H:%M')
                
                # Verificar si hay certificado con archivo
                certificado_html = absence.certificado
                if "Archivo guardado:" in absence.certificado:
                    filename = absence.certificado.replace("Archivo guardado: ", "")
                    certificado_html = f'<a href="/certificados/{filename}" target="_blank">📎 Ver certificado</a>'
                
                html_content += f"""
                <div class="record">
                    <h3>👤 {absence.name}</h3>
                    <div class="field"><span class="label">🆔 Legajo:</span> {absence.legajo}</div>
                    <div class="field"><span class="label">📅 Motivo:</span> {absence.motivo}</div>
                    <div class="field"><span class="label">⏰ Duración:</span> {absence.duracion} días</div>
                    <div class="field"><span class="label">🏥 Certificado:</span> {certificado_html}</div>
                    <div class="field"><span class="label">📆 Registrado:</span> {date_str}</div>
                    <div class="field"><span class="label">💬 Chat ID:</span> {absence.chat_id}</div>
                </div>
                """
        else:
            html_content += '<div class="no-records">📝 No hay registros de ausencias aún.</div>'
        
        html_content += """
            <br><br>
            <div style="text-align: center; color: #7f8c8d; font-size: 12px;">
                <p>🔄 Actualiza la página para ver los últimos registros</p>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        return HTMLResponse(content=f"<h1>❌ Error</h1><p>{str(e)}</p>")
    finally:
        db.close()

@app.get("/api/registros")
async def get_records_api():
    """API endpoint para obtener registros en formato JSON"""
    db = SessionLocal()
    try:
        absences = db.query(Absence).order_by(Absence.created_at.desc()).all()
        
        records = []
        for absence in absences:
            records.append({
                "id": absence.id,
                "name": absence.name,
                "legajo": absence.legajo,
                "motivo": absence.motivo,
                "duracion": absence.duracion,
                "certificado": absence.certificado,
                "created_at": absence.created_at.isoformat(),
                "chat_id": absence.chat_id
            })
        
        return {"total": len(records), "registros": records}
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@app.get("/certificados")
async def list_certificates():
    """Lista todos los certificados guardados"""
    try:
        if not os.path.exists("certificados"):
            return {"certificados": [], "total": 0}
        
        files = os.listdir("certificados")
        certificates = []
        
        for filename in files:
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join("certificados", filename)
                stat = os.stat(filepath)
                
                certificates.append({
                    "filename": filename,
                    "size_kb": round(stat.st_size / 1024, 2),
                    "created": datetime.fromtimestamp(stat.st_ctime).strftime('%d/%m/%Y %H:%M'),
                    "url": f"/certificados/{filename}"
                })
        
        # Ordenar por fecha de creación (más recientes primero)
        certificates.sort(key=lambda x: x['created'], reverse=True)
        
        return {"certificados": certificates, "total": len(certificates)}
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/certificados/{filename}")
async def get_certificate(filename: str):
    """Devuelve un archivo de certificado específico"""
    filepath = os.path.join("certificados", filename)
    
    if not os.path.exists(filepath):
        return JSONResponse({"error": "Certificado no encontrado"}, status_code=404)
    
    return FileResponse(
        filepath,
        media_type='image/jpeg',
        filename=filename
    )

# Manejar comando /start
@app.post("/webhook")
async def webhook(request: Request):
    update_data = await request.json()
    update = Update.de_json(update_data, bot)
    
    # Manejar comandos
    if update.message and update.message.text:
        if update.message.text.startswith('/start'):
            chat_id = update.effective_chat.id
            # Reiniciar conversación - cambiar step a "name" para evitar duplicado
            conversation_states[chat_id] = {
                "step": "name",
                "data": {}
            }
            await bot.send_message(
                chat_id=chat_id, 
                text="🏢 **Sistema de Registro de Ausencias**\n\nApellido y Nombre:"
            )
            return JSONResponse({"status": "ok"})
        
        elif update.message.text.startswith('/registros'):
            chat_id = update.effective_chat.id
            await show_records(chat_id)
            return JSONResponse({"status": "ok"})
        
        elif update.message.text.startswith('/help'):
            chat_id = update.effective_chat.id
            help_text = """
🏢 **Comandos disponibles:**

/start - Iniciar registro de ausencia
/registros - Ver tus registros
/help - Mostrar esta ayuda

Para registrar una ausencia, usa /start y sigue las instrucciones.
            """
            await bot.send_message(chat_id=chat_id, text=help_text)
            return JSONResponse({"status": "ok"})
    
    # Procesar el mensaje normal
    await handle_update(update)
    
    return JSONResponse({"status": "ok"})

# Configurar API de reglas
rules_api = RulesAPI()
rules_api.setup_routes(app)

if __name__ == "__main__":
    # Iniciar el servidor (NO usar uvicorn.run aquí si ya lo ejecutas por CLI)
    uvicorn.run(app, host="0.0.0.0", port=8000)
