from abc import ABC, abstractmethod
from pathlib import Path


class Sandbox(ABC):

    @property
    @abstractmethod
    def root_path(self) -> Path:
        pass

    @abstractmethod
    def resolve_safe_path(self, relative_path: str) -> Path:
        pass

    @abstractmethod
    def get_python_binary(self) -> Path:
        pass

    @abstractmethod
    def get_node_binary(self) -> str:
        pass


class Tool(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def execute(self, target: str, content: str = "") -> str:
        """Signature unique pour tous les outils."""
        pass


class LLMService(ABC):

    @abstractmethod
    def generate(
        self, prompt: str, schema: dict = None, temperature: float = 0.2
    ) -> str:
        pass
