"""
Servicio para ingesta y procesamiento de documentos
"""

from typing import List, Dict, Any
import hashlib
import json
import os
from datetime import datetime

from app.models.schemas import DocumentMetadata, DocumentType, IngestionType
from app.db.vector_store import VectorStore
from app.utils.text_processor import TextProcessor

class IngestionService:
    """
    Servicio encargado de la ingesta de documentos y su indexación semántica
    """
    
    PERSONALITY_STORAGE_PATH = "data/personality_config.json"
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.text_processor = TextProcessor()
        self._ensure_personality_storage_dir()
    
    def _ensure_personality_storage_dir(self):
        """Ensure the data directory exists for personality storage"""
        os.makedirs(os.path.dirname(self.PERSONALITY_STORAGE_PATH), exist_ok=True)
    
    def _load_personality_store(self) -> Dict[str, Any]:
        """Load personality configuration from persistent storage"""
        try:
            if os.path.exists(self.PERSONALITY_STORAGE_PATH):
                with open(self.PERSONALITY_STORAGE_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"❌ Error loading personality store: {e}")
            return {}
    
    def _save_personality_store(self, personality_store: Dict[str, Any]):
        """Save personality configuration to persistent storage"""
        try:
            with open(self.PERSONALITY_STORAGE_PATH, 'w', encoding='utf-8') as f:
                json.dump(personality_store, f, ensure_ascii=False, indent=2)
            print(f"💾 Personality configuration saved to {self.PERSONALITY_STORAGE_PATH}")
        except Exception as e:
            print(f"❌ Error saving personality store: {e}")

    async def process_knowledge_file(self, content: bytes, filename: str, metadata: Dict[str, Any] = None) -> List[str]:
        """
        Procesa un archivo como fuente de conocimiento y lo indexa en la base vectorial
        """
        return await self._process_file_for_vectordb(content, filename, metadata)
    
    async def process_personality_file(self, content: bytes, filename: str, metadata: Dict[str, Any] = None) -> List[str]:
        """
        Procesa un archivo como configuración de personalidad del agente
        
        Args:
            content: Contenido del archivo en bytes
            filename: Nombre del archivo
            metadata: Metadatos adicionales
        
        Returns:
            Lista con un ID único para el archivo de personalidad
        """
        
        print(f"🎭 Procesando archivo de personalidad: {filename}")
        
        # 1. Decodificar contenido
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            print(f"❌ Error decodificando {filename}")
            return []
        
        # El protocolo debe mantenerse íntegro sin modificaciones de formato
        cleaned_text = text_content.strip()  # Solo eliminar espacios al inicio/final
        
        print(f"📏 Contenido de personalidad: {len(cleaned_text)} caracteres")
        
        # 3. Crear ID único para este archivo de personalidad
        personality_id = f"personality_{hashlib.md5(filename.encode()).hexdigest()}"
        
        personality_store = self._load_personality_store()
        
        # 4. Almacenar en el store de personalidad
        personality_store[personality_id] = {
            "filename": filename,
            "content": cleaned_text,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "type": "personality_config"
        }
        
        self._save_personality_store(personality_store)
        
        print(f"✅ Personalidad {filename} configurada exitosamente con {len(cleaned_text)} caracteres")
        return [personality_id]
    
    async def _process_file_for_vectordb(self, content: bytes, filename: str, metadata: Dict[str, Any] = None) -> List[str]:
        """
        Procesa un archivo y lo indexa en la base vectorial (método original)
        """
        
        print(f"📄 Procesando archivo de conocimiento: {filename}")
        
        # 1. Decodificar contenido
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            print(f"❌ Error decodificando {filename}")
            return []
        
        # 2. Limpiar y procesar texto
        cleaned_text = self.text_processor.clean_text(text_content)
        
        # 3. Dividir en chunks semánticamente coherentes
        chunks = self.text_processor.create_chunks(cleaned_text)
        print(f"📝 Creados {len(chunks)} chunks para {filename}")
        
        # 4. Generar embeddings para cada chunk
        embeddings = await self.text_processor.generate_embeddings(chunks)
        
        # 5. Crear metadatos para cada chunk
        chunk_metadata = []
        base_metadata = self._create_chunk_metadata(filename, metadata)
        
        for i, chunk in enumerate(chunks):
            chunk_meta = {
                **base_metadata,
                "chunk_index": i,
                "chunk_text_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk
            }
            chunk_metadata.append(chunk_meta)
        
        # 6. Initialize vector store if needed
        if not hasattr(self.vector_store, 'index') or self.vector_store.store.index is None:
            await self.vector_store.initialize()
        
        # 7. Almacenar en vector database
        chunk_ids = await self.vector_store.store_chunks(chunks, embeddings, chunk_metadata)
        
        print(f"✅ Archivo {filename} procesado exitosamente con {len(chunk_ids)} chunks")
        return chunk_ids
    
    def get_personality_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración actual de personalidad del agente
        
        Returns:
            Diccionario con toda la configuración de personalidad
        """
        
        personality_store = self._load_personality_store()
        
        if not personality_store:
            return {
                "status": "no_personality_configured",
                "message": "No se ha configurado ninguna personalidad",
                "files": []
            }
        
        return {
            "status": "personality_configured",
            "message": f"Personalidad configurada con {len(personality_store)} archivo(s)",
            "files": [
                {
                    "id": pid,
                    "filename": config["filename"],
                    "created_at": config["created_at"],
                    "content_preview": config["content"][:200] + "..." if len(config["content"]) > 200 else config["content"]
                }
                for pid, config in personality_store.items()
            ],
            "full_personality_text": "\n\n".join([config["content"] for config in personality_store.values()])
        }
    
    async def clear_personality(self) -> bool:
        """
        Elimina toda la configuración de personalidad
        """
        
        try:
            if os.path.exists(self.PERSONALITY_STORAGE_PATH):
                os.remove(self.PERSONALITY_STORAGE_PATH)
            print("🧹 Configuración de personalidad eliminada")
            return True
        except Exception as e:
            print(f"❌ Error eliminando personalidad: {e}")
            return False
    
    # Método de compatibilidad - procesa como conocimiento por defecto
    async def process_file(self, content: bytes, filename: str, metadata: Dict[str, Any] = None) -> List[str]:
        """
        Método de compatibilidad - procesa como conocimiento por defecto
        """
        return await self.process_knowledge_file(content, filename, metadata)
    
    def _create_chunk_metadata(self, filename: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Crea metadatos para los chunks de un documento
        """
        
        base_metadata = {
            "filename": filename,
            "processed_at": datetime.now().isoformat(),
            "file_hash": hashlib.md5(filename.encode()).hexdigest(),
            "chunk_type": "document_chunk"
        }
        
        if metadata:
            base_metadata.update(metadata)
        
        return base_metadata
    
    async def get_document_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de documentos indexados
        """
        
        try:
            # Initialize vector store if needed
            if not hasattr(self.vector_store, 'store') or self.vector_store.store.index is None:
                await self.vector_store.initialize()
            
            # For FAISS, we can get detailed stats from metadata_store
            if hasattr(self.vector_store.store, 'metadata_store') and self.vector_store.store.metadata_store:
                metadata_store = self.vector_store.store.metadata_store
                unique_files = set(meta.get("filename", "") for meta in metadata_store.values())
                
                return {
                    "total_documents": len(unique_files),
                    "total_chunks": len(metadata_store),
                    "total_embeddings": len(metadata_store),
                    "storage_size": f"{len(str(metadata_store)) / 1024:.1f}KB",
                    "last_update": max((meta.get("stored_at") for meta in metadata_store.values()), default=None)
                }
            
            # For Pinecone, we get basic stats from the index
            elif hasattr(self.vector_store.store, 'index') and self.vector_store.store.index:
                try:
                    # Get index stats from Pinecone
                    index_stats = self.vector_store.store.index.describe_index_stats()
                    total_vectors = index_stats.get('total_vector_count', 0)
                    
                    return {
                        "total_documents": "N/A",  # Pinecone doesn't track unique documents easily
                        "total_chunks": total_vectors,
                        "total_embeddings": total_vectors,
                        "storage_size": f"{total_vectors * 1536 * 4 / 1024 / 1024:.1f}MB",  # Rough estimate
                        "last_update": datetime.now().isoformat()
                    }
                except Exception as e:
                    print(f"⚠️ Error getting Pinecone stats: {e}")
                    return self._get_default_stats()
            
            else:
                return self._get_default_stats()
                
        except Exception as e:
            print(f"❌ Error getting document stats: {e}")
            return self._get_default_stats()
    
    def _get_default_stats(self) -> Dict[str, Any]:
        """Returns default stats when vector store is not available"""
        return {
            "total_documents": 0,
            "total_chunks": 0,
            "total_embeddings": 0,
            "storage_size": "0MB",
            "last_update": None
        }
    
    async def remove_document(self, filename: str) -> bool:
        """
        Elimina un documento y todos sus chunks de la base vectorial
        """
        
        return await self.vector_store.remove_by_metadata({"filename": filename})
