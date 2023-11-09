from typing import Generic

from quorum.cluster.message_type import MessageType
from quorum.node.message_box.distribution_strategy.distribution_strategy import DistributionStrategy, \
    DistributionSuccessful, DistributionFailed
from quorum.node.node import INode, NodeIsDown


class LeaderDistribution(DistributionStrategy[MessageType], Generic[MessageType]):
    async def distribute(self, message: MessageType, other_nodes: set[INode[MessageType]]) -> DistributionFailed | DistributionSuccessful:
        majority = (len(other_nodes | {self}) // 2) + 1
        up_nodes = {node for node in other_nodes if not isinstance(node.role, NodeIsDown)}
        if len(up_nodes) + 1 < majority:
            return DistributionFailed()
        for node in other_nodes:
            await node.send_message(message)
        return DistributionSuccessful()
