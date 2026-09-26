from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.orchestrator.orchestrator import Orchestrator


# ==========================================
# FastAPI Application
# ==========================================

app = FastAPI(
    title="AgentForge API",
    description="Multi-Agent AI System",
    version="1.0.0"
)


# ==========================================
# CORS Configuration
# ==========================================

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Initialize Orchestrator
# ==========================================

orchestrator = Orchestrator()


# ==========================================
# Request Model
# ==========================================

class QuestionRequest(BaseModel):
    question: str


# ==========================================
# Home Route
# ==========================================

@app.get("/")
def home():
    return {
        "success": True,
        "message": "AgentForge API is running",
        "version": "1.0.0"
    }


# ==========================================
# Health Check
# ==========================================

@app.get("/health")
def health():
    return {
        "success": True,
        "status": "healthy",
        "service": "AgentForge"
    }


# ==========================================
# API Information
# ==========================================

@app.get("/info")
def info():
    return {
        "name": "AgentForge",
        "description": "Multi-Agent AI System",
        "status": "running",
        "api": "FastAPI"
    }


# ==========================================
# Ask AgentForge
# ==========================================

@app.post("/ask")
def ask_question(request: QuestionRequest):

    try:

        question = request.question.strip()

        # Empty question check
        if not question:
            return {
                "success": False,
                "question": "",
                "answer": "Please enter a question."
            }

        # Send question to Orchestrator
        answer = orchestrator.run(question)

        return {
            "success": True,
            "question": question,
            "answer": answer
        }

    except Exception as error:

        print("========================================")
        print("AGENTFORGE API ERROR")
        print("========================================")
        print(str(error))
        print("========================================")

        return {
            "success": False,
            "question": request.question,
            "answer": (
                "AgentForge encountered an unexpected problem. "
                "Please try again in a moment."
            )
        }