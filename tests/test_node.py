from __future__ import annotations

import asyncio
import unittest
from contextlib import suppress
from datetime import timedelta
from itertools import cycle
from typing import Type, Callable

from quorum.cluster.cluster import NoLeaderInCluster, TooManyLeaders
from quorum.cluster.configuration import ElectionTimeout
from quorum.node.node import DownableNode
from quorum.node.role.candidate import Candidate
from quorum.node.role.leader import Leader
from quorum.node.role.role import Role
from quorum.node.role.subject import Subject
from tests.fixtures import get_running_cluster, create_subject_node, create_leader_node, create_candidate_node


class TestNode(unittest.IsolatedAsyncioTestCase):
    def _assert_role_has_type(self, node: DownableNode, role_type: Type[Role] | tuple[Type[Role], ...]) -> None:
        self.assertIsInstance(node.role, role_type)

    def assert_is_candidate(self, node: DownableNode) -> None:
        self._assert_role_has_type(node, Candidate)

    def assert_is_subject(self, node: DownableNode) -> None:
        self._assert_role_has_type(node, Subject)

    def assert_is_not_subject(self, node: DownableNode) -> None:
        self._assert_role_has_type(node, (Candidate, Leader))

    def assert_is_leader(self, node: DownableNode) -> None:
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

    async def test_empty_clusters_have_no_leader(self) -> None:
        cluster = await get_running_cluster(nodes=set())

        assert cluster.take_me_to_a_leader() == NoLeaderInCluster()

    async def test_requesting_vote_twice_yields_nay(self) -> None:
        the_node = create_subject_node()

        await the_node.request_vote()
        vote2 = await the_node.request_vote()

        self.assertFalse(vote2)

    async def test_new_heartbeat_means_vote_again(self) -> None:
        the_node = create_subject_node()

        await the_node.request_vote()
        await the_node.heartbeat()
        vote2 = await the_node.request_vote()

        self.assertTrue(vote2)
