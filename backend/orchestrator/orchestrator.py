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





class Orchestrator:

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



    def is_sql(self, question):

        """

        Detect whether the question is related to SQL/database

        tasks.

        """



        q = question.lower()



        sql_keywords = [

            "sql",

            "database",

            "table",

            "query",

            "select",

            "insert",

            "update",

            "delete",

            "join",

            "inner join",

            "left join",

            "right join",

            "mysql",

            "postgresql",

            "sqlite",

            "oracle",

            "primary key",

            "foreign key",

            "group by",

            "having",

            "second highest salary",

        ]



        return any(

            keyword in q

            for keyword in sql_keywords

        )



    # ---------------------------------------------------------



    def is_coding(self, question):

        """

        Detect programming/coding questions.

        """



        q = question.lower()



        coding_keywords = [

            "code",

            "coding",

            "program",

            "programming",

            "python",

            "javascript",

            "java",

            "c++",

            "c#",

            "html",

            "css",

            "debug",

            "debugging",

            "bug",

            "error in my code",

            "function",

            "algorithm",

            "data structure",

            "leetcode",

            "implement",

            "implementation",

        ]



        return any(

            keyword in q

            for keyword in coding_keywords

        )



    # ---------------------------------------------------------



    def is_calculation(self, question):

        """

        Detect mathematical/calculation questions.

        """



        q = question.lower()



        calculation_keywords = [

            "calculate",

            "calculation",

            "multiplication",

            "multiply",

            "divide",

            "division",

            "addition",

            "subtract",

            "percentage",

            "percent",

            "average",

            "sum",

        ]



        arithmetic_pattern = (

            r"\d+\s*[+\-*/x×]\s*\d+"

        )



        if re.search(arithmetic_pattern, q):

            return True



        return any(

            keyword in q

            for keyword in calculation_keywords

        )



    # ---------------------------------------------------------



    def is_web_search(self, question):

        """

        Detect questions that require current/recent information.



        ResearchAgent handles these questions.

        """



        q = question.lower()



        web_keywords = [

            "latest",

            "today",

            "current",

            "recent",

            "news",

            "search",

            "this week",

            "this month",

            "now",

            "2026",

        ]



        return any(

            keyword in q

            for keyword in web_keywords

        )



    # =========================================================

    # PLANNER DETECTION

    # =========================================================



    def should_use_planner(self, question):

        """

        Determine whether the question requires multiple steps

        or multiple specialized agents.

        """



        q = question.lower()



        multi_step_patterns = [

            "and then",

            "and also",

            "also calculate",

            "then calculate",

            "then write",

            "then create",

            "then generate",

            "research and",

            "analyze and",

            "compare and",

            "find and calculate",

            "explain and calculate",

            "research and calculate",

            "calculate and explain",

            "research and create",

            "research and write",

            "research and implement",

            "analyze and create",

            "explain and implement",

        ]



        return any(

            pattern in q

            for pattern in multi_step_patterns

        )



    # =========================================================

    # AGENT SELECTION

    # =========================================================



    def select_agent(self, question):

        """

        Select the appropriate single agent.



        Priority:

            SQL

            Coding

            Calculator

            Research

            General

        """



        if self.is_sql(question):

            return "SQL"



        if self.is_coding(question):

            return "CODING"



        if self.is_calculation(question):

            return "CALCULATOR"



        if self.is_web_search(question):

            return "RESEARCH"



        return "GENERAL"



    # =========================================================

    # CONTEXT

    # =========================================================



    def build_context(self, question):

        """

        Build context using previous conversation history.

        """



        if not self.memory:

            return question



        try:

            previous_messages = (

                self.memory.get_recent_messages(

                    limit=10

                )

            )



            if not previous_messages:

                return question



            context = ""



            for message in previous_messages:

                context += f"{message}\n"



            context += (

                f"\nCurrent Question:\n{question}"

            )



            return context



        except Exception as error:



            print(

                f"Memory context error: {error}"

            )



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



            self.memory.add_message(

                role="user",

                content=question

            )



            self.memory.add_message(

                role="assistant",

                content=answer

            )



        except Exception as error:



            print(

                f"Memory save error: {error}"

            )



    # =========================================================

    # SINGLE AGENT EXECUTION

    # =========================================================



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



    def _normalize_plan_tasks(self, plan):

        """

        Normalize and validate planner tasks.



        Returns:

            list of normalized tasks

        """



        if not isinstance(plan, dict):

            raise ValueError(

                "Planner output must be a dictionary."

            )



        raw_tasks = plan.get(

            "tasks",

            []

        )



        if not isinstance(

            raw_tasks,

            list

        ):

            raise ValueError(

                "Planner tasks must be a list."

            )



        normalized_tasks = []



        used_steps = set()



        for index, raw_task in enumerate(

            raw_tasks,

            start=1

        ):



            if not isinstance(

                raw_task,

                dict

            ):

                continue



            step = raw_task.get(

                "step",

                index

            )



            try:

                step = int(step)

            except Exception:

                step = index



            if step <= 0:

                step = index



            while step in used_steps:

                step += 1



            used_steps.add(step)



            agent_name = str(

                raw_task.get(

                    "agent",

                    "GENERAL"

                )

            ).upper().strip()



            if agent_name not in self.VALID_AGENTS:

                agent_name = "GENERAL"



            task_description = str(

                raw_task.get(

                    "task",

                    ""

                )

            ).strip()



            if not task_description:

                task_description = (

                    "Complete the assigned task."

                )



            dependencies = raw_task.get(

                "depends_on",

                []

            )



            if not isinstance(

                dependencies,

                list

            ):

                dependencies = []



            clean_dependencies = []



            for dependency in dependencies:



                try:

                    dependency = int(

                        dependency

                    )

                except Exception:

                    continue



                if (

                    dependency > 0

                    and dependency != step

                    and dependency < step

                ):

                    clean_dependencies.append(

                        dependency

                    )



            clean_dependencies = list(

                dict.fromkeys(

                    clean_dependencies

                )

            )



            normalized_tasks.append(

                {

                    "step": step,

                    "agent": agent_name,

                    "task": task_description,

                    "depends_on": clean_dependencies,

                }

            )



        normalized_tasks.sort(

            key=lambda item: item["step"]

        )



        if not normalized_tasks:

            raise ValueError(

                "Planner generated no executable tasks."

            )



        return normalized_tasks



    # =========================================================

    # GRAPH WORKFLOW EXECUTION

    # =========================================================



    def execute_graph_workflow(

        self,

        original_question,

        plan

    ):

        """

        Execute a planner-generated workflow using:



            Planner

                ↓

            WorkflowGraph

                ↓

            GraphExecutor

                ↓

            Specialized Agents

                ↓

            Shared Working Memory

                ↓

            AgentMessages

                ↓

            Final Answer Agent



        Independent nodes can execute in parallel.



        Dependent nodes execute only after their

        dependency nodes complete.

        """



        print("\n========================================")

        print("GRAPH WORKFLOW EXECUTION")

        print("========================================")



        # -----------------------------------------------------

        # Normalize planner tasks

        # -----------------------------------------------------



        tasks = self._normalize_plan_tasks(

            plan

        )



        normalized_plan = {

            "is_complex": True,

            "tasks": tasks

        }



        # -----------------------------------------------------

        # Store plan

        # -----------------------------------------------------



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



        # -----------------------------------------------------

        # Build workflow graph

        # -----------------------------------------------------



        graph = WorkflowGraph.from_plan(

            tasks

        )



        print("\nWORKFLOW GRAPH")

        print("----------------------------------------")



        try:

            graph.display_ascii()

        except Exception:

            try:

                graph.display()

            except Exception as error:

                print(

                    f"Graph display error: {error}"

                )



        # -----------------------------------------------------

        # Store graph information

        # -----------------------------------------------------



        if self.shared_memory:



            try:



                self.shared_memory.set(

                    "workflow_graph",

                    {

                        "nodes": graph.nodes,

                        "edges": graph.edges,

                        "dependencies": graph.dependencies,

                    }

                )



            except Exception as error:



                print(

                    "Could not store workflow graph: "

                    f"{error}"

                )



        # -----------------------------------------------------

        # Task lookup

        # -----------------------------------------------------



        task_by_step = {

            task["step"]: task

            for task in tasks

        }



        # -----------------------------------------------------

        # Node execution function

        # -----------------------------------------------------



        def execute_node(node_id):

            """

            Execute one graph node.



            IMPORTANT:

            Results are stored here before the node returns.

            This allows the next dependency wave to read

            Shared Working Memory.

            """



            node = graph.get_node(

                node_id

            )



            if not node:

                return {

                    "node_id": node_id,

                    "status": "failed",

                    "result": (

                        f"Unknown graph node: "

                        f"{node_id}"

                    )

                }



            step = node.get(

                "step"

            )



            agent_name = str(

                node.get(

                    "agent",

                    "GENERAL"

                )

            ).upper()



            task_description = node.get(

                "task",

                ""

            )



            dependencies = graph.get_dependencies(

                node_id

            )



            dependency_steps = []



            for dependency_node in dependencies:



                dependency_node_data = (

                    graph.get_node(

                        dependency_node

                    )

                )



                if dependency_node_data:



                    dependency_step = (

                        dependency_node_data.get(

                            "step"

                        )

                    )



                    if dependency_step is not None:

                        dependency_steps.append(

                            int(dependency_step)

                        )



            print("\n----------------------------------------")

            print(

                f"EXECUTING GRAPH NODE: {node_id}"

            )

            print(

                f"STEP: {step}"

            )

            print(

                f"AGENT: {agent_name}"

            )

            print(

                f"TASK: {task_description}"

            )

            print(

                f"DEPENDS ON: {dependency_steps}"

            )

            print("----------------------------------------")



            # -------------------------------------------------

            # Dependency context

            # -------------------------------------------------



            dependency_context = (

                self.get_dependency_context(

                    dependency_steps

                )

            )



            # -------------------------------------------------

            # Agent message context

            # -------------------------------------------------



            message_context = (

                self.get_agent_message_context(

                    agent_name

                )

            )



            # -------------------------------------------------

            # Build task input

            # -------------------------------------------------



            if agent_name == "CALCULATOR":



                task_input = task_description



            else:



                task_input = f"""

Original User Question:



{original_question}





Current Task:



{task_description}





Current Step:



{step}





Current Agent:



{agent_name}





Dependencies:



{dependency_steps}





Required Dependency Results:



{dependency_context}





Messages From Other Agents:



{message_context}





Instructions:



1\. Complete the current task.

2\. Use dependency results when relevant.

3\. Use messages from other agents when relevant.

4\. Do not ignore information produced by dependency tasks.

5\. Do not unnecessarily repeat completed dependency work.

6\. Focus primarily on the current task.

7\. Produce a useful result that can be passed to the next agent.

"""



            # -------------------------------------------------

            # Execute agent

            # -------------------------------------------------



            try:



                result = self.execute_single_agent(

                    task_input,

                    agent_name

                )



                status = "completed"



            except Exception as error:



                result = (

                    f"{agent_name} Agent encountered "

                    f"an error: {str(error)}"

                )



                status = "failed"



                print(

                    f"{agent_name} execution failed: "

                    f"{error}"

                )



            # -------------------------------------------------

            # Store result immediately

            # -------------------------------------------------



            self.store_agent_result(

                step=step,

                agent_name=agent_name,

                task_description=task_description,

                result=result,

                depends_on=dependency_steps,

                status=status

            )



            # -------------------------------------------------

            # Determine downstream nodes

            # -------------------------------------------------



            downstream_nodes = graph.get_dependents(

                node_id

            )



            if downstream_nodes:



                for downstream_node in (

                    downstream_nodes

                ):



                    downstream_data = (

                        graph.get_node(

                            downstream_node

                        )

                    )



                    if not downstream_data:

                        continue



                    downstream_step = (

                        downstream_data.get(

                            "step"

                        )

                    )



                    downstream_agent = (

                        downstream_data.get(

                            "agent",

                            "GENERAL"

                        )

                    )



                    self.store_agent_message(

                        sender=agent_name,

                        receiver=str(

                            downstream_agent

                        ).upper(),

                        task=(

                            f"Result from Step "

                            f"{step} for Step "

                            f"{downstream_step}"

                        ),

                        content=result,

                        step=step,

                        status=status,

                        metadata={

                            "source_step": step,

                            "target_step": downstream_step,

                            "dependency_for": downstream_step,

                            "source_node": node_id,

                            "target_node": downstream_node,

                        }

                    )



            else:



                # -------------------------------------------------

                # Terminal node sends result to final answer

                # -------------------------------------------------



                self.store_agent_message(

                    sender=agent_name,

                    receiver="FINAL_ANSWER",

                    task=(

                        f"Final workflow result "

                        f"from Step {step}"

                    ),

                    content=result,

                    step=step,

                    status=status,

                    metadata={

                        "source_step": step,

                        "final_result": True,

                        "source_node": node_id,

                    }

                )



            print(

                f"GRAPH NODE {node_id} "

                f"COMPLETED WITH STATUS: {status}"

            )



            return {

                "node_id": node_id,

                "step": step,

                "agent": agent_name,

                "task": task_description,

                "depends_on": dependency_steps,

                "result": result,

                "status": status,

            }



        # -----------------------------------------------------

        # Execute graph

        # -----------------------------------------------------



        executor = GraphExecutor(

            graph=graph,

            execute_node=execute_node,

            max_workers=self.MAX_WORKERS,
            max_retries=2

        )



        try:



            graph_results = executor.execute()



        except Exception as error:



            print(

                f"Graph execution error: {error}"

            )



            return []
        # -----------------------------------------------------
        # Convert GraphExecutor results into AgentForge format
        # -----------------------------------------------------

        final_results = []

        execution_status = "completed"
        retry_history = {}
        raw_results = {}

        if isinstance(graph_results, dict):
            execution_status = graph_results.get(
                "status",
                "completed"
            )
            retry_history = graph_results.get(
                "retry_history",
                {}
            )
            raw_results = graph_results.get(
                "results",
                {}
            )

        elif isinstance(graph_results, list):
            raw_results = graph_results

        if self.shared_memory:
            try:
                self.shared_memory.set(
                    "workflow_status",
                    execution_status
                )
                self.shared_memory.set(
                    "retry_history",
                    retry_history
                )
            except Exception as error:
                print(
                    "Could not store workflow execution "
                    f"metadata: {error}"
                )

        if isinstance(raw_results, dict):
            iterable_results = raw_results.values()
        elif isinstance(raw_results, list):
            iterable_results = raw_results
        else:
            iterable_results = []





        for item in iterable_results:



            if not isinstance(

                item,

                dict

            ):

                continue



            node_id = item.get(

                "node_id"

            )



            step = item.get(

                "step"

            )



            agent_name = item.get(

                "agent"

            )



            task_description = item.get(

                "task"

            )



            result = item.get(

                "result",

                ""

            )



            status = item.get(

                "status",

                "completed"

            )



            # ---------------------------------------------

            # If GraphExecutor only returns node_id,

            # recover information from graph.

            # ---------------------------------------------



            if node_id and (

                step is None

                or agent_name is None

                or task_description is None

            ):



                node = graph.get_node(

                    node_id

                )



                if node:



                    if step is None:

                        step = node.get(

                            "step"

                        )



                    if agent_name is None:

                        agent_name = node.get(

                            "agent",

                            "GENERAL"

                        )



                    if task_description is None:

                        task_description = node.get(

                            "task",

                            ""

                        )



            if step is None:

                continue



            if agent_name is None:

                agent_name = "GENERAL"



            if task_description is None:

                task_description = ""



            dependencies = []



            if node_id:



                dependency_nodes = (

                    graph.get_dependencies(

                        node_id

                    )

                )



                for dependency_node in (

                    dependency_nodes

                ):



                    dependency_data = (

                        graph.get_node(

                            dependency_node

                        )

                    )



                    if dependency_data:



                        dependency_step = (

                            dependency_data.get(

                                "step"

                            )

                        )



                        if dependency_step is not None:

                            dependencies.append(

                                int(

                                    dependency_step

                                )

                            )



            final_results.append(

                {

                    "step": int(step),

                    "agent": str(

                        agent_name

                    ).upper(),

                    "task": task_description,

                    "depends_on": dependencies,

                    "result": result,

                    "status": status,

                }

            )



        # -----------------------------------------------------

        # Sort by step

        # -----------------------------------------------------



        final_results.sort(

            key=lambda item: item["step"]

        )



        # -----------------------------------------------------

        # Fallback:

        # If GraphExecutor returned nothing, recover results

        # from Shared Working Memory.

        # -----------------------------------------------------



        if not final_results and self.shared_memory:



            try:



                memory_results = (

                    self.shared_memory

                    .get_all_task_results()

                )



                if memory_results:



                    final_results = list(

                        memory_results

                    )



                    final_results.sort(

                        key=lambda item: item.get(

                            "step",

                            0

                        )

                    )



            except Exception as error:



                print(

                    "Could not recover graph results "

                    f"from shared memory: {error}"

                )



        # -----------------------------------------------------

        # Store execution results

        # -----------------------------------------------------



        if self.shared_memory:



            try:



                self.shared_memory.set(

                    "graph_execution_results",

                    final_results

                )



            except Exception as error:



                print(

                    "Could not store graph execution "

                    f"results: {error}"

                )



        print("\n========================================")

        print("GRAPH WORKFLOW COMPLETE")

        print("========================================")



        for item in final_results:



            print(

                f"Step {item['step']} | "

                f"{item['agent']} | "

                f"{item['status']}"

            )



        return final_results



    # =========================================================

    # LEGACY PLAN EXECUTION

    # =========================================================



    def execute_plan(

        self,

        original_question,

        plan

    ):

        """

        Compatibility wrapper.



        Older code may still call execute_plan().

        The new architecture uses execute_graph_workflow().

        """



        return self.execute_graph_workflow(

            original_question,

            plan

        )



    # =========================================================

    # FORMAT PLAN RESULTS

    # =========================================================



    def format_plan_results(self, results):

        """

        Fallback formatter when Final Answer Agent

        is unavailable.

        """



        output = (

            "AgentForge completed the planned "

            "workflow.\n"

        )



        output += "\n"



        for item in results:



            output += (

                f"Step {item.get('step')} "

                f"({item.get('agent')}):\n"

            )



            output += (

                f"{item.get('result')}\n\n"

            )



        return output.strip()



    # =========================================================

    # FINAL ANSWER GENERATION

    # =========================================================



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

                    context_question,

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