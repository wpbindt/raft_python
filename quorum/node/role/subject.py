from __future__ import annotations
import typing
from dataclasses import dataclass

from quorum.cluster.configuration import ClusterConfiguration
from quorum.node.role.down import Down

if typing.TYPE_CHECKING:
    from quorum.node.node import Node
from quorum.node.role.candidate import Candidate
from quorum.node.role.role import Role
from quorum.node.role.heartbeat_response import HeartbeatResponse


@dataclass
class Subject(Role):
    node: Node | None = None
    beaten: bool = False

    async def run(self, other_nodes: set[Node], cluster_configuration: ClusterConfiguration) -> None:
        await cluster_configuration.election_timeout.wait()
        if not self.beaten:
            self.node.change_role(Candidate())

    def set_node(self, node: Node) -> None:
        self.node = node

    def heartbeat(self) -> HeartbeatResponse:
        self.beaten = True

    def stop_running(self) -> None:
        pass

    async def take_down(self) -> None:
        self.node.change_role(Down(self))
