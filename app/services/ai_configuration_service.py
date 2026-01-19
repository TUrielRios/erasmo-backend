"""
Servicio para gestion de configuraciones de IA
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.models.company import AIConfiguration
from app.models.schemas import AIConfigurationCreate, AIConfigurationUpdate
import json

class AIConfigurationService:
    """Servicio para gestionar configuraciones de IA por compania"""
    
    DEFAULT_max_tokens = 15000  # Safe limit under 16,384 max for gpt-4o-mini
    DEFAULT_TEMPERATURE = 0.85  # Increased for more creative responses
    DEFAULT_TOP_P = 0.95        # For more diverse outputs
    
    @staticmethod
    def create_configuration(db: Session, config_data: AIConfigurationCreate) -> AIConfiguration:
        """Crear nueva configuracion de IA"""
        # Convertir diccionarios a JSON strings
        knowledge_base_json = json.dumps(config_data.knowledge_base) if config_data.knowledge_base else None
        personality_traits_json = json.dumps(config_data.personality_traits) if config_data.personality_traits else None
        
        ai_config = AIConfiguration(
            company_id=config_data.company_id,
            methodology_prompt=config_data.methodology_prompt,
            knowledge_base=knowledge_base_json,
            personality_traits=personality_traits_json,
            response_style=config_data.response_style,
            model_name=config_data.model_name,
            temperature=config_data.temperature if config_data.temperature is not None else AIConfigurationService.DEFAULT_TEMPERATURE,
            max_tokens=config_data.max_tokens if config_data.max_tokens is not None else AIConfigurationService.DEFAULT_max_tokens,
            instruction_priority=config_data.instruction_priority,
            knowledge_base_priority=config_data.knowledge_base_priority,
            fallback_to_general=config_data.fallback_to_general
        )
        
        db.add(ai_config)
        db.commit()
        db.refresh(ai_config)
        return ai_config
    
    @staticmethod
    def get_by_company_id(db: Session, company_id: int) -> Optional[AIConfiguration]:
        """Obtener configuracion de IA por ID de compania"""
        return db.query(AIConfiguration).filter(
            AIConfiguration.company_id == company_id,
            AIConfiguration.is_active == True
        ).first()
    
    @staticmethod
    def update_configuration(db: Session, company_id: int, config_update: AIConfigurationUpdate) -> Optional[AIConfiguration]:
        """Actualizar configuracion de IA"""
        ai_config = AIConfigurationService.get_by_company_id(db, company_id)
        if not ai_config:
            return None
        
        update_data = config_update.dict(exclude_unset=True)
        
        # Convertir diccionarios a JSON strings si estan presentes
        if "knowledge_base" in update_data and update_data["knowledge_base"]:
            update_data["knowledge_base"] = json.dumps(update_data["knowledge_base"])
        if "personality_traits" in update_data and update_data["personality_traits"]:
            update_data["personality_traits"] = json.dumps(update_data["personality_traits"])
        
        for field, value in update_data.items():
            setattr(ai_config, field, value)
        
        db.commit()
        db.refresh(ai_config)
        return ai_config
    
    @staticmethod
    def get_configuration_for_chat(db: Session, company_id: int) -> Optional[Dict[str, Any]]:
        """Obtener configuracion de IA formateada para el chat"""
        ai_config = AIConfigurationService.get_by_company_id(db, company_id)
        if not ai_config:
            return None
        
        # Convertir JSON strings de vuelta a diccionarios
        knowledge_base = json.loads(ai_config.knowledge_base) if ai_config.knowledge_base else {}
        personality_traits = json.loads(ai_config.personality_traits) if ai_config.personality_traits else {}
        
        return {
            "methodology_prompt": ai_config.methodology_prompt,
            "knowledge_base": knowledge_base,
            "personality_traits": personality_traits,
            "response_style": ai_config.response_style,
            "model_name": ai_config.model_name,
            "temperature": float(ai_config.temperature),
            "max_tokens": ai_config.max_tokens,
            "instruction_priority": ai_config.instruction_priority,
            "knowledge_base_priority": ai_config.knowledge_base_priority,
            "fallback_to_general": ai_config.fallback_to_general
        }
