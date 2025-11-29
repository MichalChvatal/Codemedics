#!/usr/bin/env python3
#
from fastapi import FastAPI, Request, Body
from pydantic import BaseModel
from model.main import RAGChatbot
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
rag_chatbot = RAGChatbot()


class User(BaseModel):
    username: str

origins = [
#    "http://localhost",          # Allow requests from localhost (port 80 or default)
#    "http://localhost:8080",     # Allow requests from localhost on port 8080
#    "http://127.0.0.1:8000",    # Allow requests from 127.0.0.1 on port 8000 (default FastAPI)
#    "http://your-frontend-domain.com",  # Replace with your actual frontend domain
#    "https://your-frontend-domain.com", # Allow HTTPS as well
    "*",  # (Use with caution!) Allows all origins - NOT recommended for production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Allows cookies to be sent in cross-origin requests (if needed)
    allow_methods=["*"],     # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],     # Allows all headers
)

@app.get("/")
async def get_hello():
    return "Hello!"

@app.post("/generate")
async def post_hello(prompt: str = Body(..., embed=True),
                     context: List[Dict] = Body(..., embed=True)):
    response_text = rag_chatbot.return_response(query=prompt)
    new_turn = {"user": prompt, "bot": response_text}
    updated_context = context + [new_turn]
    return {"response": response_text, "context": updated_context}
