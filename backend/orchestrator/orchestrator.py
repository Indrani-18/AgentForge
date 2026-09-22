import re

from backend.agents.research_agent import ResearchAgent
from backend.tools.calculator_tool import calculator
from backend.memory.memory import ConversationMemory


class Orchestrator:
    """
    Main controller of AgentForge.

    It selects the correct tool or agent
    based on the user's question.
    """

    def __init__(self):

        print("Initializing AgentForge...")

        # -------------------------------------------------
        # Initialize Research Agent
        # -------------------------------------------------

        self.research_agent = ResearchAgent()

        # -------------------------------------------------
        # Initialize Conversation Memory
        # -------------------------------------------------

        self.memory = ConversationMemory(
            max_messages=20
        )

        self.memory.load_from_file(
            "data/memory.json"
        )

        print("Research Agent      : READY")
        print("Calculator          : READY")
        print("Tavily Search       : READY")
        print("Memory              : READY")
        print("Orchestrator        : READY")

    # =====================================================
    # CALCULATION DETECTION
    # =====================================================

    def is_calculation(self, question: str) -> bool:

        question_lower = question.lower()

        # Detect expressions such as:
        # 25 + 4
        # 100 * 5
        # 50 / 2
        # 100 - 20

        if re.search(
            r"\d+\s*[\+\-\*\/x×]\s*\d+",
            question_lower
        ):
            return True

        math_words = [
            "calculate",
            "calculation",
            "multiply",
            "multiplication",
            "divide",
            "division",
            "add",
            "addition",
            "subtract",
            "subtraction",
            "percentage",
            "percent"
        ]

        return any(
            word in question_lower
            for word in math_words
        )

    # =====================================================
    # WEB SEARCH DETECTION
    # =====================================================

    def is_web_search(self, question: str) -> bool:

        question_lower = question.lower()

        search_words = [
            "latest",
            "today",
            "current",
            "recent",
            "news",
            "search",
            "this week",
            "this month",
            "now",
            "2026"
        ]

        return any(
            word in question_lower
            for word in search_words
        )

    # =====================================================
    # AGENT SELECTION
    # =====================================================

    def select_agent(self, question: str):

        if self.is_calculation(question):

            return (
                "CALCULATOR",
                "The user is asking for a mathematical calculation."
            )

        if self.is_web_search(question):

            return (
                "RESEARCH",
                "The question requires current or online information."
            )

        return (
            "RESEARCH",
            "The question is suitable for the Research Agent."
        )

    # =====================================================
    # BUILD MEMORY CONTEXT
    # =====================================================

    def build_context(self, question: str) -> str:

        previous_context = self.memory.get_context(
            limit=10
        )

        if (
            not previous_context
            or previous_context == "No previous conversation."
        ):
            return question

        return f"""
You are continuing an ongoing conversation.

Previous conversation:
{previous_context}

Current user question:
{question}

Use the previous conversation only when it helps
understand the current question.

Answer the current question directly.
Do not mention that conversation history was provided.
"""

    # =====================================================
    # RUN ORCHESTRATOR
    # =====================================================

    def run(self, question: str) -> str:

        if not question or not question.strip():
            return "Please enter a question."

        question = question.strip()

        # -------------------------------------------------
        # Select agent before saving the final response
        # -------------------------------------------------

        agent_name, reason = self.select_agent(
            question
        )

        print("\n" + "=" * 60)
        print(f"Selected Agent: {agent_name}")
        print(f"Reason: {reason}")
        print("=" * 60)

        # =================================================
        # CALCULATOR
        # =================================================

        if agent_name == "CALCULATOR":

            print("Executing Calculator...")

            try:
                result = calculator(
                    question
                )

            except Exception as error:
                result = (
                    f"Calculator error: {error}"
                )

        # =================================================
        # RESEARCH AGENT
        # =================================================

        else:

            print("Executing Research Agent...")

            try:
                context_question = self.build_context(
                    question
                )

                result = self.research_agent.research(
                    context_question
                )

            except Exception as error:
                result = (
                    f"Research Agent error: {error}"
                )

        # -------------------------------------------------
        # Save conversation
        # -------------------------------------------------

        self.memory.add_user_message(
            question
        )

        self.memory.add_assistant_message(
            result
        )

        self.memory.save_to_file(
            "data/memory.json"
        )

        return result


# =========================================================
# STANDALONE TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("                    AGENTFORGE")
    print("                MULTI-AGENT SYSTEM")
    print("=" * 60)

    try:

        orchestrator = Orchestrator()

        while True:

            question = input(
                "\nEnter your question "
                "(type 'exit' to quit): "
            ).strip()

            if question.lower() == "exit":

                print("\nAgentForge stopped.")
                break

            if not question:

                print("Please enter a question.")
                continue

            result = orchestrator.run(
                question
            )

            print("\n" + "=" * 60)
            print("FINAL ANSWER")
            print("=" * 60)

            print(result)

    except Exception as error:

        print("\nSYSTEM ERROR:")
        print(error)