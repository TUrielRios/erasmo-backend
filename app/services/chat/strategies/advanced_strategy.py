from typing import AsyncGenerator, Dict, Any, List, Optional
from app.services.chat.strategies.base_strategy import BaseResponseStrategy
from app.services.response_validator_service import ResponseValidatorService
from app.core.config import settings

class AdvancedResponseStrategy(BaseResponseStrategy):
    """
    Strategy for advanced mode: detailed responses with strict validation.
    Technical configuration only - conversational behavior comes from loaded protocol.
    """

    def __init__(self, conversation_service):
        super().__init__(conversation_service)
        # Validator initialized dynamically

    async def generate_response(
        self,
        message: str,
        session_id: str,
        user_id: int,
        context: List[Dict[str, Any]],
        history: List[Dict[str, Any]],
        key_info: Dict[str, Any],
        project_id: Optional[int],
        attachments: Optional[List[Dict[str, Any]]],
        ai_config: Any,
        user_company_data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        
        # Get configuration for advanced mode
        mode_config = self.conversation_service._get_response_mode_config("advanced")
        max_tokens = mode_config.get("max_completion_tokens", 8000)
        min_tokens = mode_config.get("min_tokens", 1100)
        
        validator = ResponseValidatorService(min_tokens=min_tokens)

        # Build system prompt using service helper (includes loaded protocol)
        system_prompt = self.conversation_service._build_system_prompt(
            user_company_data, context, attachments, project_id
        )
        
        # Add explicit instruction for length and depth
        system_prompt += (
            "\n\nMODO AVANZADO ACTIVO: Tu respuesta DEBE ser extensa, detallada y profunda. "
            "Desarrolla cada punto con ejemplos, contexto y análisis exhaustivo. "
            "El usuario espera una respuesta de AL MENOS 1200 tokens en un solo mensaje. "
            "NO seas conciso. Extiéndete en la explicación."
        )

        # Build user prompt
        user_prompt = self.conversation_service._build_normal_conversation_prompt(
            message, context, history, key_info, project_id, attachments
        )

        # Prepare API Args
        model_name = ai_config.model_name if ai_config else settings.OPENAI_MODEL
        api_args = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": True,
            "max_completion_tokens": max_tokens,
            "temperature": 1
        }

        # Stream Initial Response
        response_content = ""
        stream = self.conversation_service.openai_client.chat.completions.create(**api_args)
        
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    content = delta.content
                    response_content += content
                    yield content

        # Validate and Extend if necessary (advanced mode only)
        # We keep this as a fallback, but the prompt should handle most cases now.
        is_valid, msg, tokens = validator.validate_response_length(response_content)
        
        if not is_valid:
            print(f"⚠️ [DEBUG] Advanced response too short: {msg}. Extending...")
            # We won't print the separator to the user to make it feel more seamless if possible,
            # but since we already yielded the previous content, we can't erase it.
            # We'll just add a newline.
            yield "\n\n" 
            
            extension_prompt = (
                "Profundiza aún más en los puntos anteriores. "
                "Agrega más ejemplos, matices y detalles operativos. "
                "Necesito que la respuesta sea realmente exhaustiva."
            )
            
            messages = api_args["messages"]
            messages.append({"role": "assistant", "content": response_content})
            messages.append({"role": "user", "content": extension_prompt})
            
            api_args["messages"] = messages
            stream_extension = self.conversation_service.openai_client.chat.completions.create(**api_args)
            
            for chunk in stream_extension:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        content = delta.content
                        response_content += content
                        yield content

    def validate_response(self, response_content: str) -> bool:
        mode_config = self.conversation_service._get_response_mode_config("advanced")
        min_tokens = mode_config.get("min_tokens", 1100)
        validator = ResponseValidatorService(min_tokens=min_tokens)
        is_valid, _, _ = validator.validate_response_length(response_content)
        return is_valid

