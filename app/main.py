from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.services.document_loader import load_document_chunks
from app.services.vector_store import VectorStoreService
from app.services.rag_service import RagService


DOCUMENT_PATH = "app/data/documento.docx"


app = FastAPI(
    title="RAG Document Assistant",
    description="API for answering questions over a local document using RAG."
)


class AskRequest(BaseModel):
    user_name: str = Field(..., min_length=1, example="John Doe")
    question: str = Field(..., min_length=1, example="Who is Zara?")


class AskResponse(BaseModel):
    user_name: str
    question: str
    answer: str


@app.on_event("startup")
def startup_event():
    """
    Carga el documento, crea fragmentos y los indexa en ChromaDB cuando la API se inicia.
    """
    chunks = load_document_chunks(DOCUMENT_PATH)

    if not chunks:
        raise RuntimeError("No chunks were generated from the document.")

    vector_store = VectorStoreService()
    vector_store.index_chunks(chunks)


@app.get("/")
def health_check():
    """
    Endpoint básico para verificar que la API está funcionando.
    """
    return {"status": "ok", "message": "RAG Document Assistant is running."}


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """
    Recibe una pregunta del usuario y devuelve una respuesta generada por el pipeline RAG.
    """
    try:
        rag_service = RagService()
        answer = rag_service.answer_question(request.question)

        return AskResponse(
            user_name=request.user_name,
            question=request.question,
            answer=answer,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )