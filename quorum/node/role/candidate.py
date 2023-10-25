from __future__ import annotations

import asyncio
import math
import typing

from quorum.cluster.configuration import ClusterConfiguration
from quorum.node.role.down import Down
from quorum.node.role.leader import Leader

if typing.TYPE_CHECKING:
    from quorum.node.node import Node
from quorum.node.role.role import Role
from quorum.node.role.heartbeat_response import HeartbeatResponse


class Candidate(Role):
    def __init__(self) -> None:
        self._node: None | Node = None

    async def run(self, other_nodes: set[Node], cluster_configuration: ClusterConfiguration) -> None:
        assert self._node is not None
        if len(other_nodes) == 0:
            self._node.change_role(Leader())
            return

        for node in other_nodes:
            if await node.request_vote():
                self._node.change_role(Leader())
                return
        await asyncio.sleep(math.inf)

    def set_node(self, node: Node) -> None:
        self._node = node

    def heartbeat(self) -> HeartbeatResponse:
        return HeartbeatResponse()

    def stop_running(self) -> None:
        pass

    async def take_down(self) -> None:
        assert self._node is not None
        self._node.change_role(Down(previous_role=self))

    async def bring_back_up(self) -> None:
        pass
