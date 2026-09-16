import sys
from pathlib import Path

# Ajustement du chemin pour les imports si exécuté directement
ROOT_DIR = Path(__file__).resolve().parent
# if str(ROOT_DIR) not in sys.path:
#     sys.path.insert(0, str(ROOT_DIR))

from infrastructure.llm_adapter import LlamaCppAdapter
from infrastructure.sandbox_manager import LocalDirectorySandbox
from infrastructure.sandboxed_tools import (
    FSListTool,
    FSReadTool,
    FSWriteTool,
    FSDeleteTool,
    PythonRunTool,
    WebSearchTool,
)
from application.thinker import Thinker
from application.orchestrator import Orchestrator
import sys

sandbox = LocalDirectorySandbox(sandbox_dir="./agent_workspace")

tools = [
    FSListTool(sandbox),
    FSReadTool(sandbox),
    FSWriteTool(sandbox),
    PythonRunTool(sandbox),
    WebSearchTool(),
    FSDeleteTool(sandbox),
]

def main():
    print("==================================================")
    print("  Local Agent CLI - Initialisation du système...")
    print("==================================================")

    # 1. Configuration des chemins
    project_root = ROOT_DIR.parent
    workspace_dir = project_root / "agent_workspace"

    # 2. Modele leger    
    model_path = project_root / "models" / "Qwen3.5-0.8B-Q4_K_M.gguf"

    if not model_path.exists():
        # Fallback pour recherche automatique de tout fichier .gguf si le chemin diffère
        found_models = list((project_root / "models").glob("*.gguf"))
        if found_models:
            model_path = found_models[0]
        else:
            print(f"[Erreur critique] Aucun modèle GGUF trouvé dans {project_root / 'models'}")
            sys.exit(1)

    print(f"[*] Chargement du modèle : {model_path.name}")

    llm = LlamaCppAdapter(model_path=str(model_path), n_ctx=2048)

    agent = Orchestrator(thinker=Thinker(llm), tools=tools, max_iterations=6)

    # Premier test pour vérifier le poc
    goal = "Écris un script Python calcul.py qui calcule la factorielle de 5 et l'affiche dans le terminal, puis exécute-le."
    print(f"Goal: {goal}\n")
    print(agent.run(goal))

    # # 3. Boucle interactive REPL
    # while True:
    #     try:
    #         user_goal = input("\n[Goal] > ").strip()
    #         # Vérification de l'entrée utilisateur
    #         if not user_goal:
    #             continue
    #         if user_goal.lower() in ["/exit", "/quit", "exit", "quit"]:
    #             print("\nArrêt de l'agent. À bientôt !")
    #             break
    #         # Lancement du cycle agentique
    #         print(f"\n[Exécution en cours...] Objectif : {user_goal}")
    #         summary = agent.run(user_goal)
            
    #         print("\n---------------- RAPPORT FINAL ----------------")
    #         print(summary)
    #         print("-----------------------------------------------")
    #     except KeyboardInterrupt:
    #         # Gestion propre du Ctrl+C
    #         print("\n\nInterruption détectée. Arrêt du programme...")
    #         break
    #     except EOFError:
    #         # Gestion propre du Ctrl+D
    #         break
    #     except Exception as e:
    #         print(f"\n[Erreur inattendue] : {str(e)}")


if __name__ == "__main__":
    main()



