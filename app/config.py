"""Configuración de la aplicación"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configuración de variables de entorno"""
    
    # OpenAI
    openai_api_key: str
    
    # App
    app_name: str = "Voice Agent AI"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Audio
    max_audio_size_mb: int = 10
    allowed_audio_formats: str = ".wav,.mp3"
    
    # Models
    asr_model: str = "gpt-4o-mini-transcribe"
    llm_model: str = "gpt-5-nano"
    tts_model: str = "gpt-4o-mini-tts"
    tts_voice: str = "alloy"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def allowed_formats_list(self) -> List[str]:
        """Convierte string de formatos a lista"""
        return [fmt.strip() for fmt in self.allowed_audio_formats.split(",")]
    
    @property
    def max_audio_size_bytes(self) -> int:
        """Convierte MB a bytes"""
        return self.max_audio_size_mb * 1024 * 1024


# Instancia global de configuración
settings = Settings()
