import os
import chromadb
import cohere
from dotenv import load_dotenv


load_dotenv()


class VectorStoreService:
    def __init__(self):
        self.cohere_api_key = os.getenv("COHERE_API_KEY")

        if not self.cohere_api_key:
            raise ValueError("COHERE_API_KEY is not set in the environment variables.")

        self.cohere_client = cohere.Client(self.cohere_api_key)

        self.chroma_client = chromadb.PersistentClient(
            path="chroma_db"
        )

        self.collection = self.chroma_client.get_or_create_collection(
            name="document_chunks"
        )

    def create_embeddings(self, texts: list[str], input_type: str) -> list[list[float]]:
        """
        Crea embeddings utilizando Cohere.
        input_type debe ser:
        - search_document para fragmentos de documentos
        - search_query para preguntas del usuario
        """
        response = self.cohere_client.embed(
            texts=texts,
            model="embed-multilingual-v3.0",
            input_type=input_type,
        )

        return response.embeddings

    def index_chunks(self, chunks: list[str]) -> None:
        """
        Almacena los fragmentos del documento y sus embeddings en ChromaDB.
        Si la colección ya contiene datos, no los vuelve a indexar.
        """
        existing_items = self.collection.count()

        if existing_items > 0:
            return

        embeddings = self.create_embeddings(
            texts=chunks,
            input_type="search_document",
        )

        ids = [f"chunk_{index}" for index in range(len(chunks))]

        metadatas = [
            {"source": "documento.docx", "chunk_index": index}
            for index in range(len(chunks))
        ]

        self.collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search_relevant_context(self, question: str, n_results: int = 1) -> str:
        """
        Busca el fragmento más relevante para la pregunta del usuario.
        """
        question_embedding = self.create_embeddings(
            texts=[question],
            input_type="search_query",
        )[0]

        results = self.collection.query(
            query_embeddings=[question_embedding],
            n_results=n_results,
        )

        documents = results.get("documents", [[]])[0]

        if not documents:
            return ""

        return "\n\n".join(documents)