-- Add category column to company_documents table
ALTER TABLE company_documents 
ADD COLUMN category VARCHAR(50) NOT NULL DEFAULT 'knowledge_base';

-- Update existing records to have a default category
UPDATE company_documents 
SET category = 'knowledge_base' 
WHERE category IS NULL;
