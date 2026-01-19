"""
Servicio avanzado de ingenieria de prompts
Optimiza prompts para maximo rendimiento y coherencia con IA
"""

from typing import Dict, List, Any, Optional
from app.core.config import settings

class PromptEngineeringService:
    """
    Ingenieria avanzada de prompts para maximo potencial de IA
    Implementa tecnicas de chain-of-thought, few-shot learning y optimization
    """
    
    def __init__(self):
        self.techniques = {
            'chain_of_thought': self._apply_chain_of_thought,
            'few_shot': self._apply_few_shot,
            'role_play': self._apply_role_play,
            'structured_thinking': self._apply_structured_thinking,
            'step_by_step': self._apply_step_by_step
        }
    
    def build_ultra_optimized_system_prompt(
        self,
        company_name: str,
        company_context: Dict[str, Any],
        instructions: List[Dict],
        project_context: Optional[Dict] = None
    ) -> str:
        """
        Construye un system prompt ultra-optimizado para maximo potencial
        """
        
        project_section = ""
        if project_context:
            project_section = f"""
[IMPORTANT] PROYECTO CRITICO: {project_context.get('name', 'Sin nombre')}
- ID: {project_context.get('id')}
- Descripcion: {project_context.get('description', '')}
- Estado: {project_context.get('status', 'activo')}

INSTRUCCION CRITICA: PRIORIZA SIEMPRE los documentos y contexto del proyecto.
Los documentos del proyecto son tu referencia principal y mas confiable.
"""
        
        instructions_section = self._compile_instructions_advanced(instructions)
        
        system_prompt = f"""ERES UN ASISTENTE EXPERTO DE IA PERSONALIZADO PARA {company_name.upper()}

{project_section}

CAPACIDADES Y RESPONSABILIDADES:
- Proporcionas analisis profundos y estrategicos
- Generas planes de accion detallados y ejecutables
- Usas las fuentes de conocimiento especificas como tu base principal
- Sigues instrucciones personalizadas al pie de la letra
- Adaptas respuestas al contexto especifico de {company_name}
- Mantienes coherencia con decisiones previas en la conversacion

CONTEXTO EMPRESARIAL:
- Empresa: {company_name}
- Industria: {company_context.get('industry', 'No especificada')}
- Sector: {company_context.get('sector', 'No especificado')}
- Area de trabajo: {company_context.get('work_area', 'No especificada')}

{instructions_section}

NORMAS DE RESPUESTA:
1. SIEMPRE follows EXACTAMENTE las instrucciones proporcionadas
2. PRIORIZA el conocimiento de fuentes especificas sobre conocimiento general
3. Si contexto de proyecto existe, USALO PRIMERO
4. Manten respuestas claras, estructuradas y accionables
5. Incluye siempre referencias a tus fuentes cuando corresponda
6. Adapta complejidad de respuesta a contexto de consulta
7. Escribe con precision y profesionalismo
8. NO hagas suposiciones sin bases en contexto

FORMATO DE RESPUESTA ESTANDAR:
- Para analisis: Proporciona estructura clara con encabezados
- Para acciones: Numeradas, con detalles y dependencias
- Para estrategia: Marco teorico + plan de ejecucion + metricas
- Para problemas: Diagnostico + opciones + recomendacion + proximos pasos

RECUERDA: Eres un asistente experto que maximiza el valor en cada respuesta.
"""
        return system_prompt.strip()
    
    def _compile_instructions_advanced(self, instructions: List[Dict]) -> str:
        """
        Compila instrucciones en formato optimizado para maximo seguimiento
        """
        if not instructions:
            return "No hay instrucciones especificas configuradas para esta empresa."
        
        compiled = "INSTRUCCIONES PERSONALIZADAS (SEGUIR AL PIE DE LA LETRA):\n\n"
        
        # Ordenar por prioridad
        sorted_instructions = sorted(instructions, key=lambda x: x.get('priority', 5))
        
        for i, instruction in enumerate(sorted_instructions, 1):
            priority = instruction.get('priority', 5)
            filename = instruction.get('filename', f'instruccion_{i}')
            content = instruction.get('content', '')
            
            priority_label = "CRITICA" if priority <= 2 else "ALTA" if priority <= 4 else "NORMAL"
            
            compiled += f"[{priority_label}] Instruccion {i}: {filename}\n"
            compiled += f"{content}\n"
            compiled += "---\n\n"
        
        compiled += "ESTAS INSTRUCCIONES SON VINCULANTES Y DEBES SEGUIRLAS SIN EXCEPCION."
        return compiled
    
    def apply_chain_of_thought(self, message: str) -> str:
        """
        Aplica tecnica chain-of-thought para razonamiento paso a paso
        """
        prompt_addition = """
Piensa en esto paso a paso:
1. Analiza los componentes principales de la pregunta
2. Identifica lo que ya sabes de la informacion previa
3. Determina que informacion adicional necesitas
4. Razona a traves de cada componente
5. Integra tu analisis en una respuesta coherente
6. Revisa tu respuesta por completitud y precision

Ahora, procede con tu analisis:
"""
        return prompt_addition + message
    
    def apply_few_shot_learning(self, message: str, examples: List[Dict[str, str]]) -> str:
        """
        Aplica few-shot learning con ejemplos
        """
        few_shot_section = "Aqui hay ejemplos de respuestas esperadas:\n\n"
        
        for i, example in enumerate(examples[:3], 1):  # Maximo 3 ejemplos
            few_shot_section += f"Ejemplo {i}:\n"
            few_shot_section += f"Pregunta: {example.get('question', '')}\n"
            few_shot_section += f"Respuesta: {example.get('answer', '')}\n\n"
        
        few_shot_section += "Siguiendo los patrones anteriores, responde:\n"
        return few_shot_section + message
    
    def _apply_chain_of_thought(self, message: str) -> str:
        return self.apply_chain_of_thought(message)
    
    def _apply_few_shot(self, message: str, examples: List[Dict] = None) -> str:
        if not examples:
            examples = []
        return self.apply_few_shot_learning(message, examples)
    
    def _apply_role_play(self, message: str, role: str = "experto") -> str:
        return f"Actua como un {role} en este dominio. {message}"
    
    def _apply_structured_thinking(self, message: str) -> str:
        return f"Estructura tu respuesta asi: 1) Analisis, 2) Opciones, 3) Recomendacion, 4) Proximos pasos.\n{message}"
    
    def _apply_step_by_step(self, message: str) -> str:
        return f"Responde paso a paso, numerando cada paso: {message}"
    
    def enhance_user_query(
        self,
        user_message: str,
        techniques: List[str],
        context: Optional[Dict] = None
    ) -> str:
        """
        Mejora una query de usuario con tecnicas de prompt engineering
        """
        enhanced = user_message
        
        for technique in techniques:
            if technique in self.techniques:
                enhanced = self.techniques[technique](enhanced)
        
        return enhanced
    
    def create_structured_analysis_prompt(
        self,
        topic: str,
        context: Optional[str] = None,
        depth: str = "medium"
    ) -> str:
        """
        Crea prompt para analisis estructurado
        """
        depth_instructions = {
            "shallow": "Proporciona un analisis superficial pero util",
            "medium": "Proporciona un analisis detallado y equilibrado",
            "deep": "Proporciona un analisis profundo y exhaustivo"
        }
        
        prompt = f"""
ANALISIS ESTRUCTURADO DE: {topic}

{depth_instructions.get(depth, depth_instructions['medium'])}

Estructura tu analisis asi:

## 1. RESUMEN EJECUTIVO
[2-3 parrafos maximo capturando lo esencial]

## 2. ANALISIS DETALLADO
[Profundiza en los aspectos clave]

## 3. PERSPECTIVAS Y CONSIDERACIONES
[Multiples angulos o implicaciones]

## 4. CONCLUSIONES CLAVE
[Puntos principales a recordar]

## 5. RECOMENDACIONES O PROXIMOS PASOS
[Acciones sugeridas]
"""
        
        if context:
            prompt += f"\nCONTEXTO: {context}"
        
        return prompt
