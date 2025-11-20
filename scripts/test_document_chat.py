"""
Script para probar el envío de mensajes con documentos adjuntos
"""

import requests
import json
import time
from datetime import datetime

# Configuración del servidor
BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    """Imprime una sección formateada"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def test_document_chat_flow():
    """Prueba el flujo completo de chat con documentos"""
    
    print_section("🧪 PRUEBA: Chat con Documento Adjunto")
    
    # Paso 1: Crear un documento de prueba en memoria
    print("📝 Paso 1: Preparando documento de prueba...")
    document_content = """
    PROPUESTA COMERCIAL 2024
    
    Resumen Ejecutivo:
    Proponemos implementar un sistema de gestión de clientes (CRM) para mejorar 
    las operaciones comerciales de la empresa. El proyecto tiene un costo estimado 
    de $50,000 USD y se completará en 3 meses.
    
    Alcance del Proyecto:
    - Módulo de gestión de contactos
    - Sistema de seguimiento de ventas
    - Dashboard de reportes
    - Integración con herramientas existentes
    
    Beneficios Esperados:
    - Aumento del 30% en eficiencia de ventas
    - Mejor seguimiento de leads
    - Reportes automatizados en tiempo real
    
    Inversión:
    - Fase 1 (Mes 1): $15,000 - Diseño y planificación
    - Fase 2 (Mes 2): $20,000 - Desarrollo e implementación
    - Fase 3 (Mes 3): $15,000 - Pruebas y capacitación
    """
    
    document_summary = """
    Propuesta para implementar un CRM con costo de $50,000 USD en 3 meses. 
    Incluye gestión de contactos, seguimiento de ventas, dashboard de reportes 
    e integraciones. Se espera aumentar la eficiencia de ventas en 30%.
    """
    
    print("✅ Documento de prueba preparado")
    print(f"   - Título: PROPUESTA COMERCIAL 2024")
    print(f"   - Tamaño: {len(document_content)} caracteres")
    
    # Paso 2: Configuración del usuario de prueba
    print_section("👤 Paso 2: Configurando usuario de prueba")
    user_id = 1  # Usuario de prueba (debe existir en la base de datos)
    print(f"✅ Usando user_id: {user_id}")
    print("   ⚠️  Asegúrate de que este usuario exista en tu base de datos")
    
    # Paso 3: Crear una nueva conversación
    print_section("💬 Paso 3: Creando nueva conversación")
    try:
        response = requests.post(
            f"{BASE_URL}/chat/conversations",
            params={"user_id": user_id},
            json={
                "title": "Análisis de propuesta comercial",
                "project_id": None
            }
        )
        response.raise_for_status()
        conversation = response.json()
        session_id = conversation["session_id"]
        
        print(f"✅ Conversación creada exitosamente")
        print(f"   - Session ID: {session_id}")
        print(f"   - Título: {conversation['title']}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creando conversación: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Detalle: {e.response.text}")
        return
    
    # Paso 4: Enviar mensaje con documento adjunto
    print_section("📤 Paso 4: Enviando mensaje con documento adjunto")
    
    query_message = "¿Cuáles son los puntos principales de esta propuesta y cuál es la inversión total requerida?"
    
    attachment = {
        "type": "document",
        "filename": "propuesta_comercial_2024.txt",
        "file_format": "txt",
        "content": document_content,
        "summary": document_summary
    }
    
    print(f"📄 Mensaje: {query_message}")
    print(f"📎 Archivo adjunto: {attachment['filename']}")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/query",
            json={
                "message": query_message,
                "user_id": user_id,
                "session_id": session_id,
                "require_analysis": False,  # Respuesta normal, no análisis estructurado
                "attachments": [attachment]
            }
        )
        response.raise_for_status()
        result = response.json()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\n✅ Respuesta recibida en {processing_time:.2f} segundos")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error enviando mensaje: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Detalle: {e.response.text}")
        return
    
    # Paso 5: Mostrar la respuesta del asistente
    print_section("🤖 Paso 5: Respuesta del Asistente")
    
    print(f"Tipo de respuesta: {result['response_type']}")
    print(f"Modelo usado: {result['model_used']}")
    print(f"Tokens usados: {result['tokens_used']}")
    print(f"Tiempo de procesamiento: {result['processing_time']:.2f}s")
    
    if result.get('conceptual'):
        conceptual = result['conceptual']
        print(f"\n📊 Respuesta Conceptual (Confianza: {conceptual['confidence']*100:.1f}%):")
        print("-" * 60)
        print(conceptual['content'])
        
        if conceptual.get('sources'):
            print(f"\n📚 Fuentes: {', '.join(conceptual['sources'])}")
    
    if result.get('accional'):
        accional = result['accional']
        print(f"\n⚡ Plan de Acción (Prioridad: {accional['priority']}):")
        print("-" * 60)
        print(accional['content'])
        
        if accional.get('timeline'):
            print(f"\n⏱️  Timeline: {accional['timeline']}")
    
    # Paso 6: Verificar que el documento se procesó correctamente
    print_section("✅ Paso 6: Verificación de resultados")
    
    # Verificar si la respuesta menciona elementos clave del documento
    response_content = result.get('conceptual', {}).get('content', '').lower()
    
    keywords = {
        "crm": "CRM" in document_content,
        "50,000 o 50000": "50,000" in document_content or "50000" in response_content,
        "3 meses": "3 meses" in document_content,
        "eficiencia de ventas": "eficiencia de ventas" in document_content.lower()
    }
    
    print("🔍 Verificando que la IA leyó el documento correctamente:")
    for keyword, in_doc in keywords.items():
        in_response = keyword.replace(" o ", " ") in response_content or keyword.split(" o ")[-1] in response_content
        status = "✅" if in_response and in_doc else "⚠️"
        print(f"   {status} '{keyword}': En doc={in_doc}, En respuesta={in_response}")
    
    # Paso 7: Enviar un segundo mensaje de seguimiento
    print_section("📤 Paso 7: Enviando mensaje de seguimiento")
    
    followup_message = "¿Cuánto cuesta la fase 2 del proyecto?"
    print(f"📝 Mensaje: {followup_message}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/query",
            json={
                "message": followup_message,
                "user_id": user_id,
                "session_id": session_id,
                "require_analysis": False
                # Sin attachments - debería recordar el documento anterior
            }
        )
        response.raise_for_status()
        followup_result = response.json()
        
        print("\n✅ Respuesta de seguimiento recibida:")
        if followup_result.get('conceptual'):
            print("-" * 60)
            print(followup_result['conceptual']['content'])
        
        # Verificar si menciona $20,000 (costo de fase 2)
        followup_content = followup_result.get('conceptual', {}).get('content', '')
        if "20,000" in followup_content or "20000" in followup_content:
            print("\n✅ La IA recordó correctamente el documento del contexto anterior!")
        else:
            print("\n⚠️  La IA no mencionó el costo específico de la fase 2 ($20,000)")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en mensaje de seguimiento: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Detalle: {e.response.text}")
    
    # Paso 8: Obtener historial completo de la conversación
    print_section("📜 Paso 8: Historial de conversación")
    
    try:
        response = requests.get(
            f"{BASE_URL}/query/sessions/{session_id}",
            params={"user_id": user_id}
        )
        response.raise_for_status()
        history = response.json()
        
        print(f"📊 Conversación: {history['title']}")
        print(f"📝 Total de mensajes: {history['message_count']}")
        print(f"🕐 Creada: {history['created_at']}")
        
        print("\n💬 Mensajes:")
        for i, msg in enumerate(history['messages'], 1):
            role_emoji = "👤" if msg['role'] == 'user' else "🤖"
            print(f"\n{i}. {role_emoji} {msg['role'].upper()} ({msg['timestamp']}):")
            print(f"   {msg['content'][:150]}{'...' if len(msg['content']) > 150 else ''}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error obteniendo historial: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Detalle: {e.response.text}")
    
    print_section("🎉 PRUEBA COMPLETADA")
    print(f"Session ID para referencia: {session_id}")
    print(f"Timestamp: {datetime.now()}")
    
    return session_id

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  🧪 TEST: Chat con Documentos Adjuntos                  ║
    ║                                                          ║
    ║  Este script prueba el flujo completo de:               ║
    ║  1. Crear una conversación                              ║
    ║  2. Enviar un mensaje con un documento adjunto          ║
    ║  3. Verificar que la IA lee el documento correctamente  ║
    ║  4. Enviar un mensaje de seguimiento                    ║
    ║  5. Verificar el contexto conversacional                ║
    ║                                                          ║
    ║  ⚠️  REQUISITOS:                                         ║
    ║  - Servidor corriendo en http://localhost:8000          ║
    ║  - Usuario con ID=1 existente en la base de datos       ║
    ║  - API Key de OpenAI configurada                        ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        session_id = test_document_chat_flow()
        print(f"\n✅ Prueba exitosa! Session ID: {session_id}")
    except KeyboardInterrupt:
        print("\n\n⚠️  Prueba cancelada por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
