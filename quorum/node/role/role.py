from __future__ import annotations

import typing
from abc import ABC, abstractmethod

from quorum.cluster.configuration import ClusterConfiguration
from quorum.cluster.message_type import MessageType
from quorum.node.role.heartbeat_response import HeartbeatResponse

if typing.TYPE_CHECKING:
    from quorum.node.node import INode
    from quorum.node.message_box.distribution_strategy.distribution_strategy import DistributionStrategy


class Role(ABC, typing.Generic[MessageType]):
    @abstractmethod
    async def run(self, other_nodes: set[INode[MessageType]], cluster_configuration: ClusterConfiguration) -> None:
        pass

    @abstractmethod
    def heartbeat(self) -> HeartbeatResponse:
        pass

    @abstractmethod
    def stop_running(self) -> None:
        pass

    @abstractmethod
    def request_vote(self) -> bool:
        pass

    def get_distribution_strategy(self) -> DistributionStrategy[MessageType]:
        from quorum.node.message_box.distribution_strategy.no_distribution import NoDistribution
        return NoDistribution()
