"""Tests para el servicio LLM"""
import pytest
from unittest.mock import Mock, patch
from app.services.llm_service import process_text


@pytest.mark.asyncio
async def test_process_text_success():
    """Test de procesamiento exitoso"""
    # Mock de la respuesta de OpenAI
    mock_message = Mock()
    mock_message.content = "¡Hola! Estoy muy bien, gracias por preguntar."
    
    mock_choice = Mock()
    mock_choice.message = mock_message
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    
    with patch('app.services.llm_service.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        result = await process_text("Hola, ¿cómo estás?")
        
        assert result == "¡Hola! Estoy muy bien, gracias por preguntar."
        assert mock_client.chat.completions.create.called


@pytest.mark.asyncio
async def test_process_text_error():
    """Test de error en procesamiento"""
    with patch('app.services.llm_service.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        with pytest.raises(Exception) as exc_info:
            await process_text("Test text")
        
        assert "Error al procesar texto" in str(exc_info.value)


@pytest.mark.asyncio
async def test_process_text_with_system_prompt():
    """Test que verifica que se usa el system prompt"""
    mock_message = Mock()
    mock_message.content = "Respuesta del asistente"
    
    mock_choice = Mock()
    mock_choice.message = mock_message
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    
    with patch('app.services.llm_service.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        await process_text("¿Cuál es tu función?")
        
        # Verificar que se llamó con mensajes
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'


@pytest.mark.asyncio
async def test_process_text_empty_input():
    """Test con entrada vacía"""
    mock_message = Mock()
    mock_message.content = "No entendí tu mensaje."
    
    mock_choice = Mock()
    mock_choice.message = mock_message
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    
    with patch('app.services.llm_service.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        result = await process_text("")
        assert isinstance(result, str)
