from __future__ import annotations
import asyncio
import math
from dataclasses import dataclass
import typing

from quorum.cluster.configuration import ClusterConfiguration
if typing.TYPE_CHECKING:
    from quorum.node.node import Node
from quorum.node.role.role import Role
from quorum.node.role.heartbeat_response import HeartbeatResponse


@dataclass(frozen=True)
class Candidate(Role):
    async def run(self, other_nodes: set[Node], cluster_configuration: ClusterConfiguration) -> None:
        await asyncio.sleep(math.inf)

    def set_node(self, node: Node) -> None:
        pass

    def heartbeat(self) -> HeartbeatResponse:
        pass

    def stop_running(self) -> None:
        pass
