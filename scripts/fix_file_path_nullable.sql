-- Migración 004b: Hacer file_path nullable para soportar protocolos vinculados
-- Esto permite que los documentos puedan no tener file_path cuando usan protocolos

ALTER TABLE company_documents 
ALTER COLUMN file_path DROP NOT NULL;

-- Agregar comentario para documentar el cambio
COMMENT ON COLUMN company_documents.file_path IS 'Ruta del archivo. NULL cuando use_protocol=true';
