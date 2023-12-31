from __future__ import annotations

import asyncio
import unittest
from contextlib import suppress
from datetime import timedelta
from typing import Type, Callable

from quorum.cluster.configuration import ElectionTimeout, ClusterConfiguration
from tests.downable_node import DownableNode
from quorum.node.role.candidate import Candidate
from quorum.node.role.leader import Leader
from quorum.node.role.role import Role
from quorum.node.role.subject import Subject
from tests.fixtures import create_downable_subject_node, create_downable_leader_node


class TestNode(unittest.IsolatedAsyncioTestCase):
    def _assert_role_has_type(self, node: DownableNode[str], role_type: Type[Role[str]] | tuple[Type[Role[str]], ...]) -> None:
        self.assertIsInstance(node.role, role_type)

    def assert_is_candidate(self, node: DownableNode[str]) -> None:
        self._assert_role_has_type(node, Candidate)

    def assert_is_subject(self, node: DownableNode[str]) -> None:
        self._assert_role_has_type(node, Subject)

    def assert_is_not_subject(self, node: DownableNode[str]) -> None:
        self._assert_role_has_type(node, (Candidate, Leader))

    def assert_is_leader(self, node: DownableNode[str]) -> None:
        self._assert_role_has_type(node, Leader)

    async def remains_true(self, assertion: Callable[[], None]) -> None:
        for _ in range(100):
            assertion()
            await asyncio.sleep(0.01)

    async def eventually(self, assertion: Callable[[], None], timeout: float = 1) -> None:
        for _ in range(int(34 * timeout)):
            with suppress(AssertionError):
                assertion()
                return
            await asyncio.sleep(0.03)
        assertion()

    async def test_requesting_vote_twice_yields_nay(self) -> None:
        the_node = create_downable_subject_node()

        await the_node.request_vote()
        vote2 = await the_node.request_vote()

        self.assertFalse(vote2)

    async def test_new_heartbeat_means_vote_again(self) -> None:
        the_node = create_downable_subject_node()

        await the_node.request_vote()
        await the_node.heartbeat()
        vote2 = await the_node.request_vote()

        self.assertTrue(vote2)

    async def test_subject_who_feels_no_heartbeat_becomes_leader(self) -> None:
        the_node = create_downable_subject_node()

        asyncio.create_task(the_node.run(
            ClusterConfiguration(
                election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.1), min_timeout=timedelta(seconds=0.05)),
                heartbeat_period=timedelta(seconds=0.01)
            ))
        )

        await self.eventually(lambda: self.assert_is_leader(the_node))

    async def test_subject_who_feels_one_heartbeat_becomes_leader(self) -> None:
        the_node = create_downable_subject_node()

        asyncio.create_task(the_node.run(
            ClusterConfiguration(
                election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.1), min_timeout=timedelta(seconds=0.05)),
                heartbeat_period=timedelta(seconds=0.01)
            ))
        )

        await the_node.heartbeat()

        await self.eventually(lambda: self.assert_is_leader(the_node))

    async def test_subject_who_feels_many_heartbeats_stays_subject(self) -> None:
        the_node = create_downable_subject_node()

        async def many_heartbeats() -> None:
            for _ in range(40):
                await the_node.heartbeat()
                await asyncio.sleep(0.05)
        asyncio.create_task(many_heartbeats())

        asyncio.create_task(the_node.run(
            ClusterConfiguration(
                election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.1), min_timeout=timedelta(seconds=0.05)),
                heartbeat_period=timedelta(seconds=0.01)
            ))
        )

        await self.remains_true(lambda: self.assert_is_subject(the_node))

    async def test_leader_who_feels_heartbeat_steps_down(self) -> None:
        the_node = create_downable_leader_node()

        asyncio.create_task(the_node.run(
            ClusterConfiguration(
                election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.1), min_timeout=timedelta(seconds=0.05)),
                heartbeat_period=timedelta(seconds=0.01)
            ))
        )

        await the_node.heartbeat()

        await self.eventually(lambda: self.assert_is_subject(the_node))

    async def test_leader_who_votes_steps_down(self) -> None:
        the_node = create_downable_leader_node()

        asyncio.create_task(the_node.run(
            ClusterConfiguration(
                election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.1), min_timeout=timedelta(seconds=0.05)),
                heartbeat_period=timedelta(seconds=0.01)
            ))
        )

        await the_node.request_vote()

        self.assert_is_subject(the_node)

    async def test_leaders_stay_leader_when_no_heartbeat(self) -> None:
        the_node = create_downable_leader_node()

        asyncio.create_task(the_node.run(
            ClusterConfiguration(
                election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.01), min_timeout=timedelta(seconds=0.01)),
                heartbeat_period=timedelta(seconds=0.01)
            ))
        )

        await self.remains_true(lambda: self.assert_is_leader(the_node))
