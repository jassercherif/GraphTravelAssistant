from fastapi import APIRouter, HTTPException

from app.rag.rag_pipeline import RAGPipeline
from app.api.schemas import ChatRequest, ChatResponse


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


# Initialize once
rag_pipeline = RAGPipeline()



@router.post(
    "/",
    response_model=ChatResponse
)
async def chat(request: ChatRequest):

    try:

        query = request.query

        answer = rag_pipeline.ask(query)


        return ChatResponse(
            query=query,
            answer=answer
        )


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )