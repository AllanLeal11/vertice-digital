import os
import uuid
from flask import Flask, request, jsonify, render_template_string
from agents.base import responder, responder_paralelo
from agents.telegram_service import enviar_aprobacion, notificar

app = Flask(__name__)

sesiones = {}
aprobaciones_pendientes = {}

HTML_CHAT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vértice Digital — Panel de Agentes</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600&family=Inter:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', sans-serif; background: #0f0f1a; height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .chat-container { width: 100%; max-width: 680px; background: #1a1a2e; border-radius: 20px; border: 1px solid #2a2a4a; display: flex; flex-direction: column; height: 92vh; }
        .header { padding: 20px 24px; border-bottom: 1px solid #2a2a4a; }
        .header h1 { font-family: 'Poppins', sans-serif; font-size: 18px; color: #fff; font-weight: 600; }
        .header p { font-size: 12px; color: #6c63ff; margin-top: 2px; }
        .agents-bar { display: flex; gap: 8px; padding: 10px 24px; border-bottom: 1px solid #2a2a4a; flex-wrap: wrap; }
        .agent-pill { font-size: 11px; padding: 4px 10px; border-radius: 20px; border: 1px solid #2a2a4a; color: #888; cursor: pointer; transition: all 0.2s; }
        .agent-pill:hover, .agent-pill.active { background: #6c63ff; color: #fff; border-color: #6c63ff; }
        .messages { flex: 1; overflow-y: auto; padding: 20px 24px; display: flex; flex-direction: column; gap: 14px; }
        .messages::-webkit-scrollbar { width: 4px; }
        .messages::-webkit-scrollbar-thumb { background: #2a2a4a; border-radius: 4px; }
        .msg { max-width: 85%; padding: 12px 16px; border-radius: 14px; font-size: 14px; line-height: 1.6; }
        .msg.user { align-self: flex-end; background: #6c63ff; color: #fff; border-radius: 14px 14px 4px 14px; }
        .msg.bot { align-self: flex-start; background: #252540; color: #e0e0e0; border-radius: 14px 14px 14px 4px; border: 1px solid #2a2a4a; }
        .msg.bot-paralelo { align-self: flex-start; background: #1a2a1a; color: #90ee90; border-radius: 14px 14px 14px 4px; border: 1px solid #2a4a2a; }
        .agente-tag { font-size: 10px; font-weight: 600; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        .msg.bot .agente-tag { color: #6c63ff; }
        .msg.bot-paralelo .agente-tag { color: #90ee90; }
        .msg pre { background: #0f0f1a; padding: 10px; border-radius: 8px; overflow-x: auto; font-size: 12px; margin-top: 8px; white-space: pre-wrap; }
        .netlify-banner { background: #0a2a1a; border: 1px solid #00c851; border-radius: 10px; padding: 10px 14px; font-size: 13px; color: #00c851; margin-top: 8px; }
        .netlify-banner a { color: #00c851; text-decoration: underline; }
        .netlify-error { background: #2a0a0a; border: 1px solid #ff4444; border-radius: 10px; padding: 10px 14px; font-size: 13px; color: #ff4444; margin-top: 8px; }
        .aprobacion-banner { background: #2a1a0a; border: 1px solid #ff9800; border-radius: 10px; padding: 10px 14px; font-size: 12px; color: #ff9800; margin-top: 8px; }
        .typing { font-size: 12px; color: #555; padding: 0 24px 8px; font-style: italic; }
        .input-area { padding: 16px 24px; border-top: 1px solid #2a2a4a; display: flex; gap: 8px; }
        .input-area input { flex: 1; padding: 12px 16px; background: #252540; border: 1px solid #2a2a4a; border-radius: 24px; font-size: 14px; color: #fff; outline: none; font-family: 'Inter', sans-serif; }
        .input-area input:focus { border-color: #6c63ff; }
        .input-area input::placeholder { color: #555; }
        .input-area button { padding: 12px 20px; background: #6c63ff; color: white; border: none; border-radius: 24px; cursor: pointer; font-size: 14px; font-weight: 500; font-family: 'Inter', sans-serif; transition: background 0.2s; }
        .input-area button:hover { background: #5a52cc; }
        .modo-paralelo { font-size: 11px; color: #555; padding: 4px 24px; text-align: right; }
    </style>
</head>
<body>
<div class="chat-container">
    <div class="header">
        <h1>Vértice Digital — Panel de Agentes</h1>
        <p>Tu equipo de IA trabajando para vos</p>
    </div>
    <div class="agents-bar">
        <span class="agent-pill active" onclick="setAgente('auto', this)">Auto</span>
        <span class="agent-pill" onclick="setAgente('asistente', this)">Asistente</span>
        <span class="agent-pill" onclick="setAgente('marketing', this)">Marketing</span>
        <span class="agent-pill" onclick="setAgente('ventas', this)">Ventas</span>
        <span class="agent-pill" onclick="setAgente('desarrollador', this)">Desarrollador</span>
        <span class="agent-pill" onclick="setAgente('soporte', this)">Soporte</span>
        <span class="agent-pill" onclick="setAgente('disenador', this)">Diseñador</span>
    </div>
    <div class="messages" id="messages">
        <div class="msg bot">
            <div class="agente-tag">Asistente — Vértice Digital</div>
            Bienvenido Allan. ¿Qué hacemos hoy? Podés escribirme directamente o seleccionar un agente específico arriba.
        </div>
    </div>
    <div class="typing" id="typing"></div>
    <div class="modo-paralelo" id="modo-label"></div>
    <div class="input-area">
        <input type="text" id="input" placeholder="Decile algo a tu equipo..." onkeypress="if(event.key==='Enter') enviar()"/>
        <button onclick="enviar()">Enviar</button>
    </div>
</div>
<script>
    const sessionId = Math.random().toString(36).substr(2, 9);
    let agenteSeleccionado = 'auto';

    function setAgente(agente, el) {
        agenteSeleccionado = agente;
        document.querySelectorAll('.agent-pill').forEach(p => p.classList.remove('active'));
        el.classList.add('active');
        const label = document.getElementById('modo-label');
        label.textContent = agente === 'desarrollador' ? '⚡ Modo paralelo activo: Desarrollador + Diseñador trabajarán juntos' : '';
    }

    async function enviar() {
        const input = document.getElementById('input');
        const msg = input.value.trim();
        if (!msg) return;
        input.value = '';
        agregarMensaje(msg, 'user', '');
        document.getElementById('typing').textContent = 'Tu equipo está trabajando...';

        // Solo usar paralelo si el agente está seleccionado manualmente como desarrollador
        const esParalelo = agenteSeleccionado === 'desarrollador';
        const endpoint = esParalelo ? '/chat/paralelo' : '/chat';

        const res = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({mensaje: msg, session_id: sessionId, agente: agenteSeleccionado})
        });
        const data = await res.json();
        document.getElementById('typing').textContent = '';

        if (data.respuesta_dev) {
            agregarMensaje(data.respuesta_dev, 'bot', data.nombre_dev);
            mostrarBannersNetlify(data);
            agregarMensaje(data.respuesta_diseno, 'bot-paralelo', data.nombre_diseno);
        } else {
            agregarMensaje(data.respuesta, 'bot', data.nombre_agente);
            mostrarBannersNetlify(data);
        }

        if (data.telegram_enviado) {
            const banner = document.createElement('div');
            banner.className = 'aprobacion-banner';
            banner.textContent = '📱 Enviado a Telegram para aprobación';
            document.getElementById('messages').lastChild.appendChild(banner);
        }
    }

    function mostrarBannersNetlify(data) {
        const lastMsg = document.getElementById('messages').lastChild;
        if (data.netlify_url) {
            const banner = document.createElement('div');
            banner.className = 'netlify-banner';
            banner.innerHTML = '🚀 <b>Deployado en Netlify:</b> <a href="' + data.netlify_url + '" target="_blank">' + data.netlify_url + '</a>';
            lastMsg.appendChild(banner);
        }
        if (data.netlify_error) {
            const banner = document.createElement('div');
            banner.className = 'netlify-error';
            banner.innerHTML = '⚠️ <b>Deploy fallido:</b> ' + data.netlify_error;
            lastMsg.appendChild(banner);
        }
    }

    function agregarMensaje(texto, tipo, agente) {
        const div = document.createElement('div');
        div.className = 'msg ' + tipo;
        const tag = agente ? '<div class="agente-tag">' + agente + '</div>' : '';
        const textoFormateado = texto.replace(/```([\s\S]*?)```/g, '<pre>$1</pre>').replace(/\n/g, '<br>');
        div.innerHTML = tag + textoFormateado;
        document.getElementById('messages').appendChild(div);
        document.getElementById('messages').scrollTop = 999999;
    }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_CHAT)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    mensaje = data.get('mensaje', '').strip()
    session_id = data.get('session_id', 'default')
    agente_forzado = data.get('agente', 'auto')
    if not mensaje:
        return jsonify({"error": "Mensaje vacío"}), 400
    if session_id not in sesiones:
        sesiones[session_id] = []
    historial = sesiones[session_id]
    resultado = responder(mensaje, historial, agente_forzado)
    sesiones[session_id].append({"role": "user", "content": mensaje})
    sesiones[session_id].append({"role": "assistant", "content": resultado["respuesta"]})
    if len(sesiones[session_id]) > 20:
        sesiones[session_id] = sesiones[session_id][-20:]

    telegram_enviado = False
    palabras_aprobacion = ['post', 'publicación', 'instagram', 'facebook', 'tiktok', 'publicar']
    if any(p in mensaje.lower() for p in palabras_aprobacion):
        id_aprobacion = str(uuid.uuid4())[:8].upper()
        aprobaciones_pendientes[id_aprobacion] = {
            "contenido": resultado["respuesta"],
            "tipo": "Post redes sociales",
            "session_id": session_id
        }
        enviar_aprobacion("Post redes sociales", resultado["respuesta"], id_aprobacion)
        telegram_enviado = True

    resultado["telegram_enviado"] = telegram_enviado
    return jsonify(resultado)

@app.route('/chat/paralelo', methods=['POST'])
def chat_paralelo():
    data = request.json
    mensaje = data.get('mensaje', '').strip()
    session_id = data.get('session_id', 'default')
    if not mensaje:
        return jsonify({"error": "Mensaje vacío"}), 400
    resultado = responder_paralelo(mensaje)
    notificar(f"⚡ Tarea paralela completada:\nDesarrollador + Diseñador trabajaron en: {mensaje[:80]}...")
    return jsonify(resultado)

@app.route('/aprobar/<id_aprobacion>', methods=['POST'])
def aprobar(id_aprobacion):
    if id_aprobacion not in aprobaciones_pendientes:
        return jsonify({"error": "ID no encontrado"}), 404
    item = aprobaciones_pendientes.pop(id_aprobacion)
    notificar(f"✅ Aprobado: {item['tipo']}\nID: {id_aprobacion}\nListo para publicar.")
    return jsonify({"status": "aprobado", "contenido": item["contenido"]})

@app.route('/rechazar/<id_aprobacion>', methods=['POST'])
def rechazar(id_aprobacion):
    if id_aprobacion not in aprobaciones_pendientes:
        return jsonify({"error": "ID no encontrado"}), 404
    aprobaciones_pendientes.pop(id_aprobacion)
    notificar(f"❌ Rechazado: ID {id_aprobacion}")
    return jsonify({"status": "rechazado"})

@app.route('/webhook/telegram', methods=['POST'])
def webhook_telegram():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"ok": True})
    texto = data['message'].get('text', '').strip()
    partes = texto.split(' ', 2)
    comando = partes[0].lower()
    if comando == 'aprobar' and len(partes) >= 2:
        id_ap = partes[1].upper()
        if id_ap in aprobaciones_pendientes:
            aprobaciones_pendientes.pop(id_ap)
            notificar(f"✅ Contenido <b>{id_ap}</b> aprobado. Listo para publicar.")
        else:
            notificar(f"⚠️ ID {id_ap} no encontrado o ya procesado.")
    elif comando == 'rechazar' and len(partes) >= 2:
        id_ap = partes[1].upper()
        if id_ap in aprobaciones_pendientes:
            aprobaciones_pendientes.pop(id_ap)
            notificar(f"❌ Contenido <b>{id_ap}</b> rechazado.")
    elif comando == 'editar' and len(partes) >= 3:
        id_ap = partes[1].upper()
        feedback = partes[2]
        if id_ap in aprobaciones_pendientes:
            notificar(f"✏️ Feedback recibido para <b>{id_ap}</b>:\n{feedback}\nRevisando...")
    elif comando == 'pendientes':
        if aprobaciones_pendientes:
            lista = '\n'.join([f"• {k}: {v['tipo']}" for k, v in aprobaciones_pendientes.items()])
            notificar(f"📋 Pendientes de aprobación:\n{lista}")
        else:
            notificar("✅ No hay nada pendiente de aprobación.")
    return jsonify({"ok": True})

@app.route('/health')
def health():
    return jsonify({"status": "ok", "empresa": "Vértice Digital", "agentes": 6})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
