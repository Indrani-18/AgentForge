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







class ContextMemoryMixin:
    """
    Mixin split out of the original monolithic Orchestrator class.
    See orchestrator.py for how this is combined with the other mixins.
    """

    def build_context(self, question):
        """
        Build context using previous conversation history.
        """

        if not self.memory:
            return question

        try:
            previous_context = self.memory.get_context(limit=10)

            if not previous_context or previous_context == "No previous conversation.":
                return question

            return f"{previous_context}\n\nCurrent Question:\n{question}"

        except Exception as error:
            print(f"Memory context error: {error}")
            return question

    # =========================================================
    # SAVE CONVERSATION
    # =========================================================

    def save_conversation(self, question, answer):
        """
        Save user question and final answer.
        """

        if not self.memory:
            return

        try:
            self.memory.add_user_message(question)
            self.memory.add_assistant_message(answer)

        except Exception as error:
            print(f"Memory save error: {error}")




    # =========================================================

    # SINGLE AGENT EXECUTION

    # =========================================================



    def reset_shared_memory(self, question):

        """

        Start a fresh shared working memory for a new workflow.

        """



        if not self.shared_memory:

            return



        try:



            self.shared_memory.clear()



            self.shared_memory.set(

                "user_question",

                question

            )



            print(

                "Shared Working Memory: RESET"

            )



        except Exception as error:



            print(

                f"Shared memory reset error: {error}"

            )



    # ---------------------------------------------------------



    def store_agent_result(

        self,

        step,

        agent_name,

        task_description,

        result,

        depends_on=None,

        status="completed"

    ):

        """

        Store an agent result in shared working memory.

        """



        if not self.shared_memory:

            return



        try:



            self.shared_memory.save_task_result(

                step=step,

                agent=agent_name,

                task=task_description,

                result=result,

                depends_on=depends_on or [],

                status=status

            )



        except Exception as error:



            print(

                f"Shared memory result error: {error}"

            )



    # ---------------------------------------------------------



    def store_agent_message(

        self,

        sender,

        receiver,

        task,

        content,

        step=None,

        status="completed",

        metadata=None

    ):

        """

        Store structured agent-to-agent communication.

        """



        if not self.shared_memory:

            return None



        try:



            message = AgentMessage(

                sender=sender,

                receiver=receiver,

                task=task,

                content=content,

                step=step,

                status=status,

                metadata=metadata or {}

            )



            stored_message = (

                self.shared_memory.add_message(

                    message

                )

            )



            print(

                f"\n[Agent Message] "

                f"{sender} → {receiver}"

            )



            print(

                f"Task: {task}"

            )



            print(

                f"Step: {step}"

            )



            print(

                f"Status: {status}"

            )



            return stored_message



        except Exception as error:



            print(

                f"Shared memory message error: "

                f"{error}"

            )



            return None



    # ---------------------------------------------------------



    def get_agent_message_context(

        self,

        agent_name

    ):

        """

        Retrieve messages specifically addressed to an agent.

        """



        if not self.shared_memory:

            return "None"



        try:



            messages = (

                self.shared_memory.get_messages(

                    receiver=agent_name

                )

            )



            if not messages:

                return "None"



            context_parts = []



            for message in messages:



                if hasattr(

                    message,

                    "to_dict"

                ):

                    data = message.to_dict()

                elif isinstance(

                    message,

                    dict

                ):

                    data = message

                else:

                    data = {

                        "sender": getattr(

                            message,

                            "sender",

                            "UNKNOWN"

                        ),

                        "task": getattr(

                            message,

                            "task",

                            ""

                        ),

                        "content": getattr(

                            message,

                            "content",

                            ""

                        ),

                        "step": getattr(

                            message,

                            "step",

                            None

                        ),

                        "status": getattr(

                            message,

                            "status",

                            "completed"

                        ),

                    }



                context_parts.append(

                    f"""

From Agent: {data.get('sender')}

Step: {data.get('step')}

Task: {data.get('task')}

Status: {data.get('status')}



Message:

{data.get('content')}

"""

                )



            return "\n".join(

                context_parts

            ).strip()



        except Exception as error:



            print(

                f"Agent message context error: "

                f"{error}"

            )



            return "None"



    # ---------------------------------------------------------



    def get_dependency_context(

        self,

        dependencies

    ):

        """

        Retrieve only the results required by

        the current task.

        """



        if not self.shared_memory:

            return "None"



        if not dependencies:

            return "None"



        try:



            dependency_results = (

                self.shared_memory

                .get_dependency_results(

                    dependencies

                )

            )



            if not dependency_results:

                return "None"



            context = ""



            for item in dependency_results:



                context += (

                    f"\nStep {item['step']} "

                    f"({item['agent']}):\n"

                )



                context += (

                    f"{item['result']}\n"

                )



            return context.strip()



        except Exception as error:



            print(

                f"Dependency memory error: "

                f"{error}"

            )



            return "None"



    # =========================================================

    # PLAN NORMALIZATION

    # =========================================================