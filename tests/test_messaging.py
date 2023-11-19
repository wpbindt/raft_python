import asyncio
import unittest
from contextlib import suppress
from datetime import timedelta
from typing import Awaitable, Callable, Any

from quorum.cluster.cluster import Cluster, NoLeaderInCluster
from quorum.cluster.configuration import ElectionTimeout
from quorum.node.node import DownableNode
from tests.fixtures import get_running_cluster, create_downable_leader_node, get_frozen_cluster, create_downable_candidate_node, \
    create_downable_subject_node


class TestMessaging(unittest.IsolatedAsyncioTestCase):
    async def assert_message_in_cluster(self, cluster: Cluster[str], message: str) -> None:
        messages = await cluster.get_messages()
        self.assertIsInstance(messages, tuple)
        assert isinstance(messages, tuple)
        self.assertIn(message, messages)

    async def assert_no_messages_in_cluster(self, cluster: Cluster[str]) -> None:
        messages = await cluster.get_messages()
        assert isinstance(messages, tuple)
        self.assertTupleEqual(messages, tuple())

    async def test_that_no_messages_sent_means_no_messages_returned(self) -> None:
        cluster = await get_running_cluster({create_downable_leader_node()})

        await self.assert_no_messages_in_cluster(cluster)

    async def test_one_message_gets_returned(self) -> None:
        cluster = await get_running_cluster({create_downable_leader_node()})

        await cluster.send_message('Milkshake')

        await self.eventually(self.assert_message_in_cluster, cluster, 'Milkshake')

    async def test_leader_down_means_no_messages(self) -> None:
        node = create_downable_leader_node()
        cluster = await get_running_cluster({node})

        await cluster.send_message('Milkshake')
        await node.take_down()

        self.assertEqual(await cluster.get_messages(), NoLeaderInCluster())

    async def test_non_leader_nodes_do_not_take_messages(self) -> None:
        down_node = create_downable_leader_node()
        await down_node.take_down()
        for node in {create_downable_subject_node(), create_downable_candidate_node(), down_node}:
            with self.subTest(node.role.__class__.__name__):
                cluster = get_frozen_cluster({node})

                await cluster.send_message('Milkshake')

                self.assertEqual(await cluster.get_messages(), NoLeaderInCluster())

    async def test_that_messages_get_distributed_to_other_nodes(self) -> None:
        initial_leader = create_downable_leader_node()
        cluster = await get_running_cluster(
            nodes={
                initial_leader,
                create_downable_subject_node(),
                create_downable_subject_node(),
            },
            election_timeout=ElectionTimeout(min_timeout=timedelta(seconds=0.5), max_timeout=timedelta(seconds=0.8)),
            heartbeat_period=timedelta(seconds=0.01),
        )

        await cluster.send_message('Milkshake')
        await asyncio.sleep(0.1)  # give leader time to distribute message
        await initial_leader.take_down()
        await self.wait_for_leader(cluster)

        await self.eventually(self.assert_message_in_cluster, cluster, 'Milkshake')

    async def test_collective_memory(self) -> None:
        initial_leader = create_downable_leader_node()
        cluster = await get_running_cluster(
            nodes={
                initial_leader,
                create_downable_subject_node(),
                create_downable_subject_node(),
            },
            election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.1), min_timeout=timedelta(seconds=0.1)),
            heartbeat_period=timedelta(seconds=0.01),
        )

        await cluster.send_message('Milkshake')
        await asyncio.sleep(0.1)  # give leader time to distribute message
        await initial_leader.take_down()
        await self.wait_for_leader(cluster)
        await cluster.send_message('Fries')

        await self.eventually(self.assert_message_in_cluster, cluster, 'Milkshake')
        await self.eventually(self.assert_message_in_cluster, cluster, 'Fries')

    async def test_only_remember_messages_when_consensus_reached(self) -> None:
        initial_leader = create_downable_leader_node()
        subject = create_downable_subject_node()
        cluster = await get_running_cluster({
            initial_leader,
            subject,
        })
        await subject.take_down()

        await cluster.send_message('Milkshake')

        await self.remains_true(self.assert_no_messages_in_cluster, cluster)

    async def eventually(self, assertion: Callable[..., Awaitable[None]], *args: Any) -> None:
        for _ in range(34):
            with suppress(AssertionError):
                await assertion(*args)
                return
            await asyncio.sleep(0.03)
        await assertion(*args)

    async def remains_true(self, assertion: Callable[..., Awaitable[None]], *args: Any) -> None:
        for _ in range(34):
            await assertion(*args)
            await asyncio.sleep(0.03)

    async def wait_for_leader(self, cluster: Cluster[str]) -> None:
        for _ in range(50):
            await asyncio.sleep(0.1)
            leader = cluster.take_me_to_a_leader()
            if isinstance(leader, DownableNode):
                return
