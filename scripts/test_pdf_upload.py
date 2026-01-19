import requests
import os
import sys
import base64

# Configuracion
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
USER_ID = 1

def create_dummy_pdf(filename="test_doc.pdf"):
    """Crea un PDF valido para pruebas"""
    # PDF minimo valido 1.4
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R >>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
        b"endobj\n"
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>\n"
        b"endobj\n"
        b"4 0 obj\n"
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n"
        b"endobj\n"
        b"5 0 obj\n"
        b"<< /Length 223 >>\n"
        b"stream\n"
        b"BT\n"
        b"/F1 12 Tf\n"
        b"72 720 Td\n"
        b"(INFORME DE PROYECTO: IMPLEMENTACION DE IA EN LA EMPRESA) Tj\n"
        b"0 -20 Td\n"
        b"(1. Introduccion) Tj\n"
        b"0 -15 Td\n"
        b"(Este documento detalla el plan estrategico para la implementacion de soluciones de IA.) Tj\n"
        b"0 -15 Td\n"
        b"(El objetivo principal es optimizar los procesos operativos y mejorar la toma de decisiones.) Tj\n"
        b"ET\n"
        b"endstream\n"
        b"endobj\n"
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n"
        b"0000000010 00000 n \n"
        b"0000000060 00000 n \n"
        b"0000000117 00000 n \n"
        b"0000000236 00000 n \n"
        b"0000000304 00000 n \n"
        b"trailer\n"
        b"<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n"
        b"577\n"
        b"%%EOF"
    )
    
    try:
        with open(filename, "wb") as f:
            f.write(pdf_content)
        print(f"[DOC] PDF de prueba creado: {filename}")
        return filename
    except Exception as e:
        print(f"[ERR] Error creando PDF: {e}")
        return None

def test_upload_and_analyze():
    filename = "test_doc.pdf"
    if not create_dummy_pdf(filename):
        return

    print(f"\n[LAUNCH] Iniciando prueba de carga de PDF...")
    
    url = f"{API_URL}/files/analyze-with-message"
    
    try:
        with open(filename, "rb") as f:
            files = {"file": (filename, f, "application/pdf")}
            params = {"user_id": USER_ID}
            
            print(f" Enviando peticion a {url}...")
            response = requests.post(url, files=files, params=params)
            
            if response.status_code == 200:
                data = response.json()
                print("\n[OK] EXITO: Archivo procesado correctamente")
                print("-" * 50)
                print(f" Archivo: {data.get('filename')}")
                print(f"[CLIPBOARD] Tipo: {data.get('file_type')}")
                print(f" Mensaje del sistema: {data.get('message')}")
                print("-" * 50)
                print("Contexto extraido (primeros 200 caracteres):")
                print(data.get('file_context', '')[:200] + "...")
                return data
            else:
                print(f"\n[ERR] ERROR: Codigo de estado {response.status_code}")
                print(response.text)
                return None
                
    except Exception as e:
        print(f"\n[ERR] EXCEPCION: {str(e)}")
        return None

if __name__ == "__main__":
    test_upload_and_analyze()
