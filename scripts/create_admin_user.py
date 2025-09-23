#!/usr/bin/env python3
"""
Script para crear o actualizar un usuario administrador
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.auth_service import AuthService

def create_admin_user():
    """Crear o actualizar usuario administrador"""
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("👤 Configurando usuario administrador...")
        
        # Verificar si existe la compañía Erasmo AI
        cursor.execute("SELECT id FROM companies WHERE name = 'Erasmo AI'")
        company_result = cursor.fetchone()
        
        if not company_result:
            print("🏢 Creando compañía Erasmo AI...")
            cursor.execute("""
                INSERT INTO companies (name, industry, sector, description, is_active)
                VALUES ('Erasmo AI', 'Tecnología', 'Inteligencia Artificial', 'Plataforma de IA conversacional', true)
                RETURNING id
            """)
            company_id = cursor.fetchone()[0]
            print("✅ Compañía Erasmo AI creada")
        else:
            company_id = company_result[0]
            print("✅ Compañía Erasmo AI encontrada")
        
        # Generar hash de contraseña para admin
        admin_password = "admin123"  # Cambiar por una contraseña segura
        hashed_password = AuthService.get_password_hash(admin_password)
        
        # Verificar si ya existe el usuario admin
        cursor.execute("SELECT id, role FROM users WHERE email = 'admin@erasmo.ai'")
        user_result = cursor.fetchone()
        
        if user_result:
            user_id, current_role = user_result
            if current_role != 'admin':
                print("🔄 Actualizando usuario existente a administrador...")
                cursor.execute("""
                    UPDATE users 
                    SET role = 'admin', 
                        company_id = %s, 
                        work_area = 'Administración',
                        hashed_password = %s,
                        is_active = true
                    WHERE id = %s
                """, (company_id, hashed_password, user_id))
                print("✅ Usuario actualizado a administrador")
            else:
                print("✅ Usuario administrador ya existe y está configurado correctamente")
                # Actualizar contraseña por si acaso
                cursor.execute("UPDATE users SET hashed_password = %s WHERE id = %s", (hashed_password, user_id))
                print("🔑 Contraseña actualizada")
        else:
            print("👤 Creando nuevo usuario administrador...")
            cursor.execute("""
                INSERT INTO users (
                    username, email, hashed_password, full_name, 
                    company_id, work_area, role, is_active
                )
                VALUES (
                    'admin', 'admin@erasmo.ai', %s, 'Administrador del Sistema',
                    %s, 'Administración', 'admin', true
                )
            """, (hashed_password, company_id))
            print("✅ Usuario administrador creado")
        
        print("\n🎉 Usuario administrador configurado exitosamente!")
        print("📧 Email: admin@erasmo.ai")
        print("🔑 Contraseña: admin123")
        print("⚠️  IMPORTANTE: Cambia la contraseña después del primer login")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error configurando usuario administrador: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Iniciando configuración de usuario administrador...")
    success = create_admin_user()
    if success:
        print("🎉 Usuario administrador configurado exitosamente!")
        print("💡 Ahora puedes acceder al panel de administración en /admin")
    else:
        print("❌ Error en la configuración del usuario administrador")
        sys.exit(1)
