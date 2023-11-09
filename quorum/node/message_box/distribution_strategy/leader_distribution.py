from typing import Generic

from quorum.cluster.message_type import MessageType
from quorum.node.node import Node
from quorum.node.message_box.distribution_strategy.distribution_strategy import DistributionStrategy, \
    DistributionSuccessful, DistributionFailed
from quorum.node.role.down import Down


class LeaderDistribution(DistributionStrategy[MessageType], Generic[MessageType]):
    async def distribute(self, message: MessageType, other_nodes: set[Node[MessageType]]) -> DistributionFailed | DistributionSuccessful:
        majority = (len(other_nodes | {self}) // 2) + 1
        up_nodes = {node for node in other_nodes if not isinstance(node.role, Down)}
        if len(up_nodes) + 1 < majority:
            return DistributionFailed()
        for node in other_nodes:
            await node.send_message(message)
        return DistributionSuccessful()