"""Apply database/schema.sql to the configured database (psql-free setup)."""
import os
import re
from pathlib import Path
from urllib.parse import quote_plus

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / "backend" / ".env"
SCHEMA_FILE = ROOT / "database" / "schema.sql"

load_dotenv(dotenv_path=ENV_FILE, override=False)

host = os.getenv("DB_HOST", "localhost")
port = os.getenv("DB_PORT", "5432")
name = os.getenv("DB_NAME", "climatetwin_bharat")
user = os.getenv("DB_USER", "postgres")
password = os.getenv("DB_PASSWORD", "")

db_url = (
    f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
    f"@{host}:{port}/{name}"
)

SKIP_PREFIXES = (
    "CREATE DATABASE",
    "\\c",
    "CREATE USER",
    "GRANT ALL PRIVILEGES ON DATABASE",
    "GRANT ALL ON ALL",
)


def iter_statements(sql: str):
    buf = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if any(stripped.upper().startswith(p.upper()) for p in SKIP_PREFIXES):
            continue
        buf.append(line)
        if stripped.endswith(";"):
            yield "\n".join(buf)
            buf.clear()
    if buf:
        yield "\n".join(buf)


def main():
    sql = SCHEMA_FILE.read_text(encoding="utf-8")
    statements = list(iter_statements(sql))
    print(f"Applying {len(statements)} statements to {name} on {host}:{port} ...")

    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    for i, stmt in enumerate(statements, 1):
        try:
            cur.execute(stmt)
        except psycopg2.Error as exc:
            print(f"  [{i}] skipped/failed: {exc.pgerror or exc}")
    cur.close()
    conn.close()
    print("Schema apply finished.")


if __name__ == "__main__":
    main()
