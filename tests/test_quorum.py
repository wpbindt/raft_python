from __future__ import annotations

import asyncio
import unittest
from contextlib import suppress
from datetime import timedelta
from itertools import cycle
from typing import Type, Callable

from quorum.node.role.role import Role
from quorum.node.role.subject import Subject
from quorum.node.role.candidate import Candidate
from quorum.node.role.leader import Leader
from quorum.node.node import Node
from quorum.cluster.configuration import ClusterConfiguration, ElectionTimeout
from quorum.cluster.cluster import NoLeaderInCluster, Cluster, TooManyLeaders


class TestCluster(unittest.IsolatedAsyncioTestCase):
    def _assert_role_has_type(self, node: Node, role_type: Type[Role] | tuple[Type[Role], ...]) -> None:
        self.assertIsInstance(node.role, role_type)

    def assert_is_candidate(self, node: Node) -> None:
        self._assert_role_has_type(node, Candidate)

    def assert_is_subject(self, node: Node) -> None:
        self._assert_role_has_type(node, Subject)

    def assert_is_not_subject(self, node: Node) -> None:
        self._assert_role_has_type(node, (Candidate, Leader))

    def assert_is_leader(self, node: Node) -> None:
        self._assert_role_has_type(node, Leader)

    async def remains_true(self, assertion: Callable[[], None]) -> None:
        for _ in range(34):
            assertion()
            await asyncio.sleep(0.03)

    async def eventually(self, assertion: Callable[[], None]) -> None:
        for _ in range(34):
            with suppress(AssertionError):
                assertion()
                return
            await asyncio.sleep(0.03)
        assertion()

    async def get_cluster(
        self,
        nodes: set[Node],
        election_timeout: ElectionTimeout = ElectionTimeout(timedelta(seconds=1)),
        heartbeat_period: timedelta = timedelta(seconds=1),
    ) -> Cluster:
        cluster = Cluster(
            nodes=nodes,
            cluster_configuration=ClusterConfiguration(
                election_timeout=election_timeout,
                heartbeat_period=heartbeat_period,
            ),
        )
        asyncio.create_task(cluster.run())
        return cluster

    async def test_empty_clusters_have_no_leader(self) -> None:
        cluster = await self.get_cluster(nodes=set())

        assert cluster.take_me_to_a_leader() == NoLeaderInCluster()

    async def test_one_node_one_leader(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = await self.get_cluster({the_node})

        assert cluster.take_me_to_a_leader() == the_node

    async def test_two_nodes_one_leader(self) -> None:
        leader = Node(initial_role=Leader())
        follower = Node(initial_role=Subject())
        cluster = await self.get_cluster({leader, follower})

        assert cluster.take_me_to_a_leader() == leader

    async def test_two_nodes_multiple_leaders(self) -> None:
        leader = Node(initial_role=Leader())
        follower = Node(initial_role=Leader())
        cluster = await self.get_cluster({leader, follower})

        with self.assertRaises(TooManyLeaders):
            assert cluster.take_me_to_a_leader()

    async def test_down_means_not_a_leader(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = await self.get_cluster({the_node})

        await the_node.take_down()

        assert cluster.take_me_to_a_leader() == NoLeaderInCluster()

    async def test_down_then_back_up_means_leader_back(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = await self.get_cluster({the_node})

        await the_node.take_down()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == the_node

    async def test_resurrected_subjects_are_subjects(self) -> None:
        the_node = Node(initial_role=Subject())
        cluster = await self.get_cluster({the_node})

        await the_node.take_down()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == NoLeaderInCluster()

    async def test_down_is_idempotent(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = await self.get_cluster({the_node})

        await the_node.take_down()
        await the_node.take_down()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == the_node, str(cluster.take_me_to_a_leader())

    async def test_up_is_idempotent(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = await self.get_cluster({the_node})

        await the_node.take_down()
        await the_node.bring_back_up()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == the_node

    async def test_non_leader_nodes_announce_candidacy_after_election_timeout_passes(self) -> None:
        the_node = Node(initial_role=Subject())
        await self.get_cluster(
            nodes={the_node},
            election_timeout=ElectionTimeout(timedelta(seconds=0.02)),
        )

        await asyncio.sleep(0.05)

        self.assert_is_not_subject(the_node)

    async def test_leader_nodes_do_not_become_candidates(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = await self.get_cluster(
            nodes={the_node},
            election_timeout=ElectionTimeout(timedelta(seconds=0.02)),
        )

        await asyncio.sleep(0.05)

        assert cluster.take_me_to_a_leader() == the_node

    async def test_candidacy_is_announced_in_random_way(self) -> None:
        the_node = Node(initial_role=Subject())
        await self.get_cluster(
            nodes={the_node},
            election_timeout=ElectionTimeout(
                max_timeout=timedelta(seconds=0.2),
                randomization=(cycle((0.1,)))
            ),
        )

        await asyncio.sleep(0.03)

        self.assert_is_not_subject(the_node)

    async def test_candidacy_is_not_announced_before_min_timeout(self) -> None:
        the_node = Node(initial_role=Subject())
        await self.get_cluster(
            nodes={the_node},
            election_timeout=ElectionTimeout(
                max_timeout=timedelta(seconds=0.33),
                min_timeout=timedelta(seconds=0.33),
                randomization=(cycle((0.1,)))
            ),
        )

        await asyncio.sleep(0.01)

        self.assert_is_subject(the_node)

    async def test_live_leaders_prevent_elections(self) -> None:
        subject = Node(initial_role=Subject())
        leader = Node(initial_role=Leader())
        await self.get_cluster(
            nodes={leader, subject},
            election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.05), min_timeout=timedelta(seconds=0.05)),
            heartbeat_period=timedelta(seconds=0.01),
        )

        await asyncio.sleep(0.1)

        self.assert_is_subject(subject)

    async def test_down_leaders_do_not_prevent_elections(self) -> None:
        subject = Node(initial_role=Subject())
        leader = Node(initial_role=Leader())
        heartbeat = timedelta(seconds=0.03)
        candidacy_timeout = timedelta(seconds=0.05)
        await self.get_cluster(
            nodes={leader, subject},
            election_timeout=ElectionTimeout(max_timeout=candidacy_timeout, min_timeout=candidacy_timeout),
            heartbeat_period=timedelta(seconds=0.05),
        )
        await asyncio.sleep(0.5 * heartbeat.total_seconds())
        await leader.take_down()

        await self.eventually(lambda: self.assert_is_candidate(subject))

    async def test_leader_down_after_first_heartbeat_still_means_election(self) -> None:
        subject = Node(initial_role=Subject())
        leader = Node(initial_role=Leader())
        election_timeout = timedelta(seconds=0.2)
        heartbeat_period = timedelta(seconds=0.1)
        await self.get_cluster(
            nodes={leader, subject},
            election_timeout=ElectionTimeout(max_timeout=election_timeout, min_timeout=election_timeout),
            heartbeat_period=heartbeat_period,
        )
        await asyncio.sleep(heartbeat_period.total_seconds() + 0.05)
        await leader.take_down()

        await self.eventually(lambda: self.assert_is_candidate(subject))

    async def test_that_leaderless_cluster_eventually_has_leader(self) -> None:
        subject = Node(initial_role=Subject())
        election_timeout = timedelta(seconds=0.01)
        await self.get_cluster(
            nodes={subject},
            election_timeout=ElectionTimeout(max_timeout=election_timeout, min_timeout=election_timeout),
        )

        await self.eventually(lambda: self.assert_is_leader(subject))

    async def test_that_leaderless_cluster_eventually_has_exactly_one_leader(self) -> None:
        subjects = {
            Node(initial_role=Subject()),
            Node(initial_role=Subject()),
        }
        cluster = await self.get_cluster(
            nodes=subjects,
            election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.5), min_timeout=timedelta(seconds=0.1)),
            heartbeat_period=timedelta(0.01),
        )

        def assertion() -> None:
            assert cluster.take_me_to_a_leader() in subjects

        await self.eventually(lambda: assertion())
        await self.remains_true(lambda: assertion())

    @unittest.skip
    async def test_that_leaderless_cluster_eventually_has_exactly_one_leader_part_three(self) -> None:
        subjects = {
            Node(initial_role=Subject()),
            Node(initial_role=Subject()),
            Node(initial_role=Subject()),
        }
        cluster = await self.get_cluster(
            nodes=subjects,
            election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.5), min_timeout=timedelta(seconds=0.1)),
            heartbeat_period=timedelta(0.01),
        )

        def assertion() -> None:
            assert cluster.take_me_to_a_leader() in subjects

        await self.eventually(lambda: assertion())
        await self.remains_true(lambda: assertion())
