from pydantic import BaseModel


class ChatRequest(BaseModel):

    query: str



class ChatResponse(BaseModel):

    query: str
    answer: str