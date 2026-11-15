CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS clauses;

CREATE TABLE clauses (
    id text PRIMARY KEY,
    policy_id text NOT NULL,
    clause_id text NOT NULL,
    section text,
    title text,
    text text NOT NULL,
    see_also text[],
    embedding vector(384) NOT NULL
)