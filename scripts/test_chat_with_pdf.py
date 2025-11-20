import requests
import os
import json
from test_pdf_upload import test_upload_and_analyze

# Configuración
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")  # Updated base URL to include /api/v1
USER_ID = 1

def test_full_flow():
    # 1. Primero subimos y analizamos el archivo
    print("PASO 1: Subir y analizar archivo")
    upload_result = test_upload_and_analyze()
    
    if not upload_result:
        print("❌ Abortando prueba: Falló la carga del archivo")
        return

    file_context = upload_result.get("file_context", "")
    
    # 2. Enviamos el mensaje al chat con el contexto
    print("\nPASO 2: Enviar mensaje al chat con el contexto")
    
    chat_url = f"{API_URL}/query"
    
    # Construimos el mensaje combinando la pregunta del usuario con el contexto del archivo
    user_question = "¿De qué trata este documento?"
    full_message = f"{user_question}\n\n{file_context}"
    
    payload = {
        "user_id": USER_ID,
        "message": full_message,
        "require_analysis": False
    }
    
    try:
        print(f"📡 Enviando pregunta a {chat_url}...")
        response = requests.post(chat_url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ ÉXITO: Respuesta recibida del chat")
            print("-" * 50)
            
            # Extraer la respuesta
            conceptual = data.get("conceptual", {})
            answer = conceptual.get("content", "") if conceptual else ""
            
            print(f"🤖 Respuesta del Asistente:\n{answer}")
            print("-" * 50)
        else:
            print(f"\n❌ ERROR: Código de estado {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ EXCEPCIÓN: {str(e)}")

if __name__ == "__main__":
    test_full_flow()
