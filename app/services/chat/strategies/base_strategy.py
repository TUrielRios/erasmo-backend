from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.orm import Session

class BaseResponseStrategy(ABC):
    """
    Abstract base class for response generation strategies.
    Each mode (advanced, medium, quick) will implement this interface.
    """

    def __init__(self, conversation_service):
        self.conversation_service = conversation_service

    @abstractmethod
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
        """
        Generates a streaming response based on the strategy's logic.
        """
        pass

    @abstractmethod
    def validate_response(self, response_content: str) -> bool:
        """
        Validates the response content according to the strategy's rules.
        """
        pass
