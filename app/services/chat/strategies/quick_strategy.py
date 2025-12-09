from typing import AsyncGenerator, Dict, Any, List, Optional
from app.services.chat.strategies.base_strategy import BaseResponseStrategy
from app.core.config import settings

class QuickResponseStrategy(BaseResponseStrategy):
    """
    Strategy for quick mode: concise responses.
    Technical configuration only - conversational behavior comes from loaded protocol.
    """

    def __init__(self, conversation_service):
        super().__init__(conversation_service)
        # Config used dynamically

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
        
        # Get configuration for quick mode
        mode_config = self.conversation_service._get_response_mode_config("quick")
        max_tokens = mode_config.get("max_completion_tokens", 2000)
        prompt_instruction = mode_config.get("prompt_instruction", "")

        # Build system prompt using service helper (includes loaded protocol)
        system_prompt = self.conversation_service._build_system_prompt(
            user_company_data, context, attachments, project_id
        )
        
        if prompt_instruction:
            system_prompt += f"\n\n{prompt_instruction}"

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

        # Stream Response
        stream = self.conversation_service.openai_client.chat.completions.create(**api_args)
        
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

    def validate_response(self, response_content: str) -> bool:
        # Quick mode doesn't have strict validation
        return True

