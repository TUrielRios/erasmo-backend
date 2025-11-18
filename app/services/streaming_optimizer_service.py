"""
Servicio para optimización de streaming de respuestas
Maximiza la velocidad y calidad de respuestas en tiempo real
"""

from typing import AsyncGenerator, Dict, Any, List
import json
from datetime import datetime

class StreamingOptimizerService:
    """
    Optimiza el streaming de respuestas para máxima eficiencia
    Implementa chunking inteligente y priorización de contenido
    """
    
    def __init__(self):
        self.chunk_size = 50  # Caracteres por chunk optimizado
        self.priority_words = [
            'importante', 'crítico', 'esencial', 'primero', 'obligatorio',
            'debe', 'recomendación', 'conclusión', 'acción', 'resultado'
        ]
    
    def _calculate_chunk_size(self, total_length: int, response_tokens: int) -> int:
        """
        Calcula tamaño de chunk dinámico basado en longitud y complejidad
        """
        if response_tokens > 10000:
            return 100  # Chunks más grandes para respuestas largas
        elif response_tokens > 5000:
            return 75
        else:
            return 50
    
    def _prioritize_content(self, content: str) -> List[str]:
        """
        Prioriza contenido por importancia para streaming
        """
        lines = content.split('\n')
        prioritized = []
        
        for line in lines:
            priority = 0
            # Detectar líneas importantes
            if any(word in line.lower() for word in self.priority_words):
                priority = 2
            elif line.strip().startswith('##'):  # Headers
                priority = 1
            
            prioritized.append((priority, line))
        
        # Ordenar por prioridad pero manteniendo orden general
        return [line for _, line in prioritized]
    
    async def stream_optimized_response(
        self,
        content: str,
        streaming_callback=None
    ) -> AsyncGenerator[str, None]:
        """
        Genera streaming optimizado de contenido
        """
        chunk_size = self._calculate_chunk_size(len(content), len(content.split()))
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            
            if streaming_callback:
                await streaming_callback(chunk)
            
            yield chunk
    
    def format_streaming_chunk(self, chunk: str, is_final: bool = False) -> Dict[str, Any]:
        """
        Formatea chunk para streaming con metadatos
        """
        return {
            'content': chunk,
            'timestamp': datetime.now().isoformat(),
            'is_final': is_final,
            'metadata': {
                'chunk_size': len(chunk),
                'contains_important_keyword': any(
                    word in chunk.lower() for word in self.priority_words
                )
            }
        }
    
    def estimate_streaming_time(self, content_length: int, tokens: int) -> float:
        """
        Estima tiempo de streaming basado en contenido
        """
        # Aproximadamente 40-60ms por chunk
        chunks = content_length / self.chunk_size
        return chunks * 0.05  # segundos
