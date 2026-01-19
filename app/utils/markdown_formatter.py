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
        
        markdown = f"""# [BRAIN] Analisis Conceptual

{content}

## [KNOWLEDGE] Fuentes de Conocimiento

{MarkdownFormatter._format_sources(sources)}

## [STATS] Nivel de Confianza

**Confianza:** {confidence:.1%}

---
*Generado por Erasmo Estrategico Verbal*
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
            "alta": "[IMPORTANT]",
            "media": "[y]", 
            "baja": "[g]"
        }
        
        markdown = f"""# [ACTION] Plan de Accion

{content}

## [CLIPBOARD] Informacion del Plan

**Prioridad:** {priority_emoji.get(priority, "[o]")} {priority.title()}
"""
        
        if timeline:
            markdown += f"**Timeline:** {timeline}\n"
        
        markdown += """
---
*Generado por Erasmo Estrategico Verbal*
"""
        
        return markdown
    
    @staticmethod
    def format_clarification_questions(questions: List[Dict[str, Any]]) -> str:
        """
        Formatea preguntas de clarificacion en Markdown
        """
        
        markdown = """# [QUERY] Necesito Mas Informacion

Para darte la mejor respuesta estrategica, necesito que me ayudes con algunas clarificaciones:

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
*Una vez que me proporciones esta informacion, podre generar una respuesta conceptual y un plan de accion especifico para tu situacion.*
"""
        
        return markdown
    
    @staticmethod
    def _format_sources(sources: List[str]) -> str:
        """
        Formatea la lista de fuentes
        """
        
        if not sources:
            return "*No se encontraron fuentes especificas para esta respuesta.*"
        
        formatted = ""
        for source in sources:
            formatted += f"- [DOC] `{source}`\n"
        
        return formatted
    
    @staticmethod
    def format_error_response(error_message: str, error_code: str = None) -> str:
        """
        Formatea un mensaje de error en Markdown
        """
        
        markdown = f"""# [WARN] Error en el Procesamiento

Lo siento, he encontrado un problema al procesar tu consulta:

**Error:** {error_message}
"""
        
        if error_code:
            markdown += f"**Codigo:** `{error_code}`\n"
        
        markdown += """
## [REFRESH] Que puedes hacer:

1. **Reformula tu pregunta** - Intenta ser mas especifico
2. **Verifica la conexion** - Asegurate de que el sistema este funcionando
3. **Contacta soporte** - Si el problema persiste

---
*Erasmo Estrategico Verbal - Sistema de IA Conversacional*
"""
        
        return markdown
