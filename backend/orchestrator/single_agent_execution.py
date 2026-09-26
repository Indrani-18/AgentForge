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







class SingleAgentMixin:
    """
    Mixin split out of the original monolithic Orchestrator class.
    See orchestrator.py for how this is combined with the other mixins.
    """

    def execute_single_agent(

        self,

        question,

        agent_name

    ):

        """

        Execute one specialized agent.

        """



        agent_name = (

            str(agent_name)

            .upper()

            .strip()

        )



        try:



            # -------------------------------------------------

            # SQL

            # -------------------------------------------------



            if agent_name == "SQL":



                if not self.sql_agent:

                    return (

                        "SQL Agent is currently unavailable."

                    )



                return self.sql_agent.run(question)



            # -------------------------------------------------

            # CODING

            # -------------------------------------------------



            if agent_name == "CODING":



                if not self.coding_agent:

                    return (

                        "Coding Agent is currently unavailable."

                    )



                return self.coding_agent.run(question)



            # -------------------------------------------------

            # CALCULATOR

            # -------------------------------------------------



            if agent_name == "CALCULATOR":



                return calculator(question)



            # -------------------------------------------------

            # RESEARCH

            # -------------------------------------------------



            if agent_name == "RESEARCH":



                if not self.research_agent:

                    return (

                        "Research Agent is currently unavailable."

                    )



                return self.research_agent.research(

                    question

                )



            # -------------------------------------------------

            # GENERAL

            # -------------------------------------------------



            if agent_name == "GENERAL":



                if not self.research_agent:

                    return (

                        "General response service is unavailable."

                    )



                return self.research_agent.research(

                    question

                )



            return (

                f"Unknown agent selected: {agent_name}"

            )



        except Exception as error:



            print(

                f"{agent_name} Agent execution error: "

                f"{error}"

            )



            return (

                f"{agent_name} Agent encountered an error: "

                f"{str(error)}"

            )



    # =========================================================

    # SHARED MEMORY

    # =========================================================