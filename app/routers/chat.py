from fastapi import APIRouter, HTTPException
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import OpenAI
from app.services.embeddings import get_embeddings
import os

router = APIRouter()

# Configuración del chatbot  
EMBEDDINGS_PATH = "models/employees.faiss"
os.environ["OPENAI_API_KEY"] = "tu-api-key"  # Reemplaza con tu clave real

@router.post("/chat")
async def chat_with_ai(query: str, chat_history: list = []):
    try:
        # Obtener embeddings y datos
        faiss_index, employee_data = get_embeddings()
        
        # Configurar cadena de conversación
        qa_chain = ConversationalRetrievalChain.from_llm(
            OpenAI(temperature=0),
            retriever=faiss_index.as_retriever(),
            return_source_documents=True
        )
        
        # Ejecutar consulta
        result = qa_chain({
            "question": query,
            "chat_history": chat_history
        })
        
        return {
            "answer": result["answer"],
            "source_documents": result["source_documents"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))