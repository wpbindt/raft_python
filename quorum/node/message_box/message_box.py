from __future__ import annotations
import asyncio
from typing import Generic, NoReturn

from quorum.cluster.message_type import MessageType
from quorum.node.message_box.distribution_strategy.distribution_strategy import DistributionStrategy, DistributionFailed
from quorum.node.node_interface import InternalNode


class MessageBox(Generic[MessageType]):
    def __init__(self, distribution_strategy: DistributionStrategy[MessageType]):
        self._messages: tuple[MessageType, ...] = tuple()
        self._waiting_messages: asyncio.Queue[MessageType] = asyncio.Queue()
        self.distribution_strategy = distribution_strategy

    async def append(self, message: MessageType) -> None:
        await self._waiting_messages.put(message)

    async def get_messages(self) -> tuple[MessageType, ...]:
        return self._messages

    async def run(self, other_nodes: set[InternalNode[MessageType]]) -> NoReturn:
        while True:
            message = await self._waiting_messages.get()
            response = await self.distribution_strategy.distribute(message, other_nodes)
            if isinstance(response, DistributionFailed):
                continue
            self._messages = (*self._messages, message)
