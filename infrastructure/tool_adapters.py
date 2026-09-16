import subprocess
from domain.interfaces import Tool
import urllib.parse
import json
import re


class CurlTool(Tool):

    @property
    def name(self) -> str:
        return "curl"

    def execute(self, param: str) -> str:
        try:
            # -s = silencieux, -m 5 = timeout de 5 sec, extrait les 500 premiers caractères
            cmd = ["curl", "-s", "-m", "5", param]
            res = subprocess.run(
                cmd, capture_output=True, text=True, timeout=6
            )
            return (
                res.stdout[:500]
                if res.stdout
                else f"Error: {res.stderr[:200]}"
            )
        except Exception as e:
            return f"Failed to execute curl: {str(e)}"


class FileSystemReadTool(Tool):

    @property
    def name(self) -> str:
        return "fs_read"

    def execute(self, param: str) -> str:
        try:
            with open(param.strip(), "r", encoding="utf-8") as f:
                return f.read()[:500]
        except Exception as e:
            return f"Failed to read file: {str(e)}"


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