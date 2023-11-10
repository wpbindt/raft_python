import asyncio
from datetime import timedelta

from quorum.cluster.configuration import ClusterConfiguration, ElectionTimeout
from quorum.node.node import Node


class NodeServer:
    def __init__(
        self,
        node: Node[str],
        cluster_configuration: ClusterConfiguration,
    ) -> None:
        self._node = node
        self._cluster_configuration = cluster_configuration

    async def run(self, host: str, port: int) -> None:
        asyncio.create_task(self._node.run(self._cluster_configuration))
