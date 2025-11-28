"""Tests para el servicio ASR"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.asr_service import transcribe_audio


@pytest.mark.asyncio
async def test_transcribe_audio_success():
    """Test de transcripción exitosa"""
    # Mock de la respuesta de OpenAI
    mock_transcription = Mock()
    mock_transcription.text = "Hola, ¿cómo estás?"
    
    with patch('app.services.asr_service.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.audio.transcriptions.create.return_value = mock_transcription
        mock_openai.return_value = mock_client
        
        # Crear archivo temporal de prueba
        test_file = "test_audio.wav"
        with open(test_file, "w") as f:
            f.write("fake audio data")
        
        try:
            result = await transcribe_audio(test_file)
            
            assert result == "Hola, ¿cómo estás?"
            assert mock_client.audio.transcriptions.create.called
        finally:
            import os
            if os.path.exists(test_file):
                os.remove(test_file)


@pytest.mark.asyncio
async def test_transcribe_audio_error():
    """Test de error en transcripción"""
    with patch('app.services.asr_service.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.audio.transcriptions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        test_file = "test_audio.wav"
        with open(test_file, "w") as f:
            f.write("fake audio data")
        
        try:
            with pytest.raises(Exception) as exc_info:
                await transcribe_audio(test_file)
            
            assert "Error al transcribir audio" in str(exc_info.value)
        finally:
            import os
            if os.path.exists(test_file):
                os.remove(test_file)


@pytest.mark.asyncio
async def test_transcribe_audio_empty_response():
    """Test de respuesta vacía"""
    mock_transcription = Mock()
    mock_transcription.text = ""
    
    with patch('app.services.asr_service.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.audio.transcriptions.create.return_value = mock_transcription
        mock_openai.return_value = mock_client
        
        test_file = "test_audio.wav"
        with open(test_file, "w") as f:
            f.write("fake audio data")
        
        try:
            result = await transcribe_audio(test_file)
            assert result == ""
        finally:
            import os
            if os.path.exists(test_file):
                os.remove(test_file)
