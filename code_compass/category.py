from dataclasses import dataclass
from typing import Optional, List

from code_compass.db import DB


@dataclass
class Category:
    id: Optional[int]
    name: str
    is_active: bool = True

    # CREATE CATEGORY

    @classmethod
    def create(cls, db: DB, name: str) -> "Category":
        category = cls(id=None, name=name)
        category.save(db)
        return category

    @classmethod
    def create_default_if_db_is_empty(cls, db: DB) -> None:
        q = """
            SELECT * FROM categories;
            """
        db.cur.execute(q)
        data = db.cur.fetchone()
        if not data:
            cls.create(db, "Default")

    def save(self, db: DB) -> None:
        # Insert category if it doesn't exist or update it if it does
        q_find = """
            SELECT * FROM categories WHERE name = ?;
            """
        db.cur.execute(q_find, (self.name,))
        data = db.cur.fetchone()
        if data:
            q = """
                UPDATE categories SET name = ?, is_active = ? WHERE id = ?;
                """
            db.cur.execute(q, (self.name, self.is_active, self.id))
            db.con.commit()
        else:
            q = """
                INSERT INTO categories (name, is_active) VALUES (?, ?);
                """
            db.cur.execute(q, (self.name, self.is_active))
        db.con.commit()
        self.id = db.cur.lastrowid

    # ALL CATEGORIES

    @classmethod
    def all(cls, db: DB) -> List["Category"]:
        q = """
            SELECT * FROM categories ORDER BY name COLLATE NOCASE ASC;
            """
        db.cur.execute(q)
        data = db.cur.fetchall()
        res = []
        for i in data:
            res.append(cls(id=i[0], name=i[1], is_active=i[2]))
        return res

    # GET CATEGORY

    @classmethod
    def get(cls, db: DB, category_id: int) -> "Category":
        q = """ 
            SELECT * FROM categories WHERE id = ?;
            """
        db.cur.execute(q, (category_id,))
        data = db.cur.fetchone()
        return cls(id=data[0], name=data[1])

    @classmethod
    def get_by_name(cls, db: DB, category_name: str) -> Optional["Category"]:
        q = """ 
            SELECT * FROM categories WHERE name = ?;
            """
        db.cur.execute(q, (category_name,))
        data = db.cur.fetchone()
        if not data:
            return None
        return cls(id=data[0], name=data[1])

    # ACTIVE CATEGORY

    @classmethod
    def get_active(cls, db: DB) -> Optional["Category"]:
        q = """
            SELECT * FROM categories WHERE is_active = 1;
            """
        db.cur.execute(q)
        data = db.cur.fetchone()
        if data:
            return Category(id=data[0], name=data[1])
        return None

    def set_active(self, db: DB) -> None:
        q = """
            UPDATE categories SET is_active = 0;
            """
        db.cur.execute(q)
        q = """
            UPDATE categories SET is_active = 1 WHERE id = ?;
            """
        db.cur.execute(q, (self.id,))
        db.con.commit()

    # DELETE CATEGORY

    def delete(self, db: DB) -> None:
        # delete category and all projects that belong to it

        q = """
            DELETE FROM projects WHERE category_id = ?;
            """
        db.cur.execute(q, (self.id,))

        q = """
                    DELETE FROM categories WHERE id = ?;
                    """
        db.cur.execute(q, (self.id,))
        db.con.commit()
