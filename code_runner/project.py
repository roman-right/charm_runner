import datetime
from dataclasses import dataclass


@dataclass
class Project:
    name: str
    path: str
    last_opened: datetime.datetime
