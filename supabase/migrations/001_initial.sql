-- ATS Intelligent System - Initial Migration
-- Run this in your Supabase SQL Editor to set up tables, RLS, and storage

-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- CV Documents Table (structured data + embeddings)
-- =============================================================================
CREATE TABLE IF NOT EXISTS cv_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    original_file_path TEXT NOT NULL,
    raw_text TEXT DEFAULT '',
    structured_data JSONB DEFAULT '{}',
    embedding vector(384),
    quality_score FLOAT DEFAULT 0.0,
    status TEXT DEFAULT 'processing' CHECK (status IN ('pending', 'processing', 'active', 'error', 'archived')),
    source_type TEXT DEFAULT 'upload',
    original_filename TEXT,
    mime_type TEXT,
    file_size_bytes BIGINT,
    gdpr_consent BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    processing_error TEXT
);

-- Index for user lookups
CREATE INDEX idx_cv_documents_user_id ON cv_documents(user_id);
CREATE INDEX idx_cv_documents_status ON cv_documents(status);
CREATE INDEX idx_cv_documents_created_at ON cv_documents(created_at DESC);

-- Index for semantic search (pgvector)
-- Note: If this fails (e.g. empty table), add after inserting CVs: lists = sqrt(row_count) or 100
CREATE INDEX IF NOT EXISTS idx_cv_documents_embedding ON cv_documents 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 10);

-- Index for JSONB queries on structured_data
CREATE INDEX idx_cv_documents_structured ON cv_documents USING GIN (structured_data jsonb_path_ops);

-- =============================================================================
-- Row Level Security (RLS) - cv_documents
-- =============================================================================
ALTER TABLE cv_documents ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own CVs
CREATE POLICY "Users can view own CVs"
    ON cv_documents FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own CVs
CREATE POLICY "Users can insert own CVs"
    ON cv_documents FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own CVs
CREATE POLICY "Users can update own CVs"
    ON cv_documents FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Users can delete their own CVs
CREATE POLICY "Users can delete own CVs"
    ON cv_documents FOR DELETE
    USING (auth.uid() = user_id);

-- Note: Service role (backend) bypasses RLS and can do everything.
-- No additional policy needed for backend - it uses service_role key.

-- =============================================================================
-- Storage Bucket: cv-originals (private)
-- =============================================================================
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'cv-originals',
  'cv-originals',
  false,
  10485760,
  ARRAY['application/pdf', 'image/jpeg', 'image/png', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
)
ON CONFLICT (id) DO NOTHING;

-- Storage policy: Authenticated users can upload to their folder
CREATE POLICY "Users can upload own CVs"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'cv-originals' 
        AND auth.role() = 'authenticated'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Storage policy: Users can read their own files
CREATE POLICY "Users can read own CVs"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'cv-originals'
        AND auth.role() = 'authenticated'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Storage policy: Users can delete their own files
CREATE POLICY "Users can delete own CVs"
    ON storage.objects FOR DELETE
    USING (
        bucket_id = 'cv-originals'
        AND auth.role() = 'authenticated'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- =============================================================================
-- Function: Update updated_at timestamp
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_cv_documents_updated_at
    BEFORE UPDATE ON cv_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- RPC: Semantic search (pgvector cosine similarity)
-- =============================================================================
CREATE OR REPLACE FUNCTION match_cv_documents(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
)
RETURNS TABLE (id uuid, similarity float)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        cv_documents.id,
        1 - (cv_documents.embedding <=> query_embedding) AS similarity
    FROM cv_documents
    WHERE cv_documents.embedding IS NOT NULL
      AND 1 - (cv_documents.embedding <=> query_embedding) > match_threshold
    ORDER BY cv_documents.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- =============================================================================
-- Job Offers Table (optional - for matching/scoring)
-- =============================================================================
CREATE TABLE IF NOT EXISTS job_offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    title TEXT NOT NULL,
    description TEXT,
    required_skills TEXT[],
    location TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE job_offers ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own job offers" ON job_offers
    FOR ALL USING (auth.uid() = user_id);
