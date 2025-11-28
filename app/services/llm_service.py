"""Servicio de procesamiento de lenguaje con LLM"""
from openai import OpenAI
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def process_text(transcription: str) -> str:
    """
    Procesa el texto transcrito y genera una respuesta usando LLM
    
    Args:
        transcription: Texto transcrito del usuario
        
    Returns:
        str: Respuesta generada por el LLM
        
    Raises:
        Exception: Si hay error en el procesamiento
    """
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Prompt del sistema para el voice agent
        system_prompt = """Eres un asistente de voz amigable y útil. 
        Responde de manera concisa y natural, como en una conversación hablada.
        Mantén tus respuestas cortas (máximo 2-3 oraciones) para facilitar la síntesis de voz.
        Responde siempre en español."""
        
        logger.info(f"Procesando texto con modelo {settings.llm_model}")
        
        # Usando gpt-5-nano (el más económico)
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcription}
            ],
            max_tokens=150,  # Limitamos para mantener respuestas cortas
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content
        logger.info(f"Respuesta generada: {response_text[:50]}...")
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error en procesamiento LLM: {str(e)}")
        raise Exception(f"Error al procesar texto: {str(e)}")
