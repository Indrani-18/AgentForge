from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.orchestrator.orchestrator import Orchestrator


app = FastAPI(
    title="AgentForge API",
    description="Multi-Agent AI System",
    version="1.0.0"
)


origins = [
    "http://127.0.0.1:5000",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


orchestrator = Orchestrator()


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def home():
    return {
        "success": True,
        "message": "AgentForge API is running",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {
        "success": True,
        "status": "healthy",
        "service": "AgentForge"
    }


@app.get("/info")
def info():
    return {
        "name": "AgentForge",
        "description": "Multi-Agent AI System",
        "status": "running",
        "api": "FastAPI"
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):
    try:
        question = request.question.strip()

        if not question:
            return {
                "success": False,
                "question": "",
                "answer": "Please enter a question."
            }

        answer = orchestrator.run(question)

        return {
            "success": True,
            "question": question,
            "answer": answer
        }

    except Exception as error:
        print("========================================")
        print("AGENTFORGE ERROR")
        print("========================================")
        print(str(error))
        print("========================================")

        return {
            "success": False,
            "question": request.question,
            "answer": f"Error: {str(error)}"
        }