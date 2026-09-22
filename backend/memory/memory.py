import json
import os
from datetime import datetime


class ConversationMemory:
    """
    Stores conversation history for AgentForge.

    Features:
    - Add user messages
    - Add assistant messages
    - Retrieve conversation context
    - Clear memory
    - Save memory to JSON
    - Load memory from JSON
    """

    def __init__(self, max_messages=20):
        self.history = []
        self.max_messages = max_messages

    # ========================================================
    # ADD USER MESSAGE
    # ========================================================

    def add_user_message(self, message):

        self.history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

        self._limit_memory()

    # ========================================================
    # ADD ASSISTANT MESSAGE
    # ========================================================

    def add_assistant_message(self, message):

        self.history.append({
            "role": "assistant",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

        self._limit_memory()

    # ========================================================
    # LIMIT MEMORY
    # ========================================================

    def _limit_memory(self):

        if len(self.history) > self.max_messages:

            self.history = self.history[
                -self.max_messages:
            ]

    # ========================================================
    # GET CONTEXT
    # ========================================================

    def get_context(self, limit=10):

        if not self.history:

            return "No previous conversation."

        messages = self.history[-limit:]

        context = []

        for message in messages:

            role = message.get(
                "role",
                "unknown"
            )

            content = message.get(
                "content",
                ""
            )

            if role == "user":

                context.append(
                    f"User: {content}"
                )

            elif role == "assistant":

                context.append(
                    f"Assistant: {content}"
                )

        return "\n\n".join(context)

    # ========================================================
    # GET ALL MESSAGES
    # ========================================================

    def get_history(self):

        return self.history

    # ========================================================
    # MEMORY SIZE
    # ========================================================

    def size(self):

        return len(self.history)

    # ========================================================
    # CHECK IF EMPTY
    # ========================================================

    def is_empty(self):

        return len(self.history) == 0

    # ========================================================
    # CLEAR MEMORY
    # ========================================================

    def clear(self):

        self.history = []

    # ========================================================
    # SAVE MEMORY TO FILE
    # ========================================================

    def save_to_file(
        self,
        file_path="data/memory.json"
    ):

        directory = os.path.dirname(
            file_path
        )

        if directory:

            os.makedirs(
                directory,
                exist_ok=True
            )

        try:

            with open(
                file_path,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    self.history,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

            return True

        except OSError as e:

            print(
                f"Memory save error: {e}"
            )

            return False

    # ========================================================
    # LOAD MEMORY FROM FILE
    # ========================================================

    def load_from_file(
        self,
        file_path="data/memory.json"
    ):

        if not os.path.exists(file_path):

            return False

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if isinstance(data, list):

                self.history = data

                self._limit_memory()

                return True

            return False

        except (
            json.JSONDecodeError,
            OSError
        ) as e:

            print(
                f"Memory load error: {e}"
            )

            self.history = []

            return False


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    memory = ConversationMemory()

    memory.add_user_message(
        "What is artificial intelligence?"
    )

    memory.add_assistant_message(
        "Artificial Intelligence is a field "
        "of computer science."
    )

    print("\nConversation:")
    print(
        memory.get_context()
    )

    memory.save_to_file(
        "data/memory.json"
    )

    print(
        "\nMemory saved successfully."
    )