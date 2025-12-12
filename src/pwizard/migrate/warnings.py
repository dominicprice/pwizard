import abc
from datetime import datetime


class MigrationWarning(abc.ABC):
    @abc.abstractmethod
    def describe(self) -> str: ...


class HashesDifferWarning(MigrationWarning):
    def __init__(self, hash: str, previous_hash: str, applied_at: datetime):
        self.hash = hash
        self.previous_hash = previous_hash
        self.applied_at = applied_at

    def describe(self) -> str:
        hash_trunc = 8
        if len(self.hash) > hash_trunc:
            hash = self.hash[:hash_trunc] + "..."
        else:
            hash = self.hash
        if len(self.previous_hash) > hash_trunc:
            previous_hash = self.previous_hash[:hash_trunc] + "..."
        else:
            previous_hash = self.previous_hash
        return f"hash '{hash}' differs from previous application of the migration at {self.applied_at} with hash '{previous_hash}'"


class ParentDiffersWarning(MigrationWarning):
    def __init__(
        self,
        parent: str | None,
        previous_parent: str | None,
        applied_at: datetime,
    ):
        self.parent = parent
        self.previous_parent = previous_parent
        self.applied_at = applied_at

    def describe(self) -> str:
        return f"parent '{self.parent}' differs from previous application of the migration at {self.applied_at} with parent '{self.previous_parent}'"
