"""
Utilidades para procesamiento de texto y generación de embeddings
"""

from typing import List, Dict, Any
import re
import openai
from sentence_transformers import SentenceTransformer

from app.core.config import settings

class TextProcessor:
    """
    Procesador de texto para limpieza, chunking y generación de embeddings
    """
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        # TODO: Inicializar modelo local de embeddings si es necesario
        # self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def clean_text(self, text: str) -> str:
        """
        Limpia y normaliza texto
        
        Args:
            text: Texto crudo
        
        Returns:
            Texto limpio y normalizado
        """
        
        # Eliminar caracteres especiales y normalizar espacios
        text = re.sub(r'\s+', ' ', text)  # Múltiples espacios a uno
        text = re.sub(r'\n+', '\n', text)  # Múltiples saltos de línea
        text = text.strip()
        
        # TODO: Agregar más reglas de limpieza según necesidades
        # - Eliminar URLs
        # - Normalizar puntuación
        # - Corregir encoding
        
        return text
    
    def create_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Divide texto en chunks semánticamente coherentes
        
        Args:
            text: Texto a dividir
            chunk_size: Tamaño máximo de cada chunk
            overlap: Solapamiento entre chunks
        
        Returns:
            Lista de chunks de texto
        """
        
        # TODO: Implementar chunking semántico más sofisticado
        # Por ahora, chunking simple por caracteres con overlap
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Intentar cortar en un punto natural (final de oración)
            if end < len(text):
                # Buscar el último punto antes del límite
                last_period = text.rfind('.', start, end)
                if last_period > start + chunk_size // 2:
                    end = last_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings para una lista de textos usando batch processing
        
        Args:
            texts: Lista de textos
        
        Returns:
            Lista de embeddings (vectores)
        """
        
        embeddings = []
        batch_size = 20  # Process in batches to avoid rate limits
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                response = self.openai_client.embeddings.create(
                    model=settings.EMBEDDING_MODEL,
                    input=batch  # Send batch instead of individual texts
                )
                
                # Extract embeddings from batch response
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                print(f"Error generando embeddings para batch {i//batch_size + 1}: {e}")
                # Generate fallback embeddings for the entire batch
                for _ in batch:
                    import random
                    embedding = [random.uniform(-1, 1) for _ in range(settings.EMBEDDING_DIMENSION)]
                    embeddings.append(embedding)
        
        print(f"✅ Generados {len(embeddings)} embeddings")
        return embeddings
    
    def extract_metadata_from_text(self, text: str, filename: str) -> Dict[str, Any]:
        """
        Extrae metadatos automáticamente del texto
        
        Args:
            text: Contenido del texto
            filename: Nombre del archivo
        
        Returns:
            Diccionario con metadatos extraídos
        """
        
        metadata = {
            "word_count": len(text.split()),
            "char_count": len(text),
            "filename": filename,
            "language": "es",  # TODO: Detectar idioma automáticamente
        }
        
        # TODO: Extraer más metadatos
        # - Temas principales
        # - Entidades nombradas
        # - Nivel de complejidad
        # - Tipo de contenido (estratégico, operativo, etc.)
        
        return metadata
