import sqlite3

from code_compass.config import BASE_DIR, DB_PATH


class DB:
    def __init__(self):
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(
            DB_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        self.cur = self.con.cursor()

        q_create_categories = """
            CREATE TABLE IF NOT EXISTS
                categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR UNIQUE,
                    is_active BOOLEAN DEFAULT 0
                );
            """

        q = """
            CREATE TABLE IF NOT EXISTS
                projects (
                    name VARCHAR,
                    path VARCHAR UNIQUE,
                    last_opened TIMESTAMP,
                    category_id INTEGER
                );
            """

        self.con.execute(q_create_categories)
        self.con.execute(q)
        self.con.commit()

    def close(self):
        self.con.close()
