from __future__ import annotations
import asyncio

import typing

from quorum.cluster.configuration import ClusterConfiguration
from quorum.cluster.message_type import MessageType

if typing.TYPE_CHECKING:
    from quorum.node.node import Node, INode
    from quorum.node.message_box.distribution_strategy.distribution_strategy import DistributionStrategy
from quorum.node.role.role import Role
from quorum.node.role.heartbeat_response import HeartbeatResponse


class Leader(Role[MessageType], typing.Generic[MessageType]):
    def __init__(self, node: Node[MessageType]) -> None:
        self._stopped = False
        self._node = node

    async def run(
        self,
        other_nodes: set[INode[MessageType]],
        cluster_configuration: ClusterConfiguration,
    ) -> None:
        for node in other_nodes:
            if self._stopped:
                return
            await node.heartbeat()
        if self._stopped:
            return
        await asyncio.sleep(cluster_configuration.heartbeat_period.total_seconds())

    def get_node(self) -> Node[MessageType]:
        return self._node

    def heartbeat(self) -> HeartbeatResponse:
        from quorum.node.role.subject import Subject
        self._node.change_role(Subject(self._node))
        return HeartbeatResponse()

    def stop_running(self) -> None:
        self._stopped = True

    def request_vote(self) -> bool:
        from quorum.node.role.subject import Subject
        self._node.change_role(Subject(self._node))
        return True

    def __str__(self) -> str:
        return 'leader'

    def get_distribution_strategy(self) -> DistributionStrategy[MessageType]:
        from quorum.node.message_box.distribution_strategy.leader_distribution import LeaderDistribution
        return LeaderDistribution()
