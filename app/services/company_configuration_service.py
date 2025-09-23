"""
Servicio para configuración avanzada de compañías
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.services.company_service import CompanyService, CompanyDocumentService
from app.services.ai_configuration_service import AIConfigurationService
from app.models.schemas import DocumentCategory, AIConfigurationCreate
from app.models.company import Company, CompanyDocument, AIConfiguration
import json

class CompanyConfigurationService:
    """Servicio para configuración avanzada y gestión integral de compañías"""
    
    @staticmethod
    def get_full_configuration(db: Session, company_id: int) -> Optional[Dict[str, Any]]:
        """Obtener configuración completa de una compañía"""
        company = CompanyService.get_company_by_id(db, company_id)
        if not company:
            return None
        
        # Obtener documentos por categoría
        knowledge_docs = CompanyDocumentService.get_company_documents(
            db, company_id, DocumentCategory.KNOWLEDGE_BASE
        )
        instruction_docs = CompanyDocumentService.get_company_documents(
            db, company_id, DocumentCategory.INSTRUCTIONS
        )
        
        # Obtener configuración de IA
        ai_config = AIConfigurationService.get_by_company_id(db, company_id)
        
        # Obtener estadísticas de procesamiento
        processing_summary = CompanyDocumentService.get_processing_summary(db, company_id)
        
        return {
            "company": {
                "id": company.id,
                "name": company.name,
                "industry": company.industry,
                "sector": company.sector,
                "description": company.description,
                "is_active": company.is_active,
                "created_at": company.created_at
            },
            "documents": {
                "knowledge_base": {
                    "count": len(knowledge_docs),
                    "documents": [
                        {
                            "id": doc.id,
                            "filename": doc.filename,
                            "priority": doc.priority,
                            "processing_status": doc.processing_status,
                            "description": doc.description,
                            "uploaded_at": doc.uploaded_at
                        } for doc in knowledge_docs
                    ]
                },
                "instructions": {
                    "count": len(instruction_docs),
                    "documents": [
                        {
                            "id": doc.id,
                            "filename": doc.filename,
                            "priority": doc.priority,
                            "processing_status": doc.processing_status,
                            "description": doc.description,
                            "uploaded_at": doc.uploaded_at
                        } for doc in instruction_docs
                    ]
                }
            },
            "ai_configuration": {
                "configured": ai_config is not None,
                "model_name": ai_config.model_name if ai_config else None,
                "response_style": ai_config.response_style if ai_config else None,
                "instruction_priority": ai_config.instruction_priority if ai_config else None,
                "knowledge_base_priority": ai_config.knowledge_base_priority if ai_config else None,
                "fallback_to_general": ai_config.fallback_to_general if ai_config else None
            },
            "processing_summary": processing_summary,
            "setup_status": CompanyConfigurationService._calculate_setup_status(
                company, knowledge_docs, instruction_docs, ai_config
            )
        }
    
    @staticmethod
    async def initialize_ai_configuration(db: Session, company_id: int) -> Dict[str, Any]:
        """Inicializar configuración de IA con valores por defecto inteligentes"""
        company = CompanyService.get_company_by_id(db, company_id)
        if not company:
            return {"success": False, "error": "Compañía no encontrada"}
        
        # Verificar si ya existe configuración
        existing_config = AIConfigurationService.get_by_company_id(db, company_id)
        if existing_config:
            return {"success": False, "error": "Configuración de IA ya existe"}
        
        # Crear configuración por defecto basada en la industria
        default_config = CompanyConfigurationService._generate_default_ai_config(company)
        
        try:
            ai_config = AIConfigurationService.create_configuration(db, default_config)
            return {
                "success": True,
                "message": "Configuración de IA inicializada exitosamente",
                "ai_configuration_id": ai_config.id
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _generate_default_ai_config(company: Company) -> AIConfigurationCreate:
        """Generar configuración de IA por defecto basada en la industria"""
        industry_configs = {
            "tecnología": {
                "response_style": "technical",
                "temperature": "0.7",
                "methodology_prompt": "Eres un consultor estratégico especializado en tecnología y software. Proporciona análisis técnicos profundos y recomendaciones basadas en mejores prácticas de la industria tech."
            },
            "marketing": {
                "response_style": "creative",
                "temperature": "0.8",
                "methodology_prompt": "Eres un estratega de marketing digital experto. Enfócate en estrategias de crecimiento, branding y optimización de conversiones."
            },
            "finanzas": {
                "response_style": "analytical",
                "temperature": "0.6",
                "methodology_prompt": "Eres un consultor financiero estratégico. Proporciona análisis rigurosos basados en datos y métricas financieras."
            },
            "salud": {
                "response_style": "professional",
                "temperature": "0.6",
                "methodology_prompt": "Eres un consultor estratégico especializado en el sector salud. Considera regulaciones, ética y impacto social en tus recomendaciones."
            }
        }
        
        industry_key = company.industry.lower()
        config = industry_configs.get(industry_key, industry_configs["tecnología"])
        
        return AIConfigurationCreate(
            company_id=company.id,
            methodology_prompt=config["methodology_prompt"],
            response_style=config["response_style"],
            model_name="gpt-4",
            temperature=config["temperature"],
            max_tokens=2000,
            instruction_priority="high",
            knowledge_base_priority="high",
            fallback_to_general=True
        )
    
    @staticmethod
    def get_ai_effectiveness_metrics(db: Session, company_id: int) -> Dict[str, Any]:
        """Obtener métricas de efectividad de la IA"""
        # Aquí implementarías lógica para calcular métricas reales
        # Por ahora, retornamos métricas de ejemplo
        
        ai_config = AIConfigurationService.get_by_company_id(db, company_id)
        if not ai_config:
            return {"error": "No hay configuración de IA"}
        
        # Métricas simuladas - en producción vendrían de logs y analytics
        return {
            "response_quality": {
                "average_confidence": 0.85,
                "source_utilization": 0.92,
                "instruction_compliance": 0.88
            },
            "usage_statistics": {
                "total_queries": 156,
                "successful_responses": 148,
                "clarification_requests": 8,
                "average_response_time": 2.3
            },
            "knowledge_base_effectiveness": {
                "knowledge_docs_used": 12,
                "instruction_docs_used": 5,
                "fallback_to_general": 15
            },
            "user_satisfaction": {
                "positive_feedback": 0.91,
                "completion_rate": 0.94,
                "return_users": 0.78
            }
        }
    
    @staticmethod
    async def optimize_configuration(
        db: Session, 
        company_id: int, 
        optimization_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimizar configuración basada en métricas de uso"""
        ai_config = AIConfigurationService.get_by_company_id(db, company_id)
        if not ai_config:
            return {"success": False, "error": "No hay configuración de IA"}
        
        # Analizar datos de optimización y sugerir cambios
        suggestions = CompanyConfigurationService._analyze_optimization_data(optimization_data)
        
        # Aplicar optimizaciones automáticas si están habilitadas
        if optimization_data.get("auto_apply", False):
            from app.models.schemas import AIConfigurationUpdate
            
            update_data = AIConfigurationUpdate()
            
            # Ajustar temperatura basada en feedback
            if suggestions.get("adjust_temperature"):
                new_temp = suggestions["adjust_temperature"]
                update_data.temperature = str(new_temp)
            
            # Ajustar prioridades basada en uso
            if suggestions.get("adjust_priorities"):
                priorities = suggestions["adjust_priorities"]
                update_data.instruction_priority = priorities.get("instruction_priority")
                update_data.knowledge_base_priority = priorities.get("knowledge_base_priority")
            
            try:
                updated_config = AIConfigurationService.update_configuration(
                    db, company_id, update_data
                )
                return {
                    "success": True,
                    "message": "Configuración optimizada automáticamente",
                    "applied_changes": suggestions,
                    "updated_config": updated_config.id
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {
            "success": True,
            "suggestions": suggestions,
            "message": "Análisis completado. Revisa las sugerencias para optimizar manualmente."
        }
    
    @staticmethod
    def _analyze_optimization_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar datos y generar sugerencias de optimización"""
        suggestions = {}
        
        # Analizar temperatura basada en feedback
        if data.get("response_feedback"):
            feedback = data["response_feedback"]
            if feedback.get("too_creative", 0) > 0.3:
                suggestions["adjust_temperature"] = 0.6
            elif feedback.get("too_rigid", 0) > 0.3:
                suggestions["adjust_temperature"] = 0.8
        
        # Analizar uso de fuentes
        if data.get("source_usage"):
            usage = data["source_usage"]
            if usage.get("knowledge_base_low", False):
                suggestions["adjust_priorities"] = {
                    "knowledge_base_priority": "very_high",
                    "instruction_priority": "high"
                }
        
        # Sugerir mejoras en documentación
        if data.get("clarification_rate", 0) > 0.2:
            suggestions["improve_documentation"] = {
                "add_more_instructions": True,
                "clarify_knowledge_base": True
            }
        
        return suggestions
    
    @staticmethod
    def get_document_categories_status(db: Session, company_id: int) -> Dict[str, Any]:
        """Obtener estado detallado de documentos por categoría"""
        knowledge_docs = CompanyDocumentService.get_company_documents(
            db, company_id, DocumentCategory.KNOWLEDGE_BASE
        )
        instruction_docs = CompanyDocumentService.get_company_documents(
            db, company_id, DocumentCategory.INSTRUCTIONS
        )
        
        def analyze_category(docs):
            return {
                "total": len(docs),
                "processed": len([d for d in docs if d.processing_status == "completed"]),
                "pending": len([d for d in docs if d.processing_status == "pending"]),
                "failed": len([d for d in docs if d.processing_status == "failed"]),
                "priority_distribution": {
                    f"priority_{i}": len([d for d in docs if d.priority == i])
                    for i in range(1, 6)
                }
            }
        
        return {
            "knowledge_base": analyze_category(knowledge_docs),
            "instructions": analyze_category(instruction_docs),
            "recommendations": CompanyConfigurationService._generate_document_recommendations(
                knowledge_docs, instruction_docs
            )
        }
    
    @staticmethod
    def _generate_document_recommendations(
        knowledge_docs: List[CompanyDocument], 
        instruction_docs: List[CompanyDocument]
    ) -> List[str]:
        """Generar recomendaciones basadas en el estado de los documentos"""
        recommendations = []
        
        if len(knowledge_docs) < 3:
            recommendations.append("Considera agregar más documentos de fuentes de conocimiento para mejorar la precisión de las respuestas.")
        
        if len(instruction_docs) < 2:
            recommendations.append("Agrega documentos de instrucciones específicas para personalizar mejor el comportamiento de la IA.")
        
        failed_docs = [d for d in knowledge_docs + instruction_docs if d.processing_status == "failed"]
        if failed_docs:
            recommendations.append(f"Hay {len(failed_docs)} documentos que fallaron en el procesamiento. Revisa y vuelve a cargar.")
        
        high_priority_docs = [d for d in knowledge_docs + instruction_docs if d.priority <= 2]
        if len(high_priority_docs) < 2:
            recommendations.append("Asigna prioridad alta (1-2) a los documentos más importantes para mejorar la relevancia.")
        
        return recommendations
    
    @staticmethod
    def validate_company_setup(db: Session, company_id: int) -> Dict[str, Any]:
        """Validar que la configuración de la compañía esté completa"""
        company = CompanyService.get_company_by_id(db, company_id)
        if not company:
            return {"valid": False, "error": "Compañía no encontrada"}
        
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "score": 0,
            "max_score": 100
        }
        
        # Validar información básica de la compañía
        if not company.description:
            validation_results["warnings"].append("Falta descripción de la compañía")
        else:
            validation_results["score"] += 10
        
        # Validar documentos de conocimiento
        knowledge_docs = CompanyDocumentService.get_company_documents(
            db, company_id, DocumentCategory.KNOWLEDGE_BASE
        )
        if len(knowledge_docs) == 0:
            validation_results["issues"].append("No hay documentos de fuentes de conocimiento")
            validation_results["valid"] = False
        elif len(knowledge_docs) < 3:
            validation_results["warnings"].append("Se recomienda tener al menos 3 documentos de conocimiento")
            validation_results["score"] += 15
        else:
            validation_results["score"] += 25
        
        # Validar documentos de instrucciones
        instruction_docs = CompanyDocumentService.get_company_documents(
            db, company_id, DocumentCategory.INSTRUCTIONS
        )
        if len(instruction_docs) == 0:
            validation_results["issues"].append("No hay documentos de instrucciones")
            validation_results["valid"] = False
        else:
            validation_results["score"] += 20
        
        # Validar configuración de IA
        ai_config = AIConfigurationService.get_by_company_id(db, company_id)
        if not ai_config:
            validation_results["issues"].append("No hay configuración de IA")
            validation_results["valid"] = False
        else:
            validation_results["score"] += 25
            
            if not ai_config.methodology_prompt:
                validation_results["warnings"].append("Falta prompt de metodología personalizada")
            else:
                validation_results["score"] += 10
        
        # Validar procesamiento de documentos
        processed_docs = [d for d in knowledge_docs + instruction_docs if d.processing_status == "completed"]
        total_docs = len(knowledge_docs + instruction_docs)
        
        if total_docs > 0:
            processing_rate = len(processed_docs) / total_docs
            if processing_rate < 0.8:
                validation_results["warnings"].append(f"Solo {processing_rate:.0%} de los documentos están procesados")
            else:
                validation_results["score"] += 10
        
        return validation_results
    
    @staticmethod
    def _calculate_setup_status(
        company: Company,
        knowledge_docs: List[CompanyDocument],
        instruction_docs: List[CompanyDocument],
        ai_config: Optional[AIConfiguration]
    ) -> Dict[str, Any]:
        """Calcular estado general de configuración"""
        total_steps = 4
        completed_steps = 0
        
        # Paso 1: Información básica de la compañía
        if company.description:
            completed_steps += 1
        
        # Paso 2: Documentos de conocimiento
        if len(knowledge_docs) > 0:
            completed_steps += 1
        
        # Paso 3: Documentos de instrucciones
        if len(instruction_docs) > 0:
            completed_steps += 1
        
        # Paso 4: Configuración de IA
        if ai_config:
            completed_steps += 1
        
        completion_percentage = (completed_steps / total_steps) * 100
        
        if completion_percentage == 100:
            status = "complete"
        elif completion_percentage >= 75:
            status = "almost_complete"
        elif completion_percentage >= 50:
            status = "in_progress"
        else:
            status = "incomplete"
        
        return {
            "status": status,
            "completion_percentage": completion_percentage,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "next_steps": CompanyConfigurationService._get_next_steps(
                company, knowledge_docs, instruction_docs, ai_config
            )
        }
    
    @staticmethod
    def _get_next_steps(
        company: Company,
        knowledge_docs: List[CompanyDocument],
        instruction_docs: List[CompanyDocument],
        ai_config: Optional[AIConfiguration]
    ) -> List[str]:
        """Obtener próximos pasos recomendados"""
        next_steps = []
        
        if not company.description:
            next_steps.append("Agregar descripción detallada de la compañía")
        
        if len(knowledge_docs) == 0:
            next_steps.append("Cargar documentos de fuentes de conocimiento (.txt)")
        
        if len(instruction_docs) == 0:
            next_steps.append("Cargar documentos de instrucciones específicas (.txt)")
        
        if not ai_config:
            next_steps.append("Configurar parámetros de IA personalizada")
        
        if len(knowledge_docs) > 0 and len(instruction_docs) > 0 and ai_config:
            next_steps.append("Procesar documentos pendientes")
            next_steps.append("Probar configuración de IA")
        
        return next_steps
    
    @staticmethod
    def get_client_view_configuration(db: Session, company_id: int) -> Dict[str, Any]:
        """Obtener vista de configuración para clientes (información limitada)"""
        company = CompanyService.get_company_by_id(db, company_id)
        if not company:
            return {"error": "Compañía no encontrada"}
        
        ai_config = AIConfigurationService.get_by_company_id(db, company_id)
        processing_summary = CompanyDocumentService.get_processing_summary(db, company_id)
        
        return {
            "company_name": company.name,
            "industry": company.industry,
            "ai_configured": ai_config is not None,
            "ai_style": ai_config.response_style if ai_config else None,
            "knowledge_base_status": {
                "total_documents": processing_summary.get("by_category", {}).get("knowledge_base", 0),
                "processed_documents": processing_summary.get("by_status", {}).get("completed", 0)
            },
            "last_updated": ai_config.updated_at if ai_config else company.created_at
        }
    
    @staticmethod
    def get_ai_status_for_client(db: Session, company_id: int) -> Dict[str, Any]:
        """Obtener estado de IA para vista de cliente"""
        ai_config = AIConfigurationService.get_by_company_id(db, company_id)
        
        if not ai_config:
            return {
                "status": "not_configured",
                "message": "La IA aún no ha sido configurada para tu empresa"
            }
        
        processing_summary = CompanyDocumentService.get_processing_summary(db, company_id)
        total_docs = processing_summary.get("total_documents", 0)
        completed_docs = processing_summary.get("by_status", {}).get("completed", 0)
        
        if total_docs == 0:
            return {
                "status": "no_documents",
                "message": "No hay documentos cargados para personalizar tu IA"
            }
        
        if completed_docs < total_docs:
            return {
                "status": "processing",
                "message": f"Procesando documentos ({completed_docs}/{total_docs} completados)",
                "progress": (completed_docs / total_docs) * 100
            }
        
        return {
            "status": "ready",
            "message": "Tu IA personalizada está lista y configurada",
            "features": {
                "custom_knowledge": True,
                "specific_instructions": True,
                "personalized_responses": True
            }
        }
