import os
import json
import hashlib
import cohere
from dotenv import load_dotenv

from app.prompts.prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.services.vector_store import VectorStoreService


load_dotenv()


class RagService:
    def __init__(self):
        self.cohere_api_key = os.getenv("COHERE_API_KEY")

        if not self.cohere_api_key:
            raise ValueError("COHERE_API_KEY is not set in the environment variables.")

        self.cohere_client = cohere.Client(self.cohere_api_key)
        self.vector_store = VectorStoreService()

        self.cache_file_path = "answer_cache.json"
        self.answer_cache = self.load_cache()

    def load_cache(self) -> dict:
        """
        Carga la caché de respuestas desde un archivo JSON local.
        """
        if not os.path.exists(self.cache_file_path):
            return {}

        with open(self.cache_file_path, "r", encoding="utf-8") as cache_file:
            return json.load(cache_file)

    def save_cache(self) -> None:
        """
        Guarda la caché de respuestas en un archivo JSON local.
        """
        with open(self.cache_file_path, "w", encoding="utf-8") as cache_file:
            json.dump(
                self.answer_cache,
                cache_file,
                ensure_ascii=False,
                indent=2,
            )

    def normalize_question(self, question: str) -> str:
        """
        Normaliza la pregunta para evitar fallos de caché causados por espacios adicionales.
        """
        return " ".join(question.strip().split())

    def build_cache_key(self, question: str, context: str) -> str:
        """
        Construye una clave de caché determinista utilizando la pregunta normalizada y el contexto recuperado.
        """
        normalized_question = self.normalize_question(question)

        raw_key = json.dumps(
            {
                "question": normalized_question,
                "context": context,
            },
            ensure_ascii=False,
            sort_keys=True,
        )

        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def answer_question(self, question: str) -> str:
        """
        Recupera el contexto más relevante comparando embeddings y genera una respuesta determinista utilizando la caché.
        """
        context = self.vector_store.search_relevant_context(question)
        cache_key = self.build_cache_key(question, context)

        if cache_key in self.answer_cache:
            return self.answer_cache[cache_key]

        user_prompt = USER_PROMPT_TEMPLATE.format(
            question=question,
            context=context,
        )

        response = self.cohere_client.chat(
            model="command-r7b-12-2024",
            temperature=0,
            message=user_prompt,
            preamble=SYSTEM_PROMPT,
        )

        answer = response.text.strip()

        self.answer_cache[cache_key] = answer
        self.save_cache()

        return answer