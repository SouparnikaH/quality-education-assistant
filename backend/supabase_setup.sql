-- Quality Education Chatbot - Supabase Database Setup
-- Run this SQL in your Supabase SQL Editor

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create conversation_data table
CREATE TABLE IF NOT EXISTS conversation_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT UNIQUE NOT NULL,
    student_name TEXT,
    student_age INTEGER,
    area_of_interest TEXT,
    student_query TEXT,
    guidance_type TEXT,
    collected_at TIMESTAMP DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_conversation_data_session_id ON conversation_data(session_id);

-- Create index on guidance_type for analytics
CREATE INDEX IF NOT EXISTS idx_conversation_data_guidance_type ON conversation_data(guidance_type);

-- Add comments for documentation
COMMENT ON TABLE conversations IS 'Stores conversation session metadata';
COMMENT ON TABLE conversation_data IS 'Stores collected student information and queries';

