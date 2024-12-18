from __future__ import annotations

import asyncio
import random
from logging import getLogger
from typing import Callable, Generic

from quorum.cluster.configuration import ClusterConfiguration
from quorum.cluster.message_type import MessageType
from quorum.node.message_box.message_box import MessageBox
from quorum.node.node_interface import InternalNode
from quorum.node.role.heartbeat_response import HeartbeatResponse
from quorum.node.role.role import Role


class Node(InternalNode[MessageType], Generic[MessageType]):
    def __init__(
        self,
        initial_role: Callable[[Node[MessageType]], Role[MessageType]],
    ) -> None:
        self._running_task_lock = asyncio.Lock()
        self._id = random.randint(0, 365)
        self._role = initial_role(self)
        self._other_nodes: set[InternalNode[MessageType]] = set()
        self._messages: tuple[MessageType, ...] = tuple()
        self._message_box = MessageBox(
            distribution_strategy=self._role.get_distribution_strategy(),
        )

    def _get_id(self) -> int:
        return self._id

    def register_node(self, node: InternalNode[MessageType]) -> None:
        if node != self:
            self._log(f'registering {node}')
            self._other_nodes.add(node)

    @property
    def role(self) -> Role[MessageType]:
        return self._role

    def change_role(self, new_role: Role[MessageType]) -> None:
        self._log(f'changing role from {self._role} to {new_role}')
        self._role.stop_running()
        self._role = new_role
        self._message_box.distribution_strategy = new_role.get_distribution_strategy()

    async def pause(self) -> None:
        self._log('going down')
        await self._running_task_lock.acquire()

    async def unpause(self) -> None:
        self._log('going back up')
        self._running_task_lock.release()

    async def request_vote(self) -> bool:
        vote = self._role.request_vote()
        self._log(f'voting {vote}')
        return vote

    async def run(self, cluster_configuration: ClusterConfiguration) -> None:
        asyncio.create_task(self._message_box.run(self._other_nodes))
        while True:
            async with self._running_task_lock:
                self._log('starting new run iteration')
                await self._role.run(
                    other_nodes=self._other_nodes,
                    cluster_configuration=cluster_configuration,
                )

    async def heartbeat(self) -> HeartbeatResponse:
        self._log('receiving heartbeat')
        return self._role.heartbeat()

    def __str__(self) -> str:
        return f'{self._role} {self._id}'

    def _log(self, message: str) -> None:
        full_message = f'{self}: {message}'
        getLogger().debug(full_message)

    async def send_message(self, message: MessageType) -> None:
        await self._message_box.append(message)

    async def get_messages(self) -> tuple[MessageType, ...]:
        return await self._message_box.get_messages()
