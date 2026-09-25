from __future__ import annotations

import sqlite3


class UserRepository:
    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection

    def find_by_email(
        self,
        email: str,
    ):
        """
        Vulnerable implementation intentionally used by benchmark PR-002.
        """

        query = (
            "SELECT id, email, name "
            "FROM users "
            f"WHERE email = '{email}'"
        )

        cursor = self.connection.execute(
            query
        )

        return cursor.fetchone()
