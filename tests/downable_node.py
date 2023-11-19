from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Generic

from quorum.cluster.configuration import ClusterConfiguration
from quorum.cluster.message_type import MessageType
from quorum.node.node import INode, Node
from quorum.node.role.heartbeat_response import HeartbeatResponse
from quorum.node.role.role import Role


class DownableNode(INode[MessageType], Generic[MessageType]):
    def __init__(self, node: Node[MessageType]) -> None:
        self._actual_node = node
        self._down = False

    def _get_id(self) -> int:
        return self._actual_node._get_id()

    def register_node(self, node: INode[MessageType]) -> None:
        self._actual_node.register_node(node)

    async def request_vote(self) -> bool:
        if self._down:
            return False
        return await self._actual_node.request_vote()

    async def heartbeat(self) -> HeartbeatResponse:
        if self._down:
            return HeartbeatResponse()
        return await self._actual_node.heartbeat()

    async def send_message(self, message: MessageType) -> None:
        if self._down:
            await asyncio.sleep(1)
            return
        return await self._actual_node.send_message(message)

    async def get_messages(self) -> tuple[MessageType, ...]:
        if self._down:
            return tuple()
        return await self._actual_node.get_messages()

    @property
    def role(self) -> Role[MessageType] | NodeIsDown:
        if self._down:
            return NodeIsDown()
        return self._actual_node.role

    async def take_down(self) -> None:
        self._down = True
        await self._actual_node.pause()

    async def bring_back_up(self) -> None:
        self._down = False
        await self._actual_node.unpause()

    async def run(self, cluster_configuration: ClusterConfiguration) -> None:
        await self._actual_node.run(cluster_configuration)


@dataclass(frozen=True)
class NodeIsDown:
    pass
