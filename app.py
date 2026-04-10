from flask import Flask, request, jsonify, render_template_string
from agents.base import responder
from agents.memoria import cargar_historial, guardar_mensajes

app = Flask(__name__)

HTML_CHAT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vértice Digital — Asistente IA</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .chat-container { width: 100%; max-width: 600px; background: white; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.1); display: flex; flex-direction: column; height: 90vh; }
        .header { background: #1a1a2e; color: white; padding: 20px; border-radius: 16px 16px 0 0; text-align: center; }
        .header h1 { font-size: 20px; font-weight: 600; }
        .header p { font-size: 13px; opacity: 0.7; margin-top: 4px; }
        .messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
        .msg { max-width: 80%; padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.5; }
        .msg.user { align-self: flex-end; background: #1a1a2e; color: white; border-radius: 12px 12px 4px 12px; }
        .msg.bot { align-self: flex-start; background: #f0f2f5; color: #1a1a2e; border-radius: 12px 12px 12px 4px; }
        .msg .agente-tag { font-size: 11px; font-weight: 600; color: #6c63ff; margin-bottom: 6px; text-transform: uppercase; }
        .input-area { padding: 16px; border-top: 1px solid #eee; display: flex; gap: 8px; }
        .input-area input { flex: 1; padding: 12px 16px; border: 1.5px solid #ddd; border-radius: 24px; font-size: 14px; outline: none; }
        .input-area input:focus { border-color: #6c63ff; }
        .input-area button { padding: 12px 20px; background: #1a1a2e; color: white; border: none; border-radius: 24px; cursor: pointer; font-size: 14px; font-weight: 600; }
        .input-area button:hover { background: #6c63ff; }
        .typing { font-size: 13px; color: #999; font-style: italic; padding: 0 20px 8px; }
    </style>
</head>
<body>
<div class="chat-container">
    <div class="header">
        <h1>Vértice Digital</h1>
        <p>Asistente inteligente — TI profesional en Liberia, CR</p>
    </div>
    <div class="messages" id="messages">
        <div class="msg bot">
            <div class="agente-tag">Asistente General</div>
            ¡Bienvenido a Vértice Digital! ¿En qué puedo ayudarte hoy? Puedo ayudarte con desarrollo web, marketing digital, ventas o soporte técnico.
        </div>
    </div>
    <div class="typing" id="typing"></div>
    <div class="input-area">
        <input type="text" id="input" placeholder="Escribe tu consulta..." onkeypress="if(event.key==='Enter') enviar()"/>
        <button onclick="enviar()">Enviar</button>
    </div>
</div>
<script>
    const sessionId = Math.random().toString(36).substr(2, 9);
    async function enviar() {
        const input = document.getElementById('input');
        const msg = input.value.trim();
        if (!msg) return;
        input.value = '';
        agregarMensaje(msg, 'user', '');
        document.getElementById('typing').textContent = 'Vértice Digital está escribiendo...';
        const res = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({mensaje: msg, session_id: sessionId})
        });
        const data = await res.json();
        document.getElementById('typing').textContent = '';
        agregarMensaje(data.respuesta, 'bot', data.nombre_agente);
    }
    function agregarMensaje(texto, tipo, agente) {
        const div = document.createElement('div');
        div.className = 'msg ' + tipo;
        if (tipo === 'bot' && agente) div.innerHTML = '<div class="agente-tag">' + agente + '</div>' + texto;
        else div.textContent = texto;
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

    if not mensaje:
        return jsonify({"error": "Mensaje vacío"}), 400

    # Cargar historial persistente (últimos 40 mensajes)
    historial = cargar_historial(session_id, limite=40)
    resultado = responder(mensaje, historial)

    # Guardar la interacción en SQLite
    guardar_mensajes(session_id, [
        {"role": "user",      "content": mensaje},
        {"role": "assistant", "content": resultado["respuesta"]}
    ])

    return jsonify(resultado)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "empresa": "Vértice Digital"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
