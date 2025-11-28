"""Servicio de TTS (Text to Speech)"""
from openai import OpenAI
from app.config import settings
import base64
import logging

logger = logging.getLogger(__name__)


async def generate_speech(text: str) -> str:
    """
    Genera audio a partir de texto usando OpenAI TTS
    
    Args:
        text: Texto a convertir en voz
        
    Returns:
        str: Audio codificado en base64
        
    Raises:
        Exception: Si hay error en la generación
    """
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        
        logger.info(f"Generando audio con modelo {settings.tts_model}")
        
        # Usando gpt-4o-mini-tts (el más económico)
        response = client.audio.speech.create(
            model=settings.tts_model,
            voice=settings.tts_voice,  # Voces: alloy, echo, fable, onyx, nova, shimmer
            input=text,
            response_format="opus"  # Opus tiene mejor compatibilidad con navegadores
        )
        
        # Convertir audio a base64 para transmitir en JSON
        audio_bytes = response.content
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        logger.info(f"Audio generado exitosamente ({len(audio_bytes)} bytes)")
        
        return audio_base64
        
    except Exception as e:
        logger.error(f"Error en generación TTS: {str(e)}")
        raise Exception(f"Error al generar audio: {str(e)}")
