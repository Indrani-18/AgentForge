from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class AgentMessage:
    """
    Standard message passed between AgentForge agents.
    """

    sender: str
    receiver: str
    task: str

    content: Any = None

    step: Optional[int] = None

    status: str = "completed"

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def to_dict(self):
        """
        Convert the AgentMessage into a dictionary.
        """

        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "task": self.task,
            "content": self.content,
            "step": self.step,
            "status": self.status,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    def __str__(self):
        """
        Human-readable representation of the message.
        """

        return (
            f"[{self.sender} → {self.receiver}] "
            f"{self.task}"
        )


if __name__ == "__main__":
    message = AgentMessage(
        sender="RESEARCH",
        receiver="CODING",
        task="Implement the researched algorithm",
        content="Use merge sort based on the research results.",
        step=2,
        status="completed",
        metadata={
            "source_step": 1,
            "priority": "normal"
        }
    )

    print("AgentMessage Test")
    print("-----------------")
    print(message)
    print()
    print(message.to_dict())