from backend.agents.research_agent import ResearchAgent
from backend.tools.web.search_tool import web_search


class ResearchWorkflow:
    """
    Research Workflow

    Flow:

        User Question
              |
              v
        Web Search Agent
              |
              v
        Search Results
              |
              v
        Research Agent
              |
              v
        Final Answer
    """

    def __init__(self):

        print("Research Workflow: READY")

        # Initialize Research Agent
        self.research_agent = ResearchAgent()

    # ========================================================
    # STEP 1: WEB SEARCH
    # ========================================================

    def perform_web_search(self, question):

        print("\n" + "-" * 60)
        print("STEP 1: WEB SEARCH")
        print("-" * 60)

        try:

            search_results = web_search(
                question
            )

            print("Web search completed successfully.")

            return search_results

        except Exception as e:

            print(
                "Web search failed:",
                e
            )

            return (
                "No web search results were available. "
                f"Error: {str(e)}"
            )

    # ========================================================
    # STEP 2: RESEARCH AGENT
    # ========================================================

    def perform_research(
        self,
        question,
        search_results
    ):

        print("\n" + "-" * 60)
        print("STEP 2: RESEARCH AGENT")
        print("-" * 60)

        prompt = f"""
You are the Research Agent in AgentForge,
a multi-agent AI system.

The user asked:

{question}

A Web Search Agent searched for relevant
information and returned the following results:

--------------------------------------------------
WEB SEARCH RESULTS
--------------------------------------------------

{search_results}

--------------------------------------------------

Your task is to produce the final answer.

Instructions:

1. Answer the user's question clearly.
2. Use the web search results when relevant.
3. Do not invent facts.
4. If the search results are insufficient,
   clearly say so.
5. Organize the answer using headings
   and bullet points when useful.
6. Keep the explanation easy to understand.
7. Give the most important information first.
"""

        try:

            final_answer = self.research_agent.research(
                prompt
            )

            print(
                "Research Agent completed successfully."
            )

            return final_answer

        except Exception as e:

            print(
                "Research Agent failed:",
                e
            )

            return (
                "Research Agent error: "
                f"{str(e)}"
            )

    # ========================================================
    # COMPLETE WORKFLOW
    # ========================================================

    def research_with_web(self, question):

        print("\n")
        print("=" * 60)
        print("           AGENTFORGE RESEARCH WORKFLOW")
        print("=" * 60)

        print(
            f"\nUser Question:\n{question}"
        )

        # ----------------------------------------------------
        # STEP 1
        # ----------------------------------------------------

        search_results = self.perform_web_search(
            question
        )

        # ----------------------------------------------------
        # STEP 2
        # ----------------------------------------------------

        final_answer = self.perform_research(
            question,
            search_results
        )

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        print("\n")
        print("=" * 60)
        print("                  FINAL RESULT")
        print("=" * 60)

        print(final_answer)

        print("=" * 60)

        return final_answer


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("              AGENTFORGE")
    print("          RESEARCH WORKFLOW")
    print("=" * 60)

    try:

        # ----------------------------------------------------
        # Create workflow
        # ----------------------------------------------------

        workflow = ResearchWorkflow()

        # ----------------------------------------------------
        # Get user question
        # ----------------------------------------------------

        while True:

            question = input(
                "\nEnter your research question "
                "(type 'exit' to quit): "
            ).strip()

            # ------------------------------------------------
            # Exit
            # ------------------------------------------------

            if question.lower() == "exit":

                print(
                    "\nAgentForge workflow stopped."
                )

                break

            # ------------------------------------------------
            # Empty input
            # ------------------------------------------------

            if not question:

                print(
                    "Please enter a question."
                )

                continue

            # ------------------------------------------------
            # Run workflow
            # ------------------------------------------------

            workflow.research_with_web(
                question
            )

    except KeyboardInterrupt:

        print(
            "\n\nWorkflow interrupted by user."
        )

    except Exception as e:

        print(
            "\nSYSTEM ERROR:"
        )

        print(e)