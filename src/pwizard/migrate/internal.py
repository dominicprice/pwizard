from dataclasses import dataclass
from datetime import datetime


@dataclass
class AppliedMigration:
    parent: str | None
    hash: str
    applied_at: datetime
