import os

from dotenv import load_dotenv
from groq import Groq

from backend.tools.web.search_tool import WebSearchTool


load_dotenv()


class ResearchAgent:
    """
    Searches the web when possible, then uses Groq
    to create a clear final answer.
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

        self.web_search = None

        # Web search is optional. Groq can still answer
        # general questions if Tavily is unavailable.
        try:
            self.web_search = WebSearchTool(max_results=5)
            print("Web Search          : READY")

        except Exception as error:
            print(f"Web Search          : UNAVAILABLE ({error})")

    def search_web(self, question: str) -> str:
        if not self.web_search:
            return (
                "Web search is currently unavailable. "
                "Do not claim that current information was verified."
            )

        try:
            search_results = self.web_search.search(question)

            if not search_results:
                return (
                    "No web-search results were found. "
                    "Do not invent facts."
                )

            return str(search_results)

        except Exception as error:
            print(f"Web Search Error: {error}")

            return (
                "Web search could not be completed. "
                "Do not claim that current information was verified."
            )

    def research(self, question: str) -> str:
        if not question or not question.strip():
            return "Please enter a research question."

        question = question.strip()

        print("\nSearching the web...")
        search_results = self.search_web(question)

        prompt = f"""
You are the Research Agent of AgentForge.

Answer the user's question clearly and accurately.

Instructions:
- Give a direct answer first.
- Use the web-search results when they are available.
- Do not invent facts, sources, or current events.
- If web search was unavailable, clearly say that you could not verify current information.
- Use simple language.
- Add examples when useful.
- Organize longer answers with headings and bullet points.
- Do not mention internal AgentForge implementation details.

User question:
{question}

Web-search results:
{search_results}

Now provide the final answer.
"""

        try:
            print("Generating answer with Groq...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful, accurate research assistant."
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
                    "I could not generate an answer right now. "
                    "Please try again."
                )

            return answer.strip()

        except Exception as error:
            error_message = str(error).lower()
            print(f"Research Agent Error: {error}")

            if "429" in error_message or "rate limit" in error_message:
                return (
                    "The AI service is busy right now. "
                    "Please wait a moment and try again."
                )

            if (
                "401" in error_message
                or "authentication" in error_message
                or "invalid api key" in error_message
            ):
                return (
                    "The AI service could not be authenticated. "
                    "Please check the API configuration."
                )

            if (
                "connection" in error_message
                or "timeout" in error_message
                or "network" in error_message
            ):
                return (
                    "A network problem prevented the research request. "
                    "Please check your connection and try again."
                )

            return (
                "The Research Agent could not complete that request right now. "
                "Please try again."
            )

    def run(self, question: str) -> str:
        return self.research(question)

    def __call__(self, question: str) -> str:
        return self.research(question)