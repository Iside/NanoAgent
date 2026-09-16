from dataclasses import dataclass
from typing import Optional


@dataclass
class SubTask:
    id: int
    tool: str
    target: str  # Le nom du fichier ou l'URL
    content: Optional[str] = (
        ""  # Le code source ou texte à écrire (pour fs_write)
    )
    description: str = ""


@dataclass
class EvaluationResult:
    is_complete: bool
    reason: str


@dataclass
class TaskResult:
    task_id: int
    output: str
    error: Optional[str] = None
