from typing import Generic

from quorum.cluster.message_type import MessageType
from quorum.node.message_box.distribution_strategy.distribution_strategy import DistributionStrategy, \
    DistributionSuccessful
from quorum.node.node_interface import InternalNode


class NoDistribution(DistributionStrategy[MessageType], Generic[MessageType]):
    async def distribute(self, message: MessageType, other_nodes: set[InternalNode[MessageType]]) -> DistributionSuccessful:
        return DistributionSuccessful()
