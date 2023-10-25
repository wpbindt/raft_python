from __future__ import annotations
import typing
from abc import ABC, abstractmethod

from quorum.cluster.configuration import ClusterConfiguration
from quorum.node.role.heartbeat_response import HeartbeatResponse
if typing.TYPE_CHECKING:
    from quorum.node.node import Node


class Role(ABC):
    @abstractmethod
    async def run(self, other_nodes: set[Node], cluster_configuration: ClusterConfiguration) -> None:
        pass

    @abstractmethod
    def set_node(self, node: Node) -> None:
        pass

    @abstractmethod
    def heartbeat(self) -> HeartbeatResponse:
        pass

    @abstractmethod
    def stop_running(self) -> None:
        pass
