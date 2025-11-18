"""
Servicio de optimización de embeddings y memoria conversacional
Mejora eficiencia de embeddings y retención de información clave
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import tiktoken

class EmbeddingOptimizationService:
    """
    Servicio que optimiza:
    - Generación y compresión de embeddings
    - Clustering de información similar
    - Resumen de conversaciones largas
    - Extracción de información clave
    """
    
    def __init__(self):
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")
        self.key_info_cache: Dict[str, Dict[str, Any]] = {}
    
    def compress_embeddings(
        self,
        embeddings: List[List[float]],
        target_dimension: int = 768
    ) -> List[List[float]]:
        """
        Comprime embeddings de 1536 → 768 dimensiones usando PCA
        Reduce 50% de espacio manteniendo ~95% de información
        """
        try:
            embeddings_array = np.array(embeddings)
            
            if embeddings_array.shape[1] <= target_dimension:
                return embeddings
            
            # Aplicar PCA simple: usar SVD
            mean = embeddings_array.mean(axis=0)
            centered = embeddings_array - mean
            
            # Calcular componentes principales
            _, _, Vt = np.linalg.svd(centered.T @ centered, full_matrices=False)
            
            # Reducir a target_dimension
            projection_matrix = Vt[:target_dimension]
            compressed = embeddings_array @ projection_matrix.T
            
            return compressed.tolist()
        except Exception as e:
            print(f"Error comprimiendo embeddings: {e}")
            return embeddings
    
    def extract_key_information(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extrae información clave de la conversación para memoria a largo plazo
        """
        key_info = {
            "entities": [],
            "key_decisions": [],
            "objectives": [],
            "constraints": [],
            "technical_details": [],
            "extracted_at": datetime.now()
        }
        
        # Palabras clave para diferentes categorías
        decision_keywords = ["decidimos", "vamos a", "implementaremos", "eligimos", "acordamos"]
        objective_keywords = ["objetivo", "meta", "propósito", "finalidad"]
        constraint_keywords = ["limitación", "restricción", "constraint", "límite", "no puede"]
        tech_keywords = ["técnica", "tecnología", "código", "arquitectura", "algoritmo"]
        
        for msg in conversation_history:
            content = msg.get("content", "").lower()
            role = msg.get("role", "")
            
            if role == "user":
                # Buscar decisiones
                for keyword in decision_keywords:
                    if keyword in content:
                        key_info["key_decisions"].append(msg.get("content", "")[:200])
                
                # Buscar objetivos
                for keyword in objective_keywords:
                    if keyword in content:
                        key_info["objectives"].append(msg.get("content", "")[:200])
                
                # Buscar restricciones
                for keyword in constraint_keywords:
                    if keyword in content:
                        key_info["constraints"].append(msg.get("content", "")[:200])
                
                # Buscar detalles técnicos
                for keyword in tech_keywords:
                    if keyword in content:
                        key_info["technical_details"].append(msg.get("content", "")[:200])
        
        # Limitar a elementos únicos y relevantes
        key_info["entities"] = list(set(key_info["entities"]))[:5]
        key_info["key_decisions"] = list(dict.fromkeys(key_info["key_decisions"]))[:3]
        key_info["objectives"] = list(dict.fromkeys(key_info["objectives"]))[:3]
        key_info["constraints"] = list(dict.fromkeys(key_info["constraints"]))[:3]
        key_info["technical_details"] = list(dict.fromkeys(key_info["technical_details"]))[:3]
        
        return key_info
    
    def create_conversation_summary(
        self,
        conversation_history: List[Dict[str, Any]],
        max_tokens: int = 500
    ) -> str:
        """
        Crea un resumen comprimido de la conversación
        """
        if not conversation_history:
            return ""
        
        # Tomar primero y último mensaje como puntos de referencia
        first_message = conversation_history[0].get("content", "")[:100]
        last_message = conversation_history[-1].get("content", "")[:100]
        
        # Extraer información clave
        key_info = self.extract_key_information(conversation_history)
        
        summary = f"""
CONVERSACIÓN RESUMIDA:
- Inicio: {first_message}
- Final: {last_message}
- Total de mensajes: {len(conversation_history)}

INFORMACIÓN CLAVE:
"""
        
        if key_info["objectives"]:
            summary += f"Objetivos: {', '.join([o[:50] for o in key_info['objectives']])}\n"
        
        if key_info["key_decisions"]:
            summary += f"Decisiones: {', '.join([d[:50] for d in key_info['key_decisions']])}\n"
        
        if key_info["constraints"]:
            summary += f"Restricciones: {', '.join([c[:50] for c in key_info['constraints']])}\n"
        
        # Truncar a max_tokens
        tokens = self.encoding.encode(summary)
        if len(tokens) > max_tokens:
            summary = self.encoding.decode(tokens[:max_tokens])
        
        return summary
    
    def cluster_similar_messages(
        self,
        messages: List[Dict[str, Any]],
        max_clusters: int = 5
    ) -> List[List[Dict[str, Any]]]:
        """
        Agrupa mensajes similares para compresión
        """
        if len(messages) <= max_clusters:
            return [[msg] for msg in messages]
        
        clusters: List[List[Dict[str, Any]]] = []
        used_indices = set()
        
        # Simple clustering basado en palabras clave
        for i, msg in enumerate(messages):
            if i in used_indices:
                continue
            
            cluster = [msg]
            used_indices.add(i)
            msg_words = set(msg.get("content", "").lower().split()[:20])
            
            # Buscar mensajes similares
            for j in range(i + 1, len(messages)):
                if j in used_indices:
                    continue
                
                other_words = set(messages[j].get("content", "").lower().split()[:20])
                
                # Calcular similitud Jaccard
                overlap = len(msg_words.intersection(other_words))
                total = len(msg_words.union(other_words))
                similarity = overlap / total if total > 0 else 0
                
                if similarity > 0.4:  # Threshold de similitud
                    cluster.append(messages[j])
                    used_indices.add(j)
                    
                    if len(cluster) >= (len(messages) - len(used_indices)) // (max_clusters - len(clusters)):
                        break
            
            clusters.append(cluster)
            
            if len(clusters) >= max_clusters:
                break
        
        return clusters
    
    def optimize_conversation_memory(
        self,
        conversation_history: List[Dict[str, Any]],
        max_memory_tokens: int = 50000
    ) -> Dict[str, Any]:
        """
        Optimiza la memoria conversacional para máxima eficiencia
        """
        if not conversation_history:
            return {
                "full_history": [],
                "summary": "",
                "key_info": {},
                "optimization_ratio": 0.0
            }
        
        # Calcular tokens originales
        original_tokens = sum(
            len(self.encoding.encode(msg.get("content", ""))) 
            for msg in conversation_history
        )
        
        # Estrategia 1: Mantener últimos N mensajes completos
        recent_keep_count = max(5, min(10, len(conversation_history) // 2))
        recent_messages = conversation_history[-recent_keep_count:]
        
        # Estrategia 2: Resumen de mensajes antiguos
        older_messages = conversation_history[:-recent_keep_count]
        summary = self.create_conversation_summary(older_messages, max_tokens=2000)
        
        # Estrategia 3: Información clave extraída
        key_info = self.extract_key_information(conversation_history)
        
        # Construcción de memoria optimizada
        optimized_history = []
        
        # Agregar resumen si hay mensajes antiguos
        if summary:
            optimized_history.append({
                "role": "system",
                "content": f"RESUMEN DE CONVERSACIÓN ANTERIOR:\n{summary}",
                "type": "summary"
            })
        
        # Agregar información clave
        if any([key_info["objectives"], key_info["key_decisions"], key_info["constraints"]]):
            key_info_str = "INFORMACIÓN CLAVE RECORDADA:\n"
            if key_info["objectives"]:
                key_info_str += f"Objetivos: {', '.join(key_info['objectives'][:2])}\n"
            if key_info["key_decisions"]:
                key_info_str += f"Decisiones: {', '.join(key_info['key_decisions'][:2])}\n"
            if key_info["constraints"]:
                key_info_str += f"Restricciones: {', '.join(key_info['constraints'][:2])}\n"
            
            optimized_history.append({
                "role": "system",
                "content": key_info_str,
                "type": "key_info"
            })
        
        # Agregar mensajes recientes
        optimized_history.extend(recent_messages)
        
        # Calcular tokens optimizados
        optimized_tokens = sum(
            len(self.encoding.encode(msg.get("content", "")))
            for msg in optimized_history
        )
        
        optimization_ratio = (original_tokens - optimized_tokens) / original_tokens if original_tokens > 0 else 0
        
        return {
            "original_message_count": len(conversation_history),
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "optimization_ratio": round(optimization_ratio * 100, 2),
            "full_history": optimized_history,
            "summary": summary,
            "key_info": key_info,
            "recent_messages_kept": recent_keep_count
        }
    
    def get_memory_recommendations(
        self,
        conversation_history: List[Dict[str, Any]],
        current_tokens: int
    ) -> List[str]:
        """
        Proporciona recomendaciones para optimizar memoria
        """
        recommendations = []
        
        if len(conversation_history) > 50:
            recommendations.append("Conversación muy larga - considere crear una nueva o resumir")
        
        if current_tokens > 40000:
            recommendations.append("Uso de tokens alto - memoria se está comprimiendo automáticamente")
        
        if len(conversation_history) > 20 and current_tokens < 10000:
            recommendations.append("Buena compresión - conversación optimizada correctamente")
        
        if len(conversation_history) < 10:
            recommendations.append("Conversación corta - puede mantener contexto completo")
        
        return recommendations
