import asyncio
import http
import unittest
from datetime import timedelta

import httpx

from quorum.cluster.configuration import ClusterConfiguration, ElectionTimeout
from quorum.node.node_http_server import NodeServer
from quorum.node.role.candidate import Candidate
from quorum.node.role.leader import Leader
from quorum.node.role.subject import Subject
from tests.fixtures import create_subject_node


class TestNodeServer(unittest.IsolatedAsyncioTestCase):
    def get_cluster_configuration(
        self,
        election_timeout: timedelta = timedelta(seconds=0.1),
    ) -> ClusterConfiguration:
        return ClusterConfiguration(
            election_timeout=ElectionTimeout(max_timeout=election_timeout, min_timeout=election_timeout),
            heartbeat_period=timedelta(seconds=0.01),

        )

    async def test_running_the_app_runs_the_node(self) -> None:
        node = create_subject_node()
        server = NodeServer(node, cluster_configuration=self.get_cluster_configuration())

        server_task = asyncio.create_task(server.run(8080))

        await asyncio.sleep(0.5)

        self.assertIsInstance(node.role, (Candidate, Leader))
        server_task.cancel()

    async def send_heartbeat(self, port: int) -> None:
        async with httpx.AsyncClient() as client:
            await client.post(f'http://localhost:{port}/heartbeat')

    async def test_sending_heartbeat(self) -> None:
        node = create_subject_node()
        server = NodeServer(node, cluster_configuration=self.get_cluster_configuration(election_timeout=timedelta(seconds=0.2)))

        server_task = asyncio.create_task(server.run(8080))
        await asyncio.sleep(2)

        async def send_many_heartbeats() -> None:
            for _ in range(100):
                await self.send_heartbeat(port=8080)
                await asyncio.sleep(0.01)

        heartbeat_task = asyncio.create_task(send_many_heartbeats())

        await asyncio.sleep(0.7)

        self.assertIsInstance(node.role, Subject)

        heartbeat_task.cancel()
        server_task.cancel()
        await asyncio.sleep(2)

    async def request_vote(self, port: int) -> bool:
        async with httpx.AsyncClient() as client:
            response: httpx.Response = await client.post(f'http://localhost:{port}/request_vote')
        response.raise_for_status()
        return response.json()['vote']

    async def test_request_vote(self) -> None:
        node = create_subject_node()
        server = NodeServer(node, cluster_configuration=self.get_cluster_configuration(election_timeout=timedelta(seconds=2)))

        server_task = asyncio.create_task(server.run(8080))

        vote = await self.request_vote(port=8080)

        self.assertTrue(vote)
        server_task.cancel()
        await asyncio.sleep(2)

    async def test_request_vote_when_already_voted(self) -> None:
        node = create_subject_node()
        server = NodeServer(node, cluster_configuration=self.get_cluster_configuration(election_timeout=timedelta(seconds=2)))

        await node.request_vote()
        server_task = asyncio.create_task(server.run(8080))

        vote = await self.request_vote(port=8080)

        self.assertFalse(vote)
        server_task.cancel()
        await asyncio.sleep(2)
