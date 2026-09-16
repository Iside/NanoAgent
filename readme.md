#Quick step
add a gguf model for instance, Qwen3.5-0.8B-Q4_K_M.gguf in a folder named "models"
https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF

##Create virtual environnement 
>python -m venv .venv

##Activate the virtual environment
On Mac/Linux:
>source .venv/bin/activate
On Windows (PowerShell):
>.venv\Scripts\Activate.ps1
On Windows (Command Prompt):
>.venv\Scripts\activate.bat

##Execute
>python .\main.py
