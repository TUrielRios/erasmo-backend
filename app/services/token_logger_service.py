"""
Servicio para logging y monitoreo de tokens usado en respuestas
"""
from datetime import datetime
from typing import Dict, Any, Optional
import json

class TokenLoggerService:
    """Servicio para registrar y monitorear uso de tokens"""
    
    def __init__(self):
        self.logs = []
    
    def log_response_tokens(
        self,
        session_id: str,
        user_id: int,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        response_length: int,
        message_preview: str,
        require_analysis: bool = False
    ):
        """
        Registra información detallada de tokens usado en una respuesta
        """
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "session_id": session_id,
            "user_id": user_id,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "response_length": response_length,
            "response_preview": message_preview[:100],
            "require_analysis": require_analysis,
            "avg_tokens_per_char": round(completion_tokens / max(response_length, 1), 4),
            "efficiency": round((completion_tokens / total_tokens * 100) if total_tokens > 0 else 0, 2)
        }
        
        self._print_token_summary(log_entry)
        self.logs.append(log_entry)
    
    def log_streaming_tokens(
        self,
        session_id: str,
        user_id: int,
        model: str,
        estimated_completion_tokens: int,
        response_length: int,
        message_preview: str,
        response_time: float
    ):
        """
        Registra información de tokens para respuestas streaming
        """
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "session_id": session_id,
            "user_id": user_id,
            "model": model,
            "estimated_completion_tokens": estimated_completion_tokens,
            "response_length": response_length,
            "response_preview": message_preview[:100],
            "response_time_seconds": round(response_time, 2),
            "throughput": round(response_length / max(response_time, 0.1), 2)
        }
        
        self._print_streaming_summary(log_entry)
        self.logs.append(log_entry)
    
    def _print_token_summary(self, log_entry: Dict[str, Any]):
        """
        Imprime un resumen visual de tokens en la terminal
        """
        print(f"""
╔════════════════════════════════════════════════════════════════╗
║                  📊 TOKEN USAGE SUMMARY                         ║
╠════════════════════════════════════════════════════════════════╣
║ Session:              {log_entry['session_id'][:20]}...
║ User:                 {log_entry['user_id']}
║ Model:                {log_entry['model']}
║ ─────────────────────────────────────────────────────────────
║ Prompt Tokens:        {log_entry['prompt_tokens']:,} tokens
║ Completion Tokens:    {log_entry['completion_tokens']:,} tokens ✓
║ Total Tokens:         {log_entry['total_tokens']:,} tokens
║ ─────────────────────────────────────────────────────────────
║ Response Length:      {log_entry['response_length']:,} characters
║ Avg Tokens/Char:      {log_entry['avg_tokens_per_char']} tokens
║ Efficiency:           {log_entry['efficiency']}%
║ ─────────────────────────────────────────────────────────────
║ Response Preview:     {log_entry['response_preview'][:50]}...
║ Analysis Required:    {'Yes' if log_entry['require_analysis'] else 'No'}
╚════════════════════════════════════════════════════════════════╝
        """)
    
    def _print_streaming_summary(self, log_entry: Dict[str, Any]):
        """
        Imprime un resumen visual de tokens para streaming
        """
        print(f"""
╔════════════════════════════════════════════════════════════════╗
║               🔄 STREAMING TOKEN SUMMARY                        ║
╠════════════════════════════════════════════════════════════════╣
║ Session:              {log_entry['session_id'][:20]}...
║ User:                 {log_entry['user_id']}
║ Model:                {log_entry['model']}
║ ─────────────────────────────────────────────────────────────
║ Estimated Completion: {log_entry['estimated_completion_tokens']:,} tokens
║ Response Length:      {log_entry['response_length']:,} characters
║ Response Time:        {log_entry['response_time_seconds']}s ⏱️
║ ─────────────────────────────────────────────────────────────
║ Throughput:           {log_entry['throughput']} chars/sec
║ Response Preview:     {log_entry['response_preview'][:50]}...
╚════════════════════════════════════════════════════════════════╝
        """)
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas agregadas de tokens para una sesión
        """
        session_logs = [log for log in self.logs if log.get('session_id') == session_id]
        
        if not session_logs:
            return {"message": "No logs found for this session"}
        
        total_prompt = sum(log.get('prompt_tokens', 0) for log in session_logs)
        total_completion = sum(log.get('completion_tokens', 0) for log in session_logs)
        total_tokens = sum(log.get('total_tokens', 0) for log in session_logs)
        total_responses = len(session_logs)
        
        return {
            "session_id": session_id,
            "total_responses": total_responses,
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens_used": total_tokens,
            "average_tokens_per_response": round(total_completion / total_responses, 2),
            "most_expensive_response": max(session_logs, key=lambda x: x.get('total_tokens', 0)).get('response_preview', ''),
        }
