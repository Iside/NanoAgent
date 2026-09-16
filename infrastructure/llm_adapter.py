import atexit
from llama_cpp import Llama
from domain.interfaces import LLMService


class LlamaCppAdapter(LLMService):

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,  # 4096 recommandé pour laisser de la place au contexte
        n_threads: int = 4,
        n_gpu_layers: int = 0,
    ):
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            verbose=False,
        )
        atexit.register(self.close)

    def close(self):
        if hasattr(self, "llm") and self.llm is not None:
            del self.llm
            self.llm = None

    def generate(
        self, prompt: str, schema: dict = None, temperature: float = 0.1
    ) -> str:
        kwargs = {}
        if schema:
            kwargs["response_format"] = {
                "type": "json_object",
                "schema": schema,
            }

        response = self.llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant d'automatisation logique et concis. Ne répète jamais le même code en boucle.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=1024,  # Augmenté pour éviter la troncature
            repeat_penalty=1.2,  # CRUCIAL : empêche la boucle infinie de répétition
            **kwargs,
        )
        return response["choices"][0]["message"]["content"]
