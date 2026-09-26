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







class GraphExecutionMixin:
    """
    Mixin split out of the original monolithic Orchestrator class.
    See orchestrator.py for how this is combined with the other mixins.
    """

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