"""Tests para la API principal"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import io
import os
from pathlib import Path
from app.main import app

client = TestClient(app)

# Ruta al archivo de audio de prueba
TEST_AUDIO_PATH = Path(__file__).parent / "test_audio_1.wav"


def test_root_endpoint():
    """Test del endpoint raíz"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"


def test_health_check():
    """Test del health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@patch('app.main.transcribe_audio')
@patch('app.main.process_text')
@patch('app.main.generate_speech')
async def test_voice_agent_success(mock_tts, mock_llm, mock_asr):
    """Test del flujo completo exitoso"""
    # Configurar mocks
    mock_asr.return_value = "Hola, ¿cómo estás?"
    mock_llm.return_value = "¡Hola! Estoy bien, gracias."
    mock_tts.return_value = "ZmFrZV9hdWRpb19iYXNlNjQ="  # fake_audio_base64
    
    # Crear archivo de prueba
    audio_content = b"fake audio content"
    files = {
        "audio": ("test.wav", io.BytesIO(audio_content), "audio/wav")
    }
    
    response = client.post("/voice-agent", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "transcription" in data
    assert "response_text" in data
    assert "audio_base64" in data
    assert "processing_time" in data


def test_voice_agent_no_file():
    """Test sin archivo adjunto"""
    response = client.post("/voice-agent")
    assert response.status_code == 422  # Unprocessable Entity


def test_voice_agent_invalid_format():
    """Test con formato inválido"""
    files = {
        "audio": ("test.txt", io.BytesIO(b"not audio"), "text/plain")
    }
    
    response = client.post("/voice-agent", files=files)
    assert response.status_code == 400


def test_voice_agent_empty_file():
    """Test con archivo vacío"""
    files = {
        "audio": ("test.wav", io.BytesIO(b""), "audio/wav")
    }
    
    response = client.post("/voice-agent", files=files)
    assert response.status_code == 400


def test_voice_agent_large_file():
    """Test con archivo muy grande"""
    # Crear archivo de 20MB (mayor al límite de 10MB)
    large_content = b"x" * (20 * 1024 * 1024)
    files = {
        "audio": ("test.wav", io.BytesIO(large_content), "audio/wav")
    }
    
    response = client.post("/voice-agent", files=files)
    assert response.status_code == 400


def test_docs_available():
    """Test que verifica que la documentación está disponible"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema():
    """Test del schema OpenAPI"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
    assert "/voice-agent" in schema["paths"]


def test_voice_agent_with_real_audio():
    """Test con archivo de audio real - detecta errores reales"""
    if not TEST_AUDIO_PATH.exists():
        pytest.skip("test_audio_1.wav no encontrado")
    
    # Leer el archivo de audio real
    with open(TEST_AUDIO_PATH, "rb") as audio_file:
        files = {
            "audio": ("test_audio_1.wav", audio_file, "audio/wav")
        }
        
        response = client.post("/voice-agent", files=files)
        
        # Imprimir respuesta para debug
        print(f"\nStatus: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Este test debería revelar cualquier error real
        if response.status_code != 200:
            print(f"Error detectado: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "transcription" in data
        assert "response_text" in data
        assert "audio_base64" in data
        assert "processing_time" in data
