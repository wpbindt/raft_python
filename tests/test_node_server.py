import asyncio
import unittest
from datetime import timedelta

import aiohttp

from quorum.cluster.configuration import ClusterConfiguration, ElectionTimeout
from quorum.node.node import DownableNode
from quorum.node.node_http_server import NodeServer
from quorum.node.role.candidate import Candidate
from quorum.node.role.leader import Leader
from quorum.node.role.subject import Subject
from tests.fixtures import create_subject_node, create_leader_node


class TestNodeServer(unittest.IsolatedAsyncioTestCase):
    def get_cluster_configuration(
        self,
        election_timeout: timedelta,
    ) -> ClusterConfiguration:
        return ClusterConfiguration(
            election_timeout=ElectionTimeout(max_timeout=election_timeout, min_timeout=election_timeout),
            heartbeat_period=timedelta(seconds=0.01),
        )

    async def _kill_server(self, server_task: asyncio.Task) -> None:
        server_task.cancel()
        await asyncio.sleep(1)

    async def start_node_server(self, node: DownableNode, election_timeout: timedelta = timedelta(seconds=0.1)) -> None:
        server = NodeServer(node, cluster_configuration=self.get_cluster_configuration(election_timeout))
        server_task = asyncio.create_task(server.run(8080))
        await asyncio.sleep(0.5)
        self.addAsyncCleanup(self._kill_server, server_task)

    async def test_running_the_app_runs_the_node(self) -> None:
        node = create_subject_node()
        await self.start_node_server(node)

        self.assertIsInstance(node.role, (Candidate, Leader))

    async def send_heartbeat(self, port: int) -> None:
        async with aiohttp.ClientSession() as client:
            await client.post(f'http://localhost:{port}/heartbeat')

    async def send_message(self, port: int, message: str) -> None:
        async with aiohttp.ClientSession() as client:
            response = await client.post(
                f'http://localhost:{port}/send_message',
                json={'message': message},
                headers={'Content-Type': 'application/json'},
            )
            response.raise_for_status()

    async def test_sending_heartbeat(self) -> None:
        node = create_subject_node()
        await self.start_node_server(node)

        async def send_many_heartbeats() -> None:
            for _ in range(100):
                await self.send_heartbeat(port=8080)
                await asyncio.sleep(0.01)

        heartbeat_task = asyncio.create_task(send_many_heartbeats())

        await asyncio.sleep(0.7)

        self.assertIsInstance(node.role, Subject)

        heartbeat_task.cancel()

    async def request_vote(self, port: int) -> bool:
        async with aiohttp.ClientSession() as client:
            response = await client.post(f'http://localhost:{port}/request_vote')
            response.raise_for_status()
            response_data = await response.json()
        return response_data['vote']

    async def test_request_vote(self) -> None:
        node = create_subject_node()
        await self.start_node_server(node)

        vote = await self.request_vote(port=8080)

        self.assertTrue(vote)

    async def test_request_vote_when_already_voted(self) -> None:
        node = create_subject_node()
        await self.start_node_server(node, election_timeout=timedelta(seconds=2))

        await node.request_vote()

        vote = await self.request_vote(port=8080)

        self.assertFalse(vote)

    async def test_send_and_get_messages(self) -> None:
        node = create_leader_node()

        await self.start_node_server(node)

        await self.send_message(8080, 'hi')
        await asyncio.sleep(0.5)
        messages = await self.get_messages(8080)

        self.assertTupleEqual(messages, ('hi',))

    async def get_messages(self, port: int) -> tuple[str, ...]:
        async with aiohttp.ClientSession() as client:
            response = await client.get(f'http://localhost:{port}/get_messages')
            response.raise_for_status()
            response_data = await response.json()
        return tuple(response_data['messages'])

    async def test_multiple_nodes(self) -> None:
        self.fail()
