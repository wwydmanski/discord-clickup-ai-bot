import types
from datetime import datetime
from unittest.mock import AsyncMock, Mock
import asyncio
import types

import bot


class DummyTyping:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass


class DummyChannel:
    def __init__(self):
        self._history = []
        self.name = "general"
    def history(self, limit=20):
        async def generator():
            for msg in self._history:
                yield msg
        return generator()
    def typing(self):
        return DummyTyping()


def test_handle_task_creation_creates_task(monkeypatch):
    bot.bot._connection.user = types.SimpleNamespace(id=42)

    channel = DummyChannel()
    message = types.SimpleNamespace(
        content="<@42> implement feature",
        author=types.SimpleNamespace(display_name="User", name="user", discriminator="0001"),
        channel=channel,
        guild=types.SimpleNamespace(name="Guild"),
        created_at=datetime.utcnow(),
        jump_url="http://discord/message",
    )

    async def reply(embed=None):
        message.replied = embed
    message.reply = reply

    monkeypatch.setattr(bot, "is_task_creation_command", AsyncMock(return_value=False))
    monkeypatch.setattr(bot, "get_channel_context", AsyncMock(return_value=[]))
    monkeypatch.setattr(bot, "filter_relevant_context", AsyncMock(return_value=[]))
    monkeypatch.setattr(bot, "generate_smart_title", AsyncMock(return_value="Test Title"))
    monkeypatch.setattr(bot, "determine_target_list", lambda content: (None, "Backlog"))

    create_mock = Mock(return_value={"id": "1"})
    monkeypatch.setattr(bot.clickup_client, "create_task", create_mock)

    asyncio.run(bot.handle_task_creation(message))

    create_mock.assert_called_once()
    assert hasattr(message, "replied")
    assert message.replied.title.startswith("✅")
