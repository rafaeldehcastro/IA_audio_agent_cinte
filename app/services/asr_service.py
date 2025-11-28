"""Servicio de ASR (Automatic Speech Recognition)"""
from openai import OpenAI
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe audio a texto usando OpenAI API
    
    Args:
        audio_file_path: Ruta al archivo de audio
        
    Returns:
        str: Texto transcrito
        
    Raises:
        Exception: Si hay error en la transcripción
    """
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        
        with open(audio_file_path, "rb") as audio_file:
            logger.info(f"Transcribiendo audio con modelo {settings.asr_model}")
            
            # Usando gpt-4o-mini-transcribe (el más económico)
            transcription = client.audio.transcriptions.create(
                model=settings.asr_model,
                file=audio_file,
                language="es"  # Especificamos español
            )
        
        logger.info(f"Transcripción exitosa: {transcription.text[:50]}...")
        return transcription.text
        
    except Exception as e:
        logger.error(f"Error en transcripción: {str(e)}")
        raise Exception(f"Error al transcribir audio: {str(e)}")
