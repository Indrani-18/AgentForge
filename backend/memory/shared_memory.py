from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.models.agent_message import AgentMessage


class SharedWorkingMemory:
    """
    Shared memory used by AgentForge agents during
    a single multi-agent workflow.

    This is different from ConversationMemory.

    ConversationMemory:
        Stores conversation history.

    SharedWorkingMemory:
        Stores information produced during the
        current multi-agent task.
    """

    def __init__(self):
        self.data: Dict[str, Any] = {}

        self.task_results: Dict[int, Dict[str, Any]] = {}

        self.messages: List[Dict[str, Any]] = []

        self.created_at = datetime.now().isoformat()

    # =====================================================
    # GENERAL DATA
    # =====================================================

    def set(self, key: str, value: Any):
        """
        Store a value in shared memory.
        """

        self.data[key] = value

    # -----------------------------------------------------

    def get(
        self,
        key: str,
        default: Optional[Any] = None
    ):
        """
        Retrieve a value from shared memory.
        """

        return self.data.get(key, default)

    # -----------------------------------------------------

    def delete(self, key: str):
        """
        Delete a value from shared memory.
        """

        if key in self.data:
            del self.data[key]

    # =====================================================
    # TASK RESULTS
    # =====================================================

    def save_task_result(
        self,
        step: int,
        agent: str,
        task: str,
        result: Any,
        depends_on: Optional[List[int]] = None,
        status: str = "completed"
    ):
        """
        Store the result of an agent task.
        """

        self.task_results[step] = {
            "step": step,
            "agent": agent,
            "task": task,
            "result": result,
            "depends_on": depends_on or [],
            "status": status,
            "timestamp": datetime.now().isoformat()
        }

    # -----------------------------------------------------

    def get_task_result(self, step: int):
        """
        Retrieve a specific task result.
        """

        return self.task_results.get(step)

    # -----------------------------------------------------

    def get_all_task_results(self):
        """
        Return all task results.
        """

        return list(
            self.task_results.values()
        )

    # -----------------------------------------------------

    def get_dependency_results(
        self,
        dependencies: List[int]
    ):
        """
        Return results required by a task.
        """

        results = []

        for step in dependencies:

            result = self.get_task_result(step)

            if result:
                results.append(result)

        return results

    # =====================================================
    # AGENT MESSAGES
    # =====================================================

    def add_message(
        self,
        message_or_sender,
        receiver: Optional[str] = None,
        task: Optional[str] = None,
        content: Any = None,
        step: Optional[int] = None,
        status: str = "completed",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store a structured message between agents.

        Supports both:

        1. AgentMessage object

        2. Individual message fields
        """

        # -------------------------------------------------
        # If an AgentMessage object is provided
        # -------------------------------------------------

        if isinstance(message_or_sender, AgentMessage):

            message = message_or_sender

        # -------------------------------------------------
        # Otherwise create an AgentMessage
        # -------------------------------------------------

        else:

            message = AgentMessage(
                sender=message_or_sender,
                receiver=receiver or "",
                task=task or "",
                content=content,
                step=step,
                status=status,
                metadata=metadata or {}
            )

        # -------------------------------------------------
        # Store dictionary representation
        # -------------------------------------------------

        message_dict = message.to_dict()

        self.messages.append(
            message_dict
        )

        return message_dict

    # -----------------------------------------------------

    def get_messages(
        self,
        receiver: Optional[str] = None
    ):
        """
        Get agent messages.

        If receiver is provided, return only messages
        intended for that agent.
        """

        if receiver is None:
            return self.messages

        return [
            message
            for message in self.messages
            if message["receiver"] == receiver
        ]

    # -----------------------------------------------------

    def get_messages_by_step(
        self,
        step: int
    ):
        """
        Return messages associated with a specific step.
        """

        return [
            message
            for message in self.messages
            if message.get("step") == step
        ]

    # =====================================================
    # SNAPSHOT
    # =====================================================

    def snapshot(self):
        """
        Return the complete current shared state.
        """

        return {
            "data": self.data,
            "task_results": self.task_results,
            "messages": self.messages,
            "created_at": self.created_at
        }

    # =====================================================
    # CLEAR
    # =====================================================

    def clear(self):
        """
        Clear the current workflow memory.
        """

        self.data.clear()

        self.task_results.clear()

        self.messages.clear()

        self.created_at = datetime.now().isoformat()

    # =====================================================
    # DISPLAY
    # =====================================================

    def print_memory(self):
        """
        Display shared memory for debugging.
        """

        print("\n")
        print("=" * 60)
        print("SHARED WORKING MEMORY")
        print("=" * 60)

        # -------------------------------------------------
        # General Data
        # -------------------------------------------------

        print("\nGeneral Data:")

        if self.data:

            for key, value in self.data.items():
                print(f"{key}: {value}")

        else:
            print("None")

        # -------------------------------------------------
        # Task Results
        # -------------------------------------------------

        print("\nTask Results:")

        if self.task_results:

            for step, result in self.task_results.items():

                print(f"\nStep {step}")

                print(
                    f"Agent: {result['agent']}"
                )

                print(
                    f"Status: {result['status']}"
                )

                print(
                    f"Depends On: {result['depends_on']}"
                )

                print(
                    f"Result: {result['result']}"
                )

        else:
            print("None")

        # -------------------------------------------------
        # Agent Messages
        # -------------------------------------------------

        print("\nAgent Messages:")

        if self.messages:

            for message in self.messages:

                print(
                    f"{message['sender']} "
                    f"→ "
                    f"{message['receiver']}"
                )

                print(
                    f"Task: {message['task']}"
                )

                print(
                    f"Step: {message['step']}"
                )

                print(
                    f"Status: {message['status']}"
                )

                print(
                    f"Content: {message['content']}"
                )

        else:
            print("None")

        print("\n" + "=" * 60)


# =========================================================
# STANDALONE TEST
# =========================================================

if __name__ == "__main__":

    memory = SharedWorkingMemory()

    print("\nShared Working Memory Test")

    # =====================================================
    # GENERAL INFORMATION
    # =====================================================

    memory.set(
        "user_question",
        "Research sorting algorithms and implement one."
    )

    # =====================================================
    # TASK 1
    # =====================================================

    memory.save_task_result(
        step=1,
        agent="RESEARCH",
        task="Research sorting algorithms",
        result=(
            "Merge sort is suitable because of "
            "O(n log n) time complexity."
        ),
        depends_on=[]
    )

    # =====================================================
    # AGENT COMMUNICATION
    # =====================================================

    research_message = AgentMessage(
        sender="RESEARCH",
        receiver="CODING",
        task="Implement the selected algorithm",
        content="Use merge sort.",
        step=2,
        status="completed",
        metadata={
            "source_step": 1
        }
    )

    memory.add_message(
        research_message
    )

    # =====================================================
    # TASK 2
    # =====================================================

    memory.save_task_result(
        step=2,
        agent="CODING",
        task="Implement merge sort",
        result="Python implementation completed.",
        depends_on=[1]
    )

    # =====================================================
    # DISPLAY
    # =====================================================

    memory.print_memory()

    # =====================================================
    # TEST GENERAL DATA
    # =====================================================

    print("\nUser Question:")

    print(
        memory.get("user_question")
    )

    # =====================================================
    # TEST TASK RESULT
    # =====================================================

    print("\nTask 1 Result:")

    print(
        memory.get_task_result(1)
    )

    # =====================================================
    # TEST AGENT MESSAGES
    # =====================================================

    print("\nMessages for CODING:")

    print(
        memory.get_messages("CODING")
    )

    # =====================================================
    # TEST DEPENDENCY RESULTS
    # =====================================================

    print("\nDependency Results for Step 2:")

    print(
        memory.get_dependency_results([1])
    )