"""
Conversation history manager for FightPlan AI.
Stores the last 3 exchanges to provide context to the LLM.
"""

from typing import List, Dict


class ConversationHistory:
    """Manages a rolling window of the last 3 conversation exchanges."""

    MAX_EXCHANGES = 3

    def __init__(self):
        self._messages: List[Dict[str, str]] = []

    def add(self, role: str, content: str) -> None:
        """Add a message to the history.

        Args:
            role: Either "user" or "assistant".
            content: The message text.
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Invalid role '{role}'. Must be 'user' or 'assistant'.")

        self._messages.append({"role": role, "content": content})

        # Keep only the last MAX_EXCHANGES * 2 messages (each exchange = user + assistant)
        max_messages = self.MAX_EXCHANGES * 2
        if len(self._messages) > max_messages:
            self._messages = self._messages[-max_messages:]

    def get_formatted(self) -> str:
        """Return history formatted as a string for prompt injection.

        Returns:
            Formatted string like:
            "Previous exchanges:
            User: ...
            Assistant: ...
            "
        """
        if not self._messages:
            return ""

        lines = ["Previous exchanges:"]
        for msg in self._messages:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role_label}: {msg['content']}")

        return "\n".join(lines) + "\n"

    def get_messages(self) -> List[Dict[str, str]]:
        """Return the raw list of message dicts.

        Returns:
            List of {"role": str, "content": str} dicts.
        """
        return list(self._messages)

    def clear(self) -> None:
        """Clear all conversation history."""
        self._messages = []

    def __len__(self) -> int:
        return len(self._messages)

    def __repr__(self) -> str:
        return f"ConversationHistory({len(self._messages)} messages)"
