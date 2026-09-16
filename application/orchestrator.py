from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
from domain.interfaces import Tool
from domain.models import SubTask, TaskResult
from application.thinker import Thinker


class Orchestrator:

    def __init__(
        self,
        thinker: Thinker,
        tools: List[Tool],
        max_iterations: int = 5,
    ):
        self.thinker = thinker
        self.tools: Dict[str, Tool] = {t.name: t for t in tools}
        self.max_iterations = max_iterations

    def _get_workspace_files(self) -> List[str]:
        """Détecte les vrais scripts python générés dans l'agent_workspace."""
        fs_list = self.tools.get("fs_list")
        if not fs_list:
            return []
        # On interroge la sandbox
        output = fs_list.execute(".")
        # On extrait simplement tous les fichiers finissant par .py
        import re
        files = re.findall(r"[\'\"]([^\'\"]+\.py)[\'\"]", output)
        print(f"      [Vision Agent] Fichiers détectés sur disque : {files}")
        return files

    def _execute_subtask(self, task: SubTask) -> TaskResult:
        print(f"  -> [{task.tool}] Sur : {task.target}")
        tool = self.tools.get(task.tool)
        if not tool:
            return TaskResult(
                task_id=task.id, output="", error=f"Outil {task.tool} inexistant."
            )

        try:
            out = tool.execute(target=task.target, content=task.content)
            if out.startswith("Erreur"):
                return TaskResult(task_id=task.id, output="", error=out)
            return TaskResult(task_id=task.id, output=out)
        except Exception as e:
            return TaskResult(task_id=task.id, output="", error=str(e))

    def run(self, user_goal: str) -> str:
        history: List[str] = []
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n==========================================")
            print(f"[*] Cycle d'exécution #{iteration}/{self.max_iterations}")
            print(f"==========================================")

            # 1. Perception de l'environnement réel
            files_in_workspace = self._get_workspace_files()
            history_str = "\n".join(history)
            # 2. Réflexion conditionnée par l'état réel
            tasks = self.thinker.plan_next_step(
                user_goal, history_str, files_in_workspace
            )
            if not tasks:
                print("[-] Aucune action décidée.")
                break

                        # 3. Exécution séquentielle (dédoublonnée)
            batch_results = []
            has_executed_script = False
            last_out = ""

            # On ne prend que la 1ère tâche si le SLM a dupliqué
            tasks_to_run = tasks[:1]

            for task in tasks_to_run:
                res = self._execute_subtask(task)
                batch_results.append(res)
                msg = res.output if res.output else res.error
                print(f"  <= Résultat : {msg}")
                history.append(f"Action {task.tool} -> {msg}")

                if task.tool in ["run_python", "run_javascript"]:
                    # Détection de succès : sortie standard non vide
                    if (
                        "Sortie standard :" in msg
                        and "aucune sortie console" not in msg
                    ):
                        has_executed_script = True
                        last_out = msg
                    elif "aucune sortie console" in msg:
                        print(
                            "  [!] Attention : Le script a tourné mais n'affiche rien (manque print)."
                        )
                        # On force la suppression du fichier pour le réécrire avec un print au cycle suivant
                        fs_tool = self.tools.get("fs_write")
                        # Permet de reboucler sur une écriture propre

            # 4. Arrêt net en cas de succès avec affichage
            if has_executed_script:
                print("\n==========================================")
                print("[MISSION ACCOMPLIE AVEC SUCCÈS]")
                print("==========================================")
                return f"Succès au cycle {iteration} !\n{last_out}\n"

        return f"Arrêt après {self.max_iterations} cycles sans accomplissement."
