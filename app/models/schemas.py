"""
Esquemas Pydantic para requests y responses
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class UserCreate(BaseModel):
    """Schema para crear un nuevo usuario"""
    username: str = Field(min_length=3, max_length=50, description="Nombre de usuario único")
    email: EmailStr = Field(description="Correo electrónico del usuario")
    password: str = Field(min_length=6, max_length=100, description="Contraseña del usuario")
    full_name: Optional[str] = Field(default=None, max_length=255, description="Nombre completo del usuario")

class UserLogin(BaseModel):
    """Schema para login de usuario"""
    email: str = Field(description="Email del usuario")
    password: str = Field(description="Contraseña del usuario")

class UserResponse(BaseModel):
    """Schema para respuesta de usuario"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    """Schema para respuesta de autenticación con tokens JWT"""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema para datos del token"""
    username: Optional[str] = None
    user_id: Optional[int] = None

class ConversationCreate(BaseModel):
    """Schema para crear una nueva conversación"""
    title: Optional[str] = Field(default=None, max_length=500, description="Título de la conversación")

class ConversationResponse(BaseModel):
    """Schema para respuesta de conversación"""
    id: int
    session_id: str
    user_id: int
    title: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    """Schema para respuesta de mensaje"""
    id: int
    conversation_id: int
    role: str
    content: str
    timestamp: datetime
    message_metadata: Optional[str]
    
    class Config:
        from_attributes = True

class ConversationWithMessages(ConversationResponse):
    """Schema para conversación con sus mensajes"""
    messages: List[MessageResponse] = []

class ResponseLevel(str, Enum):
    """Niveles de respuesta del agente"""
    CONCEPTUAL = "conceptual"
    ACCIONAL = "accional"
    CLARIFICATION = "clarification"

class DocumentType(str, Enum):
    """Tipos de documentos soportados"""
    TXT = "txt"
    MARKDOWN = "md"

class IngestionType(str, Enum):
    """Tipos de ingesta soportados"""
    PERSONALITY = "personality"  # Define el comportamiento y estilo del agente
    KNOWLEDGE = "knowledge"      # Fuentes de información para consultas

class DocumentMetadata(BaseModel):
    """Metadatos de un documento indexado"""
    filename: str
    file_type: DocumentType
    ingestion_type: IngestionType = Field(description="Tipo de ingesta: personalidad o conocimiento")
    dimension: str = Field(description="Dimensión del conocimiento (ej: estrategia, liderazgo)")
    modelo_base: str = Field(description="Modelo conceptual base del documento")
    tipo_output: str = Field(description="Tipo de salida esperada del documento")
    created_at: datetime = Field(default_factory=datetime.now)
    file_size: int
    chunk_count: int

class IngestRequest(BaseModel):
    """Request para ingesta de documentos"""
    files: List[str] = Field(description="Lista de nombres de archivos a procesar")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadatos adicionales")

class IngestResponse(BaseModel):
    """Response de ingesta de documentos"""
    success: bool
    message: str
    processed_files: List[str]
    failed_files: List[str]
    total_chunks: int
    metadata: List[DocumentMetadata]

class QueryRequest(BaseModel):
    """Request para consulta conversacional"""
    message: str = Field(min_length=1, max_length=10000)
    session_id: Optional[str] = Field(default=None, description="ID de sesión para mantener contexto")
    user_id: Optional[int] = Field(default=None, description="ID del usuario autenticado")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Contexto adicional")

class ConceptualResponse(BaseModel):
    """Respuesta a nivel conceptual (por qué)"""
    content: str = Field(description="Explicación conceptual en Markdown")
    sources: List[str] = Field(description="Fuentes de conocimiento utilizadas")
    confidence: float = Field(ge=0.0, le=1.0, description="Nivel de confianza de la respuesta")

class AccionalResponse(BaseModel):
    """Respuesta a nivel accional (qué hacer)"""
    content: str = Field(description="Acciones específicas en Markdown")
    priority: str = Field(description="Nivel de prioridad: alta, media, baja")
    timeline: Optional[str] = Field(description="Marco temporal sugerido")

class ClarificationQuestion(BaseModel):
    """Pregunta de clarificación"""
    question: str
    context: str
    suggested_answers: Optional[List[str]] = None

class QueryResponse(BaseModel):
    """Response completa de consulta"""
    response_type: ResponseLevel
    session_id: str
    
    # Respuestas estructuradas
    conceptual: Optional[ConceptualResponse] = None
    accional: Optional[AccionalResponse] = None
    clarification: Optional[List[ClarificationQuestion]] = None
    
    # Metadatos de la respuesta
    processing_time: float
    tokens_used: int
    model_used: str

class HealthResponse(BaseModel):
    """Response del endpoint de salud"""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]
