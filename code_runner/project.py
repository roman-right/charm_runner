import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    id: Optional[int]
    name: str


@dataclass
class Project:
    name: str
    path: str
    last_opened: datetime.datetime
    category: Category
