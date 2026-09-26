from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict

from backend.graph.workflow_graph import WorkflowGraph
from backend.workflow.retry_manager import RetryManager


class GraphExecutor:
    """
    Executes a WorkflowGraph.

    Features:
    - Dependency-aware execution
    - Parallel execution of independent nodes
    - Automatic retry of failed nodes
    - Blocks dependent nodes when a required dependency fails
    - Retry history tracking
    """

    MAX_WORKERS = 5
    DEFAULT_MAX_RETRIES = 2

    def __init__(
        self,
        graph: WorkflowGraph,
        execute_node: Callable[[str], Any],
        max_workers: int = MAX_WORKERS,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.graph = graph
        self.execute_node = execute_node

        self.max_workers = max(1, int(max_workers))
        self.max_retries = max(0, int(max_retries))

        # Execution state
        self.results: Dict[str, Any] = {}
        self.completed_nodes = set()
        self.failed_nodes = set()
        self.blocked_nodes = set()

        # Retry manager
        self.retry_manager = RetryManager(
            max_retries=self.max_retries
        )

    # ==========================================================
    # SINGLE NODE EXECUTION WITH RETRY
    # ==========================================================

    def _execute_single_node(self, node_id: str):
        """
        Execute one graph node.

        A failed node is automatically retried according to
        max_retries.
        """

        node = self.graph.get_node(node_id)

        if node is None:
            return {
                "status": "failed",
                "error": f"Node '{node_id}' not found.",
            }

        step = node.get("step")
        agent = node.get("agent", "UNKNOWN")

        # Create retry record
        self.retry_manager.create_record(
            step=step,
            agent=agent,
        )

        while True:

            # Start an attempt
            record = self.retry_manager.start_attempt(
                step=step,
                agent=agent,
            )

            attempt_number = record.attempts

            print(
                f"\n[GRAPH] Executing {node_id} "
                f"(Agent: {agent}, Attempt: {attempt_number})"
            )

            try:

                # Execute actual agent
                result = self.execute_node(node_id)

                # --------------------------------------------------
                # Check result status
                # --------------------------------------------------

                failed = False
                error_message = None

                if isinstance(result, dict):

                    status = str(
                        result.get("status", "")
                    ).lower()

                    if status in {
                        "failed",
                        "failure",
                        "error",
                    }:
                        failed = True

                        error_message = result.get(
                            "error",
                            "Agent execution failed.",
                        )

                # --------------------------------------------------
                # SUCCESS
                # --------------------------------------------------

                if not failed:

                    self.retry_manager.mark_success(
                        step=step
                    )

                    print(
                        f"[GRAPH] {node_id} completed "
                        f"successfully on attempt "
                        f"{attempt_number}."
                    )

                    return result

                # --------------------------------------------------
                # FAILURE
                # --------------------------------------------------

                self.retry_manager.mark_failure(
                    step=step,
                    error=error_message,
                )

                # --------------------------------------------------
                # RETRY
                # --------------------------------------------------

                if self.retry_manager.should_retry(step):

                    print(
                        f"[GRAPH] {node_id} failed."
                    )

                    print(
                        f"[GRAPH] Retrying "
                        f"{node_id}..."
                    )

                    continue

                # --------------------------------------------------
                # FINAL FAILURE
                # --------------------------------------------------

                print(
                    f"[GRAPH] {node_id} failed after "
                    f"{attempt_number} attempts."
                )

                return result

            except Exception as error:

                # Record unexpected exception
                self.retry_manager.mark_failure(
                    step=step,
                    error=str(error),
                )

                # Retry if allowed
                if self.retry_manager.should_retry(step):

                    print(
                        f"[GRAPH] {node_id} raised an "
                        f"exception."
                    )

                    print(
                        f"[GRAPH] Retrying "
                        f"{node_id}..."
                    )

                    continue

                # No retries remaining
                print(
                    f"[GRAPH] {node_id} failed after "
                    f"{attempt_number} attempts."
                )

                return {
                    "status": "failed",
                    "error": str(error),
                    "step": step,
                    "agent": agent,
                }

    # ==========================================================
    # FIND BLOCKED NODES
    # ==========================================================

    def _find_blocked_nodes(self):
        """
        Find nodes whose dependencies have failed or
        have already been blocked.
        """

        newly_blocked = []

        for node_id in self.graph.nodes:

            # Already finished
            if node_id in self.completed_nodes:
                continue

            # Already failed
            if node_id in self.failed_nodes:
                continue

            # Already blocked
            if node_id in self.blocked_nodes:
                continue

            dependencies = self.graph.get_dependencies(
                node_id
            )

            for dependency in dependencies:

                if (
                    dependency in self.failed_nodes
                    or dependency in self.blocked_nodes
                ):

                    self.blocked_nodes.add(
                        node_id
                    )

                    newly_blocked.append(
                        node_id
                    )

                    print(
                        f"[GRAPH] {node_id} blocked "
                        f"because dependency "
                        f"'{dependency}' failed."
                    )

                    break

        return newly_blocked

    # ==========================================================
    # EXECUTE GRAPH
    # ==========================================================

    def execute(self):
        """
        Execute the complete workflow graph.

        Independent nodes can run in parallel.

        Dependent nodes wait until all their dependencies
        have completed successfully.
        """

        print("\n========================================")
        print("GRAPH EXECUTOR STARTED")
        print("========================================")

        # ======================================================
        # GRAPH VALIDATION
        # ======================================================

        validation_result = self.graph.validate()

        # Your current WorkflowGraph.validate()
        # returns True or False.

        if validation_result is False:

            print("\nGraph validation failed.")

            return {
                "status": "failed",
                "error": "Invalid workflow graph.",
                "validation_errors": True,
                "results": {},
                "completed_nodes": [],
                "failed_nodes": [],
                "blocked_nodes": [],
                "retry_history": {},
            }

        # ======================================================
        # DISPLAY GRAPH
        # ======================================================

        try:
            self.graph.display_ascii()
        except Exception:
            pass

        # ======================================================
        # MAIN EXECUTION LOOP
        # ======================================================

        while True:

            # --------------------------------------------------
            # Find blocked nodes
            # --------------------------------------------------

            self._find_blocked_nodes()

            # --------------------------------------------------
            # Find ready nodes
            # --------------------------------------------------

            ready_nodes = self.graph.get_ready_nodes(
                completed=self.completed_nodes,
                running=set(),
            )

            # --------------------------------------------------
            # Remove nodes that cannot run
            # --------------------------------------------------

            ready_nodes = [
                node_id
                for node_id in ready_nodes
                if node_id not in self.blocked_nodes
                and node_id not in self.failed_nodes
                and node_id not in self.completed_nodes
            ]

            # --------------------------------------------------
            # Nothing ready
            # --------------------------------------------------

            if not ready_nodes:

                total_nodes = len(
                    self.graph.nodes
                )

                finished_nodes = (
                    len(self.completed_nodes)
                    + len(self.failed_nodes)
                    + len(self.blocked_nodes)
                )

                # Everything finished
                if finished_nodes >= total_nodes:
                    break

                # Prevent infinite loop
                print(
                    "\n[GRAPH] No nodes are ready "
                    "and workflow cannot continue."
                )

                break

            print(
                f"\n[GRAPH] Ready nodes: "
                f"{ready_nodes}"
            )

            # ==================================================
            # PARALLEL EXECUTION
            # ==================================================

            with ThreadPoolExecutor(
                max_workers=self.max_workers
            ) as executor:

                future_to_node = {
                    executor.submit(
                        self._execute_single_node,
                        node_id,
                    ): node_id
                    for node_id in ready_nodes
                }

                for future in as_completed(
                    future_to_node
                ):

                    node_id = future_to_node[
                        future
                    ]

                    try:

                        result = future.result()

                        self.results[
                            node_id
                        ] = result

                        # --------------------------------------------------
                        # Determine final node status
                        # --------------------------------------------------

                        if isinstance(
                            result,
                            dict,
                        ):

                            status = str(
                                result.get(
                                    "status",
                                    "",
                                )
                            ).lower()

                            if status in {
                                "failed",
                                "failure",
                                "error",
                            }:

                                self.failed_nodes.add(
                                    node_id
                                )

                            else:

                                self.completed_nodes.add(
                                    node_id
                                )

                        else:

                            # Non-dict results are considered successful
                            self.completed_nodes.add(
                                node_id
                            )

                    except Exception as error:

                        print(
                            f"[GRAPH] Unexpected error "
                            f"in {node_id}: {error}"
                        )

                        self.results[
                            node_id
                        ] = {
                            "status": "failed",
                            "error": str(error),
                        }

                        self.failed_nodes.add(
                            node_id
                        )

            # ==================================================
            # PROGRESS
            # ==================================================

            print(
                "\n[GRAPH] Current progress:"
            )

            print(
                f"Completed: "
                f"{list(self.completed_nodes)}"
            )

            print(
                f"Failed: "
                f"{list(self.failed_nodes)}"
            )

            print(
                f"Blocked: "
                f"{list(self.blocked_nodes)}"
            )

        # ======================================================
        # FINAL WORKFLOW STATUS
        # ======================================================

        if self.failed_nodes:

            workflow_status = "failed"

        elif self.blocked_nodes:

            workflow_status = "partial"

        else:

            workflow_status = "completed"

        # ======================================================
        # FINAL SUMMARY
        # ======================================================

        print("\n========================================")
        print("GRAPH EXECUTOR FINISHED")
        print("========================================")

        print(
            f"Status: {workflow_status}"
        )

        print(
            f"Completed: "
            f"{len(self.completed_nodes)}"
        )

        print(
            f"Failed: "
            f"{len(self.failed_nodes)}"
        )

        print(
            f"Blocked: "
            f"{len(self.blocked_nodes)}"
        )

        return {
            "status": workflow_status,
            "results": self.results,
            "completed_nodes": list(
                self.completed_nodes
            ),
            "failed_nodes": list(
                self.failed_nodes
            ),
            "blocked_nodes": list(
                self.blocked_nodes
            ),
            "retry_history": (
                self.retry_manager
                .get_all_records()
            ),
        }

    # ==========================================================
    # RESULT HELPERS
    # ==========================================================

    def get_result(self, node_id: str):
        """Return the result of one node."""

        return self.results.get(
            node_id
        )

    def get_results(self):
        """Return all node results."""

        return self.results

    def get_retry_history(self):
        """Return retry history."""

        return (
            self.retry_manager
            .get_all_records()
        )

    # ==========================================================
    # PRINT RESULTS
    # ==========================================================

    def print_results(self):

        print("\n========================================")
        print("GRAPH RESULTS")
        print("========================================")

        if not self.results:

            print("No results.")

        else:

            for node_id, result in (
                self.results.items()
            ):

                print(
                    f"\nNode: {node_id}"
                )

                print(
                    "-" * 40
                )

                print(result)

        # ------------------------------------------------------
        # Retry history
        # ------------------------------------------------------

        print(
            "\n========================================"
        )

        print("RETRY HISTORY")

        print(
            "========================================"
        )

        self.retry_manager.print_status()


# ==============================================================
# STANDALONE TEST
# ==============================================================

if __name__ == "__main__":

    print("GraphExecutor Retry Test")
    print("========================")

    # ----------------------------------------------------------
    # Test workflow
    # ----------------------------------------------------------

    tasks = [
        {
            "step": 1,
            "agent": "RESEARCH",
            "task": "Research merge sort",
            "depends_on": [],
        },
        {
            "step": 2,
            "agent": "SQL",
            "task": "Analyze database requirements",
            "depends_on": [],
        },
        {
            "step": 3,
            "agent": "CODING",
            "task": "Implement merge sort",
            "depends_on": [1],
        },
        {
            "step": 4,
            "agent": "GENERAL",
            "task": "Combine research and SQL results",
            "depends_on": [2, 3],
        },
    ]

    # ----------------------------------------------------------
    # Create graph
    # ----------------------------------------------------------

    graph = WorkflowGraph.from_plan(
        tasks
    )

    # ----------------------------------------------------------
    # Fake agent attempt counter
    # ----------------------------------------------------------

    attempt_counter = {}

    # ----------------------------------------------------------
    # Fake node execution
    # ----------------------------------------------------------

    def fake_execute_node(node_id):

        attempt_counter[node_id] = (
            attempt_counter.get(
                node_id,
                0,
            )
            + 1
        )

        attempt = attempt_counter[
            node_id
        ]

        print(
            f"[FAKE AGENT] "
            f"{node_id} attempt "
            f"{attempt}"
        )

        # ----------------------------------------------
        # Simulate temporary failure
        # ----------------------------------------------

        if (
            node_id == "step_1"
            and attempt < 3
        ):

            return {
                "status": "failed",
                "error": "Temporary test failure",
            }

        # ----------------------------------------------
        # Successful execution
        # ----------------------------------------------

        return {
            "status": "completed",
            "node": node_id,
            "message": (
                f"{node_id} "
                f"completed successfully."
            ),
        }

    # ----------------------------------------------------------
    # Create executor
    # ----------------------------------------------------------

    executor = GraphExecutor(
        graph=graph,
        execute_node=fake_execute_node,
        max_workers=3,
        max_retries=2,
    )

    # ----------------------------------------------------------
    # Execute
    # ----------------------------------------------------------

    result = executor.execute()

    # ----------------------------------------------------------
    # Print results
    # ----------------------------------------------------------

    executor.print_results()

    # ----------------------------------------------------------
    # Final result
    # ----------------------------------------------------------

    print(
        "\nFinal Result:"
    )

    print(result)