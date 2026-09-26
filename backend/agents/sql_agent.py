import os

from dotenv import load_dotenv
from groq import Groq

from backend.utils.logger import logger


load_dotenv()


class SQLAgent:
    """
    Handles SQL queries, SQL explanations,
    database concepts, and query debugging.
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

        logger.info("sql_agent_started")

    def run(self, question: str) -> str:
        if not question or not question.strip():
            return "Please enter an SQL question."

        question = question.strip()

        prompt = f"""
You are the SQL Agent of AgentForge.

Help the user with SQL and database questions.

Rules:
- Provide correct SQL queries.
- Explain the query in simple language.
- Use clear SQL code blocks.
- State assumptions about table and column names.
- Explain errors when debugging SQL.
- Do not invent database results.
- If the database type matters, mention the SQL dialect assumption.

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
                            "You are a helpful SQL and database assistant."
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
                    "I could not generate an SQL answer right now. "
                    "Please try again."
                )

            logger.info("sql_request_completed")
            return answer.strip()

        except Exception as error:
            logger.error("sql_agent_error | error=%s", error)

            return (
                "The SQL Agent could not complete that request right now. "
                "Please try again."
            )

    def __call__(self, question: str) -> str:
        return self.run(question)