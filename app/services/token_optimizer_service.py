"""
Servicio avanzado de optimización de tokens para maximizar el potencial de la IA
Gestiona el presupuesto de tokens, compresión inteligente y caché de contexto
"""

import tiktoken
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import hashlib
import json
from sqlalchemy.orm import Session
from app.core.config import settings

class TokenOptimizerService:
    """
    Servicio para optimizar el uso de tokens en conversaciones
    Implementa estrategias inteligentes de compresión, caché y presupuesto
    """
    
    def __init__(self):
        self.encoding = tiktoken.encoding_for_model(settings.OPENAI_MODEL)
        self.context_cache: Dict[str, Dict[str, Any]] = {}
        self.compression_cache: Dict[str, str] = {}
        self.token_stats: Dict[str, Dict[str, int]] = {}
    
    def calculate_total_budget(self) -> int:
        """
        Calcula el presupuesto total de tokens disponible
        Aprovecha el máximo contexto de GPT-4o (128K)
        """
        model = settings.OPENAI_MODEL
        
        if "gpt-4" in model:
            # GPT-4o tiene contexto de 128K, usamos 120K agresivamente
            total_budget = 120000  # Increased from 100K to 120K
        elif "gpt-3.5" in model:
            total_budget = 15000
        else:
            total_budget = settings.MAX_CONTEXT_LENGTH * 4
        
        return total_budget
    
    def allocate_budget(self, prompt_role: str = "full_analysis") -> Dict[str, int]:
        """
        Asigna presupuesto de tokens para diferentes partes con MÁXIMO POTENCIAL
        Aumentados significativamente todos los presupuestos para máxima calidad
        """
        total_budget = self.calculate_total_budget()
        
        if prompt_role == "full_analysis":
            # Análisis profundo con máximo contexto
            return {
                "system_prompt": 3000,          # Increased from 2000
                "context": 80000,               # Increased from 60000
                "conversation_history": 50000, # Increased from 30000
                "response": settings.MAX_RESPONSE_TOKENS,  # 32000
                "buffer": settings.TOKEN_BUDGET_BUFFER
            }
        elif prompt_role == "normal_chat":
            # Chat conversacional optimizado
            return {
                "system_prompt": 2500,  # Increased from 1500
                "context": 60000,       # Increased from 40000
                "conversation_history": 35000,  # Increased from 20000
                "response": 10000,      # Increased from 6000
                "buffer": settings.TOKEN_BUDGET_BUFFER
            }
        elif prompt_role == "quick_response":
            # Respuesta rápida con contexto limitado
            return {
                "system_prompt": 1500,  # Increased from 1000
                "context": 30000,       # Increased from 20000
                "conversation_history": 15000,  # Increased from 10000
                "response": 6000,       # Increased from 4000
                "buffer": settings.TOKEN_BUDGET_BUFFER
            }
        else:
            return self.allocate_budget("full_analysis")
    
    def count_tokens(self, text: str) -> int:
        """Contar tokens en un texto"""
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            print(f"Error contando tokens: {e}")
            return len(text.split()) * 1.3  # Estimación aproximada
    
    def compress_context(self, context: List[Dict[str, Any]], max_tokens: int) -> List[Dict[str, Any]]:
        """
        Comprime el contexto de manera MENOS agresiva para mantener calidad
        Reduced compression aggressiveness - keep more content now that we have more tokens
        """
        compressed_context = []
        total_tokens = 0
        
        # Priorizar por relevancia y categoría
        priority_order = {
            'project_vector_search': 1,      # Máxima prioridad
            'project_knowledge': 2,
            'project_file': 2,
            'company_vector_search': 3,
            'company_knowledge': 4,
            'general': 5
        }
        
        # Ordenar por prioridad
        sorted_context = sorted(
            context, 
            key=lambda x: (priority_order.get(x.get('category'), 99), -x.get('relevance_score', 0))
        )
        
        for item in sorted_context:
            content = item.get('content', '')
            item_tokens = self.count_tokens(content)
            
            if item_tokens > 3000:
                compressed_content = self._compress_single_document(content, 2500)
                item_tokens = self.count_tokens(compressed_content)
                item['content'] = compressed_content
            
            if total_tokens + item_tokens <= max_tokens:
                compressed_context.append(item)
                total_tokens += item_tokens
            elif total_tokens < max_tokens * 0.85:  # Increased from 0.8 to 0.85
                # Truncar documento para encajar en presupuesto
                remaining_budget = max_tokens - total_tokens
                truncated = self._truncate_to_tokens(content, remaining_budget - 100)
                item['content'] = truncated
                compressed_context.append(item)
                break
        
        return compressed_context
    
    def _compress_single_document(self, text: str, target_tokens: int) -> str:
        """
        Comprime un documento usando estrategias menos agresivas ahora
        Improved: Keep more content, focus on structure preservation
        """
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.compression_cache:
            return self.compression_cache[text_hash]
        
        sentences = text.split('.')
        compressed = []
        current_tokens = 0
        
        important_keywords = [
            'importante', 'crítico', 'esencial', 'primero', 'obligatorio', 'debe',
            'debe seguir', 'clave', 'fundamental', 'prioritario', 'urgente', 'requiere',
            'necesario', 'conclusión', 'resumen', 'resultado', 'implicación', 'impacto'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_tokens = self.count_tokens(sentence)
            
            is_important = any(kw in sentence.lower() for kw in important_keywords)
            
            if is_important or current_tokens + sentence_tokens <= target_tokens:
                compressed.append(sentence)
                current_tokens += sentence_tokens
            
            if current_tokens >= target_tokens:
                break
        
        compressed_text = '. '.join(compressed)
        self.compression_cache[text_hash] = compressed_text
        
        return compressed_text
    
    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Trunca texto a un número específico de tokens"""
        try:
            tokens = self.encoding.encode(text)
            if len(tokens) <= max_tokens:
                return text
            
            truncated_tokens = tokens[:max_tokens]
            return self.encoding.decode(truncated_tokens)
        except Exception as e:
            print(f"Error truncando texto: {e}")
            words = text.split()
            approx_words = max_tokens // 1.3
            return ' '.join(words[:int(approx_words)])
    
    def optimize_prompt(
        self, 
        system_prompt: str,
        context: List[Dict[str, Any]],
        history: List[Dict[str, Any]],
        user_message: str,
        prompt_role: str = "full_analysis"
    ) -> Tuple[str, str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Optimiza el prompt completo para máximo rendimiento
        Uses new aggressive budgets for maximum context and response quality
        """
        budget = self.allocate_budget(prompt_role)
        
        # Comprimir contexto con nuevos presupuestos generosos
        compressed_context = self.compress_context(context, budget['context'])
        
        # Comprimir historial con presupuestos aumentados
        compressed_history = self._compress_history(history, budget['conversation_history'])
        
        # Truncar system prompt si es necesario
        system_tokens = self.count_tokens(system_prompt)
        if system_tokens > budget['system_prompt']:
            system_prompt = self._truncate_to_tokens(system_prompt, budget['system_prompt'])
        
        return system_prompt, user_message, compressed_context, compressed_history
    
    def _compress_history(self, history: List[Dict[str, Any]], max_tokens: int) -> List[Dict[str, Any]]:
        """
        Comprime el historial de manera menos agresiva con presupuestos mayores
        Keep more history messages now with increased token budget
        """
        if not history:
            return []
        
        recent_messages = history[-8:]
        older_messages = history[:-8]
        
        compressed = []
        total_tokens = 0
        
        # Agregar mensajes recientes sin comprimir
        for msg in recent_messages:
            content = msg.get('content', '')
            tokens = self.count_tokens(content)
            total_tokens += tokens
            compressed.append(msg)
        
        # Procesar mensajes antiguos con compresión
        if older_messages and total_tokens < max_tokens:
            remaining_budget = max_tokens - total_tokens
            
            for msg in reversed(older_messages):  # Del más reciente al más antiguo
                content = msg.get('content', '')
                tokens = self.count_tokens(content)
                
                if tokens <= remaining_budget:
                    compressed.insert(0, msg)
                    total_tokens += tokens
                    remaining_budget -= tokens
                elif msg.get('role') == 'user' and remaining_budget > 500:
                    # Intentar agregar resumen de mensaje del usuario
                    compressed_content = self._compress_single_document(content, remaining_budget - 100)
                    msg_copy = msg.copy()
                    msg_copy['content'] = compressed_content
                    compressed.insert(0, msg_copy)
                    break
        
        return compressed
    
    def estimate_response_time(self, total_input_tokens: int) -> float:
        """
        Estima el tiempo de respuesta basado en tokens de entrada
        Útil para feedback del usuario
        """
        # GPT-4o: ~15-20ms por token procesado
        base_time = 0.5  # segundos
        processing_time = (total_input_tokens / 1000) * 0.015
        return base_time + processing_time
    
    def get_token_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de uso de tokens para una sesión
        """
        if session_id not in self.token_stats:
            self.token_stats[session_id] = {
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_cost': 0.0,
                'message_count': 0,
                'avg_tokens_per_message': 0,
                'last_updated': None
            }
        
        stats = self.token_stats[session_id]
        return {
            **stats,
            'last_updated': stats['last_updated'].isoformat() if stats['last_updated'] else None
        }
    
    def record_token_usage(
        self, 
        session_id: str, 
        input_tokens: int, 
        output_tokens: int
    ):
        """Registra el uso de tokens para una sesión"""
        if session_id not in self.token_stats:
            self.token_stats[session_id] = {
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_cost': 0.0,
                'message_count': 0,
                'avg_tokens_per_message': 0,
                'last_updated': None
            }
        
        stats = self.token_stats[session_id]
        stats['total_input_tokens'] += input_tokens
        stats['total_output_tokens'] += output_tokens
        stats['message_count'] += 1
        
        # Calcular promedio
        if stats['message_count'] > 0:
            stats['avg_tokens_per_message'] = (stats['total_input_tokens'] + stats['total_output_tokens']) / stats['message_count']
        
        stats['total_cost'] = (input_tokens * 0.000005) + (output_tokens * 0.000015)
        
        stats['last_updated'] = datetime.now()
    
    def should_use_smart_context(self, session_id: str) -> bool:
        """
        Determina si se debe usar contexto inteligente
        More conservative about aggressive compression now
        """
        stats = self.get_token_stats(session_id)
        
        if stats['total_cost'] > 5.0:  # Increased threshold from 1.0
            return True
        
        if stats['message_count'] > 100:  # Increased from 50
            return True
        
        return settings.ENABLE_TOKEN_OPTIMIZATION
