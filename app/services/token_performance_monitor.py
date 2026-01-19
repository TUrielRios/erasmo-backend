"""
Monitor avanzado de rendimiento y optimizacion de tokens
Proporciona insights en tiempo real sobre uso y eficiencia
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from app.core.config import settings

class TokenPerformanceMonitor:
    """
    Monitorea y optimiza el rendimiento del sistema basado en tokens
    """
    
    def __init__(self):
        self.session_metrics: Dict[str, Dict[str, Any]] = {}
        self.global_stats = {
            'total_sessions': 0,
            'total_tokens_processed': 0,
            'total_cost': 0.0,
            'average_tokens_per_response': 0,
            'peak_tokens_used': 0,
            'performance_score': 0.85
        }
    
    def start_session_tracking(self, session_id: str, user_id: int, company_id: int):
        """Inicia tracking de tokens para una sesion"""
        self.session_metrics[session_id] = {
            'user_id': user_id,
            'company_id': company_id,
            'start_time': datetime.now(),
            'messages': [],
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0.0,
            'avg_latency': 0.0,
            'quality_score': 0.85,
            'cache_hits': 0,
            'cache_misses': 0
        }
        self.global_stats['total_sessions'] += 1
    
    def record_message(
        self,
        session_id: str,
        role: str,
        tokens: int,
        latency: float,
        cached: bool = False
    ):
        """Registra metricas de un mensaje"""
        if session_id not in self.session_metrics:
            return
        
        session = self.session_metrics[session_id]
        
        if role == 'user':
            session['total_input_tokens'] += tokens
        else:
            session['total_output_tokens'] += tokens
        
        # Actualizar estadisticas globales
        self.global_stats['total_tokens_processed'] += tokens
        self.global_stats['peak_tokens_used'] = max(
            self.global_stats['peak_tokens_used'],
            session['total_input_tokens'] + session['total_output_tokens']
        )
        
        # Rastrear latencia
        if not session['messages']:
            session['avg_latency'] = latency
        else:
            msg_count = len(session['messages'])
            session['avg_latency'] = (session['avg_latency'] * msg_count + latency) / (msg_count + 1)
        
        # Rastrear cache
        if cached:
            session['cache_hits'] += 1
        else:
            session['cache_misses'] += 1
        
        session['messages'].append({
            'role': role,
            'tokens': tokens,
            'latency': latency,
            'cached': cached,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Obtiene resumen de sesion con recomendaciones"""
        if session_id not in self.session_metrics:
            return {}
        
        session = self.session_metrics[session_id]
        total_tokens = session['total_input_tokens'] + session['total_output_tokens']
        
        # Calcular puntuacion de eficiencia
        efficiency_score = self._calculate_efficiency(session)
        
        # Determinar recomendaciones
        recommendations = self._generate_recommendations(session, efficiency_score)
        
        return {
            'session_id': session_id,
            'user_id': session['user_id'],
            'duration_seconds': (datetime.now() - session['start_time']).total_seconds(),
            'messages_count': len(session['messages']),
            'total_tokens': total_tokens,
            'input_tokens': session['total_input_tokens'],
            'output_tokens': session['total_output_tokens'],
            'avg_latency_ms': round(session['avg_latency'] * 1000, 2),
            'cache_hit_rate': self._calculate_cache_rate(session),
            'estimated_cost': self._calculate_cost(session),
            'efficiency_score': efficiency_score,
            'quality_score': session['quality_score'],
            'recommendations': recommendations
        }
    
    def _calculate_efficiency(self, session: Dict[str, Any]) -> float:
        """Calcula puntuacion de eficiencia (0-1)"""
        total_tokens = session['total_input_tokens'] + session['total_output_tokens']
        messages = len(session['messages'])
        
        if messages == 0:
            return 0.0
        
        # Eficiencia: tokens output vs input (queremos output alto)
        if session['total_input_tokens'] > 0:
            output_ratio = session['total_output_tokens'] / session['total_input_tokens']
        else:
            output_ratio = 0.0
        
        # Latencia: queremos latencia baja
        latency_efficiency = max(0.0, 1.0 - (session['avg_latency'] / 5.0))
        
        # Cache: queremos hit rate alto
        total_cache_ops = session['cache_hits'] + session['cache_misses']
        if total_cache_ops > 0:
            cache_efficiency = session['cache_hits'] / total_cache_ops
        else:
            cache_efficiency = 0.0
        
        # Combinar scores
        efficiency = (
            min(output_ratio * 0.3, 1.0) * 0.3 +  # Output ratio
            latency_efficiency * 0.4 +              # Latencia
            cache_efficiency * 0.3                  # Cache hit rate
        )
        
        return round(min(efficiency, 1.0), 2)
    
    def _calculate_cache_rate(self, session: Dict[str, Any]) -> float:
        """Calcula tasa de cache hit"""
        total = session['cache_hits'] + session['cache_misses']
        if total == 0:
            return 0.0
        return round((session['cache_hits'] / total) * 100, 2)
    
    def _calculate_cost(self, session: Dict[str, Any]) -> float:
        """Calcula costo estimado"""
        # GPT-4o: $0.005/$0.015 per 1K tokens
        input_cost = (session['total_input_tokens'] / 1000) * 0.005
        output_cost = (session['total_output_tokens'] / 1000) * 0.015
        return round(input_cost + output_cost, 6)
    
    def _generate_recommendations(self, session: Dict[str, Any], efficiency: float) -> List[str]:
        """Genera recomendaciones de optimizacion"""
        recommendations = []
        
        # Basado en cache
        cache_rate = self._calculate_cache_rate(session)
        if cache_rate < 30:
            recommendations.append("Aumentar reutilizacion de cache para reducir tokens")
        
        # Basado en latencia
        if session['avg_latency'] > 3.0:
            recommendations.append("Latencia alta - considere usar streaming")
        
        # Basado en eficiencia
        if efficiency < 0.6:
            recommendations.append("Eficiencia baja - considere optimizar presupuesto")
        
        # Basado en tokens
        total_tokens = session['total_input_tokens'] + session['total_output_tokens']
        if total_tokens > 50000 and len(session['messages']) < 10:
            recommendations.append("Alto uso de tokens - considere comprimir contexto")
        
        if not recommendations:
            recommendations.append("Rendimiento optimo")
        
        return recommendations
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Obtiene estadisticas globales del sistema"""
        total_tokens = self.global_stats['total_tokens_processed']
        
        if self.global_stats['total_sessions'] > 0:
            avg_tokens = total_tokens / self.global_stats['total_sessions']
        else:
            avg_tokens = 0
        
        return {
            'total_sessions': self.global_stats['total_sessions'],
            'total_tokens_processed': total_tokens,
            'average_tokens_per_session': round(avg_tokens, 0),
            'peak_tokens_used': self.global_stats['peak_tokens_used'],
            'total_estimated_cost': round(self.global_stats['total_cost'], 4),
            'performance_score': self.global_stats['performance_score'],
            'system_health': self._calculate_system_health()
        }
    
    def _calculate_system_health(self) -> str:
        """Calcula salud del sistema"""
        if self.global_stats['performance_score'] > 0.9:
            return "excellent"
        elif self.global_stats['performance_score'] > 0.75:
            return "good"
        elif self.global_stats['performance_score'] > 0.6:
            return "fair"
        else:
            return "needs_improvement"
    
    def export_metrics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Exporta metricas para analisis"""
        if session_id:
            return self.get_session_summary(session_id)
        else:
            return self.get_global_stats()
