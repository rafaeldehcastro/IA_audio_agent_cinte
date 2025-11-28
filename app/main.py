"""API principal - Voice Agent AI"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import time
import logging
from contextlib import asynccontextmanager

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
