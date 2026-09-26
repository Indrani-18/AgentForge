import os

from dotenv import load_dotenv
from groq import Groq

from backend.utils.logger import logger


load_dotenv()


class CodingAgent:
    """
    Handles programming questions, code explanations,
    debugging, and code generation.
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is missing.")

        self.client = Groq(api_key=api_key)

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        )

        logger.info("coding_agent_started")

    def run(self, question: str) -> str:
        if not question or not question.strip():
            return "Please enter a coding question."

        question = question.strip()

        prompt = f"""
You are the Coding Agent of AgentForge.

Help the user with programming questions.

Rules:
- Give correct and readable code.
- Explain the solution simply.
- Point out errors clearly when debugging code.
- Use code blocks when showing code.
- Do not invent library functions or results.
- If the request is unclear, ask one helpful question.

User question:
{question}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful programming assistant."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=2048
            )

            answer = response.choices[0].message.content

            if not answer or not answer.strip():
                return (
                    "I could not generate a coding answer right now. "
                    "Please try again."
                )

            logger.info("coding_request_completed")
            return answer.strip()

        except Exception as error:
            logger.error("coding_agent_error | error=%s", error)

            return (
                "The Coding Agent could not complete that request right now. "
                "Please try again."
            )

    def __call__(self, question: str) -> str:
        return self.run(question)