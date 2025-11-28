# Voice Agent AI 🎙️🤖

Microservicio de voz inteligente con componentes **Agentic AI** que permite interacciones de voz de extremo a extremo usando modelos de OpenAI.

## 📋 Descripción

Sistema que procesa audio humano, lo transcribe, genera una respuesta inteligente y la convierte de vuelta a voz. Implementa el flujo completo: **ASR → LLM → TTS**.

### Flujo de procesamiento

```
Usuario habla (audio) 
  → ASR (Speech to Text)
  → LLM (Procesamiento inteligente)
  → TTS (Text to Speech)
  → Sistema responde (audio)
```

## 🚀 Características

- ✅ **ASR**: Transcripción de voz a texto con `gpt-4o-mini-transcribe`
- ✅ **LLM**: Procesamiento inteligente con `gpt-5-nano`
- ✅ **TTS**: Síntesis de voz con `gpt-4o-mini-tts`
- ✅ **API REST**: FastAPI con documentación OpenAPI automática
- ✅ **Docker**: Containerización completa
- ✅ **CI/CD**: Pipeline automatizado con GitHub Actions
- ✅ **Tests**: Cobertura de tests unitarios

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Framework | FastAPI 0.104+ |
| IA | OpenAI API (ASR, LLM, TTS) |
| Testing | Pytest + Coverage |
| Containerización | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Deploy | Render / Railway |

## 📦 Instalación

### Requisitos previos

- Python 3.11+
- Docker (opcional)
- OpenAI API Key

### Instalación local

1. **Clonar el repositorio**
```bash
git clone https://github.com/rafaeldehcastro/IA_audio_agent_cinte.git
cd IA_audio_agent_cinte
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env y agregar tu OPENAI_API_KEY
```

5. **Ejecutar la aplicación**
```bash
uvicorn app.main:app --reload
```

La API estará disponible en `http://localhost:8000`

### Instalación con Docker

1. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env y agregar tu OPENAI_API_KEY
```

2. **Construir y ejecutar**
```bash
docker-compose up --build
```

La API estará disponible en `http://localhost:8000`

## 🎯 Uso

### Endpoint principal: `/voice-agent`

**POST** - Procesa audio y genera respuesta hablada

**Ejemplo con cURL:**
```bash
curl -X POST "http://localhost:8000/voice-agent" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "audio=@audio.wav"
```

**Respuesta:**
```json
{
  "transcription": "Hola, ¿cómo estás?",
  "response_text": "¡Hola! Estoy muy bien, gracias por preguntar. ¿En qué puedo ayudarte?",
  "audio_base64": "//uQxAA...",
  "processing_time": 2.34
}
```

### Otros endpoints

- **GET** `/` - Información del servicio
- **GET** `/health` - Health check
- **GET** `/docs` - Documentación Swagger interactiva
- **GET** `/openapi.json` - Schema OpenAPI

### Ejemplo con Python

```python
import requests
import base64

# Enviar audio
with open("audio.wav", "rb") as f:
    files = {"audio": f}
    response = requests.post(
        "http://localhost:8000/voice-agent",
        files=files
    )

result = response.json()
print(f"Transcripción: {result['transcription']}")
print(f"Respuesta: {result['response_text']}")

# Guardar audio de respuesta
audio_data = base64.b64decode(result['audio_base64'])
with open("response.mp3", "wb") as f:
    f.write(audio_data)
```

## 🧪 Tests

### Ejecutar tests
```bash
pytest tests/ -v
```

### Tests con cobertura
```bash
pytest tests/ --cov=app --cov-report=html
```

### Tests específicos
```bash
pytest tests/test_asr_service.py -v
pytest tests/test_llm_service.py -v
pytest tests/test_tts_service.py -v
pytest tests/test_api.py -v
```

## 📁 Estructura del Proyecto

```
IA_audio_agent_cinte/
├── README.md
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app principal
│   ├── config.py               # Configuración
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── asr_service.py      # Speech to Text
│   │   ├── llm_service.py      # Procesamiento LLM
│   │   └── tts_service.py      # Text to Speech
│   └── utils/
│       ├── __init__.py
│       └── audio_utils.py      # Utilidades de audio
├── tests/
│   ├── __init__.py
│   ├── test_asr_service.py
│   ├── test_llm_service.py
│   ├── test_tts_service.py
│   └── test_api.py
└── docs/
    └── architecture.md          # Documentación técnica
```

## 🏗️ Arquitectura

Para ver la arquitectura detallada del sistema, consultar [docs/architecture.md](docs/architecture.md)

### Componentes principales

1. **API REST (FastAPI)**: Punto de entrada HTTP
2. **ASR Service**: Transcripción de audio con `gpt-4o-mini-transcribe`
3. **LLM Service**: Procesamiento con `gpt-5-nano`
4. **TTS Service**: Síntesis de voz con `gpt-4o-mini-tts`

### Decisiones técnicas

- **Modelos económicos**: Se utilizan los modelos más baratos de OpenAI
  - ASR: $0.003/minuto
  - LLM: $0.05 input / $0.40 output (por 1M tokens)
  - TTS: $0.015/minuto
- **Arquitectura modular**: Servicios separados para facilitar testing y mantenimiento
- **Async/await**: Para operaciones I/O no bloqueantes
- **Validación robusta**: Pydantic para validación de datos
- **Documentación automática**: OpenAPI/Swagger integrado

## 💰 Costos Estimados

Por petición típica (audio de 1 minuto):
- ASR: $0.003
- LLM: ~$0.0001 (500 tokens)
- TTS: $0.015
- **Total**: ~$0.018 por petición

## 🚀 Deployment

### Render

1. Conectar repositorio en Render
2. Configurar variables de entorno: `OPENAI_API_KEY`
3. Deploy automático en cada push a `main`

### Railway

```bash
railway login
railway init
railway up
```

### Fly.io

```bash
fly launch
fly secrets set OPENAI_API_KEY=your_key
fly deploy
```

## 🔧 Configuración

Variables de entorno (archivo `.env`):

```env
OPENAI_API_KEY=your_api_key_here
APP_NAME=Voice Agent AI
DEBUG=False
MAX_AUDIO_SIZE_MB=10
ALLOWED_AUDIO_FORMATS=.wav,.mp3
ASR_MODEL=gpt-4o-mini-transcribe
LLM_MODEL=gpt-5-nano
TTS_MODEL=gpt-4o-mini-tts
TTS_VOICE=alloy
```

## 📝 Licencia

Este proyecto es parte de un desafío técnico para CINTE.

## 👨‍💻 Autor

Rafael de Castro
- GitHub: [@rafaeldehcastro](https://github.com/rafaeldehcastro)
- Email: ghereler113@gmail.com

---

**Nota**: Este es un proyecto de demostración técnica que implementa un microservicio de voz inteligente con componentes Agentic AI.
