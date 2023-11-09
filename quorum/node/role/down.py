from __future__ import annotations

import asyncio
import math
import typing

from quorum.cluster.configuration import ClusterConfiguration

if typing.TYPE_CHECKING:
    from quorum.node.node import Node, INode
from quorum.node.role.role import Role
if typing.TYPE_CHECKING:
    from quorum.node.role.type_aliases import UpRole
from quorum.node.role.heartbeat_response import HeartbeatResponse


class Down(Role):
    def __init__(self, previous_role: UpRole) -> None:
        self._previous_role = previous_role
        self._node = previous_role.get_node()

    async def run(self, other_nodes: set[INode], cluster_configuration: ClusterConfiguration) -> None:
        await asyncio.sleep(math.inf)

    def get_node(self) -> Node:
        return self._node

    def heartbeat(self) -> HeartbeatResponse:
        return HeartbeatResponse()

    def stop_running(self) -> None:
        pass

    async def request_vote(self) -> bool:
        return False

    def __str__(self) -> str:
        return 'down'
