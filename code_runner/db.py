import sqlite3
from typing import Dict, List, Optional

from code_runner.config import BASE_DIR, DB_PATH
from code_runner.project import Project, Category


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
        self.add_default_category_if_the_db_is_empty()
        self.con.execute(q)
        self.con.commit()

    def add_default_category_if_the_db_is_empty(self):
        q = """
            SELECT * FROM categories;
            """
        self.cur.execute(q)
        data = self.cur.fetchone()
        if not data:
            self.add_category_if_not_exists(Category(id=None, name="Default"))

    def add_category_if_not_exists(self, category: Category):
        q_find = """
            SELECT * FROM categories WHERE name = ?;
            """
        self.cur.execute(q_find, (category.name,))
        data = self.cur.fetchone()
        if data:
            category.id = data[0]
        else:
            q = """
                INSERT INTO categories (
                    name
                )
                VALUES (
                    ?
                )
                """
            self.cur.execute(q, (category.name,))
            self.con.commit()
            category.id = self.cur.lastrowid
        return category

    def set_category_active(self, category: Category):
        q_set_all_categories_to_not_active = """
            UPDATE categories SET is_active = 0;
            """
        q_set_current_category_to_active = """
            UPDATE categories SET is_active = 1 WHERE id = ?;
            """
        self.cur.execute(q_set_all_categories_to_not_active)
        self.cur.execute(q_set_current_category_to_active, (category.id,))
        self.con.commit()

    def add_project(self, project: Project):
        category_id = self.add_category_if_not_exists(project.category).id

        q = """
            INSERT INTO projects VALUES (
                ?,
                ?,
                ?,
                ?
            )
            """
        self.cur.execute(
            q, (project.name, project.path, project.last_opened, category_id)
        )
        self.con.commit()

    def update_project(self, project: Project):
        project.category = self.add_category_if_not_exists(project.category)
        q = """
            UPDATE projects SET
                name = ?,
                path = ?,
                last_opened = ?,
                category_id = ?
            WHERE
                path = ?
            """
        self.cur.execute(
            q,
            (
                project.name,
                project.path,
                project.last_opened,
                project.category.id,
                project.path,
            ),
        )
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

    def delete_category_and_all_projects(self, category: Category):
        q = """
            DELETE FROM
                projects
            WHERE
                category_id = ?
            """
        self.cur.execute(q, (category.id,))
        q = """
            DELETE FROM
                categories
            WHERE
                id = ?
            """
        self.cur.execute(q, (category.id,))
        self.con.commit()

    def get_category_by_name(self, category_name: str) -> Optional[Category]:
        q = """ 
            SELECT * FROM categories WHERE name = ?;
            """
        self.cur.execute(q, (category_name,))
        data = self.cur.fetchone()
        if not data:
            return None
        return Category(id=data[0], name=data[1])

    def get_category_by_id(self, category_id: int) -> Category:
        q = """ 
            SELECT * FROM categories WHERE id = ?;
            """
        self.cur.execute(q, (category_id,))
        data = self.cur.fetchone()
        return Category(id=data[0], name=data[1])

    def get_all_projects(
        self, category_name: Optional[str] = None
    ) -> Dict[str, Project]:
        if category_name is None:
            q = """
                SELECT * FROM projects ORDER BY name COLLATE NOCASE ASC;
                """
            self.cur.execute(q)
        else:
            q = """
                SELECT * FROM projects WHERE category_id = (
                    SELECT id FROM categories WHERE name = ?
                ) ORDER BY name COLLATE NOCASE ASC;
                """
            self.cur.execute(q, (category_name,))

        data = self.cur.fetchall()
        res = {}
        for i in data:
            res[i[1]] = Project(
                name=i[0],
                path=i[1],
                last_opened=i[2],
                category=self.get_category_by_id(i[3]),
            )
        return res

    def get_all_categories(self) -> List[Category]:
        q = """
            SELECT * FROM categories ORDER BY name COLLATE NOCASE ASC;
            """
        self.cur.execute(q)
        data = self.cur.fetchall()
        res = []
        for i in data:
            res.append(Category(id=i[0], name=i[1], is_active=i[2]))
        return res

    def get_active_category(self) -> Category:
        q = """
            SELECT * FROM categories WHERE is_active = 1;
            """
        self.cur.execute(q)
        data = self.cur.fetchone()
        return Category(id=data[0], name=data[1], is_active=data[2])
