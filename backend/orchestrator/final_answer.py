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







class FinalAnswerMixin:
    """
    Mixin split out of the original monolithic Orchestrator class.
    See orchestrator.py for how this is combined with the other mixins.
    """

    def generate_final_answer(

        self,

        original_question,

        agent_results

    ):

        """

        Send all agent results to the Final Answer Agent.

        """



        if not self.final_answer_agent:



            print(

                "Final Answer Agent unavailable. "

                "Using fallback formatter."

            )



            final_answer = (

                self.format_plan_results(

                    agent_results

                )

            )



            if self.shared_memory:



                try:



                    self.shared_memory.set(

                        "final_answer",

                        final_answer

                    )



                except Exception:

                    pass



            return final_answer



        try:



            final_answer = (

                self.final_answer_agent

                .generate_final_answer(

                    original_question,

                    agent_results

                )

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



                except Exception as memory_error:



                    print(

                        "Could not store final answer "

                        f"in shared memory: {memory_error}"

                    )



            return final_answer



        except Exception as error:



            print(

                f"Final Answer Agent error: {error}"

            )



            return self.format_plan_results(

                agent_results

            )



    # =========================================================

    # MAIN RUN METHOD

    # =========================================================