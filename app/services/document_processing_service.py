"""
Servicio para procesamiento inteligente de documentos
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.services.company_service import CompanyDocumentService
from app.models.schemas import DocumentCategory
import re
import asyncio

class DocumentProcessingService:
    """Servicio para procesamiento inteligente de documentos por categoría"""
    
    @staticmethod
    async def process_company_documents(db: Session, company_id: int) -> Dict[str, Any]:
        """Procesar todos los documentos pendientes de una compañía"""
        pending_docs = db.query(CompanyDocument).filter(
            CompanyDocument.company_id == company_id,
            CompanyDocument.processing_status == "pending",
            CompanyDocument.is_active == True
        ).all()
        
        results = {
            "processed": [],
            "failed": [],
            "total": len(pending_docs)
        }
        
        for doc in pending_docs:
            try:
                # Actualizar estado a procesando
                CompanyDocumentService.update_processing_status(
                    db, doc.id, "processing"
                )
                
                # Procesar según categoría
                if doc.category == DocumentCategory.KNOWLEDGE_BASE:
                    success = await DocumentProcessingService._process_knowledge_document(db, doc)
                elif doc.category == DocumentCategory.INSTRUCTIONS:
                    success = await DocumentProcessingService._process_instruction_document(db, doc)
                else:
                    success = await DocumentProcessingService._process_general_document(db, doc)
                
                if success:
                    CompanyDocumentService.update_processing_status(
                        db, doc.id, "completed", processed_chunks=1, total_chunks=1
                    )
                    results["processed"].append(doc.filename)
                else:
                    CompanyDocumentService.update_processing_status(
                        db, doc.id, "failed", error_message="Error en procesamiento"
                    )
                    results["failed"].append(doc.filename)
                    
            except Exception as e:
                CompanyDocumentService.update_processing_status(
                    db, doc.id, "failed", error_message=str(e)
                )
                results["failed"].append(doc.filename)
        
        return results
    
    @staticmethod
    async def _process_knowledge_document(db: Session, document) -> bool:
        """Procesar documento de fuentes de conocimiento"""
        try:
            content = CompanyDocumentService.get_document_content(
                db, document.company_id, document.id
            )
            if not content:
                return False
            
            # Aquí implementarías la lógica específica para documentos de conocimiento
            # Por ejemplo: vectorización, indexación, extracción de conceptos clave
            
            # Placeholder para procesamiento específico
            processed_content = DocumentProcessingService._extract_knowledge_concepts(content)
            
            return True
            
        except Exception as e:
            print(f"Error procesando documento de conocimiento {document.filename}: {e}")
            return False
    
    @staticmethod
    async def _process_instruction_document(db: Session, document) -> bool:
        """Procesar documento de instrucciones"""
        try:
            content = CompanyDocumentService.get_document_content(
                db, document.company_id, document.id
            )
            if not content:
                return False
            
            # Aquí implementarías la lógica específica para documentos de instrucciones
            # Por ejemplo: extracción de reglas, validación de formato, estructuración
            
            # Placeholder para procesamiento específico
            processed_instructions = DocumentProcessingService._extract_instructions(content)
            
            return True
            
        except Exception as e:
            print(f"Error procesando documento de instrucciones {document.filename}: {e}")
            return False
    
    @staticmethod
    async def _process_general_document(db: Session, document) -> bool:
        """Procesar documento general"""
        try:
            content = CompanyDocumentService.get_document_content(
                db, document.company_id, document.id
            )
            if not content:
                return False
            
            # Procesamiento básico para documentos generales
            return True
            
        except Exception as e:
            print(f"Error procesando documento general {document.filename}: {e}")
            return False
    
    @staticmethod
    def _extract_knowledge_concepts(content: str) -> Dict[str, Any]:
        """Extraer conceptos clave de documentos de conocimiento"""
        # Implementación placeholder - aquí irían algoritmos de NLP
        concepts = {
            "key_terms": [],
            "definitions": {},
            "relationships": [],
            "categories": []
        }
        
        # Ejemplo básico de extracción de términos
        lines = content.split('\n')
        for line in lines:
            if ':' in line and len(line.split(':')) == 2:
                key, value = line.split(':', 1)
                concepts["definitions"][key.strip()] = value.strip()
        
        return concepts
    
    @staticmethod
    def _extract_instructions(content: str) -> Dict[str, Any]:
        """Extraer instrucciones estructuradas"""
        instructions = {
            "rules": [],
            "procedures": [],
            "conditions": [],
            "priorities": []
        }
        
        # Ejemplo básico de extracción de instrucciones
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('REGLA:') or line.startswith('RULE:'):
                instructions["rules"].append(line)
            elif line.startswith('PROCEDIMIENTO:') or line.startswith('PROCEDURE:'):
                instructions["procedures"].append(line)
            elif line.startswith('SI ') or line.startswith('IF '):
                instructions["conditions"].append(line)
            elif line.startswith('PRIORIDAD:') or line.startswith('PRIORITY:'):
                instructions["priorities"].append(line)
        
        return instructions
    
    @staticmethod
    def get_company_knowledge_summary(db: Session, company_id: int) -> Dict[str, Any]:
        """Obtener resumen del conocimiento procesado de una compañía"""
        knowledge_docs = CompanyDocumentService.get_knowledge_base_documents(db, company_id)
        instruction_docs = CompanyDocumentService.get_instruction_documents(db, company_id)
        
        summary = {
            "knowledge_base": {
                "total_documents": len(knowledge_docs),
                "processed_documents": len([d for d in knowledge_docs if d.processing_status == "completed"]),
                "key_areas": [],
                "priority_distribution": {}
            },
            "instructions": {
                "total_documents": len(instruction_docs),
                "processed_documents": len([d for d in instruction_docs if d.processing_status == "completed"]),
                "rule_count": 0,
                "priority_distribution": {}
            }
        }
        
        # Analizar distribución de prioridades
        for doc in knowledge_docs + instruction_docs:
            category = "knowledge_base" if doc.category == DocumentCategory.KNOWLEDGE_BASE else "instructions"
            priority = f"priority_{doc.priority}"
            if priority not in summary[category]["priority_distribution"]:
                summary[category]["priority_distribution"][priority] = 0
            summary[category]["priority_distribution"][priority] += 1
        
        return summary
