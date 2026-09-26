import re

import time

from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.agents.coding_agent import CodingAgent

from backend.agents.research_agent import ResearchAgent

from backend.agents.sql_agent import SQLAgent

from backend.agents.planner_agent import PlannerAgent

from backend.agents.final_answer_agent import FinalAnswerAgent

from backend.memory.memory import ConversationMemory

from backend.memory.shared_memory import SharedWorkingMemory



from backend.models.agent_message import AgentMessage



from backend.graph.workflow_graph import WorkflowGraph

from backend.graph.graph_executor import GraphExecutor



from backend.tools.calculator_tool import calculator

from backend.utils.logger import logger






from backend.orchestrator.routing import RoutingMixin
from backend.orchestrator.context_memory import ContextMemoryMixin
from backend.orchestrator.single_agent_execution import SingleAgentMixin
from backend.orchestrator.graph_execution import GraphExecutionMixin
from backend.orchestrator.final_answer import FinalAnswerMixin


class Orchestrator(
    RoutingMixin,
    ContextMemoryMixin,
    SingleAgentMixin,
    GraphExecutionMixin,
    FinalAnswerMixin,
):

    """

    Central controller of the AgentForge multi-agent system.



    Responsibilities:

        - Understand the user question

        - Select the appropriate agent

        - Decide when a multi-step plan is required

        - Create workflow graphs

        - Execute independent tasks in parallel

        - Respect task dependencies

        - Pass information between agents

        - Maintain shared working memory

        - Maintain structured AgentMessages

        - Generate the final answer

        - Store conversation history

    """



    MAX_WORKERS = 5



    VALID_AGENTS = {

        "RESEARCH",

        "CODING",

        "SQL",

        "CALCULATOR",

        "GENERAL",

    }



    # =========================================================

    # INITIALIZATION

    # =========================================================



    def __init__(self):



        print("\n========================================")

        print("INITIALIZING AGENTFORGE")

        print("========================================")



        # -----------------------------------------------------

        # Research Agent

        # -----------------------------------------------------



        self.research_agent = None



        try:

            self.research_agent = ResearchAgent()

            print("Research Agent: READY")



        except Exception as error:

            print(

                f"Research Agent initialization failed: {error}"

            )



        # -----------------------------------------------------

        # Coding Agent

        # -----------------------------------------------------



        self.coding_agent = None



        try:

            self.coding_agent = CodingAgent()

            print("Coding Agent: READY")



        except Exception as error:

            print(

                f"Coding Agent initialization failed: {error}"

            )



        # -----------------------------------------------------

        # SQL Agent

        # -----------------------------------------------------



        self.sql_agent = None



        try:

            self.sql_agent = SQLAgent()

            print("SQL Agent: READY")



        except Exception as error:

            print(

                f"SQL Agent initialization failed: {error}"

            )



        # -----------------------------------------------------

        # Planner Agent

        # -----------------------------------------------------



        self.planner_agent = None



        try:

            self.planner_agent = PlannerAgent()

            print("Planner Agent: READY")



        except Exception as error:

            print(

                f"Planner Agent initialization failed: {error}"

            )



        # -----------------------------------------------------

        # Final Answer Agent

        # -----------------------------------------------------



        self.final_answer_agent = None



        try:

            self.final_answer_agent = FinalAnswerAgent()

            print("Final Answer Agent: READY")



        except Exception as error:

            print(

                f"Final Answer Agent initialization failed: {error}"

            )



        # -----------------------------------------------------

        # Conversation Memory

        # -----------------------------------------------------



        try:

            self.memory = ConversationMemory()

            print("Conversation Memory: READY")



        except Exception as error:

            print(

                f"Conversation Memory initialization failed: {error}"

            )

            self.memory = None



        # -----------------------------------------------------

        # Shared Working Memory

        # -----------------------------------------------------



        try:

            self.shared_memory = SharedWorkingMemory()

            print("Shared Working Memory: READY")



        except Exception as error:

            print(

                "Shared Working Memory initialization failed: "

                f"{error}"

            )

            self.shared_memory = None



        print("========================================")

        print("AGENTFORGE INITIALIZATION COMPLETE")

        print("========================================\n")



    # =========================================================

    # QUESTION CLASSIFICATION

    # =========================================================



    def run(self, question):

        """

        Main entry point for AgentForge.



        Workflow:



            User Question

                    ↓

            Reset Shared Memory

                    ↓

            Planner Decision

                    ↓

             ┌──────────────┐

             │              │

        Single Agent    Multi-Agent

             │              │

             │         Planner Agent

             │              ↓

             │       Workflow Graph

             │              ↓

             │       Graph Executor

             │              ↓

             │       Parallel Agents

             │              ↓

             └──────→ Shared Memory

                            ↓

                     Final Answer Agent

                            ↓

                    Conversation Memory

        """



        start_time = time.time()



        if question is None:

            return "Please enter a valid question."



        question = str(

            question

        ).strip()



        if not question:

            return "Please enter a valid question."



        print("\n========================================")

        print("AGENTFORGE")

        print("========================================")



        print(

            f"USER QUESTION: {question}"

        )



        try:



            # =================================================

            # RESET SHARED WORKING MEMORY

            # =================================================



            self.reset_shared_memory(

                question

            )



            # =================================================

            # PLANNER MODE

            # =================================================



            if (

                self.should_use_planner(

                    question

                )

                and self.planner_agent

            ):



                print(

                    "\nMODE: MULTI-AGENT "

                    "PLANNER"

                )



                # -------------------------------------------------

                # Create plan

                # -------------------------------------------------



                plan = (

                    self.planner_agent

                    .create_plan(

                        question

                    )

                )



                # -------------------------------------------------

                # Validate planner result

                # -------------------------------------------------



                if (

                    isinstance(

                        plan,

                        dict

                    )

                    and plan.get(

                        "is_complex"

                    ) is True

                    and len(

                        plan.get(

                            "tasks",

                            []

                        )

                    ) > 1

                ):



                    print(

                        "\nPLAN GENERATED"

                    )



                    try:



                        self.planner_agent.print_plan(

                            plan

                        )



                    except Exception:

                        pass



                    # -------------------------------------------------

                    # Normalize plan

                    # -------------------------------------------------



                    normalized_tasks = (

                        self._normalize_plan_tasks(

                            plan

                        )

                    )



                    normalized_plan = {

                        "is_complex": True,

                        "tasks": normalized_tasks

                    }



                    # -------------------------------------------------

                    # Store plan

                    # -------------------------------------------------



                    if self.shared_memory:



                        try:



                            self.shared_memory.set(

                                "plan",

                                normalized_plan

                            )



                        except Exception as error:



                            print(

                                "Could not store plan: "

                                f"{error}"

                            )



                    # -------------------------------------------------

                    # Execute graph workflow

                    # -------------------------------------------------



                    results = (

                        self.execute_graph_workflow(

                            question,

                            normalized_plan

                        )

                    )



                    # -------------------------------------------------

                    # Generate final answer

                    # -------------------------------------------------



                    final_answer = (

                        self.generate_final_answer(

                            question,

                            results

                        )

                    )



                    # -------------------------------------------------

                    # Save conversation

                    # -------------------------------------------------



                    self.save_conversation(

                        question,

                        final_answer

                    )



                    # -------------------------------------------------

                    # Logging

                    # -------------------------------------------------



                    duration = (

                        time.time()

                        - start_time

                    )



                    logger.info(

                        f"PLANNER | "

                        f"{question} | "

                        f"{duration:.2f}s"

                    )



                    print(

                        "\n========================================"

                    )



                    print(

                        "FINAL ANSWER"

                    )



                    print(

                        "========================================"

                    )



                    print(

                        final_answer

                    )



                    return final_answer



                else:



                    print(

                        "\nPlanner did not create "

                        "a multi-step plan."

                    )



            # =================================================

            # NORMAL SINGLE-AGENT MODE

            # =================================================



            context_question = (

                self.build_context(

                    question

                )

            )



            agent_name = (

                self.select_agent(

                    question

                )

            )



            print(

                f"\nSELECTED AGENT: "

                f"{agent_name}"

            )



            # -------------------------------------------------

            # Execute selected agent

            # -------------------------------------------------



            result = (

                self.execute_single_agent(

                    question if agent_name == "CALCULATOR" else context_question,

                    agent_name

                )

            )



            final_answer = str(

                result

            )



            # -------------------------------------------------

            # Store single-agent result

            # -------------------------------------------------



            self.store_agent_result(

                step=1,

                agent_name=agent_name,

                task_description=question,

                result=final_answer,

                depends_on=[],

                status="completed"

            )



            # -------------------------------------------------

            # Store AgentMessage

            # -------------------------------------------------



            self.store_agent_message(

                sender=agent_name,

                receiver="FINAL_ANSWER",

                task=question,

                content=final_answer,

                step=1,

                status="completed",

                metadata={

                    "source_step": 1,

                    "final_result": True

                }

            )



            # -------------------------------------------------

            # Store final answer

            # -------------------------------------------------



            if self.shared_memory:



                try:



                    self.shared_memory.set(

                        "final_answer",

                        final_answer

                    )



                except Exception:

                    pass



            # -------------------------------------------------

            # Save conversation

            # -------------------------------------------------



            self.save_conversation(

                question,

                final_answer

            )



            # -------------------------------------------------

            # Logging

            # -------------------------------------------------



            duration = (

                time.time()

                - start_time

            )



            logger.info(

                f"{agent_name} | "

                f"{question} | "

                f"{duration:.2f}s"

            )



            print(

                "\n========================================"

            )



            print(

                "FINAL ANSWER"

            )



            print(

                "========================================"

            )



            print(

                final_answer

            )



            return final_answer



        except Exception as error:



            duration = (

                time.time()

                - start_time

            )



            print(

                "\n========================================"

            )



            print(

                "ORCHESTRATOR ERROR"

            )



            print(

                "========================================"

            )



            print(

                str(error)

            )



            logger.error(

                f"ORCHESTRATOR ERROR | "

                f"{question} | "

                f"{error} | "

                f"{duration:.2f}s"

            )



            return (

                "AgentForge encountered an unexpected "

                "problem while processing your question."

            )





# ============================================================

# COMMAND LINE TESTING

# ============================================================





if __name__ == "__main__":



    orchestrator = Orchestrator()



    print("\n")

    print("========================================")

    print("AGENTFORGE CLI")

    print("========================================")

    print("Type 'exit' to quit.")

    print("========================================")



    while True:



        question = input(

            "\nEnter your question: "

        ).strip()



        if question.lower() == "exit":



            print(

                "\nAgentForge stopped."

            )



            break



        if not question:



            print(

                "Please enter a question."

            )



            continue



        answer = orchestrator.run(

            question

        )



        print("\n")