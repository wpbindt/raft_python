import asyncio
import logging
from dataclasses import dataclass
from typing import Generic

from quorum.cluster.message_type import MessageType
from quorum.node.role.leader import Leader
from quorum.node.node import Node
from tests.downable_node import DownableNode
from quorum.cluster.configuration import ClusterConfiguration


@dataclass(frozen=True)
class NoLeaderInCluster:
    pass


class Cluster(Generic[MessageType]):
    def __init__(
        self,
        nodes: set[Node[MessageType]] | set[DownableNode[MessageType]],
        cluster_configuration: ClusterConfiguration,
    ) -> None:
        self._set_up_logger()

        self._configuration = cluster_configuration
        self._nodes: list[Node[MessageType] | DownableNode[MessageType]] = list(nodes)

        self._let_nodes_know_of_each_others_existence()

    def _set_up_logger(self) -> None:
        logger = logging.getLogger()
        if len(logger.handlers) == 0:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s,%(msecs)03d - %(message)s', datefmt='%H:%M:%S'))
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def _let_nodes_know_of_each_others_existence(self) -> None:
        for node in self._nodes:
            for other_node in self._nodes:
                node.register_node(other_node)

    async def send_message(self, message: MessageType) -> None:
        maybe_leader = self.take_me_to_a_leader()
        if isinstance(maybe_leader, NoLeaderInCluster):
            return
        await maybe_leader.send_message(message)

    async def get_messages(self) -> tuple[MessageType, ...] | NoLeaderInCluster:
        maybe_leader = self.take_me_to_a_leader()
        if isinstance(maybe_leader, NoLeaderInCluster):
            return NoLeaderInCluster()
        return await maybe_leader.get_messages()

    def take_me_to_a_leader(self) -> Node[MessageType] | DownableNode[MessageType] | NoLeaderInCluster:
        current_leaders = {node for node in self._nodes if isinstance(node.role, Leader)}
        if len(current_leaders) == 0:
            return NoLeaderInCluster()
        if len(current_leaders) > 1:
            raise TooManyLeaders
        return next(iter(current_leaders))

    async def run(self) -> None:
        await asyncio.gather(*[node.run(self._configuration) for node in self._nodes])

    def __str__(self) -> str:
        lines = [
            'CLUSTER',
            30 * '-',
            *[str(node) for node in self._nodes],
        ]
        return '\n'.join(lines)


class TooManyLeaders(Exception):
    pass
