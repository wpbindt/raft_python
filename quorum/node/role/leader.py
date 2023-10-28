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
    def __init__(self) -> None:
        self._stopped = False
        self._node: None | Node = None

    async def run(self, other_nodes: set[Node], cluster_configuration: ClusterConfiguration) -> None:
        self._stopped = False
        while not self._stopped:
            await asyncio.sleep(cluster_configuration.heartbeat_period.total_seconds())
            if self._stopped:
                return
            for node in other_nodes:
                node.heartbeat()

    def set_node(self, node: Node) -> None:
        self._node = node

    def heartbeat(self) -> HeartbeatResponse:
        return HeartbeatResponse()

    def stop_running(self) -> None:
        self._stopped = True

    async def take_down(self) -> None:
        assert self._node is not None
        self._node.change_role(Down(previous_role=self))

    async def bring_back_up(self) -> None:
        pass

    def __str__(self) -> str:
        return 'leader'
