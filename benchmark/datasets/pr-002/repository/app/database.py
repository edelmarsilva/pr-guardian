from __future__ import annotations

import sqlite3

def create_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(
    ":memory:",
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
    """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL
    )
    """
    )

    connection.executemany(
    """
    INSERT INTO users (
        id,
        email,
        name
    )
    VALUES (?, ?, ?)
    """,
    [
        (
            1,
            "alice@example.com",
            "Alice",
        ),
        (
            2,
            "bob@example.com",
            "Bob",
        ),
    ],
    )

    connection.commit()

    return connection
