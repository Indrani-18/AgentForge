import os

from dotenv import load_dotenv
from groq import Groq

from backend.tools.web.search_tool import WebSearchTool


# Load variables from .env
load_dotenv()


class ResearchAgent:
    """
    Research Agent of AgentForge.

    It:
    1. Receives a research question.
    2. Searches the web.
    3. Sends search results to Groq.
    4. Generates a final answer.
    """

    def __init__(self):
        # Get Groq API key
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found.\n"
                "Please add GROQ_API_KEY=your_api_key "
                "to the .env file."
            )

        # Create Groq client
        self.client = Groq(
            api_key=api_key
        )

        # Groq model
        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        )

        # Create web search tool
        self.web_search = WebSearchTool(
            max_results=5
        )

    def search_web(self, question):
        """
        Search the web for the user's question.
        """

        try:
            search_results = self.web_search.search(
                question
            )

            if not search_results:
                return "No search results found."

            return search_results

        except Exception as e:
            print("\nWeb Search Error:")
            print(str(e))

            return (
                "Web search could not be completed. "
                "Please answer using general knowledge."
            )

    def research(self, question):
        """
        Main research workflow.
        """

        # Check empty question
        if not question or not question.strip():
            return "Please enter a research question."

        question = question.strip()

        # Step 1: Search the web
        print("\nSearching the web...")

        search_results = self.search_web(
            question
        )

        # Step 2: Create prompt for Groq
        prompt = f"""
You are the Research Agent of AgentForge.

Your job is to answer questions clearly and accurately.

Instructions:
- Give a direct answer first.
- Use the web-search results provided below.
- Explain important concepts.
- Use simple language when possible.
- Give examples when useful.
- Organize longer answers with headings and bullet points.
- Do not invent facts.
- If the search results are insufficient, say so clearly.
- Do not mention internal AgentForge implementation details.

User question:
{question}

Web-search results:
{search_results}

Now provide the final answer.
"""

        try:
            # Step 3: Send request to Groq
            print("Generating answer with Groq...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful and accurate "
                            "research assistant."
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

            # Step 4: Extract answer
            answer = response.choices[0].message.content

            if not answer:
                return (
                    "The Research Agent received "
                    "an empty response."
                )

            return answer.strip()

        except Exception as e:
            error_message = str(e)

            print("\nResearch Agent Error:")
            print(error_message)

            # Handle rate limit
            if "429" in error_message:
                return (
                    "Groq API rate limit reached. "
                    "Please wait a moment and try again."
                )

            # Handle authentication error
            if (
                "401" in error_message
                or "authentication" in error_message.lower()
                or "invalid api key" in error_message.lower()
            ):
                return (
                    "Groq API authentication failed. "
                    "Please check your GROQ_API_KEY "
                    "in the .env file."
                )

            # Handle other errors
            return (
                f"Research Agent Error: {error_message}"
            )

    def run(self, question):
        """
        Alias for the main research method.
        """

        return self.research(question)

    def __call__(self, question):
        """
        Allows this agent to be called like a function.
        """

        return self.research(question)


# ---------------------------------------------------------
# Standalone testing
# ---------------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("       AGENTFORGE - RESEARCH AGENT")
    print("=" * 60)

    try:
        # Create agent
        agent = ResearchAgent()

        # Get question
        question = input(
            "\nEnter your research question: "
        ).strip()

        # Run research
        print("\nResearch Agent is working...\n")

        result = agent.research(
            question
        )

        print("=" * 60)
        print("RESEARCH RESULT")
        print("=" * 60)

        print(result)

    except Exception as e:
        print("\nSYSTEM ERROR:")
        print(e)