import datetime
from dataclasses import dataclass
from typing import List

from code_compass.category import Category
from code_compass.db import DB


@dataclass
class Project:
    name: str
    path: str
    last_opened: datetime.datetime
    category: Category

    # CREATE PROJECT

    @classmethod
    def create(
        cls, db: DB, name: str, path: str, category: Category
    ) -> "Project":
        q = """
            INSERT INTO projects (name, path, last_opened, category_id)
            VALUES (?, ?, ?, ?);
            """
        db.cur.execute(q, (name, path, datetime.datetime.now(), category.id))
        db.con.commit()

        return cls(
            name=name,
            path=path,
            last_opened=datetime.datetime.now(),
            category=category,
        )

    def save(self, db: DB) -> None:
        # Insert if project doesn't exist or update if it does

        if self.category.id is None:
            category = Category.get_by_name(db, self.category.name)
            if category:
                self.category = category
            else:
                self.category.save(db)

        q_find = """
            SELECT * FROM projects WHERE path = ?;
            """
        db.cur.execute(q_find, (self.path,))
        data = db.cur.fetchone()
        if data:
            q = """
                UPDATE projects SET name = ?, last_opened = ?, category_id = ?
                WHERE path = ?;
                """
            db.cur.execute(
                q,
                (
                    self.name,
                    datetime.datetime.now(),
                    self.category.id,
                    self.path,
                ),
            )
        else:
            q = """
                INSERT INTO projects (name, path, last_opened, category_id)
                VALUES (?, ?, ?, ?);
                """

            db.cur.execute(
                q,
                (
                    self.name,
                    self.path,
                    datetime.datetime.now(),
                    self.category.id,
                ),
            )
        db.con.commit()

    @classmethod
    def get(cls, db: DB, path: str) -> "Project":
        q = """
            SELECT * FROM projects WHERE path = ?;
            """
        db.cur.execute(q, (path,))
        data = db.cur.fetchone()
        return cls(
            name=data[0],
            path=data[1],
            last_opened=data[2],
            category=Category.get(db, data[3]),
        )

    @classmethod
    def all(cls, db: DB) -> List["Project"]:
        q = """
            SELECT * FROM projects ORDER BY name ASC;
            """
        db.cur.execute(q)
        data = db.cur.fetchall()
        res = []
        for i in data:
            res.append(
                cls(
                    name=i[0],
                    path=i[1],
                    last_opened=i[2],
                    category=Category.get(db, i[3]),
                )
            )
        return res

    @classmethod
    def all_by_category(cls, db: DB, category: Category) -> List["Project"]:
        q = """
            SELECT * FROM projects WHERE category_id = ? ORDER BY name ASC;
            """
        db.cur.execute(q, (category.id,))
        data = db.cur.fetchall()
        res = []
        for i in data:
            res.append(
                cls(
                    name=i[0],
                    path=i[1],
                    last_opened=i[2],
                    category=Category.get(db, i[3]),
                )
            )
        return res

    def delete(self, db: DB) -> None:
        q = """
            DELETE FROM projects WHERE path = ?;
            """
        db.cur.execute(q, (self.path,))
        db.con.commit()
