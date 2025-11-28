"""Schemas de Pydantic para requests/responses"""
from pydantic import BaseModel, Field
from typing import Optional


class VoiceAgentResponse(BaseModel):
    """Respuesta del voice agent"""
    transcription: str = Field(..., description="Texto transcrito del audio de entrada")
    response_text: str = Field(..., description="Respuesta generada por el LLM")
    audio_base64: str = Field(..., description="Audio de respuesta codificado en base64")
    processing_time: float = Field(..., description="Tiempo total de procesamiento en segundos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "transcription": "Hola, ¿cómo estás?",
                "response_text": "¡Hola! Estoy muy bien, gracias por preguntar. ¿En qué puedo ayudarte hoy?",
                "audio_base64": "//uQx...",
                "processing_time": 2.34
            }
        }


class ErrorResponse(BaseModel):
    """Respuesta de error"""
    error: str = Field(..., description="Mensaje de error")
    detail: Optional[str] = Field(None, description="Detalle adicional del error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid audio format",
                "detail": "Only .wav and .mp3 files are supported"
            }
        }
