from __future__ import annotations
import asyncio

import typing

from quorum.cluster.configuration import ClusterConfiguration
from quorum.node.role.down import Down

if typing.TYPE_CHECKING:
    from quorum.node.node import Node
from quorum.node.role.role import Role
from quorum.node.role.heartbeat_response import HeartbeatResponse


class Leader(Role):
    def __init__(self, node: Node) -> None:
        self._stopped = False
        self._node = node

    async def run(self, other_nodes: set[Node], cluster_configuration: ClusterConfiguration) -> None:
        self._stopped = False
        while not self._stopped:
            for node in other_nodes:
                node.heartbeat()
            if self._stopped:
                return
            await asyncio.sleep(cluster_configuration.heartbeat_period.total_seconds())

    def get_node(self) -> Node:
        return self._node

    def heartbeat(self) -> HeartbeatResponse:
        from quorum.node.role.subject import Subject
        self._node.change_role(Subject(self._node))
        return HeartbeatResponse()

    def stop_running(self) -> None:
        self._stopped = True

    async def take_down(self) -> None:
        self._node.change_role(Down(previous_role=self))

    async def bring_back_up(self) -> None:
        pass

    async def request_vote(self) -> bool:
        from quorum.node.role.subject import Subject
        self._node.change_role(Subject(self._node))
        return True

    def __str__(self) -> str:
        return 'leader'
