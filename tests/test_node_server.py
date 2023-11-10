import asyncio
import unittest
from datetime import timedelta

from quorum.cluster.configuration import ClusterConfiguration, ElectionTimeout
from quorum.node.node_http_server import NodeServer
from quorum.node.role.candidate import Candidate
from quorum.node.role.leader import Leader
from tests.fixtures import create_subject_node


class TestNodeServer(unittest.IsolatedAsyncioTestCase):
    def get_cluster_configuration(self) -> ClusterConfiguration:
        return ClusterConfiguration(
            election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.1), min_timeout=timedelta(seconds=0.1)),
            heartbeat_period=timedelta(seconds=0.01),

        )

    async def test_running_the_app_runs_the_node(self) -> None:
        node = create_subject_node()
        server = NodeServer(node, cluster_configuration=self.get_cluster_configuration())

        server_task = asyncio.create_task(server.run('localhost', 8080))

        await asyncio.sleep(0.5)

        self.assertIsInstance(node.role, (Candidate, Leader))
        server_task.cancel()
        await server_task
