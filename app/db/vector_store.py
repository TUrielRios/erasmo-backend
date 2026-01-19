"""
Abstraccion para manejo de base de datos vectorial
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import numpy as np
import faiss
import pickle
import os
import json
from datetime import datetime
import unicodedata
import hashlib

from app.core.config import settings

class VectorStoreInterface(ABC):
    """Interfaz abstracta para bases de datos vectoriales"""
    
    @abstractmethod
    async def initialize(self):
        """Inicializa la conexion con la base de datos"""
        pass
    
    @abstractmethod
    async def store_chunks(self, chunks: List[str], embeddings: List[List[float]], metadata: List[Dict]) -> List[str]:
        """Almacena chunks con sus embeddings y metadatos"""
        pass
    
    @abstractmethod
    async def similarity_search(self, query: str, top_k: int = 5, company_id: int = None, project_id: int = None) -> List[Dict[str, Any]]:
        """Busca chunks similares a una query"""
        pass
    
    @abstractmethod
    async def remove_by_metadata(self, metadata_filter: Dict[str, Any]) -> bool:
        """Elimina chunks basado en metadatos"""
        pass

class PineconeVectorStore(VectorStoreInterface):
    """Implementacion con Pinecone"""
    
    def __init__(self):
        self.index = None
        self.pc = None
        self.text_processor = None
    
    async def initialize(self):
        """Inicializa conexion con Pinecone"""
        print("[INFO] Inicializando Pinecone Vector Store...")
        
        try:
            from pinecone import Pinecone
            
            if not self.text_processor:
                from app.utils.text_processor import TextProcessor
                self.text_processor = TextProcessor()
            
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Check if index exists, create if not
            if settings.PINECONE_INDEX_NAME not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=settings.EMBEDDING_DIMENSION,
                    metric='cosine',
                    spec={
                        'serverless': {
                            'cloud': 'aws',
                            'region': 'us-east-1'
                        }
                    }
                )
                print(f"[OK] Creado nuevo indice Pinecone: {settings.PINECONE_INDEX_NAME}")
            
            self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
            print(f"[OK] Conectado a indice Pinecone: {settings.PINECONE_INDEX_NAME}")
            
        except Exception as e:
            print(f"[ERR] Error inicializando Pinecone: {e}")
            raise
    
    async def store_chunks(self, chunks: List[str], embeddings: List[List[float]], metadata: List[Dict]) -> List[str]:
        """Almacena en Pinecone"""
        if not self.index:
            await self.initialize()
        
        vectors_to_upsert = []
        chunk_ids = []
        
        for i, (chunk, embedding, meta) in enumerate(zip(chunks, embeddings, metadata)):
            filename = meta.get('filename', 'unknown')
            # Convert to ASCII by removing accents and non-ASCII characters
            ascii_filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
            # Remove any remaining problematic characters and replace with underscore
            ascii_filename = ''.join(c if c.isalnum() or c in '-_.' else '_' for c in ascii_filename)
            
            chunk_id = f"chunk_{ascii_filename}_{i}_{hash(chunk) % 10000}"
            chunk_ids.append(chunk_id)
            
            # Prepare vector for Pinecone
            vector_data = {
                'id': chunk_id,
                'values': embedding,
                'metadata': {
                    **meta,
                    'content': chunk,  # Store actual text in metadata
                    'chunk_id': chunk_id,
                    'stored_at': datetime.now().isoformat()
                }
            }
            vectors_to_upsert.append(vector_data)
        
        # Upsert in batches (Pinecone has limits)
        batch_size = 100
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            self.index.upsert(vectors=batch)
        
        print(f"[OK] Almacenados {len(chunks)} chunks en Pinecone")
        return chunk_ids
    
    async def similarity_search(self, query: str, top_k: int = 5, company_id: int = None, project_id: int = None) -> List[Dict[str, Any]]:
        """Busqueda de similitud en Pinecone"""
        if not self.index:
            await self.initialize()
        
        if not self.text_processor:
            from app.utils.text_processor import TextProcessor
            self.text_processor = TextProcessor()
        
        try:
            # Generate embedding for query
            query_embeddings = await self.text_processor.generate_embeddings([query])
            query_embedding = query_embeddings[0]
            
            filter_dict = {}
            if project_id is not None:
                filter_dict["project_id"] = {"$eq": project_id}
                print(f"[SEARCH] [PINECONE] Filtering by project_id: {project_id}")
            elif company_id is not None:
                filter_dict["company_id"] = {"$eq": company_id}
                print(f"[SEARCH] [PINECONE] Filtering by company_id: {company_id}")
            
            # Search in Pinecone with filtering
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )
            
            results = []
            for match in search_results.matches:
                if match.score > 0.7:  # Similarity threshold
                    results.append({
                        "content": match.metadata.get('content', ''),
                        "metadata": match.metadata,
                        "score": float(match.score),
                        "source": match.metadata.get('filename', 'unknown')
                    })
            
            if project_id:
                print(f"[SEARCH] Encontrados {len(results)} documentos relevantes para proyecto {project_id}: '{query[:50]}...'")
            elif company_id:
                print(f"[SEARCH] Encontrados {len(results)} documentos relevantes para empresa {company_id}: '{query[:50]}...'")
            else:
                print(f"[SEARCH] Encontrados {len(results)} documentos relevantes para: '{query[:50]}...'")
            return results
            
        except Exception as e:
            print(f"[ERR] Error en busqueda Pinecone: {e}")
            return []
    
    async def remove_by_metadata(self, metadata_filter: Dict[str, Any]) -> bool:
        """Elimina de Pinecone por metadatos"""
        if not self.index:
            await self.initialize()
        
        try:
            # Pinecone doesn't support direct metadata filtering for deletion
            # We need to query first, then delete by IDs
            # This is a simplified implementation
            
            # For now, delete all vectors (you might want to implement more sophisticated filtering)
            if 'filename' in metadata_filter:
                # Delete by namespace or implement custom logic
                print(f"[DELETE] Eliminacion por metadatos en Pinecone: {metadata_filter}")
                # self.index.delete(delete_all=True)  # Use with caution
                return True
            
            return False
            
        except Exception as e:
            print(f"[ERR] Error eliminando de Pinecone: {e}")
            return False
    
    async def close(self):
        """Cierra conexion"""
        print("[SAVE] Pinecone Vector Store cerrado")
        pass

class FAISSVectorStore(VectorStoreInterface):
    """Implementacion con FAISS (local)"""
    
    def __init__(self):
        self.index = None
        self.metadata_store = {}
        self.chunk_store = {}  # Store actual text chunks
        self.index_path = "data/faiss_index.bin"
        self.metadata_path = "data/metadata.json"
        self.chunks_path = "data/chunks.json"
        self.next_id = 0
        self.text_processor = None
    
    async def initialize(self):
        """Inicializa FAISS"""
        print("[INIT] Inicializando FAISS Vector Store...")
        
        if not self.text_processor:
            from app.utils.text_processor import TextProcessor
            self.text_processor = TextProcessor()
        
        os.makedirs("data", exist_ok=True)
        
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            print(f"[OK] Cargado indice FAISS existente con {self.index.ntotal} vectores")
        else:
            self.index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSION)  # Inner product for cosine similarity
            print("[OK] Creado nuevo indice FAISS")
        
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata_store = json.load(f)
        
        if os.path.exists(self.chunks_path):
            with open(self.chunks_path, 'r', encoding='utf-8') as f:
                self.chunk_store = json.load(f)
        
        if self.metadata_store:
            self.next_id = max(int(k) for k in self.metadata_store.keys()) + 1
    
    async def store_chunks(self, chunks: List[str], embeddings: List[List[float]], metadata: List[Dict]) -> List[str]:
        """Almacena en FAISS"""
        if not self.index:
            await self.initialize()
        
        chunk_ids = []
        
        embeddings_array = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings_array)  # Normalize for cosine similarity
        
        self.index.add(embeddings_array)
        
        for i, (chunk, meta) in enumerate(zip(chunks, metadata)):
            chunk_id = str(self.next_id + i)
            chunk_ids.append(chunk_id)
            
            # Store chunk text
            self.chunk_store[chunk_id] = chunk
            
            # Store metadata with timestamp
            meta_with_id = {**meta, "chunk_id": chunk_id, "stored_at": datetime.now().isoformat()}
            self.metadata_store[chunk_id] = meta_with_id
        
        self.next_id += len(chunks)
        
        await self._save_to_disk()
        
        print(f"[OK] Almacenados {len(chunks)} chunks en FAISS")
        return chunk_ids
    
    async def similarity_search(self, query: str, top_k: int = 5, company_id: int = None, project_id: int = None) -> List[Dict[str, Any]]:
        """Busqueda en FAISS"""
        if not self.index or self.index.ntotal == 0:
            print("[WARN] No hay documentos indexados para buscar")
            return []
        
        if not self.text_processor:
            from app.utils.text_processor import TextProcessor
            self.text_processor = TextProcessor()
        
        # Generate real embedding for the query
        query_embeddings = await self.text_processor.generate_embeddings([query])
        query_embedding = np.array([query_embeddings[0]], dtype=np.float32)
        faiss.normalize_L2(query_embedding)
        
        scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for invalid indices
                continue
            
            chunk_ids = list(self.chunk_store.keys())
            if idx < len(chunk_ids):
                chunk_id = chunk_ids[idx]
                if chunk_id in self.chunk_store and chunk_id in self.metadata_store:
                    metadata = self.metadata_store[chunk_id]
                    
                    if project_id is not None and metadata.get('project_id') != project_id:
                        continue
                    elif company_id is not None and project_id is None and metadata.get('company_id') != company_id:
                        continue
                    
                    results.append({
                        "content": self.chunk_store[chunk_id],
                        "metadata": metadata,
                        "score": float(score),
                        "source": metadata.get("filename", "unknown")
                    })
        
        if project_id:
            print(f"[SEARCH] Encontrados {len(results)} documentos relevantes para proyecto {project_id}: '{query[:50]}...'")
        elif company_id:
            print(f"[SEARCH] Encontrados {len(results)} documentos relevantes para empresa {company_id}: '{query[:50]}...'")
        else:
            print(f"[SEARCH] Encontrados {len(results)} documentos relevantes para: '{query[:50]}...'")
        return results
    
    async def remove_by_metadata(self, metadata_filter: Dict[str, Any]) -> bool:
        """Elimina de FAISS"""
        to_remove = []
        for chunk_id, metadata in self.metadata_store.items():
            match = all(metadata.get(k) == v for k, v in metadata_filter.items())
            if match:
                to_remove.append(chunk_id)
        
        if not to_remove:
            return False
        
        for chunk_id in to_remove:
            if chunk_id in self.chunk_store:
                del self.chunk_store[chunk_id]
            if chunk_id in self.metadata_store:
                del self.metadata_store[chunk_id]
        
        # Rebuild FAISS index after deletions
        if to_remove:
            await self._rebuild_index()
        
        print(f"[DELETE] Eliminados {len(to_remove)} chunks")
        return True
    
    async def _rebuild_index(self):
        """Rebuilds FAISS index after deletions"""
        # In production, you'd want a more sophisticated deletion strategy
        remaining_chunks = list(self.chunk_store.keys())
        if not remaining_chunks:
            self.index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSION)
            self.next_id = 0
        else:
            print("[WARN] Reconstruccion de indice requerida despues de eliminacion")
            # For now, just reset - in production you'd regenerate embeddings
            self.index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSION)
        
        await self._save_to_disk()
    
    async def _save_to_disk(self):
        """Save index and metadata to disk"""
        faiss.write_index(self.index, self.index_path)
        
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata_store, f, ensure_ascii=False, indent=2)
        
        with open(self.chunks_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunk_store, f, ensure_ascii=False, indent=2)
    
    async def close(self):
        """Cierra FAISS"""
        await self._save_to_disk()
        print("[SAVE] FAISS Vector Store guardado y cerrado")

class VectorStore:
    """Factory para crear el vector store apropiado"""
    
    def __init__(self):
        if settings.VECTOR_DB_TYPE == "pinecone":
            self.store = PineconeVectorStore()
        elif settings.VECTOR_DB_TYPE == "faiss":
            self.store = FAISSVectorStore()
        else:
            raise ValueError(f"Vector DB type no soportado: {settings.VECTOR_DB_TYPE}")
    
    async def initialize(self):
        """Inicializa el vector store"""
        await self.store.initialize()
    
    async def store_chunks(self, chunks: List[str], embeddings: List[List[float]], metadata: List[Dict]) -> List[str]:
        """Almacena chunks"""
        return await self.store.store_chunks(chunks, embeddings, metadata)
    
    async def similarity_search(self, query: str, top_k: int = 5, company_id: int = None, project_id: int = None) -> List[Dict[str, Any]]:
        """Busqueda de similitud"""
        return await self.store.similarity_search(query, top_k, company_id, project_id)
    
    async def remove_by_metadata(self, metadata_filter: Dict[str, Any]) -> bool:
        """Elimina por metadatos"""
        return await self.store.remove_by_metadata(metadata_filter)
    
    async def close(self):
        """Cierra conexion"""
        await self.store.close()
