from pathlib import Path

from .db import get_connection


def migration_directory() -> Path:
    return Path(__file__).resolve().parent.parent / "migrations"


def split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []

    for line in sql_text.splitlines():
        current.append(line)
        if ";" in line:
            statement = "\n".join(current).strip()
            if statement:
                statements.append(statement)
            current = []

    trailing = "\n".join(current).strip()
    if trailing:
        statements.append(trailing)

    return statements


def apply_migrations() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              filename TEXT PRIMARY KEY,
              applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        applied = {
            row["filename"]
            for row in conn.execute(
                "SELECT filename FROM schema_migrations"
            ).fetchall()
        }

        for path in sorted(migration_directory().glob("*.sql")):
            if path.name in applied:
                continue

            with conn.transaction():
                for statement in split_sql_statements(path.read_text(encoding="utf-8")):
                    conn.execute(statement)
                conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)",
                    (path.name,),
                )


if __name__ == "__main__":
    apply_migrations()