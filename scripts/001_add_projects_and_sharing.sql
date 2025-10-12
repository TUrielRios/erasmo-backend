-- Migration: Add projects and sharing functionality
-- Date: 2025-01-07

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    custom_instructions TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add project_id column to conversations table
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL;

-- Create project_shares table for sharing projects
CREATE TABLE IF NOT EXISTS project_shares (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    shared_with_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission VARCHAR(50) DEFAULT 'view',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, shared_with_user_id)
);

-- Create conversation_shares table for sharing individual conversations
CREATE TABLE IF NOT EXISTS conversation_shares (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    shared_with_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission VARCHAR(50) DEFAULT 'view',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(conversation_id, shared_with_user_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_company_id ON projects(company_id);
CREATE INDEX IF NOT EXISTS idx_conversations_project_id ON conversations(project_id);
CREATE INDEX IF NOT EXISTS idx_project_shares_project_id ON project_shares(project_id);
CREATE INDEX IF NOT EXISTS idx_project_shares_user_id ON project_shares(shared_with_user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_shares_conversation_id ON conversation_shares(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversation_shares_user_id ON conversation_shares(shared_with_user_id);

-- Add comments for documentation
COMMENT ON TABLE projects IS 'Projects contain chats, files, and custom instructions';
COMMENT ON TABLE project_shares IS 'Sharing permissions for projects within a company';
COMMENT ON TABLE conversation_shares IS 'Sharing permissions for individual conversations within a company';
COMMENT ON COLUMN conversations.project_id IS 'Optional reference to parent project';
