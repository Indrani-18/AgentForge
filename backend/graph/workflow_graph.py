from typing import Dict, List, Set, Any


class WorkflowGraph:
    """
    Represents the workflow of AgentForge.

    Nodes:
        Agents/tasks in the workflow.

    Edges:
        Dependencies between tasks.

    Example:

        RESEARCH → CODING

    means CODING must wait for RESEARCH.
    """

    def __init__(self):
        # Node information
        self.nodes: Dict[str, Dict[str, Any]] = {}

        # Directed edges:
        # source -> list of destination nodes
        self.edges: Dict[str, List[str]] = {}

        # Reverse edges:
        # destination -> list of source nodes
        self.dependencies: Dict[str, List[str]] = {}

    # =========================================================
    # ADD NODE
    # =========================================================

    def add_node(
        self,
        node_id: str,
        agent: str = None,
        task: str = "",
        step: int = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Add an agent/task node to the workflow.
        """

        node_id = str(node_id)

        if node_id not in self.nodes:

            self.nodes[node_id] = {
                "id": node_id,
                "agent": agent or node_id,
                "task": task,
                "step": step,
                "metadata": metadata or {}
            }

            self.edges[node_id] = []
            self.dependencies[node_id] = []

        else:

            # Update existing node information
            if agent is not None:
                self.nodes[node_id]["agent"] = agent

            if task:
                self.nodes[node_id]["task"] = task

            if step is not None:
                self.nodes[node_id]["step"] = step

            if metadata:
                self.nodes[node_id]["metadata"].update(
                    metadata
                )

    # =========================================================
    # ADD EDGE
    # =========================================================

    def add_edge(
        self,
        source: str,
        destination: str
    ):
        """
        Create a dependency:

            source → destination

        Destination depends on source.
        """

        source = str(source)
        destination = str(destination)

        # Automatically create missing nodes
        if source not in self.nodes:
            self.add_node(source)

        if destination not in self.nodes:
            self.add_node(destination)

        # Prevent duplicate edges
        if destination not in self.edges[source]:

            self.edges[source].append(
                destination
            )

        if source not in self.dependencies[destination]:

            self.dependencies[destination].append(
                source
            )

    # =========================================================
    # GET NODE
    # =========================================================

    def get_node(
        self,
        node_id: str
    ):
        """
        Return information about a node.
        """

        return self.nodes.get(
            str(node_id)
        )

    # =========================================================
    # GET DEPENDENCIES
    # =========================================================

    def get_dependencies(
        self,
        node_id: str
    ) -> List[str]:
        """
        Return nodes that must finish before
        this node can execute.
        """

        return self.dependencies.get(
            str(node_id),
            []
        )

    # =========================================================
    # GET DEPENDENTS
    # =========================================================

    def get_dependents(
        self,
        node_id: str
    ) -> List[str]:
        """
        Return nodes that depend on this node.
        """

        return self.edges.get(
            str(node_id),
            []
        )

    # =========================================================
    # READY NODES
    # =========================================================

    def get_ready_nodes(
        self,
        completed: Set[str],
        running: Set[str] = None
    ) -> List[str]:
        """
        Find nodes whose dependencies have all completed.

        Example:

            RESEARCH → CODING

        If RESEARCH is completed,
        CODING becomes ready.
        """

        running = running or set()

        ready = []

        for node_id in self.nodes:

            # Already completed/running
            if node_id in completed:
                continue

            if node_id in running:
                continue

            required = set(
                self.dependencies.get(
                    node_id,
                    []
                )
            )

            if required.issubset(
                completed
            ):
                ready.append(node_id)

        return ready

    # =========================================================
    # TOPOLOGICAL ORDER
    # =========================================================

    def topological_sort(self) -> List[str]:
        """
        Return nodes in dependency order.

        Raises ValueError if a cycle exists.
        """

        in_degree = {
            node_id: len(
                self.dependencies.get(
                    node_id,
                    []
                )
            )
            for node_id in self.nodes
        }

        queue = [
            node_id
            for node_id, degree in in_degree.items()
            if degree == 0
        ]

        result = []

        while queue:

            current = queue.pop(0)

            result.append(current)

            for dependent in self.edges.get(
                current,
                []
            ):

                in_degree[dependent] -= 1

                if in_degree[dependent] == 0:

                    queue.append(
                        dependent
                    )

        if len(result) != len(
            self.nodes
        ):

            raise ValueError(
                "Workflow graph contains a cycle."
            )

        return result

    # =========================================================
    # VALIDATE GRAPH
    # =========================================================

    def validate(self):
        """
        Validate the workflow graph.

        Returns:
            True if valid.

        Raises:
            ValueError if invalid.
        """

        # Ensure all edge destinations exist
        for source, destinations in (
            self.edges.items()
        ):

            if source not in self.nodes:
                raise ValueError(
                    f"Unknown source node: {source}"
                )

            for destination in destinations:

                if destination not in self.nodes:

                    raise ValueError(
                        f"Unknown destination node: "
                        f"{destination}"
                    )

        # Detect cycles
        self.topological_sort()

        return True

    # =========================================================
    # BUILD FROM PLAN
    # =========================================================

    @classmethod
    def from_plan(
        cls,
        tasks: List[Dict[str, Any]]
    ):
        """
        Build a WorkflowGraph from the planner's task list.

        Example task:

        {
            "step": 2,
            "agent": "CODING",
            "task": "Implement merge sort",
            "depends_on": [1]
        }
        """

        graph = cls()

        step_to_node = {}

        # -----------------------------------------------------
        # Create nodes
        # -----------------------------------------------------

        for task in tasks:

            step = task.get(
                "step"
            )

            if step is None:
                continue

            node_id = f"step_{step}"

            step_to_node[step] = node_id

            graph.add_node(
                node_id=node_id,
                agent=task.get(
                    "agent",
                    "GENERAL"
                ),
                task=task.get(
                    "task",
                    ""
                ),
                step=step,
                metadata={
                    "depends_on": task.get(
                        "depends_on",
                        []
                    )
                }
            )

        # -----------------------------------------------------
        # Create dependency edges
        # -----------------------------------------------------

        for task in tasks:

            step = task.get(
                "step"
            )

            if step not in step_to_node:
                continue

            current_node = step_to_node[
                step
            ]

            dependencies = task.get(
                "depends_on",
                []
            )

            for dependency in dependencies:

                if dependency in step_to_node:

                    dependency_node = (
                        step_to_node[
                            dependency
                        ]
                    )

                    graph.add_edge(
                        dependency_node,
                        current_node
                    )

        graph.validate()

        return graph

    # =========================================================
    # DISPLAY GRAPH
    # =========================================================

    def display(self):
        """
        Print a human-readable workflow graph.
        """

        print("\n")
        print("=" * 70)
        print("AGENTFORGE WORKFLOW GRAPH")
        print("=" * 70)

        if not self.nodes:

            print("Graph is empty.")

            return

        ordered_nodes = (
            self.topological_sort()
        )

        for node_id in ordered_nodes:

            node = self.nodes[
                node_id
            ]

            agent = node.get(
                "agent",
                node_id
            )

            task = node.get(
                "task",
                ""
            )

            dependencies = (
                self.dependencies.get(
                    node_id,
                    []
                )
            )

            dependents = (
                self.edges.get(
                    node_id,
                    []
                )
            )

            print(
                f"\n{node_id}"
            )

            print(
                f"  Agent: {agent}"
            )

            print(
                f"  Task: {task}"
            )

            print(
                f"  Depends On: "
                f"{dependencies}"
            )

            print(
                f"  Leads To: "
                f"{dependents}"
            )

        print("\n" + "=" * 70)

    # =========================================================
    # DISPLAY ASCII GRAPH
    # =========================================================

    def display_ascii(self):
        """
        Display a simple ASCII representation.
        """

        print("\nWorkflow:")

        ordered_nodes = (
            self.topological_sort()
        )

        if not ordered_nodes:

            print("Empty")

            return

        for index, node_id in enumerate(
            ordered_nodes
        ):

            node = self.nodes[
                node_id
            ]

            agent = node.get(
                "agent",
                node_id
            )

            print(
                f"[{agent}]"
            )

            if index < len(
                ordered_nodes
            ) - 1:

                print(
                    "    ↓"
                )


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 70)
    print("WORKFLOW GRAPH TEST")
    print("=" * 70)

    tasks = [
        {
            "step": 1,
            "agent": "RESEARCH",
            "task": "Research merge sort",
            "depends_on": []
        },
        {
            "step": 2,
            "agent": "SQL",
            "task": "Analyze database requirements",
            "depends_on": []
        },
        {
            "step": 3,
            "agent": "CODING",
            "task": "Implement merge sort",
            "depends_on": [1]
        },
        {
            "step": 4,
            "agent": "GENERAL",
            "task": "Combine research and SQL results",
            "depends_on": [2, 3]
        }
    ]

    graph = WorkflowGraph.from_plan(
        tasks
    )

    graph.display()

    graph.display_ascii()

    print("\nTopological Order:")

    print(
        graph.topological_sort()
    )

    print("\nInitially Ready Nodes:")

    print(
        graph.get_ready_nodes(
            completed=set()
        )
    )

    print("\nAfter Step 1 Completion:")

    print(
        graph.get_ready_nodes(
            completed={
                "step_1"
            }
        )
    )

    print("\nGraph Validation:")

    print(
        graph.validate()
    )

    print("\nWorkflow Graph Test Complete.")