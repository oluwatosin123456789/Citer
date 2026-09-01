CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS repos (
    id            SERIAL PRIMARY KEY,
    url           TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL,
    default_branch TEXT,
    commit_hash   TEXT,
    status        TEXT NOT NULL DEFAULT 'pending',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS code_chunks (
    id           SERIAL PRIMARY KEY,
    repo_id      INTEGER NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
    file_path    TEXT NOT NULL,
    symbol_name  TEXT,
    symbol_type  TEXT,
    start_line   INT,
    end_line     INT,
    language     TEXT,
    content      TEXT NOT NULL,
    embedding    vector(1536),
    metadata     JSONB,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_code_chunks_repo ON code_chunks (repo_id);
CREATE INDEX IF NOT EXISTS idx_code_chunks_symbol ON code_chunks (symbol_name);
CREATE INDEX IF NOT EXISTS idx_code_chunks_file ON code_chunks (file_path);
CREATE INDEX IF NOT EXISTS idx_code_chunks_embedding
    ON code_chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    repo_id     INTEGER REFERENCES repos(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id          SERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    citations   JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id              SERIAL PRIMARY KEY,
    dataset_name    TEXT,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    pass_rate       FLOAT,
    hallucination_rate FLOAT,
    avg_latency_ms  FLOAT,
    report          JSONB
);