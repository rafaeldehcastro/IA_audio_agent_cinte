"""Router para Audio Chat conversacional"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import time
import logging
import uuid
from pathlib import Path
import tempfile
import os

from app.services.asr_service import transcribe_audio
from app.services.llm_service import process_text
from app.services.tts_service import generate_speech
from app.utils.audio_utils import validate_audio_file, save_temp_file, cleanup_temp_file

logger = logging.getLogger(__name__)

# Almacenamiento en memoria para sesiones de chat
# En producción, usar Redis o DB
chat_sessions: Dict[str, List[Dict[str, str]]] = {}

router = APIRouter(prefix="/audio-chat", tags=["Audio Chat"])


@router.get("/demo", response_class=HTMLResponse)
async def audio_chat_demo():
    """Página de demo para el audio chat conversacional"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Audio Chat - Voice Agent AI</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 30px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            h1 {
                color: #667eea;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
            }
            .chat-box {
                height: 400px;
                overflow-y: auto;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
                background: #f8f9fa;
            }
            .message {
                margin: 15px 0;
                padding: 12px 15px;
                border-radius: 10px;
                max-width: 70%;
                word-wrap: break-word;
            }
            .user-message {
                background: #667eea;
                color: white;
                margin-left: auto;
                text-align: right;
            }
            .assistant-message {
                background: #e9ecef;
                color: #333;
            }
            .upload-section {
                margin: 20px 0;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
            }
            .record-section {
                display: flex;
                align-items: center;
                gap: 10px;
                margin: 15px 0;
                padding: 15px;
                background: white;
                border-radius: 8px;
                border: 2px solid #e0e0e0;
            }
            .recording {
                border-color: #dc3545;
                animation: pulse 1.5s infinite;
            }
            @keyframes pulse {
                0%, 100% { border-color: #dc3545; }
                50% { border-color: #ff6b7a; }
            }
            input[type="file"] {
                margin: 10px 0;
            }
            button {
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                margin: 5px;
            }
            button:hover {
                background: #5568d3;
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .record-btn {
                background: #dc3545;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                font-size: 24px;
                padding: 0;
            }
            .record-btn.recording {
                background: #dc3545;
                animation: pulse-btn 1.5s infinite;
            }
            @keyframes pulse-btn {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
            .record-btn:hover {
                background: #c82333;
            }
            .timer {
                font-size: 20px;
                font-weight: bold;
                color: #dc3545;
                min-width: 60px;
            }
            .clear-btn {
                background: #dc3545;
            }
            .clear-btn:hover {
                background: #c82333;
            }
            .info-badge {
                display: inline-block;
                background: #28a745;
                color: white;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 12px;
                margin: 5px 0;
            }
            .loading {
                display: none;
                color: #667eea;
                margin-top: 10px;
            }
            audio {
                width: 100%;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎙️ Audio Chat Conversacional</h1>
            <p>Mantén conversaciones naturales por voz. El sistema recuerda el contexto! 💬</p>
            
            <div class="info-badge" id="sessionBadge">Nueva conversación</div>
            
            <div class="chat-box" id="chatBox">
                <p style="text-align: center; color: #999;">
                    La conversación aparecerá aquí...
                </p>
            </div>
            
            <div class="upload-section">
                <h3>🎤 Grabar Audio</h3>
                <div class="record-section" id="recordSection">
                    <button class="record-btn" id="recordBtn" onclick="toggleRecording()">⏺️</button>
                    <span class="timer" id="timer">0:00</span>
                    <span id="recordStatus">Presiona para grabar</span>
                </div>
                
                <h3>📁 O Subir Archivo</h3>
                <input type="file" id="audioFile" accept="audio/*">
                <br>
                <button onclick="sendAudio()">🚀 Enviar Audio</button>
                <button class="clear-btn" onclick="clearChat()">🗑️ Nueva Conversación</button>
                <div class="loading" id="loading">⏳ Procesando... (5-10 segundos)</div>
            </div>
        </div>

        <script>
            let sessionId = null;
            let conversationHistory = [];
            let mediaRecorder = null;
            let audioChunks = [];
            let recordingInterval = null;
            let recordingStartTime = 0;

            async function toggleRecording() {
                const recordBtn = document.getElementById('recordBtn');
                const recordStatus = document.getElementById('recordStatus');
                const recordSection = document.getElementById('recordSection');
                const timer = document.getElementById('timer');
                
                if (!mediaRecorder || mediaRecorder.state === 'inactive') {
                    // Iniciar grabación
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ 
                            audio: {
                                sampleRate: 48000,
                                channelCount: 1,
                                echoCancellation: true,
                                noiseSuppression: true
                            }
                        });
                        
                        // Intentar usar formato compatible directamente
                        let options = { mimeType: 'audio/webm' };
                        if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                            options = { mimeType: 'audio/webm;codecs=opus' };
                        }
                        
                        mediaRecorder = new MediaRecorder(stream, options);
                        audioChunks = [];
                        
                        mediaRecorder.ondataavailable = (event) => {
                            if (event.data.size > 0) {
                                audioChunks.push(event.data);
                            }
                        };
                        
                        mediaRecorder.onstop = async () => {
                            // Crear blob con el tipo MIME correcto
                            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                            
                            // Crear archivo con extensión correcta
                            const audioFile = new File([audioBlob], 'recording.webm', { 
                                type: 'audio/webm'
                            });
                            
                            // Auto-enviar el audio grabado
                            await sendRecordedAudio(audioFile);
                            
                            // Detener el stream
                            stream.getTracks().forEach(track => track.stop());
                        };
                        
                        mediaRecorder.start();
                        recordingStartTime = Date.now();
                        
                        // UI de grabación
                        recordBtn.classList.add('recording');
                        recordBtn.textContent = '⏹️';
                        recordSection.classList.add('recording');
                        recordStatus.textContent = 'Grabando... (presiona para detener)';
                        
                        // Iniciar timer
                        recordingInterval = setInterval(() => {
                            const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
                            const minutes = Math.floor(elapsed / 60);
                            const seconds = elapsed % 60;
                            timer.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
                        }, 1000);
                        
                    } catch (error) {
                        alert('Error al acceder al micrófono: ' + error.message);
                    }
                } else {
                    // Detener grabación
                    mediaRecorder.stop();
                    clearInterval(recordingInterval);
                    
                    // Reset UI
                    recordBtn.classList.remove('recording');
                    recordBtn.textContent = '⏺️';
                    recordSection.classList.remove('recording');
                    recordStatus.textContent = 'Presiona para grabar';
                    timer.textContent = '0:00';
                }
            }

            async function sendRecordedAudio(audioFile) {
                const loading = document.getElementById('loading');
                const chatBox = document.getElementById('chatBox');
                
                // Mostrar loading
                loading.style.display = 'block';
                document.querySelectorAll('button').forEach(btn => btn.disabled = true);
                
                try {
                    const formData = new FormData();
                    formData.append('audio', audioFile);
                    if (sessionId) {
                        formData.append('session_id', sessionId);
                    }
                    
                    const response = await fetch('/audio-chat/', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error('Error en el servidor: ' + response.status);
                    }
                    
                    const data = await response.json();
                    
                    // Guardar session_id
                    if (!sessionId) {
                        sessionId = data.session_id;
                        document.getElementById('sessionBadge').textContent = 
                            '✓ Conversación activa';
                    }
                    
                    // Limpiar placeholder
                    if (chatBox.children.length === 1 && 
                        chatBox.children[0].textContent.includes('aparecerá aquí')) {
                        chatBox.innerHTML = '';
                    }
                    
                    // Agregar mensaje del usuario
                    const userDiv = document.createElement('div');
                    userDiv.className = 'message user-message';
                    userDiv.textContent = '🎤 ' + data.transcription;
                    chatBox.appendChild(userDiv);
                    
                    // Agregar respuesta del asistente
                    const assistantDiv = document.createElement('div');
                    assistantDiv.className = 'message assistant-message';
                    assistantDiv.innerHTML = `
                        <strong>🤖 Asistente:</strong><br>
                        ${data.response_text}
                    `;
                    chatBox.appendChild(assistantDiv);
                    
                    // Agregar audio
                    const audioDiv = document.createElement('div');
                    audioDiv.className = 'message assistant-message';
                    const audioBytes = atob(data.audio_base64);
                    const audioArray = new Uint8Array(audioBytes.length);
                    for (let i = 0; i < audioBytes.length; i++) {
                        audioArray[i] = audioBytes.charCodeAt(i);
                    }
                    const audioBlob = new Blob([audioArray], { type: 'audio/mpeg' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    audioDiv.innerHTML = '<audio controls autoplay src="' + audioUrl + '"></audio>';
                    chatBox.appendChild(audioDiv);
                    
                    chatBox.scrollTop = chatBox.scrollHeight;
                    
                } catch (error) {
                    alert('Error: ' + error.message);
                } finally {
                    loading.style.display = 'none';
                    document.querySelectorAll('button').forEach(btn => btn.disabled = false);
                }
            }

            async function sendAudio() {
                const fileInput = document.getElementById('audioFile');
                const loading = document.getElementById('loading');
                const chatBox = document.getElementById('chatBox');
                
                if (!fileInput.files[0]) {
                    alert('Por favor selecciona un archivo de audio');
                    return;
                }
                
                // Mostrar loading
                loading.style.display = 'block';
                document.querySelectorAll('button').forEach(btn => btn.disabled = true);
                
                try {
                    // Preparar FormData
                    const formData = new FormData();
                    formData.append('audio', fileInput.files[0]);
                    if (sessionId) {
                        formData.append('session_id', sessionId);
                    }
                    
                    // Llamar al endpoint
                    const response = await fetch('/audio-chat/', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error('Error en el servidor: ' + response.status);
                    }
                    
                    const data = await response.json();
                    
                    // Guardar session_id
                    if (!sessionId) {
                        sessionId = data.session_id;
                        document.getElementById('sessionBadge').textContent = 
                            '✓ Conversación activa';
                    }
                    
                    // Limpiar placeholder si es el primer mensaje
                    if (chatBox.children.length === 1 && 
                        chatBox.children[0].textContent.includes('aparecerá aquí')) {
                        chatBox.innerHTML = '';
                    }
                    
                    // Agregar mensaje del usuario
                    const userDiv = document.createElement('div');
                    userDiv.className = 'message user-message';
                    userDiv.textContent = '🎤 ' + data.transcription;
                    chatBox.appendChild(userDiv);
                    
                    // Agregar respuesta del asistente
                    const assistantDiv = document.createElement('div');
                    assistantDiv.className = 'message assistant-message';
                    assistantDiv.innerHTML = `
                        <strong>🤖 Asistente:</strong><br>
                        ${data.response_text}
                    `;
                    chatBox.appendChild(assistantDiv);
                    
                    // Crear y agregar reproductor de audio
                    const audioDiv = document.createElement('div');
                    audioDiv.className = 'message assistant-message';
                    const audioBytes = atob(data.audio_base64);
                    const audioArray = new Uint8Array(audioBytes.length);
                    for (let i = 0; i < audioBytes.length; i++) {
                        audioArray[i] = audioBytes.charCodeAt(i);
                    }
                    const audioBlob = new Blob([audioArray], { type: 'audio/mpeg' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    audioDiv.innerHTML = '<audio controls src="' + audioUrl + '"></audio>';
                    chatBox.appendChild(audioDiv);
                    
                    // Scroll al final
                    chatBox.scrollTop = chatBox.scrollHeight;
                    
                    // Limpiar input
                    fileInput.value = '';
                    
                } catch (error) {
                    alert('Error: ' + error.message);
                } finally {
                    loading.style.display = 'none';
                    document.querySelectorAll('button').forEach(btn => btn.disabled = false);
                }
            }

            async function clearChat() {
                if (!sessionId) {
                    alert('No hay conversación activa');
                    return;
                }
                
                if (!confirm('¿Seguro que quieres borrar esta conversación?')) {
                    return;
                }
                
                try {
                    await fetch('/audio-chat/' + sessionId, {
                        method: 'DELETE'
                    });
                    
                    // Resetear UI
                    sessionId = null;
                    document.getElementById('chatBox').innerHTML = 
                        '<p style="text-align: center; color: #999;">La conversación aparecerá aquí...</p>';
                    document.getElementById('sessionBadge').textContent = 'Nueva conversación';
                    
                } catch (error) {
                    alert('Error al borrar conversación: ' + error.message);
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


class AudioChatResponse(BaseModel):
    """Respuesta del audio chat"""
    session_id: str = Field(..., description="ID de la sesión de chat")
    transcription: str = Field(..., description="Texto transcrito del audio")
    response_text: str = Field(..., description="Respuesta del LLM con contexto")
    audio_base64: str = Field(..., description="Audio de respuesta en base64")
    conversation_history: List[Dict[str, str]] = Field(..., description="Historial de la conversación")
    processing_time: float = Field(..., description="Tiempo de procesamiento")


@router.post(
    "/",
    response_model=AudioChatResponse,
    summary="Audio Chat conversacional con historial",
    description="""
    Endpoint de chat por voz que mantiene contexto de conversación.
    
    - Envía audio y opcionalmente un session_id
    - El sistema recuerda conversaciones previas
    - El LLM responde con contexto completo
    - Retorna audio + historial actualizado
    
    Primera vez: no envíes session_id, se creará uno nuevo
    Conversaciones siguientes: usa el session_id retornado
    """
)
async def audio_chat(
    audio: UploadFile = File(..., description="Archivo de audio (.wav o .mp3)"),
    session_id: Optional[str] = Form(None, description="ID de sesión (opcional, se crea si no existe)")
):
    """
    Chat conversacional por audio con historial
    
    Args:
        audio: Archivo de audio del usuario
        session_id: ID de sesión para mantener contexto (opcional)
        
    Returns:
        AudioChatResponse: Respuesta con audio, texto e historial
    """
    temp_file_path = None
    start_time = time.time()
    
    try:
        # Log detallado de la petición recibida
        logger.info(f"=== NUEVA PETICIÓN AUDIO CHAT ===")
        logger.info(f"Archivo recibido: {audio.filename}")
        logger.info(f"Content-Type: {audio.content_type}")
        logger.info(f"Session ID recibido: {session_id}")
        
        # Crear o recuperar sesión
        if not session_id or session_id not in chat_sessions:
            session_id = str(uuid.uuid4())
            chat_sessions[session_id] = []
            logger.info(f"Nueva sesión creada: {session_id}")
        else:
            logger.info(f"Continuando sesión: {session_id}")
        
        # 1. Validar y procesar audio
        logger.info("Iniciando validación de audio...")
        await validate_audio_file(audio)
        logger.info("Audio validado exitosamente")
        
        logger.info("Guardando archivo temporal...")
        temp_file_path = await save_temp_file(audio)
        logger.info(f"Archivo guardado en: {temp_file_path}")
        
        # 2. Transcribir audio (ASR) - OpenAI acepta WAV, MP3, WEBM, OGG, etc
        logger.info("Transcribiendo audio...")
        transcription = await transcribe_audio(temp_file_path)
        logger.info(f"Transcripción: {transcription}")
        
        # 4. Agregar mensaje del usuario al historial
        chat_sessions[session_id].append({
            "role": "user",
            "content": transcription
        })
        
        # 5. Procesar con LLM usando todo el contexto
        logger.info("Procesando con LLM (con contexto)...")
        response_text = await process_text_with_context(
            transcription, 
            chat_sessions[session_id][:-1]  # Historial sin el mensaje actual
        )
        logger.info(f"Respuesta LLM: {response_text}")
        
        # 6. Agregar respuesta del asistente al historial
        chat_sessions[session_id].append({
            "role": "assistant",
            "content": response_text
        })
        
        # 7. Generar audio de respuesta (TTS)
        logger.info("Generando audio...")
        audio_base64 = await generate_speech(response_text)
        
        # Calcular tiempo
        processing_time = round(time.time() - start_time, 2)
        
        logger.info(f"Chat procesado en {processing_time}s")
        
        return AudioChatResponse(
            session_id=session_id,
            transcription=transcription,
            response_text=response_text,
            audio_base64=audio_base64,
            conversation_history=chat_sessions[session_id],
            processing_time=processing_time
        )
        
    except HTTPException as he:
        logger.error(f"HTTPException: {he.status_code} - {he.detail}")
        raise
        
    except Exception as e:
        logger.error(f"Error en audio chat: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando audio chat: {str(e)}"
        )
        
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            cleanup_temp_file(temp_file_path)


@router.delete("/{session_id}", summary="Eliminar sesión de chat")
async def delete_session(session_id: str):
    """Elimina una sesión de chat y su historial"""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        logger.info(f"Sesión eliminada: {session_id}")
        return {"message": f"Sesión {session_id} eliminada"}
    else:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")


@router.get("/{session_id}/history", summary="Obtener historial de sesión")
async def get_session_history(session_id: str):
    """Obtiene el historial de una sesión"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    return {
        "session_id": session_id,
        "history": chat_sessions[session_id],
        "message_count": len(chat_sessions[session_id])
    }


async def process_text_with_context(current_message: str, history: List[Dict[str, str]]) -> str:
    """
    Procesa el mensaje actual con el contexto del historial
    
    Args:
        current_message: Mensaje actual del usuario
        history: Historial previo de la conversación
        
    Returns:
        str: Respuesta del LLM con contexto
    """
    # Construir contexto para el LLM
    if not history:
        # Primera interacción, usar el servicio normal
        return await process_text(current_message)
    
    # Construir un prompt con contexto
    context_prompt = "Historial de conversación:\n"
    for msg in history[-6:]:  # Últimos 6 mensajes para no exceder tokens
        role = "Usuario" if msg["role"] == "user" else "Asistente"
        context_prompt += f"{role}: {msg['content']}\n"
    
    context_prompt += f"\nUsuario: {current_message}\nAsistente:"
    
    # Usar el servicio LLM con el contexto completo
    return await process_text(context_prompt)
