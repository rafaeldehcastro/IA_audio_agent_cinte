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
        
        # Determinar el nombre del archivo con extensión correcta
        import os
        filename = os.path.basename(audio_file_path)
        
        with open(audio_file_path, "rb") as audio_file:
            logger.info(f"Transcribiendo audio: {filename} con modelo {settings.asr_model}")
            
            # Importante: Especificar el nombre del archivo para que OpenAI detecte el formato
            from pathlib import Path
            file_tuple = (filename, audio_file, "application/octet-stream")
            
            transcription = client.audio.transcriptions.create(
                model=settings.asr_model,
                file=file_tuple,
                language="es"  # Especificamos español
            )
        
        logger.info(f"Transcripción exitosa: {transcription.text[:50]}...")
        return transcription.text
        
    except Exception as e:
        logger.error(f"Error en transcripción: {str(e)}", exc_info=True)
        raise Exception(f"Error al transcribir audio: {str(e)}")
