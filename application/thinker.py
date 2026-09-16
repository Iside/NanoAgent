import json
import re
from typing import List
from domain.interfaces import LLMService
from domain.models import SubTask


class Thinker:

    def __init__(self, llm: LLMService):
        self.llm = llm

    def plan_next_step(
        self, goal: str, history: str, files_present: List[str]
    ) -> List[SubTask]:
        has_python_file = any(f.endswith(".py") for f in files_present)

        if not has_python_file:
            # PHASE 1 : Création de fichier
            schema = {
                "type": "object",
                "properties": {
                    "tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "tool": {
                                    "type": "string",
                                    "enum": ["fs_write"],
                                },
                                "target": {"type": "string"},
                                "content": {"type": "string"},
                                "description": {"type": "string"},
                            },
                            "required": ["id", "tool", "target", "content"],
                        },
                    }
                },
                "required": ["tasks"],
            }
            prompt = f"""OBJECTIF : {goal}
Consignes strictes de génération de code :
- Si c'est du python Tu DOIS inclure un print() pour afficher le résultat dans le terminal (ex: print(resultat)).
- Si c'est un site web dit juste que c'est fait si le resultat est suffisant pour l'ojectif fixé
- N'inclus aucune commande interactive (pas d'input())."""
        else:
            # PHASE 2 : Exécution (Content n'est PLUS requis)
            target_script = [f for f in files_present if f.endswith(".py")][0]
            schema = {
                "type": "object",
                "properties": {
                    "tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "tool": {
                                    "type": "string",
                                    "enum": ["run_python"],
                                },
                                "target": {
                                    "type": "string",
                                    "enum": [target_script],
                                },
                                "description": {"type": "string"},
                            },
                            "required": ["id", "tool", "target"],
                        },
                    }
                },
                "required": ["tasks"],
            }
            prompt = f"""OBJECTIF : {goal}
Le fichier '{target_script}' existe.
Action requise : Exécute-le si possible avec l'outil 'run_python' ou 'run_node'."""

        raw = self.llm.generate(prompt, schema=schema, temperature=0.0)

        # 1. Nettoyage de base
        raw_clean = raw.strip()
        if not raw_clean.endswith("}"):
            if not raw_clean.endswith('"'):
                raw_clean += '"'
            raw_clean += "}]}"

        # 2. Parsing robuste
        try:
            # strict=False permet d'accepter les sauts de ligne réels dans les chaînes JSON
            parsed = json.loads(raw_clean, strict=False)
            tasks = []
            for t in parsed.get("tasks", []):
                tasks.append(
                    SubTask(
                        id=int(t.get("id", 1)),
                        tool=t.get("tool"),
                        target=t.get("target"),
                        content=t.get("content", ""),
                        description=t.get("description", ""),
                    )
                )
            return tasks

        except Exception as e:
            # Filet de secours Regex si le JSON a un format trop exotique
            print(f"[Thinker Warning] Fallback JSON : {e}")
            try:
                # Si le parser strict échoue, on extrait les informations clés
                tool_match = re.search(
                    r'"tool"\s*:\s*"(fs_write|run_python)"', raw_clean
                )
                target_match = re.search(
                    r'"target"\s*:\s*"([^"]+)"', raw_clean
                )
                if tool_match and target_match:
                    return [
                        SubTask(
                            id=1,
                            tool=tool_match.group(1),
                            target=target_match.group(1),
                            content="",
                            description="Tâche récupérée par fallback",
                        )
                    ]
            except Exception:
                pass
            return []
