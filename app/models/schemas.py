"""
Esquemas Pydantic para requests y responses
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class CompanyCreate(BaseModel):
    """Schema para crear una nueva compañía"""
    name: str = Field(min_length=2, max_length=255, description="Nombre de la compañía")
    industry: str = Field(min_length=2, max_length=255, description="Industria")
    sector: str = Field(min_length=2, max_length=255, description="Sector")
    description: Optional[str] = Field(default=None, description="Descripción de la compañía")

class CompanyResponse(BaseModel):
    """Schema para respuesta de compañía"""
    id: int
    name: str
    industry: str
    sector: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    user_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    """Schema para crear un nuevo usuario"""
    username: str = Field(min_length=3, max_length=50, description="Nombre de usuario único")
    email: EmailStr = Field(description="Correo electrónico del usuario")
    password: str = Field(min_length=6, max_length=100, description="Contraseña del usuario")
    full_name: Optional[str] = Field(default=None, max_length=255, description="Nombre completo del usuario")
    
    # Nuevos campos obligatorios para registro
    company_name: str = Field(min_length=2, max_length=255, description="Nombre de la compañía")
    industry: str = Field(min_length=2, max_length=255, description="Industria de la compañía")
    sector: str = Field(min_length=2, max_length=255, description="Sector de la compañía")
    work_area: str = Field(min_length=2, max_length=255, description="Área de desempeño del usuario")

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
    work_area: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    company: Optional[CompanyResponse]
    
    class Config:
        from_attributes = True

class CompanyDocumentCreate(BaseModel):
    """Schema para crear documento de compañía"""
    filename: str = Field(description="Nombre del archivo")
    category: str  # Placeholder for DocumentCategory
    description: Optional[str] = Field(default=None, description="Descripción del documento")
    priority: int = Field(default=1, ge=1, le=5, description="Prioridad del documento (1=más alta, 5=más baja)")
    is_active: bool = Field(default=True, description="Si el documento está activo")

class CompanyDocumentResponse(BaseModel):
    """Schema para respuesta de documento de compañía"""
    id: int
    company_id: int
    filename: str
    category: str  # Placeholder for DocumentCategory
    description: Optional[str]
    priority: int
    file_size: int
    uploaded_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class CompanyDocumentUpdate(BaseModel):
    """Schema para actualizar documento de compañía"""
    description: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    is_active: Optional[bool] = None
    category: Optional[str] = None  # Placeholder for DocumentCategory

class DocumentType(str, Enum):
    """Tipos de documentos soportados"""
    TXT = "txt"
    MARKDOWN = "md"
    PDF = "pdf"  # Added PDF support

class IngestionType(str, Enum):
    """Tipos de ingesta de documentos"""
    KNOWLEDGE = "knowledge"
    PERSONALITY = "personality"

class DocumentCategory(str, Enum):
    """Categorías de documentos para personalización de IA"""
    KNOWLEDGE_BASE = "knowledge_base"  # Fuentes de conocimiento especiales
    INSTRUCTIONS = "instructions"      # Instrucciones específicas para la IA
    COMPANY_INFO = "company_info"      # Información general de la empresa

class AIConfigurationCreate(BaseModel):
    """Schema para crear configuración de IA"""
    company_id: int
    methodology_prompt: Optional[str] = Field(default=None, description="Prompt de metodología personalizada")
    knowledge_base: Optional[Dict[str, Any]] = Field(default=None, description="Base de conocimiento")
    personality_traits: Optional[Dict[str, Any]] = Field(default=None, description="Rasgos de personalidad")
    response_style: str = Field(default="professional", description="Estilo de respuesta")
    model_name: str = Field(default="gpt-4", description="Modelo de IA a usar")
    temperature: str = Field(default="0.7", description="Temperatura del modelo")
    max_tokens: int = Field(default=2000, description="Máximo de tokens")
    instruction_priority: str = Field(default="high", description="Prioridad de seguimiento de instrucciones")
    knowledge_base_priority: str = Field(default="high", description="Prioridad de fuentes de conocimiento")
    fallback_to_general: bool = Field(default=True, description="Si usar conocimiento general cuando no hay suficiente información")

class AIConfigurationUpdate(BaseModel):
    """Schema para actualizar configuración de IA"""
    methodology_prompt: Optional[str] = None
    knowledge_base: Optional[Dict[str, Any]] = None
    personality_traits: Optional[Dict[str, Any]] = None
    response_style: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[int] = None
    instruction_priority: Optional[str] = None
    knowledge_base_priority: Optional[str] = None
    fallback_to_general: Optional[bool] = None

class AIConfigurationResponse(BaseModel):
    """Schema para respuesta de configuración de IA"""
    id: int
    company_id: int
    methodology_prompt: Optional[str]
    knowledge_base: Optional[Dict[str, Any]]
    personality_traits: Optional[Dict[str, Any]]
    response_style: str
    model_name: str
    temperature: str
    max_tokens: int
    instruction_priority: str
    knowledge_base_priority: str
    fallback_to_general: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    company: CompanyResponse
    
    class Config:
        from_attributes = True

class DocumentProcessingStatus(str, Enum):
    """Estados de procesamiento de documentos"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class CompanyDocumentProcessing(BaseModel):
    """Schema para procesamiento de documentos"""
    document_id: int
    status: DocumentProcessingStatus
    processed_chunks: int
    total_chunks: int
    error_message: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None

class AdminCompanyDocumentUpload(BaseModel):
    """Schema para carga de documentos desde admin"""
    category: DocumentCategory = Field(description="Categoría del documento")
    description: Optional[str] = Field(default=None, description="Descripción del documento")
    priority: int = Field(default=1, ge=1, le=5, description="Prioridad del documento")

class CompanyDocumentUpload(BaseModel):
    """Schema para carga de documentos"""
    files: List[str] = Field(description="Lista de nombres de archivos .txt")

# class AuthResponse(BaseModel):
#     """Schema para respuesta de autenticación con tokens JWT"""
#     user: UserResponse
#     access_token: str
#     refresh_token: str
#     token_type: str = "bearer"

# class TokenData(BaseModel):
#     """Schema para datos del token"""
#     username: Optional[str] = None
#     user_id: Optional[int] = None

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
    metadata: List[Dict[str, Any]]

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

class DocumentMetadata(BaseModel):
    """Metadatos de documentos procesados"""
    filename: str = Field(description="Nombre del archivo")
    file_type: DocumentType = Field(description="Tipo de archivo")
    ingestion_type: IngestionType = Field(description="Tipo de ingesta")
    dimension: str = Field(description="Dimensión del conocimiento")
    modelo_base: str = Field(description="Modelo conceptual base")
    tipo_output: str = Field(description="Tipo de salida esperada")
    file_size: int = Field(description="Tamaño del archivo en bytes")
    chunk_count: int = Field(description="Número de chunks generados")
    processed_at: Optional[datetime] = Field(default=None, description="Fecha de procesamiento")
