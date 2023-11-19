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
from tests.fixtures import get_running_cluster, create_downable_subject_node, create_downable_leader_node, create_downable_candidate_node


class TestCluster(unittest.IsolatedAsyncioTestCase):
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

    async def test_empty_clusters_have_no_leader(self) -> None:
        cluster = await get_running_cluster(nodes=set())

        assert cluster.take_me_to_a_leader() == NoLeaderInCluster()

    async def test_one_node_one_leader(self) -> None:
        the_node = create_downable_leader_node()
        cluster = await get_running_cluster({the_node})

        assert cluster.take_me_to_a_leader() == the_node

    async def test_two_nodes_one_leader(self) -> None:
        leader = create_downable_leader_node()
        follower = create_downable_subject_node()
        cluster = await get_running_cluster({leader, follower})

        assert cluster.take_me_to_a_leader() == leader

    async def test_two_nodes_multiple_leaders(self) -> None:
        leader = create_downable_leader_node()
        follower = create_downable_leader_node()
        cluster = await get_running_cluster({leader, follower})

        with self.assertRaises(TooManyLeaders):
            assert cluster.take_me_to_a_leader()

    async def test_down_then_back_up_means_leader_back(self) -> None:
        the_node = create_downable_leader_node()
        cluster = await get_running_cluster({the_node})

        await the_node.take_down()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == the_node

    async def test_resurrected_subjects_are_subjects(self) -> None:
        the_node = create_downable_subject_node()
        cluster = await get_running_cluster({the_node})

        await the_node.take_down()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == NoLeaderInCluster()

    async def test_non_leader_nodes_announce_candidacy_after_election_timeout_passes(self) -> None:
        the_node = create_downable_subject_node()
        await get_running_cluster(
            nodes={the_node},
            election_timeout=ElectionTimeout(timedelta(seconds=0.02)),
        )

        await asyncio.sleep(0.05)

        self.assert_is_not_subject(the_node)

    async def test_candidacy_is_announced_in_random_way(self) -> None:
        the_node = create_downable_subject_node()
        await get_running_cluster(
            nodes={the_node},
            election_timeout=ElectionTimeout(
                max_timeout=timedelta(seconds=1),
                randomization=(cycle((0.01,)))
            ),
        )

        await asyncio.sleep(0.03)

        self.assert_is_not_subject(the_node)

    async def test_candidacy_is_not_announced_before_min_timeout(self) -> None:
        the_node = create_downable_subject_node()
        await get_running_cluster(
            nodes={the_node},
            election_timeout=ElectionTimeout(
                max_timeout=timedelta(seconds=0.33),
                min_timeout=timedelta(seconds=0.33),
                randomization=(cycle((0.1,)))
            ),
        )

        await asyncio.sleep(0.01)

        self.assert_is_subject(the_node)

    async def test_down_leaders_do_not_prevent_elections(self) -> None:
        subject_1 = create_downable_subject_node()
        subject_2 = create_downable_subject_node()
        leader = create_downable_leader_node()
        heartbeat = timedelta(seconds=0.03)
        candidacy_timeout = timedelta(seconds=0.06)
        candidacy_timeout_min = timedelta(seconds=0.04)
        await get_running_cluster(
            nodes={leader, subject_1, subject_2},
            election_timeout=ElectionTimeout(
                max_timeout=candidacy_timeout,
                min_timeout=candidacy_timeout_min,
                randomization=cycle([0, 1]),
            ),
            heartbeat_period=timedelta(seconds=0.05),
        )
        await asyncio.sleep(0.5 * heartbeat.total_seconds())
        await leader.take_down()

        def assertion() -> None:
            node_roles = {type(subject_1.role), type(subject_2.role)}
            self.assertIn(Leader, node_roles)

        await self.eventually(assertion)

    async def test_that_leaderless_cluster_eventually_has_leader(self) -> None:
        subject = create_downable_subject_node()
        election_timeout = timedelta(seconds=0.01)
        await get_running_cluster(
            nodes={subject},
            election_timeout=ElectionTimeout(max_timeout=election_timeout, min_timeout=election_timeout),
        )

        await self.eventually(lambda: self.assert_is_leader(subject))

    async def test_that_leaderless_cluster_eventually_has_exactly_one_leader(self) -> None:
        subjects = {
            create_downable_subject_node(),
            create_downable_subject_node(),
        }
        cluster = await get_running_cluster(
            nodes=subjects,
            election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.5), min_timeout=timedelta(seconds=0.1)),
            heartbeat_period=timedelta(seconds=0.01),
        )

        def assertion() -> None:
            assert cluster.take_me_to_a_leader() in subjects

        await self.eventually(lambda: assertion())
        await self.remains_true(lambda: assertion())

    async def test_that_a_leaderless_cluster_will_never_have_more_than_one_leader(self) -> None:
        nodes = {create_downable_subject_node() for _ in range(3)}
        await get_running_cluster(
            nodes=nodes,
            election_timeout=ElectionTimeout(
                max_timeout=timedelta(seconds=0.2),
                min_timeout=timedelta(seconds=0.2)
            ),
            heartbeat_period=timedelta(seconds=0.03),
        )

        def assertion() -> None:
            leaders = {node for node in nodes if isinstance(node.role, Leader)}
            self.assertLessEqual(len(leaders), 1)

        await self.remains_true(assertion)

    async def test_that_with_majority_down_no_leader_is_elected(self) -> None:
        live_nodes = {
            create_downable_subject_node(),
            create_downable_subject_node(),
        }
        dead_nodes = {
            create_downable_subject_node(),
            create_downable_subject_node(),
            create_downable_leader_node(),
        }
        await get_running_cluster(
            nodes=dead_nodes | live_nodes,
            election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.1)),
        )
        for dead_node in dead_nodes:
            await dead_node.take_down()

        def assertion() -> None:
            leaders = {node for node in live_nodes if isinstance(node.role, Leader)}
            self.assertEqual(len(leaders), 0)

        await self.remains_true(assertion)

    async def test_that_all_candidates_eventually_stabilizes_to_one_leader(self) -> None:
        nodes = {create_downable_candidate_node() for _ in range(3)}
        await get_running_cluster(
            nodes=nodes,
            election_timeout=ElectionTimeout(
                max_timeout=timedelta(seconds=0.3),
                min_timeout=timedelta(seconds=0.2)
            ),
            heartbeat_period=timedelta(seconds=0.03),
        )

        def assertion() -> None:
            subjects = {node for node in nodes if isinstance(node.role, Subject)}
            leaders = {node for node in nodes if isinstance(node.role, Leader)}
            self.assertEqual(len(leaders), 1)
            self.assertEqual(len(subjects), 2)

        await self.eventually(assertion)
