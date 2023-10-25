import asyncio
from dataclasses import dataclass

from quorum.node.role.leader import Leader
from quorum.node.node import Node
from quorum.cluster.configuration import ClusterConfiguration


@dataclass(frozen=True)
class NoLeaderInCluster:
    pass


class Cluster:
    def __init__(
        self,
        nodes: set[Node],
        cluster_configuration: ClusterConfiguration,
    ) -> None:
        self._nodes = nodes
        for node in self._nodes:
            for other_node in self._nodes:
                node.register_node(other_node)
        self._configuration = cluster_configuration

    def take_me_to_a_leader(self) -> Node | NoLeaderInCluster:
        current_leaders = {node for node in self._nodes if isinstance(node.role, Leader)}
        if len(current_leaders) == 0:
            return NoLeaderInCluster()
        if len(current_leaders) > 1:
            raise TooManyLeaders
        return next(iter(current_leaders))

    async def run(self) -> None:
        await asyncio.gather(*[node.run(self._configuration) for node in self._nodes])


class TooManyLeaders(Exception):
    pass
