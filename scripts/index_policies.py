import json
import os

import psycopg
from dotenv import load_dotenv
from fastembed import TextEmbedding
from pgvector.psycopg import register_vector


POLICIES_DIR = "data/policies"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

INSERT_SQL = """
    INSERT INTO clauses (id, policy_id, clause_id, section, title, text, see_also, embedding)
    VALUES (%(id)s, %(policy_id)s, %(clause_id)s, %(section)s, %(title)s, %(text)s, %(see_also)s, %(embedding)s)
"""


def load_policies(path: str) -> list[dict]:
    """Load all policy JSON files from path into a flat list of clauses, each tagged with its policy_id."""
    clauses = []
    for filename in sorted(os.listdir(path)):
        if filename.endswith(".json"):
            file_path = os.path.join(path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for clause in data["clauses"]:
                    clauses.append({
                        "policy_id": data["policy_id"],
                        "clause_id": clause["clause_id"],
                        "section": clause["section"],
                        "title": clause["title"],
                        "text": clause["text"],
                        "see_also": clause["see_also"],
                    })
    return clauses


def build_row(clause: dict) -> dict:
    """Build a DB row: global id (home:2.2) and policy-prefixed see_also references."""
    clause["id"] = f"{clause['policy_id']}:{clause['clause_id']}"
    clause["see_also"] = [f"{clause['policy_id']}:{s}" for s in clause["see_also"]]
    return clause


def embed_texts(texts: list[str]) -> list:
    """Embed all texts in one batch call with BGE via fastembed."""
    model = TextEmbedding(model_name=EMBEDDING_MODEL)
    return list(model.embed(texts))


def write_to_db(rows: list[dict], database_url: str) -> None:
    """Rebuild the clauses table from rows in a single transaction."""
    with psycopg.connect(database_url) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE clauses")
            cur.executemany(INSERT_SQL, rows)


def main() -> None:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

    clauses = load_policies(POLICIES_DIR)
    rows = [build_row(clause) for clause in clauses]

    # Prepend the clause title to give the embedding more context (contextual chunk header).
    # The stored `text` column stays clean for citations.
    texts = [f"{row['title']}: {row['text']}" for row in rows]
    vectors = embed_texts(texts)
    for row, vector in zip(rows, vectors):
        row["embedding"] = vector

    write_to_db(rows, database_url)
    print(f"Indexed {len(rows)} clauses into the clauses table.")


if __name__ == "__main__":
    main()