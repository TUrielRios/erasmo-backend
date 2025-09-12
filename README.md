# Erasmo Estratégico Verbal - Backend

Backend modular y escalable para agente conversacional estratégico con capacidades de ingesta de conocimiento y respuestas estructuradas.

## 🚀 Características

- **Ingesta de Conocimiento**: Procesamiento de archivos .txt y .md con indexación semántica
- **Respuestas Estratégicas**: Dos niveles de respuesta (conceptual y accional)
- **Clarificación Inteligente**: Detección de ambigüedad y preguntas de clarificación
- **Base Vectorial**: Soporte para Pinecone, FAISS y otras bases vectoriales
- **API RESTful**: Endpoints bien documentados con FastAPI
- **Escalabilidad**: Arquitectura modular preparada para futuras fases

## 📋 Requisitos

- Python 3.11+
- OpenAI API Key
- Pinecone API Key (opcional, puede usar FAISS local)

## 🛠️ Instalación

1. **Clonar repositorio**
\`\`\`bash
git clone <repo-url>
cd erasmo-backend
\`\`\`

2. **Crear entorno virtual**
\`\`\`bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
\`\`\`

3. **Instalar dependencias**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

4. **Configurar variables de entorno**
\`\`\`bash
cp .env.example .env
# Editar .env con tus API keys
\`\`\`

5. **Ejecutar servidor**
\`\`\`bash
python main.py
\`\`\`

## 🐳 Docker

\`\`\`bash
# Desarrollo con Docker Compose
docker-compose up --build

# Solo backend
docker build -t erasmo-backend .
docker run -p 8000:8000 --env-file .env erasmo-backend
\`\`\`

## 📚 Uso de la API

### Endpoints Principales

#### 1. Health Check
\`\`\`bash
GET /api/v1/health
\`\`\`

#### 2. Ingesta de Documentos
\`\`\`bash
POST /api/v1/ingest
Content-Type: multipart/form-data

# Subir archivos .txt o .md
\`\`\`

#### 3. Consulta Conversacional
\`\`\`bash
POST /api/v1/query
Content-Type: application/json

{
  "message": "¿Cómo puedo mejorar mi estrategia de liderazgo?",
  "session_id": "optional-session-id"
}
\`\`\`

### Respuestas del Sistema

El sistema puede devolver tres tipos de respuestas:

1. **Respuesta Estructurada** (input claro):
   - Nivel conceptual (por qué)
   - Nivel accional (qué hacer)

2. **Preguntas de Clarificación** (input ambiguo):
   - Preguntas específicas para obtener más contexto

3. **Error** (problema en el procesamiento):
   - Mensaje de error formateado

## 🏗️ Arquitectura

\`\`\`
/erasmo-backend
├── app/
│   ├── api/endpoints/     # Endpoints FastAPI
│   ├── services/          # Lógica de negocio
│   ├── db/               # Conexión vector DB
│   ├── models/           # Esquemas Pydantic
│   ├── utils/            # Utilidades
│   └── core/             # Configuración
├── main.py               # Servidor principal
├── requirements.txt      # Dependencias
├── Dockerfile           # Contenedor
└── docker-compose.yml   # Orquestación
\`\`\`

## 🔧 Configuración

### Variables de Entorno Principales

- `OPENAI_API_KEY`: API key de OpenAI
- `VECTOR_DB_TYPE`: Tipo de base vectorial (pinecone/faiss)
- `PINECONE_API_KEY`: API key de Pinecone
- `DEBUG`: Modo desarrollo (true/false)

### Personalización

- **Vector Database**: Cambiar `VECTOR_DB_TYPE` en configuración
- **Modelo LLM**: Modificar `OPENAI_MODEL` para usar diferentes modelos
- **Chunking**: Ajustar parámetros en `TextProcessor`
- **Memoria**: Configurar `CONVERSATION_MEMORY_SIZE`

## 📈 Próximas Fases

- **Fase 2**: Subagentes especializados (Diagnóstico, Académico)
- **Fase 3**: Interface web y mejoras de UX
- **Fase 4**: Integración con sistemas externos

## 🧪 Testing

\`\`\`bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=app tests/
\`\`\`

## 📝 Documentación API

Una vez ejecutando el servidor, visita:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Contribución

1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

[Especificar licencia]

---

**Erasmo Estratégico Verbal** - Sistema de IA Conversacional para Estrategia y Liderazgo
