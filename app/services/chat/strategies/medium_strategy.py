from typing import AsyncGenerator, Dict, Any, List, Optional
from app.services.chat.strategies.base_strategy import BaseResponseStrategy
from app.services.response_validator_service import ResponseValidatorService
from app.core.config import settings

class MediumResponseStrategy(BaseResponseStrategy):
    """
    Strategy for medium mode: balanced responses.
    Technical configuration only - conversational behavior comes from loaded protocol.
    """

    def __init__(self, conversation_service):
        super().__init__(conversation_service)
        # Validator initialized dynamically or with defaults, but we'll use config in generate_response

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
        
        # Get configuration for medium mode
        # Standard configuration
        max_tokens = 4000
        min_tokens = 0
        
        validator = ResponseValidatorService(min_tokens=min_tokens)

        # Build system prompt using service helper (includes loaded protocol)
        system_prompt = self.conversation_service._build_system_prompt(
            user_company_data, context, attachments, project_id
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
            "max_tokens": max_tokens,
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

        # Validate and Extend if necessary
        is_valid, msg, tokens = validator.validate_response_length(response_content)
        
        if not is_valid and tokens < min_tokens:
            print(f"[WARN] [DEBUG] Medium response too short: {msg}. Extending...")
            yield "\n\n_...continuando para mayor detalle..._\n\n"
            
            extension_prompt = (
                "Continua la respuesta anterior agregando mas detalles relevantes y explicaciones. "
                "Asegurate de cubrir el tema con suficiente profundidad."
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
        min_tokens = 0
        validator = ResponseValidatorService(min_tokens=min_tokens)
        is_valid, _, _ = validator.validate_response_length(response_content)
        return is_valid

