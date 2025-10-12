-- Migration: Add project files table
-- Description: Adds support for file uploads to projects (instructions, knowledge base, references)

-- Create enum types for project files
DO $$ BEGIN
    CREATE TYPE file_category AS ENUM ('instructions', 'knowledge_base', 'reference', 'general');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE file_processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create project_files table
CREATE TABLE IF NOT EXISTS project_files (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    category file_category NOT NULL DEFAULT 'general',
    
    -- Processing status
    processing_status file_processing_status NOT NULL DEFAULT 'pending',
    processed_chunks INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Metadata
    description TEXT,
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_project_files_project_id ON project_files(project_id);
CREATE INDEX IF NOT EXISTS idx_project_files_category ON project_files(category);
CREATE INDEX IF NOT EXISTS idx_project_files_status ON project_files(processing_status);
CREATE INDEX IF NOT EXISTS idx_project_files_active ON project_files(is_active);
CREATE INDEX IF NOT EXISTS idx_project_files_priority ON project_files(priority);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_project_files_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_project_files_updated_at
    BEFORE UPDATE ON project_files
    FOR EACH ROW
    EXECUTE FUNCTION update_project_files_updated_at();

-- Add comments for documentation
COMMENT ON TABLE project_files IS 'Archivos asociados a proyectos (instrucciones, conocimiento, referencias)';
COMMENT ON COLUMN project_files.category IS 'Categoría del archivo: instructions, knowledge_base, reference, general';
COMMENT ON COLUMN project_files.processing_status IS 'Estado de procesamiento del archivo';
COMMENT ON COLUMN project_files.priority IS 'Prioridad del archivo (1=más alta, 10=más baja)';

-- Create storage directory structure (this would be done by the application)
-- documents/projects/project_{id}/

COMMIT;
