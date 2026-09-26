import os
import json

from dotenv import load_dotenv
from groq import Groq


# Load environment variables from .env
load_dotenv()


class PlannerAgent:
    """
    Planner Agent for AgentForge.

    Responsibilities:
    - Analyze a complex user request
    - Break it into smaller tasks
    - Select the appropriate agent for each task
    - Define task dependencies
    - Return a structured execution plan
    """

    AVAILABLE_AGENTS = [
        "RESEARCH",
        "CODING",
        "SQL",
        "CALCULATOR",
        "GENERAL"
    ]

    def __init__(self):
        """
        Initialize the Planner Agent.
        """

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is missing. "
                "Please check your .env file."
            )

        self.client = Groq(api_key=api_key)

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        )

        print("Planner Agent: READY")

    # =====================================================
    # CREATE PLAN
    # =====================================================

    def create_plan(self, question: str) -> dict:
        """
        Analyze a user question and create a multi-step plan.

        Returns:
            Dictionary containing:
            - is_complex
            - tasks
        """

        if not question or not question.strip():

            return {
                "is_complex": False,
                "tasks": []
            }

        question = question.strip()

        prompt = f"""
You are the Planner Agent of AgentForge.

Your responsibility is to analyze a user's request and
break complex requests into smaller logical tasks.

Available agents:

1. RESEARCH
   Use for:
   - Web research
   - Current information
   - Recent information
   - Fact finding
   - Online information

2. CODING
   Use for:
   - Programming
   - Code generation
   - Debugging
   - Algorithms
   - Programming explanations

3. SQL
   Use for:
   - SQL queries
   - Databases
   - MySQL
   - PostgreSQL
   - SQLite
   - Database concepts

4. CALCULATOR
   Use for:
   - Mathematical calculations
   - Arithmetic
   - Percentages
   - Numerical operations

5. GENERAL
   Use for:
   - General explanations
   - General knowledge
   - Conversations
   - Questions that do not require another specialized agent

IMPORTANT RULES:

- Use ONLY the available agent names.
- Break complex requests into logical steps.
- Put tasks in the order they should be executed.
- Do not create unnecessary tasks.
- If the request needs only one agent, create one task.
- Every task MUST contain a "depends_on" field.
- "depends_on" must be a list of previous task step numbers.
- Use [] when a task has no dependencies.
- If a task requires the result of Task 1, use [1].
- If a task requires the results of Task 1 and Task 2, use [1, 2].
- A task may only depend on an earlier task.
- Do not create circular dependencies.
- Do not make a task depend on itself.
- Make dependencies reflect the actual information flow between tasks.
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include ```json.
- Do not include explanations outside the JSON.

User request:

{question}

Return exactly this structure:

{{
    "is_complex": true,
    "tasks": [
        {{
            "step": 1,
            "agent": "RESEARCH",
            "task": "Describe exactly what this agent should do",
            "depends_on": []
        }},
        {{
            "step": 2,
            "agent": "CODING",
            "task": "Describe exactly what this agent should do using the required previous result",
            "depends_on": [1]
        }}
    ]
}}
"""

        try:

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a task planning agent. "
                            "Return valid JSON only."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0
            )

            content = response.choices[0].message.content.strip()

            # -------------------------------------------------
            # Remove accidental markdown fences
            # -------------------------------------------------

            if content.startswith("```json"):
                content = content[7:]

            elif content.startswith("```"):
                content = content[3:]

            if content.endswith("```"):
                content = content[:-3]

            content = content.strip()

            # -------------------------------------------------
            # Convert JSON string to Python dictionary
            # -------------------------------------------------

            plan = json.loads(content)

            # -------------------------------------------------
            # Validate planner response
            # -------------------------------------------------

            validated_plan = self._validate_plan(plan)

            return validated_plan

        except json.JSONDecodeError as error:

            print(
                f"Planner JSON error: {error}"
            )

            return {
                "is_complex": False,
                "tasks": []
            }

        except Exception as error:

            print(
                f"Planner Agent error: {error}"
            )

            return {
                "is_complex": False,
                "tasks": []
            }

    # =====================================================
    # VALIDATE PLAN
    # =====================================================

    def _validate_plan(self, plan: dict) -> dict:
        """
        Validate and clean the plan returned by the LLM.

        Validation includes:
        - Valid agent names
        - Valid task descriptions
        - Valid dependency format
        - Dependencies must reference earlier tasks
        - No self-dependencies
        """

        if not isinstance(plan, dict):

            return {
                "is_complex": False,
                "tasks": []
            }

        is_complex = bool(
            plan.get("is_complex", False)
        )

        tasks = plan.get(
            "tasks",
            []
        )

        if not isinstance(tasks, list):

            tasks = []

        valid_tasks = []

        # -------------------------------------------------
        # First pass: validate basic task information
        # -------------------------------------------------

        for index, task in enumerate(
            tasks,
            start=1
        ):

            if not isinstance(task, dict):
                continue

            agent = str(
                task.get(
                    "agent",
                    ""
                )
            ).upper().strip()

            description = str(
                task.get(
                    "task",
                    ""
                )
            ).strip()

            if agent not in self.AVAILABLE_AGENTS:
                print(
                    f"Skipping invalid agent: {agent}"
                )
                continue

            if not description:
                print(
                    f"Skipping empty task at step {index}"
                )
                continue

            # -------------------------------------------------
            # Read dependencies
            # -------------------------------------------------

            dependencies = task.get(
                "depends_on",
                []
            )

            # If LLM returns something other than a list,
            # replace it with an empty dependency list.

            if not isinstance(
                dependencies,
                list
            ):
                dependencies = []

            cleaned_dependencies = []

            for dependency in dependencies:

                try:

                    dependency = int(
                        dependency
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    continue

                # A task cannot depend on itself
                if dependency == index:
                    continue

                # Dependency must refer to an earlier step
                if dependency >= index:
                    continue

                # Dependency must be positive
                if dependency <= 0:
                    continue

                if dependency not in cleaned_dependencies:
                    cleaned_dependencies.append(
                        dependency
                    )

            valid_tasks.append(
                {
                    "step": index,
                    "agent": agent,
                    "task": description,
                    "depends_on": cleaned_dependencies
                }
            )

        # -------------------------------------------------
        # Second validation:
        # dependencies must point to existing tasks
        # -------------------------------------------------

        valid_step_numbers = {
            task["step"]
            for task in valid_tasks
        }

        for task in valid_tasks:

            task["depends_on"] = [
                dependency
                for dependency in task["depends_on"]
                if dependency in valid_step_numbers
            ]

        # -------------------------------------------------
        # If only one task exists, it is not really complex
        # -------------------------------------------------

        if len(valid_tasks) <= 1:

            is_complex = False

        return {
            "is_complex": is_complex,
            "tasks": valid_tasks
        }

    # =====================================================
    # PRINT PLAN
    # =====================================================

    def print_plan(self, plan: dict):
        """
        Display a plan in a readable format.
        """

        print("\n" + "=" * 60)
        print("AGENTFORGE EXECUTION PLAN")
        print("=" * 60)

        if not plan.get("tasks"):

            print("No tasks were created.")

            print("=" * 60)

            return

        print(
            f"\nComplex Plan: "
            f"{plan.get('is_complex', False)}"
        )

        for task in plan["tasks"]:

            print(
                f"\nStep {task['step']}"
            )

            print(
                f"Agent      : {task['agent']}"
            )

            print(
                f"Task       : {task['task']}"
            )

            print(
                f"Depends On : {task.get('depends_on', [])}"
            )

        print("\n" + "=" * 60)

    # =====================================================
    # STANDALONE TESTING
    # =====================================================


if __name__ == "__main__":

    try:

        planner = PlannerAgent()

        print("\nAgentForge Planner Agent")
        print("Type 'exit' to stop.")

        while True:

            question = input(
                "\nEnter a complex question: "
            ).strip()

            if question.lower() == "exit":

                print(
                    "\nPlanner Agent stopped."
                )

                break

            if not question:

                print(
                    "Please enter a question."
                )

                continue

            plan = planner.create_plan(
                question
            )

            planner.print_plan(
                plan
            )

            print("\nRAW JSON:")

            print(
                json.dumps(
                    plan,
                    indent=4
                )
            )

    except Exception as error:

        print(
            f"\nFailed to start Planner Agent: {error}"
        )