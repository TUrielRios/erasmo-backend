-- Migración para agregar columnas faltantes a la tabla messages
-- Ejecutar este script en tu base de datos PostgreSQL

-- Agregar columna updated_at
ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;

-- Agregar columna is_edited
ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS is_edited BOOLEAN DEFAULT FALSE NOT NULL;

-- Agregar columna message_metadata
ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS message_metadata TEXT;

-- Actualizar updated_at para registros existentes (usar timestamp como valor inicial)
UPDATE messages 
SET updated_at = timestamp 
WHERE updated_at IS NULL;

-- Crear índice en updated_at para mejorar rendimiento de consultas
CREATE INDEX IF NOT EXISTS idx_messages_updated_at ON messages(updated_at);

-- Verificar que las columnas se agregaron correctamente
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'messages' 
AND column_name IN ('updated_at', 'is_edited', 'message_metadata');
