import subprocess
import urllib.parse
import json
import re
from domain.interfaces import Tool, Sandbox


class FSListTool(Tool):

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    @property
    def name(self) -> str:
        return "fs_list"

    def execute(self, target: str = ".", content: str = "") -> str:
        try:
            p = target if target and target.strip() else "."
            safe = self.sandbox.resolve_safe_path(p)
            files = [
                f.name for f in safe.iterdir() if f.name != ".sandbox_venv"
            ]
            return (
                f"Fichiers dans '{p}': {files}"
                if files
                else "Répertoire vide."
            )
        except Exception as e:
            return f"Erreur FSList: {str(e)}"


class FSReadTool(Tool):

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    @property
    def name(self) -> str:
        return "fs_read"

    def execute(self, target: str, content: str = "") -> str:
        try:
            safe = self.sandbox.resolve_safe_path(target)
            if not safe.is_file():
                return f"Erreur: '{target}' n'est pas un fichier."
            return safe.read_text(encoding="utf-8")[:1000]
        except Exception as e:
            return f"Erreur FSRead: {str(e)}"


class FSWriteTool(Tool):

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    @property
    def name(self) -> str:
        return "fs_write"

    def execute(self, target: str, content: str = "") -> str:
        try:
            if not target:
                return "Erreur: Le nom du fichier (target) est vide."
            safe = self.sandbox.resolve_safe_path(target)
            safe.parent.mkdir(parents=True, exist_ok=True)
            safe.write_text(content, encoding="utf-8")
            return f"Succès: Fichier '{safe.name}' écrit ({len(content)} octets)."
        except Exception as e:
            return f"Erreur FSWrite: {str(e)}"


class PythonRunTool(Tool):

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    @property
    def name(self) -> str:
        return "run_python"

    def execute(self, target: str, content: str = "") -> str:
        try:
            py_bin = str(self.sandbox.get_python_binary())

            if target.endswith(".py"):
                script = self.sandbox.resolve_safe_path(target)
                if not script.exists():
                    return f"Erreur: Le fichier '{target}' n'existe pas encore."
                cmd = [py_bin, str(script)]
            else:
                cmd = [py_bin, "-c", target]

            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.sandbox.root_path,
                timeout=10,
            )

            out = res.stdout.strip()
            err = res.stderr.strip()
            if res.returncode != 0:
                return f"Erreur Python (code {res.returncode}): {err}"
            return (
                f"Sortie standard : {out}"
                if out
                else "Script exécuté avec succès (aucune sortie console)."
            )
        except subprocess.TimeoutExpired:
            return "Erreur: Timeout (10s)."
        except Exception as e:
            return f"Erreur run_python: {str(e)}"


class WebSearchTool(Tool):
    """Effectue une recherche web via curl et DuckDuckGo."""
    @property
    def name(self) -> str:
        return "web_search"
    def execute(self, target: str, content: str = "") -> str:
        query = target.strip()
        if not query:
            return "Erreur: La requête de recherche est vide."
        try:
            # Encodage URL de la requête
            encoded_query = urllib.parse.quote(query)
            # Appel curl sur l'API publique Instant Answer de DuckDuckGo
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            cmd = [
                "curl",
                "-s",  # Mode silencieux
                "-L",  # Suit les redirections
                "-A",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",  # User agent propre
                "--max-time",
                "8",  # Timeout réseau court
                url,
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                return f"Erreur de connexion réseau : {res.stderr}"
            raw_json = res.stdout.strip()
            if not raw_json:
                return "Aucun résultat trouvé sur le web."
            data = json.loads(raw_json)
            # Synthèse des résultats textuels utiles
            summary = []
            if data.get("AbstractText"):
                summary.append(f"Résumé: {data['AbstractText']}")
            # Récupération des sujets connexes
            for topic in data.get("RelatedTopics", [])[:3]:
                if "Text" in topic:
                    summary.append(f"- {topic['Text']}")
            if not summary:
                # Fallback : si DuckDuckGo ne renvoie pas d'Abstract direct
                return (
                    f"Résultat DuckDuckGo : Information générale disponible pour '{query}', "
                    "mais aucun résumé direct n'a pu être extrait."
                )
            return "\n".join(summary)[:1500]
        except subprocess.TimeoutExpired:
            return "Erreur: Timeout réseau lors de la recherche (10s)."
        except Exception as e:
            return f"Erreur web_search: {str(e)}"


class FSDeleteTool(Tool):
    """Supprime un fichier dans le workspace sécurisé."""
    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox
    @property
    def name(self) -> str:
        return "fs_delete"
    def execute(self, target: str, content: str = "") -> str:
        try:
            path = self.sandbox.resolve_safe_path(target)
            if not path.exists():
                return f"Erreur: Le fichier '{target}' n'existe pas."
            if path.is_dir():
                return f"Erreur: '{target}' est un dossier, fs_delete ne supprime que des fichiers."
            path.unlink()
            return f"Succès: Le fichier '{target}' a été supprimé."
        except Exception as e:
            return f"Erreur de suppression: {str(e)}"