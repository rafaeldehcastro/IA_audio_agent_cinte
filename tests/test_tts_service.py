"""Tests para el servicio TTS"""
import pytest
from unittest.mock import Mock, patch
import base64
from app.services.tts_service import generate_speech


@pytest.mark.asyncio
async def test_generate_speech_success():
    """Test de generación de audio exitosa"""
    # Mock de audio bytes
    fake_audio = b"fake audio content"
    
    mock_response = Mock()
    mock_response.content = fake_audio
    
    with patch('app.services.tts_service.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.audio.speech.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        result = await generate_speech("Hola mundo")
        
        # Verificar que el resultado es base64 válido
        assert isinstance(result, str)
        decoded = base64.b64decode(result)
        assert decoded == fake_audio
        assert mock_client.audio.speech.create.called


@pytest.mark.asyncio
async def test_generate_speech_error():
    """Test de error en generación"""
    with patch('app.services.tts_service.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.audio.speech.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        with pytest.raises(Exception) as exc_info:
            await generate_speech("Test text")
        
        assert "Error al generar audio" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_speech_with_config():
    """Test que verifica la configuración del modelo"""
    fake_audio = b"audio data"
    
    mock_response = Mock()
    mock_response.content = fake_audio
    
    with patch('app.services.tts_service.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.audio.speech.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        await generate_speech("Texto de prueba")
        
        # Verificar parámetros de la llamada
        call_args = mock_client.audio.speech.create.call_args
        assert call_args.kwargs['input'] == "Texto de prueba"
        assert call_args.kwargs['response_format'] == "mp3"


@pytest.mark.asyncio
async def test_generate_speech_empty_text():
    """Test con texto vacío"""
    fake_audio = b"empty audio"
    
    mock_response = Mock()
    mock_response.content = fake_audio
    
    with patch('app.services.tts_service.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.audio.speech.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        result = await generate_speech("")
        
        # Debe retornar algo aunque sea vacío
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_speech_long_text():
    """Test con texto largo"""
    long_text = "Este es un texto muy largo. " * 50
    fake_audio = b"long audio content"
    
    mock_response = Mock()
    mock_response.content = fake_audio
    
    with patch('app.services.tts_service.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.audio.speech.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        result = await generate_speech(long_text)
        
        assert isinstance(result, str)
        assert len(result) > 0
