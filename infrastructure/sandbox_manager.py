from pathlib import Path
import sys
import venv
import shutil
from domain.interfaces import Sandbox


class LocalDirectorySandbox(Sandbox):

    def __init__(self, sandbox_dir: str):
        self._root = Path(sandbox_dir).resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._venv_dir = self._root / ".sandbox_venv"
        self._ensure_venv()
        self._ensure_node()

    @property
    def root_path(self) -> Path:
        return self._root

    def _ensure_venv(self):
        if not self._venv_dir.exists():
            venv.create(self._venv_dir, with_pip=True)

    def _ensure_node(self):
        self._node_bin = shutil.which("node")

    def get_python_binary(self) -> Path:
        if sys.platform == "win32":
            return self._venv_dir / "Scripts" / "python.exe"
        return self._venv_dir / "bin" / "python"

    def get_node_binary(self) -> str:
        if not self._node_bin:
            raise RuntimeError("Node.js n'est pas installé sur la machine.")
        return self._node_bin

    def resolve_safe_path(self, path_str: str) -> Path:
        p_clean = path_str.strip().replace("\\", "/")

        if p_clean in [".", "", "./", "/"]:
            return self._root

        # Nettoyage des hallucinations de type root /app/
        for prefix in ["/app/", "app/", "/workspace/", "workspace/", "/"]:
            if p_clean.startswith(prefix):
                p_clean = p_clean[len(prefix) :]

        # Résolution du chemin complet
        target = (self._root / p_clean).resolve()

        # Sécurité anti-traversal
        if not str(target).startswith(str(self._root)):
            raise PermissionError(
                f"Accès refusé : tentative de sortie de sandbox !"
            )

        # Création automatique du sous-dossier parent si besoin (ex: site/)
        target.parent.mkdir(parents=True, exist_ok=True)

        return target
