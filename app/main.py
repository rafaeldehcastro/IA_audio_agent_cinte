"""API principal - Voice Agent AI"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, Response, HTMLResponse
import time
import logging
from contextlib import asynccontextmanager
import base64

from app.config import settings
from app.models.schemas import VoiceAgentResponse, ErrorResponse
from app.services.asr_service import transcribe_audio
from app.services.llm_service import process_text
from app.services.tts_service import generate_speech
from app.utils.audio_utils import validate_audio_file, save_temp_file, cleanup_temp_file

# Configurar logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    logger.info(f"Iniciando {settings.app_name} v{settings.app_version}")
    logger.info(f"Modelos configurados: ASR={settings.asr_model}, LLM={settings.llm_model}, TTS={settings.tts_model}")
    yield
    logger.info("Cerrando aplicación")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Microservicio de voz inteligente con componentes Agentic AI",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Endpoint raíz con información del servicio"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "endpoints": {
            "voice_agent": "/voice-agent",
            "voice_agent_audio": "/voice-agent-audio",
            "test_page": "/test-audio",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check del servicio"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


@app.get("/test-audio", response_class=HTMLResponse)
async def test_audio_page():
    """Página de prueba para el voice agent"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Voice Agent Test</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #007bff;
                padding-bottom: 10px;
            }
            .upload-section {
                margin: 30px 0;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 5px;
            }
            input[type="file"] {
                margin: 10px 0;
            }
            button {
                background: #007bff;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 10px;
            }
            button:hover {
                background: #0056b3;
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            #result {
                margin-top: 30px;
                padding: 20px;
                background: #e8f4f8;
                border-radius: 5px;
                display: none;
            }
            .info {
                margin: 10px 0;
                padding: 10px;
                background: white;
                border-left: 4px solid #007bff;
            }
            audio {
                width: 100%;
                margin-top: 15px;
            }
            .loading {
                display: none;
                color: #007bff;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 Voice Agent AI - Test</h1>
            <p>Sube un archivo de audio (.wav o .mp3) para probar el sistema end-to-end</p>
            
            <div class="upload-section">
                <input type="file" id="audioFile" accept="audio/*">
                <br>
                <button onclick="processAudio()">🚀 Procesar Audio</button>
                <div class="loading" id="loading">⏳ Procesando... (puede tomar 5-10 segundos)</div>
            </div>
            
            <div id="result">
                <h3>Resultados:</h3>
                <div class="info">
                    <strong>📝 Transcripción:</strong>
                    <p id="transcription"></p>
                </div>
                <div class="info">
                    <strong>💬 Respuesta del LLM:</strong>
                    <p id="response"></p>
                </div>
                <div class="info">
                    <strong>🔊 Audio Generado:</strong>
                    <audio id="audioPlayer" controls></audio>
                </div>
                <div class="info">
                    <strong>⏱️ Tiempo de procesamiento:</strong>
                    <p id="time"></p>
                </div>
            </div>
        </div>

        <script>
            async function processAudio() {
                const fileInput = document.getElementById('audioFile');
                const loading = document.getElementById('loading');
                const result = document.getElementById('result');
                const button = document.querySelector('button');
                
                if (!fileInput.files[0]) {
                    alert('Por favor selecciona un archivo de audio');
                    return;
                }
                
                // Mostrar loading
                loading.style.display = 'block';
                button.disabled = true;
                result.style.display = 'none';
                
                try {
                    // Preparar FormData
                    const formData = new FormData();
                    formData.append('audio', fileInput.files[0]);
                    
                    // Llamar al endpoint
                    const response = await fetch('/voice-agent', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error('Error en el servidor: ' + response.status);
                    }
                    
                    const data = await response.json();
                    
                    // Mostrar resultados
                    document.getElementById('transcription').textContent = data.transcription;
                    document.getElementById('response').textContent = data.response_text;
                    document.getElementById('time').textContent = data.processing_time + ' segundos';
                    
                    // Crear blob de audio y reproducir
                    const audioBytes = atob(data.audio_base64);
                    const audioArray = new Uint8Array(audioBytes.length);
                    for (let i = 0; i < audioBytes.length; i++) {
                        audioArray[i] = audioBytes.charCodeAt(i);
                    }
                    const audioBlob = new Blob([audioArray], { type: 'audio/mpeg' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    const audioPlayer = document.getElementById('audioPlayer');
                    audioPlayer.src = audioUrl;
                    
                    result.style.display = 'block';
                    
                } catch (error) {
                    alert('Error: ' + error.message);
                } finally {
                    loading.style.display = 'none';
                    button.disabled = false;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post(
    "/voice-agent",
    response_model=VoiceAgentResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Archivo inválido"},
        500: {"model": ErrorResponse, "description": "Error en procesamiento"}
    },
    summary="Procesa audio y genera respuesta hablada",
    description="""
    Endpoint principal que procesa voz de extremo a extremo:
    1. Recibe archivo de audio (.wav o .mp3)
    2. Transcribe audio a texto (ASR)
    3. Procesa texto con LLM
    4. Genera respuesta en audio (TTS)
    5. Retorna transcripción, respuesta y audio en base64
    """
)
async def voice_agent(audio: UploadFile = File(..., description="Archivo de audio (.wav o .mp3)")):
    """
    Procesa un archivo de audio y genera una respuesta hablada
    
    Args:
        audio: Archivo de audio del usuario
        
    Returns:
        VoiceAgentResponse: Respuesta con transcripción, texto y audio
    """
    temp_file_path = None
    start_time = time.time()
    
    try:
        logger.info(f"Nueva petición recibida: {audio.filename}")
        
        # 1. Validar archivo
        await validate_audio_file(audio)
        
        # 2. Guardar archivo temporal
        temp_file_path = await save_temp_file(audio)
        
        # 3. Transcribir audio a texto (ASR)
        logger.info("Iniciando transcripción (ASR)")
        transcription = await transcribe_audio(temp_file_path)
        
        # 4. Procesar texto con LLM
        logger.info("Procesando texto con LLM")
        response_text = await process_text(transcription)
        
        # 5. Generar audio de respuesta (TTS)
        logger.info("Generando audio de respuesta (TTS)")
        audio_base64 = await generate_speech(response_text)
        
        # Calcular tiempo total
        processing_time = round(time.time() - start_time, 2)
        
        logger.info(f"Procesamiento completado en {processing_time}s")
        
        return VoiceAgentResponse(
            transcription=transcription,
            response_text=response_text,
            audio_base64=audio_base64,
            processing_time=processing_time
        )
        
    except HTTPException:
        # Re-lanzar excepciones HTTP
        raise
        
    except Exception as e:
        logger.error(f"Error en procesamiento: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en el procesamiento: {str(e)}"
        )
        
    finally:
        # Limpiar archivo temporal
        if temp_file_path:
            cleanup_temp_file(temp_file_path)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Manejador personalizado de excepciones HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc.detail) if exc.detail else None
        ).model_dump()
    )


@app.post(
    "/voice-agent-audio",
    response_class=Response,
    responses={
        200: {
            "content": {"audio/mpeg": {}},
            "description": "Audio MP3 generado"
        },
        400: {"model": ErrorResponse, "description": "Archivo inválido"},
        500: {"model": ErrorResponse, "description": "Error en procesamiento"}
    },
    summary="Procesa audio y retorna respuesta directa en MP3",
    description="""
    Similar a /voice-agent pero retorna el audio directamente como MP3 
    para reproducir en el navegador o descargar.
    
    Proceso:
    1. Recibe archivo de audio (.wav o .mp3)
    2. Transcribe a texto (ASR)
    3. Procesa con LLM
    4. Genera respuesta en audio (TTS)
    5. Retorna MP3 directamente
    
    Útil para probar desde Swagger UI y escuchar la respuesta.
    """
)
async def voice_agent_audio(audio: UploadFile = File(..., description="Archivo de audio (.wav o .mp3)")):
    """
    Procesa audio y retorna la respuesta directamente como MP3
    
    Args:
        audio: Archivo de audio del usuario
        
    Returns:
        Response: Audio MP3 de la respuesta
    """
    temp_file_path = None
    
    try:
        logger.info(f"Nueva petición voice-agent-audio: {audio.filename}")
        
        # 1. Validar archivo
        await validate_audio_file(audio)
        
        # 2. Guardar archivo temporal
        temp_file_path = await save_temp_file(audio)
        
        # 3. Transcribir audio a texto (ASR)
        logger.info("Iniciando transcripción (ASR)")
        transcription = await transcribe_audio(temp_file_path)
        logger.info(f"Transcripción: {transcription}")
        
        # 4. Procesar texto con LLM
        logger.info("Procesando texto con LLM")
        response_text = await process_text(transcription)
        logger.info(f"Respuesta LLM: {response_text}")
        
        # 5. Generar audio de respuesta (TTS)
        logger.info("Generando audio de respuesta (TTS)")
        audio_base64 = await generate_speech(response_text)
        
        # Decodificar base64 a bytes
        audio_bytes = base64.b64decode(audio_base64)
        
        logger.info(f"Audio generado: {len(audio_bytes)} bytes")
        
        # Retornar audio directamente
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=response.mp3",
                "X-Transcription": transcription[:100],  # Primeros 100 chars
                "X-Response-Text": response_text[:100],
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Error en procesamiento: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en el procesamiento: {str(e)}"
        )
        
    finally:
        if temp_file_path:
            cleanup_temp_file(temp_file_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
