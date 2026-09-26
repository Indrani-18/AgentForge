from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class RetryRecord:
    """
    Stores retry information for one workflow task.
    """

    step: int
    agent: str
    attempts: int = 0
    max_retries: int = 2
    status: str = "pending"
    errors: list = field(default_factory=list)

    def to_dict(self):
        return {
            "step": self.step,
            "agent": self.agent,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "status": self.status,
            "errors": self.errors,
        }


class RetryManager:
    """
    Controls automatic retry behavior for AgentForge tasks.
    """

    DEFAULT_MAX_RETRIES = 2

    def __init__(self, max_retries=None):

        if max_retries is None:
            max_retries = self.DEFAULT_MAX_RETRIES

        self.max_retries = max(
            0,
            int(max_retries)
        )

        self.records: Dict[int, RetryRecord] = {}

    # =========================================================
    # CREATE RECORD
    # =========================================================

    def create_record(
        self,
        step,
        agent
    ):
        """
        Create a retry record for a task.
        """

        record = RetryRecord(
            step=int(step),
            agent=str(agent).upper(),
            max_retries=self.max_retries
        )

        self.records[int(step)] = record

        return record

    # =========================================================
    # GET RECORD
    # =========================================================

    def get_record(self, step):
        """
        Return retry record for a step.
        """

        return self.records.get(
            int(step)
        )

    # =========================================================
    # START ATTEMPT
    # =========================================================

    def start_attempt(
        self,
        step,
        agent
    ):
        """
        Register a new execution attempt.
        """

        record = self.get_record(
            step
        )

        if record is None:

            record = self.create_record(
                step,
                agent
            )

        record.attempts += 1
        record.status = "running"

        return record

    # =========================================================
    # SUCCESS
    # =========================================================

    def mark_success(
        self,
        step
    ):
        """
        Mark a task as successfully completed.
        """

        record = self.get_record(
            step
        )

        if record:

            record.status = "completed"

        return record

    # =========================================================
    # FAILURE
    # =========================================================

    def mark_failure(
        self,
        step,
        error
    ):
        """
        Record a task failure.
        """

        record = self.get_record(
            step
        )

        if record is None:
            return None

        record.errors.append(
            str(error)
        )

        if self.can_retry(step):

            record.status = "retrying"

        else:

            record.status = "failed"

        return record

    # =========================================================
    # CAN RETRY
    # =========================================================

    def can_retry(self, step):
        """
        Determine whether another attempt is allowed.

        max_retries = 2 means:

            Attempt 1
            Attempt 2
            Attempt 3

        In other words, the initial attempt plus
        two retries.
        """

        record = self.get_record(
            step
        )

        if record is None:
            return False

        return (
            record.attempts
            <= record.max_retries
        )

    # =========================================================
    # SHOULD RETRY
    # =========================================================

    def should_retry(self, step):
        """
        Return True when the task should be attempted again.
        """

        record = self.get_record(
            step
        )

        if record is None:
            return False

        return (
            record.status == "retrying"
            and self.can_retry(step)
        )

    # =========================================================
    # MARK BLOCKED
    # =========================================================

    def mark_blocked(
        self,
        step
    ):
        """
        Mark a task as blocked.
        """

        record = self.get_record(
            step
        )

        if record:

            record.status = "blocked"

        return record

    # =========================================================
    # GET ALL RECORDS
    # =========================================================

    def get_all_records(self):
        """
        Return all retry records.
        """

        return {
            step: record.to_dict()
            for step, record
            in self.records.items()
        }

    # =========================================================
    # RESET
    # =========================================================

    def reset(self):
        """
        Clear retry history.
        """

        self.records.clear()

    # =========================================================
    # DISPLAY
    # =========================================================

    def print_status(self):

        print("\n========================================")
        print("RETRY STATUS")
        print("========================================")

        if not self.records:

            print("No retry records.")

            return

        for step, record in self.records.items():

            print(
                f"Step {step} | "
                f"Agent: {record.agent} | "
                f"Attempts: {record.attempts} | "
                f"Status: {record.status}"
            )

            if record.errors:

                for index, error in enumerate(
                    record.errors,
                    start=1
                ):

                    print(
                        f"  Error {index}: {error}"
                    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    manager = RetryManager(
        max_retries=2
    )

    manager.create_record(
        step=1,
        agent="RESEARCH"
    )

    print("Retry Manager Test")
    print("------------------")

    manager.start_attempt(
        step=1,
        agent="RESEARCH"
    )

    manager.mark_failure(
        step=1,
        error="Temporary API error"
    )

    print(
        manager.get_record(1).to_dict()
    )

    manager.start_attempt(
        step=1,
        agent="RESEARCH"
    )

    manager.mark_failure(
        step=1,
        error="Temporary timeout"
    )

    print(
        manager.get_record(1).to_dict()
    )

    manager.start_attempt(
        step=1,
        agent="RESEARCH"
    )

    manager.mark_success(
        step=1
    )

    manager.print_status()