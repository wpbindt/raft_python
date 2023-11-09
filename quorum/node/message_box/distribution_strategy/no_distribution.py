from typing import Generic

from quorum.cluster.message_type import MessageType
from quorum.node.node import Node
from quorum.node.message_box.distribution_strategy.distribution_strategy import DistributionStrategy, \
    DistributionSuccessful


class NoDistribution(DistributionStrategy[MessageType], Generic[MessageType]):
    async def distribute(self, message: MessageType, other_nodes: set[Node[MessageType]]) -> DistributionSuccessful:
        return DistributionSuccessful()
