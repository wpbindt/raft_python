import asyncio
from typing import Generic

from quorum.cluster.message_type import MessageType
from quorum.node.message_box.distribution_strategy.distribution_strategy import DistributionStrategy, \
    DistributionSuccessful, DistributionFailed
from quorum.node.node import INode, NodeIsDown


class LeaderDistribution(DistributionStrategy[MessageType], Generic[MessageType]):
    async def distribute(self, message: MessageType, other_nodes: set[INode[MessageType]]) -> DistributionFailed | DistributionSuccessful:
        majority = (len(other_nodes | {self}) // 2) + 1
        message_sending_tasks = asyncio.as_completed(
            {node.send_message(message) for node in other_nodes},
            timeout=0.5,
        )
        for message_sent, _ in zip(message_sending_tasks, range(majority - 1)):
            try:
                await message_sent
            except asyncio.TimeoutError:
                return DistributionFailed()
        return DistributionSuccessful()
