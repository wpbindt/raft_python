from __future__ import annotations

import asyncio
import random
from abc import ABC, abstractmethod
from logging import getLogger
from typing import Callable, Generic

from quorum.cluster.configuration import ClusterConfiguration
from quorum.cluster.message_type import MessageType
from quorum.node.message_box.message_box import MessageBox
from quorum.node.role.down import Down
from quorum.node.role.heartbeat_response import HeartbeatResponse
from quorum.node.role.role import Role


class INode(ABC, Generic[MessageType]):
    @abstractmethod
    async def request_vote(self) -> bool:
        pass

    @abstractmethod
    def heartbeat(self) -> HeartbeatResponse:
        pass

    @abstractmethod
    async def send_message(self, message: MessageType) -> None:
        pass

    @abstractmethod
    async def get_messages(self) -> tuple[MessageType, ...]:
        pass


class Node(INode, Generic[MessageType]):
    def __init__(
        self,
        initial_role: Callable[[Node], Role],
    ) -> None:
        self._id = random.randint(0, 365)
        self._role = initial_role(self)
        self._other_nodes: set[INode] = set()
        self._messages: tuple[MessageType, ...] = tuple()
        self._message_box = MessageBox(
            distribution_strategy=self._role.get_distribution_strategy(),
        )

    def register_node(self, node: INode) -> None:
        if node != self:
            self._log(f'registering {node}')
            self._other_nodes.add(node)

    @property
    def role(self) -> Role:
        return self._role

    def change_role(self, new_role: Role) -> None:
        self._log(f'changing role from {self._role} to {new_role}')
        self._role.stop_running()
        self._role = new_role
        self._message_box.distribution_strategy = new_role.get_distribution_strategy()

    async def take_down(self) -> None:
        self._log('going down')
        await self._role.take_down()

    async def bring_back_up(self) -> None:
        self._log('going back up')
        await self._role.bring_back_up()

    async def request_vote(self) -> bool:
        vote = await self._role.request_vote()
        self._log(f'voting {vote}')
        return vote

    async def run(self, cluster_configuration: ClusterConfiguration) -> None:
        asyncio.create_task(self._message_box.run(self._other_nodes))
        while True:
            self._log('starting new run iteration')
            await self._role.run(
                other_nodes=self._other_nodes,
                cluster_configuration=cluster_configuration,
            )

    def heartbeat(self) -> HeartbeatResponse:
        self._log('receiving heartbeat')
        return self._role.heartbeat()

    def __str__(self) -> str:
        return f'{self._role} {self._id}'

    def _log(self, message: str) -> None:
        full_message = f'{self}: {message}'
        getLogger().debug(full_message)

    async def send_message(self, message: MessageType) -> None:
        if isinstance(self._role, Down):
            return
        await self._message_box.append(message)

    async def get_messages(self) -> tuple[MessageType, ...]:
        return await self._message_box.get_messages()
