"""
Utilidades para formateo de respuestas en Markdown
"""

from typing import Dict, Any, List
from datetime import datetime

class MarkdownFormatter:
    """
    Formateador para generar respuestas estructuradas en Markdown
    """
    
    @staticmethod
    def format_conceptual_response(
        content: str,
        sources: List[str],
        confidence: float,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Formatea una respuesta conceptual en Markdown
        """
        
        markdown = f"""# 🧠 Análisis Conceptual

{content}

## 📚 Fuentes de Conocimiento

{MarkdownFormatter._format_sources(sources)}

## 📊 Nivel de Confianza

**Confianza:** {confidence:.1%}

---
*Generado por Erasmo Estratégico Verbal*
"""
        
        return markdown
    
    @staticmethod
    def format_accional_response(
        content: str,
        priority: str,
        timeline: str = None,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Formatea una respuesta accional en Markdown
        """
        
        priority_emoji = {
            "alta": "🔴",
            "media": "🟡", 
            "baja": "🟢"
        }
        
        markdown = f"""# ⚡ Plan de Acción

{content}

## 📋 Información del Plan

**Prioridad:** {priority_emoji.get(priority, "⚪")} {priority.title()}
"""
        
        if timeline:
            markdown += f"**Timeline:** {timeline}\n"
        
        markdown += """
---
*Generado por Erasmo Estratégico Verbal*
"""
        
        return markdown
    
    @staticmethod
    def format_clarification_questions(questions: List[Dict[str, Any]]) -> str:
        """
        Formatea preguntas de clarificación en Markdown
        """
        
        markdown = """# ❓ Necesito Más Información

Para darte la mejor respuesta estratégica, necesito que me ayudes con algunas clarificaciones:

"""
        
        for i, question in enumerate(questions, 1):
            markdown += f"""## {i}. {question['question']}

*{question['context']}*

"""
            
            if question.get('suggested_answers'):
                markdown += "**Opciones sugeridas:**\n"
                for answer in question['suggested_answers']:
                    markdown += f"- {answer}\n"
                markdown += "\n"
        
        markdown += """---
*Una vez que me proporciones esta información, podré generar una respuesta conceptual y un plan de acción específico para tu situación.*
"""
        
        return markdown
    
    @staticmethod
    def _format_sources(sources: List[str]) -> str:
        """
        Formatea la lista de fuentes
        """
        
        if not sources:
            return "*No se encontraron fuentes específicas para esta respuesta.*"
        
        formatted = ""
        for source in sources:
            formatted += f"- 📄 `{source}`\n"
        
        return formatted
    
    @staticmethod
    def format_error_response(error_message: str, error_code: str = None) -> str:
        """
        Formatea un mensaje de error en Markdown
        """
        
        markdown = f"""# ⚠️ Error en el Procesamiento

Lo siento, he encontrado un problema al procesar tu consulta:

**Error:** {error_message}
"""
        
        if error_code:
            markdown += f"**Código:** `{error_code}`\n"
        
        markdown += """
## 🔄 Qué puedes hacer:

1. **Reformula tu pregunta** - Intenta ser más específico
2. **Verifica la conexión** - Asegúrate de que el sistema esté funcionando
3. **Contacta soporte** - Si el problema persiste

---
*Erasmo Estratégico Verbal - Sistema de IA Conversacional*
"""
        
        return markdown
