-- Migration 004: Add protocols table and update company_documents
-- Adds support for centralized protocol management

-- Create protocols table
CREATE TABLE IF NOT EXISTS protocols (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    content TEXT NOT NULL,
    version VARCHAR(50) NOT NULL DEFAULT 'v1',
    category VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_user_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create index on name for faster lookups
CREATE INDEX IF NOT EXISTS idx_protocols_name ON protocols(name);
CREATE INDEX IF NOT EXISTS idx_protocols_category ON protocols(category);
CREATE INDEX IF NOT EXISTS idx_protocols_is_active ON protocols(is_active);

-- Add protocol support columns to company_documents
ALTER TABLE company_documents 
    ADD COLUMN IF NOT EXISTS protocol_id INTEGER REFERENCES protocols(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS use_protocol BOOLEAN NOT NULL DEFAULT FALSE;

-- Create index on protocol_id for faster joins
CREATE INDEX IF NOT EXISTS idx_company_documents_protocol_id ON company_documents(protocol_id);

-- Verification queries
SELECT 'protocols table created' AS status, COUNT(*) AS count FROM protocols;
SELECT 'company_documents columns added' AS status, 
       column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'company_documents' 
  AND column_name IN ('protocol_id', 'use_protocol');
