import asyncio
from datetime import timedelta
from typing import Iterable, Callable, Awaitable, Any
import unittest

from quorum.cluster.configuration import ClusterConfiguration, ElectionTimeout
from quorum.node.node import DownableNode, INode, Node
from quorum.node.node_http_client import NodeHttpClient
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

    async def _kill_server(self, server_task: asyncio.Task[Any]) -> None:
        server_task.cancel()
        await asyncio.sleep(1)

    async def start_node_server(
        self,
        node: Node[str],
        election_timeout: timedelta = timedelta(seconds=0.1),
        remote_nodes: Iterable[INode[str]] = tuple(),
    ) -> None:
        server = NodeServer(
            node=node,
            cluster_configuration=self.get_cluster_configuration(election_timeout),
            remote_nodes=remote_nodes
        )
        server_task = asyncio.create_task(server.run(8080))
        await asyncio.sleep(0.5)
        self.addAsyncCleanup(self._kill_server, server_task)

    async def send_heartbeat(self, port: int) -> None:
        client = NodeHttpClient(f'http://localhost:{port}')
        await client.heartbeat()

    async def send_message(self, port: int, message: str) -> None:
        client = NodeHttpClient(f'http://localhost:{port}')
        await client.send_message(message)

    async def request_vote(self, port: int) -> bool:
        client = NodeHttpClient(f'http://localhost:{port}')
        return await client.request_vote()

    async def get_messages(self, port: int) -> tuple[str, ...]:
        client = NodeHttpClient(f'http://localhost:{port}')
        return await client.get_messages()

    async def remains_true(self, assertion: Callable[..., Awaitable[None]], *args: Any) -> None:
        for _ in range(34):
            await assertion(*args)
            await asyncio.sleep(0.03)

    async def test_running_the_app_runs_the_node(self) -> None:
        node = create_subject_node()
        await self.start_node_server(node)

        self.assertIsInstance(node.role, (Candidate, Leader))

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

    async def test_server_registers_remote_nodes_with_local_node(self) -> None:
        subject = create_subject_node()
        leader = create_leader_node()
        election_timeout = timedelta(seconds=0.1)

        await self.start_node_server(node=leader, election_timeout=election_timeout, remote_nodes={subject})

        asyncio.create_task(subject.run(self.get_cluster_configuration(election_timeout)))

        async def assert_subject_still_subject() -> None:
            self.assertIsInstance(subject.role, Subject)

        await self.remains_true(assert_subject_still_subject)
