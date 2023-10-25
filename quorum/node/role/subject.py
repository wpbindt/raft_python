from __future__ import annotations

import typing

from quorum.cluster.configuration import ClusterConfiguration
from quorum.node.role.down import Down

if typing.TYPE_CHECKING:
    from quorum.node.node import Node
from quorum.node.role.candidate import Candidate
from quorum.node.role.role import Role
from quorum.node.role.heartbeat_response import HeartbeatResponse


class Subject(Role):
    def __init__(self) -> None:
        self._node: Node | None = None
        self._beaten = False

    async def run(self, other_nodes: set[Node], cluster_configuration: ClusterConfiguration) -> None:
        await cluster_configuration.election_timeout.wait()
        if not self._beaten:
            self._node.change_role(Candidate())

    def set_node(self, node: Node) -> None:
        self._node = node

    def heartbeat(self) -> HeartbeatResponse:
        self._beaten = True

    def stop_running(self) -> None:
        pass

    async def take_down(self) -> None:
        self._node.change_role(Down(previous_role=self))

    async def bring_back_up(self) -> None:
        pass
