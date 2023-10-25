from __future__ import annotations

import asyncio
import math
import typing

from quorum.cluster.configuration import ClusterConfiguration

if typing.TYPE_CHECKING:
    from quorum.node.node import Node
from quorum.node.role.role import Role
if typing.TYPE_CHECKING:
    from quorum.node.role.type_aliases import UpRole
from quorum.node.role.heartbeat_response import HeartbeatResponse


class Down(Role):
    def __init__(self, previous_role: UpRole) -> None:
        self._previous_role = previous_role
        self._node: None | Node = None

    async def run(self, other_nodes: set[Node], cluster_configuration: ClusterConfiguration) -> None:
        await asyncio.sleep(math.inf)

    def set_node(self, node: Node) -> None:
        self._node = node

    def heartbeat(self) -> HeartbeatResponse:
        return HeartbeatResponse()

    def stop_running(self) -> None:
        pass

    async def take_down(self) -> None:
        pass

    async def bring_back_up(self) -> None:
        assert self._node is not None
        self._node.change_role(self._previous_role)
