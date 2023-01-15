import datetime
import sqlite3
from typing import Dict

from code_runner.config import BASE_DIR, DB_PATH
from code_runner.project import Project


class DB:
    def __init__(self):
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(
            DB_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        q = """
            CREATE TABLE IF NOT EXISTS
                projects (
                    name VARCHAR,
                    path VARCHAR UNIQUE,
                    last_opened TIMESTAMP
                );
            """
        self.cur = self.con.cursor()
        self.con.execute(q)

    def add_project(self, project: Project):
        q = """
            INSERT INTO projects VALUES (
                ?,
                ?,
                ?
            )
            """
        self.cur.execute(q, (project.name, project.path, project.last_opened))
        self.con.commit()

    def update_project(self, project: Project):
        q = """
            UPDATE
                projects
            SET
                last_opened = ?
            WHERE
                path = ?
            """
        self.cur.execute(q, (datetime.datetime.now(), project.path))
        self.con.commit()

    def delete_project(self, project: Project):
        q = """
            DELETE FROM
                projects
            WHERE
                path = ?
            """
        self.cur.execute(q, (project.path,))
        self.con.commit()

    def get_all_projects(self) -> Dict[str, Project]:
        q = """
            SELECT * FROM projects ORDER BY name COLLATE NOCASE ASC;
            """
        self.cur.execute(q)
        data = self.cur.fetchall()
        res = {}
        for i in data:
            res[i[1]] = Project(name=i[0], path=i[1], last_opened=i[2])
        return res
