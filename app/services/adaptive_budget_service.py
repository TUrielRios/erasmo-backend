"""
Servicio de presupuesto adaptativo de tokens
Ajusta dinámicamente la asignación de tokens según la complejidad de la consulta
y el historial de la conversación
"""

from typing import Dict, List, Tuple, Any, Optional
import tiktoken
from app.core.config import settings

class AdaptiveBudgetService:
    """
    Servicio que adapta dinámicamente el presupuesto de tokens
    basado en complejidad de consulta, historial y configuración del usuario
    """
    
    def __init__(self):
        self.encoding = tiktoken.encoding_for_model(settings.OPENAI_MODEL)
        self.complexity_cache: Dict[str, int] = {}
    
    def analyze_query_complexity(self, message: str) -> Tuple[str, float]:
        """
        Analiza la complejidad de la consulta del usuario con métricas avanzadas
        Retorna (nivel, factor_multiplicador)
        
        Niveles: "trivial", "simple", "medium", "complex", "very_complex"
        Factor: multiplicador para presupuesto base
        """
        words = message.split()
        word_count = len(words)
        
        # Características de complejidad expandidas
        complexity_keywords = {
            "analizar": 1.8, "comparar": 1.6, "estrategia": 1.9, "problema": 1.5,
            "solución": 1.4, "optimizar": 1.7, "implementar": 1.6, "evaluar": 1.5,
            "predecir": 1.6, "impacto": 1.5, "consecuencia": 1.5, "metodología": 1.8,
            "framework": 1.6, "estructura": 1.5, "proceso": 1.4, "diseñar": 1.7,
            "arquitectura": 1.7, "integración": 1.6, "escalabilidad": 1.7, "rendimiento": 1.6,
            "seguridad": 1.6, "riesgo": 1.5, "oportunidad": 1.5, "validación": 1.5,
            "experiencia": 1.5, "innovación": 1.6, "transformación": 1.7, "múltiple": 1.4,
            "variante": 1.4, "alternativa": 1.4, "simulación": 1.6, "escenario": 1.5
        }
        
        # Contar palabras de complejidad
        message_lower = message.lower()
        complexity_score = 1.0
        keyword_matches = 0
        
        for keyword, score in complexity_keywords.items():
            if keyword in message_lower:
                complexity_score += (score - 1.0) * 0.25
                keyword_matches += 1
        
        # Detectar estructuras complejas (múltiples oraciones, preguntas anidadas)
        question_marks = message.count('?')
        periods = message.count('.')
        colons = message.count(':')
        structure_complexity = (question_marks * 0.3) + (periods * 0.1) + (colons * 0.2)
        complexity_score += structure_complexity * 0.1
        
        # Ajustar por longitud con escalas mejoradas
        if word_count < 5:
            complexity_level = "trivial"
            factor = 0.6
        elif word_count < 15:
            complexity_level = "simple"
            factor = 0.9
        elif word_count < 35:
            complexity_level = "medium"
            factor = 1.1
        elif word_count < 70:
            complexity_level = "complex"
            factor = 1.5
        else:
            complexity_level = "very_complex"
            factor = 1.8
        
        # Ajustar agresivamente por palabras clave
        if keyword_matches >= 4:
            factor += 0.4
            if complexity_level != "very_complex":
                complexity_level = "very_complex"
        elif keyword_matches >= 3:
            factor += 0.25
            if complexity_level in ["medium", "complex"]:
                complexity_level = "complex"
        elif keyword_matches >= 2:
            factor += 0.15
        
        # Limitar factor (ahora con máximo más alto)
        factor = min(factor, 2.5)  # Aumentado de 2.0 a 2.5
        factor = max(factor, 0.6)   # Aumentado de 0.5 a 0.6
        
        return complexity_level, factor
    
    def calculate_adaptive_budget(
        self,
        message: str,
        history_length: int,
        available_context: int,
        require_analysis: bool = False
    ) -> Dict[str, int]:
        """
        Calcula presupuesto adaptativo MEJORADO con máximo potencial de IA
        Asignaciones significativamente aumentadas para respuestas de calidad superior
        """
        complexity_level, complexity_factor = self.analyze_query_complexity(message)
        
        if require_analysis:
            base_response = 10000      # Adjusted to safe limit
            base_context = 80000       # Increased context window
            base_history = 40000       # More conversation history
        else:
            base_response = 7000       # Normal chat with good depth
            base_context = 60000       # Substantial context
            base_history = 25000       # Reasonable history
        
        # Ajustar por complejidad (ahora más agresivo)
        response_tokens = int(base_response * complexity_factor * 1.2)
        context_tokens = int(base_context * complexity_factor * 1.15)
        history_tokens = int(base_history * complexity_factor)
        
        # Ajustar por historial con lógica mejorada
        if history_length > 50:
            history_tokens = int(history_tokens * 0.9)
        elif history_length > 20:
            history_tokens = int(history_tokens * 0.95)
        elif history_length < 5:
            history_tokens = int(history_tokens * 0.7)
        
        response_tokens = min(response_tokens, 15000)  # Safe under 16K limit
        response_tokens = max(response_tokens, 4000)   # Minimum for quality
        
        context_tokens = min(context_tokens, available_context)
        context_tokens = max(context_tokens, 20000)  # Mínimo aumentado
        
        history_tokens = min(history_tokens, available_context // 2)
        history_tokens = max(history_tokens, 10000)  # Mínimo aumentado
        
        return {
            "complexity_level": complexity_level,
            "complexity_factor": complexity_factor,
            "response_tokens": response_tokens,
            "context_tokens": context_tokens,
            "history_tokens": history_tokens,
            "system_prompt_tokens": 2000,  # Aumentado de 1500
            "buffer_tokens": settings.TOKEN_BUDGET_BUFFER,
            "total_allocated": response_tokens + context_tokens + history_tokens + 2000 + settings.TOKEN_BUDGET_BUFFER
        }
    
    def should_use_streaming(
        self,
        expected_tokens: int,
        user_preference: Optional[bool] = None,
        complexity_level: Optional[str] = None
    ) -> bool:
        """
        Determina si se debe usar streaming con lógica mejorada
        """
        if user_preference is not None:
            return user_preference
        
        # Usar streaming para respuestas complejas o largas
        use_for_length = expected_tokens > 2000  # Reducido de 3000 para más streaming
        use_for_complexity = complexity_level in ["complex", "very_complex"]
        
        return use_for_length or use_for_complexity

    def estimate_response_quality(
        self,
        complexity_level: str,
        allocated_tokens: int,
        has_project_context: bool = False,
        has_custom_instructions: bool = False
    ) -> Dict[str, Any]:
        """
        Estima la calidad esperada con métricas mejoradas
        """
        quality_score = 0.5
        
        # Ajustar por complejidad
        complexity_scores = {
            "trivial": 0.4,
            "simple": 0.6,
            "medium": 0.75,
            "complex": 0.88,
            "very_complex": 0.95
        }
        quality_score = complexity_scores.get(complexity_level, 0.7)
        
        # Ajustar por tokens disponibles (ahora con escala mejorada)
        if allocated_tokens < 4000:
            quality_score *= 0.8
        elif allocated_tokens < 8000:
            quality_score *= 0.9
        elif allocated_tokens > 10000:
            quality_score = min(quality_score + 0.2, 1.0)
        elif allocated_tokens > 15000:
            quality_score = min(quality_score + 0.3, 1.0)
        
        # Ajustar por contexto personalizado
        if has_project_context:
            quality_score = min(quality_score + 0.12, 1.0)
        if has_custom_instructions:
            quality_score = min(quality_score + 0.1, 1.0)
        
        quality_level = "poor"
        if quality_score < 0.35:
            quality_level = "poor"
        elif quality_score < 0.55:
            quality_level = "fair"
        elif quality_score < 0.8:
            quality_level = "good"
        else:
            quality_level = "excellent"
        
        return {
            "quality_score": round(quality_score, 2),
            "quality_level": quality_level,
            "recommendations": self._generate_quality_recommendations(quality_score, complexity_level, allocated_tokens),
            "estimated_latency_seconds": self._estimate_latency(allocated_tokens)
        }

    def _generate_quality_recommendations(
        self,
        quality_score: float,
        complexity_level: str,
        allocated_tokens: int
    ) -> List[str]:
        """
        Genera recomendaciones para mejorar calidad
        """
        recommendations = []
        
        if quality_score < 0.5:
            recommendations.append("Considere aumentar los tokens de respuesta")
        
        if complexity_level == "very_complex":
            recommendations.append("Esta es una consulta muy compleja - considere dividirla")
        
        if allocated_tokens < 6000:
            recommendations.append("Puede que necesite más tokens para una respuesta detallada")
        
        if quality_score >= 0.8:
            recommendations.append("Excelente presupuesto para esta consulta")
        
        return recommendations
    
    def _estimate_latency(self, total_tokens: int) -> float:
        """
        Estima latencia de respuesta basada en tokens
        """
        # GPT-4o: ~15-20ms por token para procesamiento
        base_latency = 0.5  # segundos
        token_processing = (total_tokens / 1000) * 0.018
        return round(base_latency + token_processing, 2)
    
    def count_tokens(self, text: str) -> int:
        """Contar tokens en un texto"""
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception:
            return len(text.split()) * 1.3
