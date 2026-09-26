import os
import re

from dotenv import load_dotenv
from groq import Groq

from backend.tools.web.search_tool import WebSearchTool


load_dotenv()


class ResearchAgent:
    """
    Research Agent with a ReAct-style loop.

    Instead of one search followed by one answer, the agent repeats
    a Thought -> Action -> Observation cycle:

        Thought:     does it have enough information yet?
        Action:      SEARCH[<refined query>]  or  FINISH
        Observation: the web-search results for that query

    This continues until the model decides it has enough information
    (FINISH) or MAX_ITERATIONS is reached, whichever comes first.
    """

    MAX_ITERATIONS = 3

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
            self.web_search = WebSearchTool(max_results=3)
            print("Web Search          : READY")

        except Exception as error:
            print(f"Web Search          : UNAVAILABLE ({error})")

    # =====================================================
    # LOW-LEVEL HELPERS
    # =====================================================

    def search_web(self, query: str) -> str:
        if not self.web_search:
            return (
                "Web search is currently unavailable. "
                "Do not claim that current information was verified."
            )

        try:
            search_results = self.web_search.search(query)

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

    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int, retries: int = 2) -> str:
        """
        Shared Groq call used by both the reasoning step and the
        final-answer step, with the same error handling as before.

        Some models (gpt-oss in particular) occasionally emit an internal
        tool-call format instead of plain text, even with no tools
        registered, which Groq rejects with a 400 "tool_use_failed" /
        "Tool choice is none, but model called a tool" error. This is
        intermittent model behaviour, not a logic bug, so it's worth a
        couple of quick retries before giving up.
        """

        last_error = None

        for attempt in range(retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens
                )

                content = response.choices[0].message.content
                return content.strip() if content else ""

            except Exception as error:
                last_error = error
                error_message = str(error).lower()

                if "tool_use_failed" in error_message or "tool choice is none" in error_message:
                    print(
                        f"Research Agent: transient tool-call glitch from the model "
                        f"(attempt {attempt + 1}/{retries + 1}), retrying..."
                    )
                    continue

                # Any other error is not worth retrying -- fall through to
                # the normal error handling below immediately.
                break

        error = last_error
        error_message = str(error).lower()
        print(f"Research Agent Error: {error}")

        if "429" in error_message or "rate limit" in error_message:
            raise RuntimeError(
                "The AI service is busy right now. "
                "Please wait a moment and try again."
            ) from error

        if (
            "401" in error_message
            or "authentication" in error_message
            or "invalid api key" in error_message
        ):
            raise RuntimeError(
                "The AI service could not be authenticated. "
                "Please check the API configuration."
            ) from error

        if (
            "connection" in error_message
            or "timeout" in error_message
            or "network" in error_message
        ):
            raise RuntimeError(
                "A network problem prevented the research request. "
                "Please check your connection and try again."
            ) from error

        raise RuntimeError(
            "The Research Agent could not complete that request right now. "
            "Please try again."
        ) from error

    # =====================================================
    # REACT LOOP
    # =====================================================

    def _reasoning_prompt(self, question: str, scratchpad: str) -> str:
        return f"""
You are the Research Agent of AgentForge, working step by step (ReAct style).

User question:
{question}

So far you have done this:
{scratchpad if scratchpad else "(nothing yet)"}

Important: if you have not searched yet, and the question involves
anything current, recent, or time-sensitive (prices, versions, dates,
news, events, releases), you do NOT already know the answer reliably.
Search first -- do not FINISH before at least one search on this kind
of question.

Decide the SINGLE next step. Reply in EXACTLY this format, nothing else:

Thought: <one or two sentences about what you know and what is missing>
Action: SEARCH[<a focused search query>]

OR, if you already have enough information to answer well:

Thought: <one or two sentences about why you have enough information>
Action: FINISH
"""

    def _parse_action(self, raw_response: str):
        """
        Returns a tuple (thought, action_type, query_or_none).
        action_type is "SEARCH" or "FINISH".
        Falls back to FINISH if parsing fails, so a malformed
        response can never loop forever.
        """

        thought_match = re.search(r"Thought:\s*(.+)", raw_response)
        thought = thought_match.group(1).strip() if thought_match else ""

        search_match = re.search(r"Action:\s*SEARCH\[(.+?)\]", raw_response, re.IGNORECASE)
        if search_match:
            return thought, "SEARCH", search_match.group(1).strip()

        return thought, "FINISH", None

    def research(self, question: str) -> str:
        if not question or not question.strip():
            return "Please enter a research question."

        question = question.strip()
        scratchpad_steps = []

        print("\n" + "=" * 50)
        print("RESEARCH AGENT: STARTING REACT LOOP")
        print("=" * 50)

        for iteration in range(1, self.MAX_ITERATIONS + 1):
            scratchpad = "\n".join(scratchpad_steps)

            try:
                raw_response = self._call_llm(
                    system_prompt=(
                        "You are a precise research planner. "
                        "Follow the requested format exactly."
                    ),
                    user_prompt=self._reasoning_prompt(question, scratchpad),
                    max_tokens=200
                )
            except RuntimeError as friendly_error:
                return str(friendly_error)

            thought, action_type, query = self._parse_action(raw_response)

            if action_type == "FINISH" and not scratchpad_steps:
                # The model decided it already knows enough without ever
                # searching -- for a Research Agent that defeats the
                # purpose, so force at least one search before FINISH
                # is honoured. Fall back to the raw question as the
                # search query.
                print(
                    "\n[Iteration 1] Model tried to FINISH with no search "
                    "yet -- forcing one search first."
                )
                action_type, query = "SEARCH", question

            print(f"\n[Iteration {iteration}]")
            print(f"Thought: {thought}")

            if action_type == "FINISH":
                print("Action: FINISH")
                break

            print(f"Action: SEARCH[{query}]")

            observation = self.search_web(query)

            # Truncate before storing, not just before printing -- the
            # full scratchpad gets resent to Groq on every subsequent
            # call, so untruncated observations compound fast and can
            # trip rate limits by iteration 2 or 3.
            MAX_OBSERVATION_CHARS = 1200
            if len(observation) > MAX_OBSERVATION_CHARS:
                observation = observation[:MAX_OBSERVATION_CHARS] + " ...(truncated)"

            print(f"Observation: {observation[:300]}{'...' if len(observation) > 300 else ''}")

            scratchpad_steps.append(
                f"Thought: {thought}\n"
                f"Action: SEARCH[{query}]\n"
                f"Observation: {observation}"
            )
        else:
            print("\nReached MAX_ITERATIONS without FINISH — answering with what was gathered.")

        print("=" * 50)

        final_scratchpad = "\n\n".join(scratchpad_steps) if scratchpad_steps else (
            "No web search was performed for this question."
        )

        answer_prompt = f"""
You are the Research Agent of AgentForge.

Answer the user's question clearly and accurately, using the research
gathered below.

Instructions:
- Give a direct answer first.
- Use the research below when it is relevant.
- Do not invent facts, sources, or current events.
- If no useful research was found, clearly say that you could not verify current information.
- Use simple language.
- Add examples when useful.
- Organize longer answers with headings and bullet points.
- Do not mention internal AgentForge implementation details or the ReAct process itself.

User question:
{question}

Research gathered:
{final_scratchpad}

Now provide the final answer.
"""

        try:
            answer = self._call_llm(
                system_prompt="You are a helpful, accurate research assistant.",
                user_prompt=answer_prompt,
                max_tokens=2048
            )
        except RuntimeError as friendly_error:
            return str(friendly_error)

        if not answer:
            return "I could not generate an answer right now. Please try again."

        return answer

    def run(self, question: str) -> str:
        return self.research(question)

    def __call__(self, question: str) -> str:
        return self.research(question)